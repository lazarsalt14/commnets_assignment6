"""
Road: A directional road segment connecting two junctions (or source/sink nodes).
Vehicles travel along a road in one direction only.
"""
from collections import deque


class Road:
    """
    A directional road from node `start` to node `end`.

    Attributes
    ----------
    road_id    : str   – unique identifier
    start      : str   – ID of the originating node (Junction / Source)
    end        : str   – ID of the destination node (Junction / Sink)
    capacity   : int   – max vehicles that can be *on* the road simultaneously
    length     : float – conceptual length (arbitrary units); travel_time = length / speed_limit
    speed_limit: float – speed in units/time-step
    """

    def __init__(self, road_id: str, start: str, end: str,
                 capacity: int = 10, length: float = 1.0, speed_limit: float = 1.0):
        self.road_id = road_id
        self.start = start
        self.end = end
        self.capacity = capacity
        self.length = length
        self.speed_limit = speed_limit
        self.travel_time = max(1, int(length / speed_limit))  # time-steps to traverse

        # vehicles currently travelling: list of (vehicle, arrival_time_step)
        self._in_transit: list = []
        # vehicles queued at the end of road waiting to enter next node
        self._queue: deque = deque()

        # statistics
        self.total_vehicles = 0
        self.total_wait_steps = 0
        self._queue_history: list = []   # queue length per step

    # ------------------------------------------------------------------
    # Capacity helpers
    # ------------------------------------------------------------------

    @property
    def occupancy(self) -> int:
        return len(self._in_transit) + len(self._queue)

    def is_full(self) -> bool:
        return self.occupancy >= self.capacity

    def can_accept(self) -> bool:
        return not self.is_full()

    # ------------------------------------------------------------------
    # Vehicle movement
    # ------------------------------------------------------------------

    def admit_vehicle(self, vehicle, current_step: int):
        """Put a vehicle onto this road. Returns True on success."""
        if self.is_full():
            return False
        arrival = current_step + self.travel_time
        self._in_transit.append((vehicle, arrival))
        vehicle.current_road = self.road_id
        self.total_vehicles += 1
        return True

    def step(self, current_step: int):
        """
        Advance one simulation time-step.
        Vehicles that have finished travelling move to the front queue.
        Returns list of vehicles newly ready to leave (at end-node).
        """
        self._queue_history.append(len(self._queue))

        still_travelling = []
        for vehicle, arrival in self._in_transit:
            if current_step >= arrival:
                self._queue.append(vehicle)
            else:
                still_travelling.append((vehicle, arrival))
        self._in_transit = still_travelling

    def peek_queue(self):
        """Return the first vehicle in the exit queue without removing it."""
        return self._queue[0] if self._queue else None

    def dequeue_vehicle(self):
        """Remove and return the front vehicle from the exit queue."""
        if self._queue:
            v = self._queue.popleft()
            return v
        return None

    def queue_length(self) -> int:
        return len(self._queue)

    # ------------------------------------------------------------------
    # Statistics helpers
    # ------------------------------------------------------------------

    def avg_queue_length(self) -> float:
        if not self._queue_history:
            return 0.0
        return sum(self._queue_history) / len(self._queue_history)

    def __repr__(self):
        return (f"Road({self.road_id}: {self.start}→{self.end}, "
                f"cap={self.capacity}, occ={self.occupancy})")
