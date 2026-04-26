"""
Router: computes shortest paths through the road network.

Uses Dijkstra's algorithm on the graph of nodes (junctions + sources + sinks).
Edge weights = road travel_time.
"""
import heapq


class Router:
    """
    Builds a graph from roads and finds shortest paths.

    Parameters
    ----------
    roads     : dict {road_id: Road}
    """

    def __init__(self, roads: dict):
        self._graph: dict = {}
        for road_id, road in roads.items():
            self._graph.setdefault(road.start, [])
            self._graph.setdefault(road.end, [])
            self._graph[road.start].append((road.travel_time, road_id, road.end))

    def shortest_path(self, source: str, destination: str) -> list:
        """
        Return ordered list of node IDs from source to destination (inclusive).
        Returns empty list if no path exists.
        """
        if source == destination:
            return [source]

        dist = {source: 0}
        prev = {}   # {node: (from_node, road_id)}
        heap = [(0, source)]

        while heap:
            cost, node = heapq.heappop(heap)
            if cost > dist.get(node, float("inf")):
                continue
            if node == destination:
                break
            for edge_cost, road_id, neighbour in self._graph.get(node, []):
                new_cost = cost + edge_cost
                if new_cost < dist.get(neighbour, float("inf")):
                    dist[neighbour] = new_cost
                    prev[neighbour] = (node, road_id)
                    heapq.heappush(heap, (new_cost, neighbour))

        if destination not in prev and destination != source:
            return []   # no path

        path = []
        node = destination
        while node != source:
            path.append(node)
            node = prev[node][0]
        path.append(source)
        path.reverse()
        return path

    def route_vehicle(self, vehicle, source: str, destination: str):
        """Assign a route to a vehicle. Returns True if route found."""
        path = self.shortest_path(source, destination)
        if not path:
            return False
        vehicle.route = path
        vehicle.route_index = 1   
        return True
