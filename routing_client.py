import re
import time

import requests

GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/{profile}"

COORD_PATTERN = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
)


class RoutingError(Exception):
    pass


class OpenRouteServiceClient:
    """Cliente para geocodificação e cálculo de rotas via OpenRouteService (gratuito)."""

    def __init__(self, api_key, profile="driving-car", cache=None, request_delay=1.6):
        if not api_key:
            raise RoutingError(
                "ORS_API_KEY não configurada. Defina no arquivo .env (veja .env.example)."
            )
        self.api_key = api_key
        self.profile = profile
        self.cache = cache
        self.request_delay = request_delay

    def _throttle(self):
        time.sleep(self.request_delay)

    def geocode(self, address):
        """Retorna (lon, lat) para um endereço em texto, ou coordenadas já prontas."""
        direct = COORD_PATTERN.match(address)
        if direct:
            lat, lon = float(direct.group(1)), float(direct.group(2))
            return (lon, lat)

        if self.cache:
            cached = self.cache.get_coords(address)
            if cached:
                return tuple(cached)

        self._throttle()
        resp = requests.get(
            GEOCODE_URL,
            params={"api_key": self.api_key, "text": address, "size": 1},
            timeout=20,
        )
        if resp.status_code != 200:
            raise RoutingError(
                f"Falha ao geocodificar '{address}': HTTP {resp.status_code} - {resp.text[:200]}"
            )
        data = resp.json()
        features = data.get("features") or []
        if not features:
            raise RoutingError(f"Endereço não encontrado: '{address}'")

        lon, lat = features[0]["geometry"]["coordinates"]
        if self.cache:
            self.cache.set_coords(address, [lon, lat])
        return (lon, lat)

    def get_route(self, origin_address, destination_address):
        """Retorna dict com distance_km e duration_min para origem/destino em texto."""
        if self.cache:
            cached = self.cache.get_route(origin_address, destination_address, self.profile)
            if cached:
                return cached

        origin_coords = self.geocode(origin_address)
        dest_coords = self.geocode(destination_address)

        self._throttle()
        resp = requests.get(
            DIRECTIONS_URL.format(profile=self.profile),
            params={
                "api_key": self.api_key,
                "start": f"{origin_coords[0]},{origin_coords[1]}",
                "end": f"{dest_coords[0]},{dest_coords[1]}",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise RoutingError(
                f"Falha ao calcular rota '{origin_address}' -> '{destination_address}': "
                f"HTTP {resp.status_code} - {resp.text[:200]}"
            )
        data = resp.json()
        try:
            summary = data["features"][0]["properties"]["summary"]
        except (KeyError, IndexError) as exc:
            raise RoutingError(
                f"Resposta inesperada da API para '{origin_address}' -> '{destination_address}'"
            ) from exc

        result = {
            "distance_km": round(summary["distance"] / 1000, 2),
            "duration_min": round(summary["duration"] / 60, 1),
        }

        if self.cache:
            self.cache.set_route(origin_address, destination_address, self.profile, result)
        return result
