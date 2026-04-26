"""
main.py - Traffic Simulator Entry Point
========================================
Defines a planar road network with 7 junctions, 2 sources, 3 sinks,
and 16 directional roads. Runs the simulation and produces:
  - simulation.gif  (animation)
  - statistics.png  (statistics charts)
  - statistics.txt  (text report)

Usage:
    python3 main.py
"""

import json
from traffic_sim import Road, Junction, Vehicle, TrafficSource, Sink, SimulationEngine
from traffic_sim.visualizer import Visualizer

# ──────────────────────────────────────────────
# 1.  NETWORK TOPOLOGY DEFINITION
# ──────────────────────────────────────────────
#
#   Network layout (roughly):
#
#   SRC_A ──► J1 ──► J2 ──► J3 ──► SINK_N
#              │      ▲      │
#              ▼      │      ▼
#             J4 ────►J5 ──► J6 ──► SINK_E
#              │             ▲
#              ▼             │
#   SRC_B ──► J7 ────────────┘ ──► SINK_S
#
#  Junctions: J1(4-way), J2(3-way), J3(3-way), J4(3-way),
#             J5(4-way), J6(3-way), J7(3-way)

SIM_STEPS = 300
RECORD_EVERY = 2     
ANIMATION_FPS = 10

# ── Node positions──────────────────────────
NODE_POS = {
    "SRC_A": (0.0, 2.0),
    "SRC_B": (0.0, 0.0),
    "J1":    (1.0, 2.0),
    "J2":    (2.0, 2.0),
    "J3":    (3.0, 2.0),
    "J4":    (1.0, 1.0),
    "J5":    (2.0, 1.0),
    "J6":    (3.0, 1.0),
    "J7":    (1.0, 0.0),
    "SINK_N":(4.0, 2.0),
    "SINK_E":(4.0, 1.0),
    "SINK_S":(4.0, 0.0),
}

NODE_TYPES = {
    "SRC_A": "source",
    "SRC_B": "source",
    "J1":    "junction",
    "J2":    "junction",
    "J3":    "junction",
    "J4":    "junction",
    "J5":    "junction",
    "J6":    "junction",
    "J7":    "junction",
    "SINK_N":"sink",
    "SINK_E":"sink",
    "SINK_S":"sink",
}

# Destination colors (one per sink)
DEST_COLORS = {
    "SINK_N": "#00ff88",   # green
    "SINK_E": "#ff9900",   # orange
    "SINK_S": "#cc44ff",   # purple
}

# ──────────────────────────────────────────────
# 2.  BUILD SIMULATION ENGINE
# ──────────────────────────────────────────────

def build_network() -> SimulationEngine:
    engine = SimulationEngine()

    # ── Junctions (id, pos, green_time) ──────────────────────────────
    junctions = [
        Junction("J1", NODE_POS["J1"], green_time=4),   # 4-way hub
        Junction("J2", NODE_POS["J2"], green_time=3),   # 3-way
        Junction("J3", NODE_POS["J3"], green_time=3),   # 3-way
        Junction("J4", NODE_POS["J4"], green_time=3),   # 3-way
        Junction("J5", NODE_POS["J5"], green_time=4),   # 4-way hub
        Junction("J6", NODE_POS["J6"], green_time=3),   # 3-way
        Junction("J7", NODE_POS["J7"], green_time=3),   # 3-way
    ]
    for j in junctions:
        engine.add_junction(j)

    # ── Sinks ─────────────────────────────────────────────────────────
    sinks = [
        Sink("SINK_N", NODE_POS["SINK_N"]),
        Sink("SINK_E", NODE_POS["SINK_E"]),
        Sink("SINK_S", NODE_POS["SINK_S"]),
    ]
    for s in sinks:
        engine.add_sink(s)

    # ── Roads  (id, start, end, capacity, length, speed_limit) ────────
    #  Format: Road(road_id, start, end, capacity, length, speed_limit)
    roads = [
        # SRC_A → J1
        Road("R01", "SRC_A", "J1",  capacity=8,  length=1, speed_limit=1),
        # SRC_B → J7
        Road("R02", "SRC_B", "J7",  capacity=8,  length=1, speed_limit=1),

        # Main horizontal spine (top)
        Road("R03", "J1",  "J2",   capacity=6,  length=1, speed_limit=1),
        Road("R04", "J2",  "J3",   capacity=6,  length=1, speed_limit=1),
        Road("R05", "J3",  "SINK_N", capacity=10, length=1, speed_limit=1),

        # Middle horizontal
        Road("R06", "J4",  "J5",   capacity=6,  length=1, speed_limit=1),
        Road("R07", "J5",  "J6",   capacity=6,  length=1, speed_limit=1),
        Road("R08", "J6",  "SINK_E", capacity=10, length=1, speed_limit=1),

        # Verticals left side
        Road("R09", "J1",  "J4",   capacity=5,  length=1, speed_limit=1),
        Road("R10", "J4",  "J7",   capacity=5,  length=1, speed_limit=1),

        # Verticals middle
        Road("R11", "J5",  "J2",   capacity=5,  length=1, speed_limit=1),   # upward
        Road("R12", "J3",  "J6",   capacity=5,  length=1, speed_limit=1),   # downward

        # J7 connections
        Road("R13", "J7",  "J5",   capacity=6,  length=2, speed_limit=1),   # longer road
        Road("R14", "J7",  "SINK_S", capacity=10, length=1, speed_limit=1),

        # Cross links for richer routing options
        Road("R15", "J2",  "J5",   capacity=4,  length=1, speed_limit=1),
        Road("R16", "J6",  "J3",   capacity=4,  length=1, speed_limit=1),   # back route
    ]

    for r in roads:
        engine.add_road(r)


    sources = [
        TrafficSource(
            source_id="SRC_A_gen",
            node_id="SRC_A",
            destinations=["SINK_N", "SINK_E", "SINK_S"],
            rate=0.4,
            mode="poisson",
            dest_colors=DEST_COLORS,
        ),
        TrafficSource(
            source_id="SRC_B_gen",
            node_id="SRC_B",
            destinations=["SINK_N", "SINK_E", "SINK_S"],
            rate=0.35,
            mode="poisson",
            dest_colors=DEST_COLORS,
        ),
    ]
    for src in sources:
        engine.add_source(src)

    # ── Wire everything together ───────────────────────────────────────
    engine.build()
    return engine


