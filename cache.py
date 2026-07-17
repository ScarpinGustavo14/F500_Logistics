import json
import os


class RouteCache:
    """Cache local em JSON para evitar recalcular a mesma rota/endereço."""

    def __init__(self, path="route_cache.json"):
        self.path = path
        self._data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"geocode": {}, "route": {}}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_coords(self, address):
        return self._data["geocode"].get(address.strip().lower())

    def set_coords(self, address, coords):
        self._data["geocode"][address.strip().lower()] = coords

    def _route_key(self, origin, destination, profile):
        return f"{profile}|{origin.strip().lower()}|{destination.strip().lower()}"

    def get_route(self, origin, destination, profile):
        return self._data["route"].get(self._route_key(origin, destination, profile))

    def set_route(self, origin, destination, profile, result):
        self._data["route"][self._route_key(origin, destination, profile)] = result
