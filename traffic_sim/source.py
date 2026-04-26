"""
TrafficSource: generates vehicles at a junction or dedicated source node.

Supports:
  - constant rate  (fixed number per time window)
  - Poisson process (random arrivals)
"""
import random
import math


class TrafficSource:
    """
    Generates vehicles at node `node_id`.

    Parameters
    ----------
    source_id       : str
    node_id         : str   - junction/source node where vehicles spawn
    destinations    : list  - possible destination node IDs (chosen uniformly)
    rate            : float - average vehicles per time-step
    mode            : 'constant' | 'poisson'
    dest_colors     : dict  - {destination: color_hex}  for visualisation
    """

    def __init__(self, source_id: str, node_id: str, destinations: list,
                 rate: float = 0.5, mode: str = "poisson",
                 dest_colors: dict = None):
        self.source_id = source_id
        self.node_id = node_id
        self.destinations = destinations
        self.rate = rate
        self.mode = mode
        self.dest_colors = dest_colors or {}

        self._accumulator = 0.0   # for constant mode
        self.total_spawned = 0

    def generate(self, current_step: int) -> int:
        """Return how many vehicles to spawn this step."""
        if self.mode == "constant":
            self._accumulator += self.rate
            count = int(self._accumulator)
            self._accumulator -= count
            return count
        elif self.mode == "poisson":
            return self._poisson_sample(self.rate)
        return 0

    @staticmethod
    def _poisson_sample(lam: float) -> int:
        """Sample from Poisson distribution (Knuth algorithm)."""
        if lam <= 0:
            return 0
        L = math.exp(-lam)
        k, p = 0, 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    def pick_destination(self) -> str:
        return random.choice(self.destinations)

    def color_for(self, destination: str) -> str:
        return self.dest_colors.get(destination, "#AAAAAA")

    def __repr__(self):
        return (f"TrafficSource({self.source_id} @ {self.node_id}, "
                f"rate={self.rate}, mode={self.mode})")