# ──────────────────────────────────────────────
# 3.  RUN & REPORT
# ──────────────────────────────────────────────

def print_stats(stats: dict):
    print("\n" + "═" * 55)
    print("  TRAFFIC SIMULATION — RESULTS")
    print("═" * 55)
    print(f"  Simulation Steps  : {stats['total_steps']}")
    print(f"  Vehicles Spawned  : {stats['total_spawned']}")
    print(f"  Vehicles Absorbed : {stats['total_absorbed']}")
    print(f"  Still in Network  : {stats['vehicles_in_network']}")
    print(f"  Avg Travel Time   : {stats['avg_travel_time']:.2f} steps")
    print(f"  Min/Max Travel    : {stats['min_travel_time']} / {stats['max_travel_time']} steps")
    print(f"  Avg Queue Length  : {stats['avg_queue_length']:.2f}")
    print(f"  Peak Queue Length : {stats['peak_queue_length']}")
    print()
    print("  Per Sink:")
    for sid, s in stats["per_sink"].items():
        print(f"    {sid:8s}: absorbed={s['absorbed']:4d}, "
              f"avg_travel={s['avg_travel_time']:.1f}")
    print()
    print("  Per Junction (vehicles passed):")
    for jid, j in stats["per_junction"].items():
        print(f"    {jid:4s} ({j['ways']}-way): {j['vehicles_passed']:4d} vehicles")
    print()
    print("  Per Road (total vehicles | avg queue):")
    for rid, r in stats["per_road"].items():
        print(f"    {rid}: {r['total_vehicles']:4d} veh | "
              f"avg_q={r['avg_queue']:.2f}")
    print("═" * 55 + "\n")


def save_stats_txt(stats: dict, path: str = "statistics.txt"):
    lines = []
    lines.append("TRAFFIC SIMULATION STATISTICS")
    lines.append("=" * 50)
    for k, v in stats.items():
        if k in ("throughput_per_step", "queue_per_step", "per_sink",
                 "per_road", "per_junction"):
            continue
        lines.append(f"{k}: {v}")
    lines.append("\nPer Sink:")
    for sid, s in stats["per_sink"].items():
        lines.append(f"  {sid}: {s}")
    lines.append("\nPer Junction:")
    for jid, j in stats["per_junction"].items():
        lines.append(f"  {jid}: {j}")
    lines.append("\nPer Road:")
    for rid, r in stats["per_road"].items():
        lines.append(f"  {rid}: {r}")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Statistics text  → {path}")


# ──────────────────────────────────────────────
# 4.  ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import random, os
    random.seed(42)

    print("Building network...")
    engine = build_network()

    print(f"Running simulation for {SIM_STEPS} steps...")
    engine.run(steps=SIM_STEPS, record_every=RECORD_EVERY)

    stats = engine.statistics()
    print_stats(stats)

    # Save text stats
    out_dir = "."
    os.makedirs(out_dir, exist_ok=True)

    save_stats_txt(stats, f"{out_dir}/statistics.txt")


    print("Rendering animation (this may take a minute)...")
    viz = Visualizer(
        engine=engine,
        node_positions=NODE_POS,
        node_types=NODE_TYPES,
        dest_colors=DEST_COLORS,
        title="Multi-Junction Traffic Simulator",
    )
    gif_path = viz.animate(
        output_path=f"{out_dir}/simulation.gif",
        fps=ANIMATION_FPS,
        skip=1,
    )

    print("Rendering statistics chart...")
    viz.plot_statistics(stats, output_path=f"{out_dir}/statistics.png")

    print("\nDone! Output files:")
    print(f"  {out_dir}/simulation.gif")
    print(f"  {out_dir}/statistics.png")
    print(f"  {out_dir}/statistics.txt")
