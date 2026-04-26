"""
Visualizer: produces animated GIF/MP4 and statistics charts.

Draws the road network as a directed graph and animates vehicles moving
along edges, with different colors per destination.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
import numpy as np


class Visualizer:
    """
    Render a traffic simulation into an animation and statistics figure.

    Parameters
    ----------
    engine          : SimulationEngine
    node_positions  : dict {node_id: (x, y)}
    node_types      : dict {node_id: 'junction'|'source'|'sink'}
    dest_colors     : dict {destination_id: color_hex}
    title           : str
    """

    def __init__(self, engine, node_positions: dict, node_types: dict,
                 dest_colors: dict, title: str = "Traffic Simulator"):
        self.engine = engine
        self.node_pos = node_positions
        self.node_types = node_types
        self.dest_colors = dest_colors
        self.title = title

        self.fig = None
        self.ax_net = None

    def _draw_network_background(self, ax):
        """Draw roads and nodes once as background."""
        ax.set_facecolor("#1a1a2e")

        # Draw roads (arrows)
        for road_id, road in self.engine.roads.items():
            if road.start not in self.node_pos or road.end not in self.node_pos:
                continue
            x0, y0 = self.node_pos[road.start]
            x1, y1 = self.node_pos[road.end]

            # offset for bidirectional roads
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            perp_x, perp_y = -dy / length * 0.04, dx / length * 0.04

            ax.annotate("",
                xy=(x1 + perp_x, y1 + perp_y),
                xytext=(x0 + perp_x, y0 + perp_y),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color="#4a9eff",
                    lw=1.8,
                    mutation_scale=14,
                    alpha=0.6,
                ),
            )
            # road label
            mx, my = (x0 + x1) / 2 + perp_x * 3, (y0 + y1) / 2 + perp_y * 3
            ax.text(mx, my, road_id, fontsize=5, color="#6a9fd8", ha="center",
                    va="center", alpha=0.7)

        # Draw nodes
        for node_id, (x, y) in self.node_pos.items():
            ntype = self.node_types.get(node_id, "junction")
            if ntype == "source":
                marker, color, size, zorder = "D", "#00ff88", 160, 5
            elif ntype == "sink":
                marker, color, size, zorder = "s", "#ff4466", 160, 5
            else:
                marker, color, size, zorder = "o", "#e0e0ff", 120, 5

            ax.scatter([x], [y], s=size, c=color, marker=marker,
                       zorder=zorder, edgecolors="white", linewidths=0.8)
            ax.text(x, y + 0.07, node_id, fontsize=7, color="white",
                    ha="center", va="bottom", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=2, foreground="black")])

    def _vehicle_xy(self, v_info: dict) -> tuple:
        """Compute (x, y) for a vehicle given road + progress."""
        road_id = v_info["road"]
        road = self.engine.roads.get(road_id)
        if road is None:
            return None, None
        start = self.node_pos.get(road.start)
        end = self.node_pos.get(road.end)
        if start is None or end is None:
            return None, None

        p = v_info["progress"]
        x = start[0] + (end[0] - start[0]) * p
        y = start[1] + (end[1] - start[1]) * p

        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length > 0:
            x += -dy / length * 0.04
            y += dx / length * 0.04

        if v_info.get("in_queue"):
            qp = v_info.get("queue_pos", 0)
            x -= dx / length * 0.03 * qp
            y -= dy / length * 0.03 * qp

        return x, y

    def animate(self, output_path: str = "simulation.gif",
                fps: int = 8, skip: int = 1):
        """
        Create animation.

        Parameters
        ----------
        output_path : path ending in .gif or .mp4
        fps         : frames per second
        skip        : render every `skip`-th frame
        """
        frames = self.engine.frames[::skip]

        fig, axes = plt.subplots(1, 2, figsize=(14, 7),
                                  gridspec_kw={"width_ratios": [2, 1]})
        fig.patch.set_facecolor("#0d0d1f")
        ax_net, ax_stats = axes

        ax_net.set_facecolor("#1a1a2e")
        ax_stats.set_facecolor("#1a1a2e")
        for spine in ax_net.spines.values():
            spine.set_color("#334466")
        for spine in ax_stats.spines.values():
            spine.set_color("#334466")

        # compute bounds
        xs = [p[0] for p in self.node_pos.values()]
        ys = [p[1] for p in self.node_pos.values()]
        pad = 0.3
        ax_net.set_xlim(min(xs) - pad, max(xs) + pad)
        ax_net.set_ylim(min(ys) - pad, max(ys) + pad)
        ax_net.set_aspect("equal")
        ax_net.tick_params(colors="#6688aa")
        ax_net.set_title(self.title, color="white", fontsize=11, fontweight="bold")

        # draw static network
        self._draw_network_background(ax_net)

        # legend
        legend_patches = [
            mpatches.Patch(color="#00ff88", label="Source"),
            mpatches.Patch(color="#ff4466", label="Sink"),
            mpatches.Patch(color="#e0e0ff", label="Junction"),
        ]
        for dest, col in self.dest_colors.items():
            legend_patches.append(mpatches.Patch(color=col, label=f"→{dest}"))
        ax_net.legend(handles=legend_patches, loc="lower left",
                      facecolor="#1a1a2e", edgecolor="#334466",
                      labelcolor="white", fontsize=7)

        # vehicle scatter (updated each frame)
        veh_scatter = ax_net.scatter([], [], s=28, zorder=10, linewidths=0.4,
                                      edgecolors="white")

        # stats panel
        steps_so_far = [f["step"] for f in frames]
        max_step = max(steps_so_far) if steps_so_far else 1

        ax_stats.set_xlim(0, max_step)
        ax_stats.set_ylim(0, max(max(self.engine._queue_per_step or [1]), 1) * 1.2)
        ax_stats.set_xlabel("Time Step", color="#99aacc", fontsize=8)
        ax_stats.set_ylabel("Count", color="#99aacc", fontsize=8)
        ax_stats.tick_params(colors="#6688aa", labelsize=7)
        ax_stats.set_title("Live Statistics", color="white", fontsize=9)
        ax_stats.grid(alpha=0.2, color="#334466")

        queue_line, = ax_stats.plot([], [], color="#ffaa00", lw=1.5,
                                     label="Total Queue")
        absorb_line, = ax_stats.plot([], [], color="#00ccff", lw=1.5,
                                      label="Absorbed")
        ax_stats.legend(facecolor="#1a1a2e", edgecolor="#334466",
                        labelcolor="white", fontsize=7)

        step_text = ax_net.text(0.02, 0.97, "", transform=ax_net.transAxes,
                                color="white", fontsize=9, va="top",
                                fontfamily="monospace")

        q_hist, a_hist, s_hist = [], [], []

        def update(frame_idx):
            frame = frames[frame_idx]
            step = frame["step"]

            # vehicle positions & colors
            xs_v, ys_v, colors_v = [], [], []
            for v in frame["vehicles"]:
                x, y = self._vehicle_xy(v)
                if x is not None:
                    xs_v.append(x)
                    ys_v.append(y)
                    colors_v.append(v["color"])

            if xs_v:
                veh_scatter.set_offsets(np.column_stack([xs_v, ys_v]))
                veh_scatter.set_facecolor(colors_v)
            else:
                veh_scatter.set_offsets(np.empty((0, 2)))

            # stats lines
            q = self.engine._queue_per_step[min(step, len(self.engine._queue_per_step) - 1)]
            a = frame["total_absorbed"]
            q_hist.append(q)
            a_hist.append(a)
            s_hist.append(step)

            queue_line.set_data(s_hist, q_hist)
            absorb_line.set_data(s_hist, a_hist)
            ax_stats.set_ylim(0, max(q_hist + a_hist + [1]) * 1.2)

            step_text.set_text(
                f"Step: {step:4d} | Active: {frame['active_count']:3d} | "
                f"Absorbed: {frame['total_absorbed']:4d}"
            )
            return veh_scatter, queue_line, absorb_line, step_text

        anim = FuncAnimation(fig, update, frames=len(frames),
                              interval=1000 // fps, blit=True)

        plt.tight_layout()

        if output_path.endswith(".mp4"):
            try:
                writer = FFMpegWriter(fps=fps)
                anim.save(output_path, writer=writer)
            except Exception:
                gif_path = output_path.replace(".mp4", ".gif")
                print(f"ffmpeg not available, saving as {gif_path}")
                anim.save(gif_path, writer=PillowWriter(fps=fps))
                output_path = gif_path
        else:
            anim.save(output_path, writer=PillowWriter(fps=fps))

        plt.close(fig)
        print(f"Animation saved → {output_path}")
        return output_path

    # ------------------------------------------------------------------
    # Statistics figure
    # ------------------------------------------------------------------

    def plot_statistics(self, stats: dict, output_path: str = "statistics.png"):
        """Save a multi-panel statistics figure."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.patch.set_facecolor("#0d0d1f")
        fig.suptitle(f"{self.title} — Statistics", color="white",
                     fontsize=13, fontweight="bold")

        panel_style = dict(facecolor="#1a1a2e")
        tick_style = dict(colors="#6688aa", labelsize=8)
        label_style = dict(color="#99aacc", fontsize=9)

        steps = range(len(stats["throughput_per_step"]))

        # 1. Throughput per step
        ax = axes[0][0]
        ax.set(**panel_style)
        ax.tick_params(**tick_style)
        ax.plot(steps, stats["throughput_per_step"], color="#00ccff", lw=1.2)
        ax.fill_between(steps, stats["throughput_per_step"], alpha=0.15, color="#00ccff")
        ax.set_title("Throughput (vehicles/step)", color="white", fontsize=9)
        ax.set_xlabel("Step", **label_style)
        ax.grid(alpha=0.2, color="#334466")
        for spine in ax.spines.values():
            spine.set_color("#334466")

        # 2. Queue length over time
        ax = axes[0][1]
        ax.set(**panel_style)
        ax.tick_params(**tick_style)
        ax.plot(steps, stats["queue_per_step"], color="#ffaa00", lw=1.2)
        ax.fill_between(steps, stats["queue_per_step"], alpha=0.15, color="#ffaa00")
        ax.set_title("Total Queue Length", color="white", fontsize=9)
        ax.set_xlabel("Step", **label_style)
        ax.grid(alpha=0.2, color="#334466")
        for spine in ax.spines.values():
            spine.set_color("#334466")

        # 3. Per-road vehicle counts (bar)
        ax = axes[1][0]
        ax.set(**panel_style)
        ax.tick_params(**tick_style)
        road_ids = list(stats["per_road"].keys())
        counts = [stats["per_road"][r]["total_vehicles"] for r in road_ids]
        bars = ax.bar(road_ids, counts, color="#5577ff", edgecolor="#334466")
        ax.set_title("Vehicles per Road (total)", color="white", fontsize=9)
        ax.set_xlabel("Road", **label_style)
        for spine in ax.spines.values():
            spine.set_color("#334466")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=6)

        # 4. Summary text
        ax = axes[1][1]
        ax.set(**panel_style)
        ax.axis("off")
        summary = (
            f"Simulation Steps:    {stats['total_steps']}\n"
            f"Vehicles Spawned:    {stats['total_spawned']}\n"
            f"Vehicles Absorbed:   {stats['total_absorbed']}\n"
            f"Still in Network:    {stats['vehicles_in_network']}\n\n"
            f"Avg Travel Time:     {stats['avg_travel_time']:.1f} steps\n"
            f"Min Travel Time:     {stats['min_travel_time']} steps\n"
            f"Max Travel Time:     {stats['max_travel_time']} steps\n\n"
            f"Avg Queue Length:    {stats['avg_queue_length']:.2f}\n"
            f"Peak Queue Length:   {stats['peak_queue_length']}\n\n"
            "Per Sink:\n"
        )
        for sid, s in stats["per_sink"].items():
            summary += f"  {sid}: {s['absorbed']} absorbed, avg={s['avg_travel_time']:.1f}\n"

        ax.text(0.05, 0.95, summary, transform=ax.transAxes,
                color="white", fontsize=8.5, va="top", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="#0d1f33", edgecolor="#334466"))
        ax.set_title("Summary", color="white", fontsize=9)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor="#0d0d1f")
        plt.close(fig)
        print(f"Statistics saved → {output_path}")
