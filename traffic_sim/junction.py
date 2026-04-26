"""
Junction: an intersection node that connects multiple roads.

Supports 2-way, 3-way, and 4-way (and more) configurations.
Scheduling policy: round-robin among incoming roads (fair queuing).
"""


class Junction:
    """
    A traffic junction / intersection.

    Parameters
    ----------
    junction_id : str
    pos         : (float, float)  – (x, y) for visualisation
    green_time  : int             – steps each incoming road gets "green"
    """

    def __init__(self, junction_id: str, pos: tuple = (0.0, 0.0), green_time: int = 3):
        self.junction_id = junction_id
        self.pos = pos
        self.green_time = green_time

        self.incoming_roads: list = []   # roads whose `.end == junction_id`
        self.outgoing_roads: list = []   # roads whose `.start == junction_id`


        self._phase: int = 0            # index into incoming_roads that is currently green
        self._phase_timer: int = 0      # steps remaining for current phase


        self.vehicles_passed = 0
        self._wait_history: list = []


    def add_incoming(self, road_id: str):
        if road_id not in self.incoming_roads:
            self.incoming_roads.append(road_id)

    def add_outgoing(self, road_id: str):
        if road_id not in self.outgoing_roads:
            self.outgoing_roads.append(road_id)

    def ways(self) -> int:
        """Number of ways (max of in/out degree, for labelling)."""
        return max(len(self.incoming_roads), len(self.outgoing_roads))

    def _active_incoming(self) -> str | None:
        """Return road_id of the currently green incoming road."""
        if not self.incoming_roads:
            return None
        return self.incoming_roads[self._phase % len(self.incoming_roads)]

    def step(self, roads: dict, current_step: int) -> list:
        """
        Process one time-step at this junction.
        `roads` is a dict {road_id: Road}.
        Returns list of vehicles that have been forwarded to their next road.
        """
        forwarded = []

        if not self.incoming_roads:
            return forwarded

        self._phase_timer += 1
        if self._phase_timer >= self.green_time:
            self._phase_timer = 0
            self._phase = (self._phase + 1) % len(self.incoming_roads)

        active_road_id = self._active_incoming()
        if active_road_id not in roads:
            return forwarded

        road = roads[active_road_id]
        vehicle = road.peek_queue()
        if vehicle is None:
            return forwarded

        next_node = vehicle.next_node
        if next_node is None:
            road.dequeue_vehicle()
            return forwarded

        target_road = self._find_outgoing_road(next_node, roads)
        if target_road is None:
            return forwarded

        if target_road.can_accept():
            road.dequeue_vehicle()
            vehicle.advance_route()
            target_road.admit_vehicle(vehicle, current_step)
            self.vehicles_passed += 1
            forwarded.append(vehicle)

        return forwarded

    def _find_outgoing_road(self, target_node_id: str, roads: dict):
        """Return the outgoing Road leading to target_node_id, or None."""
        for road_id in self.outgoing_roads:
            if road_id in roads and roads[road_id].end == target_node_id:
                return roads[road_id]
        return None

    def __repr__(self):
        return (f"Junction({self.junction_id}, {self.ways()}-way, "
                f"in={self.incoming_roads}, out={self.outgoing_roads})")
