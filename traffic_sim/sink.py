"""
Sink: a node where vehicles exit the network.

When a vehicle's next_node is a sink, the sink absorbs it and records stats.
"""


class Sink:
    """
    A sink node (traffic exit point).

    Parameters
    ----------
    sink_id : str  – must match the node_id used in routes
    pos     : (float, float)  – visualisation position
    """

    def __init__(self, sink_id: str, pos: tuple = (0.0, 0.0)):
        self.sink_id = sink_id
        self.pos = pos

        self.incoming_roads: list = []

        self.absorbed: list = []          
        self.total_travel_times: list = []

    def add_incoming(self, road_id: str):
        if road_id not in self.incoming_roads:
            self.incoming_roads.append(road_id)

    def absorb(self, vehicle, current_step: int):
        """Remove vehicle from network, record statistics."""
        vehicle.arrival_step = current_step
        travel = current_step - vehicle.spawn_step
        self.total_travel_times.append(travel)
        self.absorbed.append(vehicle)

    def step(self, roads: dict, current_step: int) -> list:
        """
        Pull any ready vehicles off incoming roads and absorb them.
        Returns list of absorbed vehicles this step.
        """
        absorbed_this_step = []
        for road_id in self.incoming_roads:
            if road_id not in roads:
                continue
            road = roads[road_id]
            while road.peek_queue() is not None:
                vehicle = road.peek_queue()
                if vehicle.next_node == self.sink_id or vehicle.has_arrived():
                    road.dequeue_vehicle()
                    vehicle.advance_route()
                    self.absorb(vehicle, current_step)
                    absorbed_this_step.append(vehicle)
                else:
                    break 
        return absorbed_this_step

    @property
    def throughput(self) -> int:
        return len(self.absorbed)

    def avg_travel_time(self) -> float:
        if not self.total_travel_times:
            return 0.0
        return sum(self.total_travel_times) / len(self.total_travel_times)

    def __repr__(self):
        return f"Sink({self.sink_id}, absorbed={self.throughput})"
