"""
pairwise-city-planning-system - CityPlanningSystem

Core city-planning simulation: roads, zoning, citizens, traffic, economy.
"""


class CityPlanningSystem:
    ROAD_HIERARCHY = {
        "highway": {"level": 3, "capacity": 2000, "speed": 100, "cost": 500, "maintenance": 50},
        "avenue": {"level": 2, "capacity": 800, "speed": 60, "cost": 200, "maintenance": 20},
        "street": {"level": 1, "capacity": 200, "speed": 30, "cost": 50, "maintenance": 5},
    }
    ZONE_TYPES = ("residential", "commercial", "industrial")
    DENSITY_MAX_FLOORS = {"low": 3, "medium": 8, "high": 40}
    ZONE_JOBS = {"residential": 0, "commercial": 10, "industrial": 20}
    ZONE_TAX = {"residential": 5, "commercial": 50, "industrial": 80}
    DEMOLITION_COMPENSATION = 1000
    SERVICE_COST_PER_CITIZEN = 2

    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.roads = {}          # (x, y) -> road_type
        self.zones = {}          # (x, y) -> {"type", "density", "floors"}
        self.demolished = []     # tiles cleared by road construction
        self.citizens = []       # {"id", "home", "work", "location", "employed", "satisfaction"}
        self.population = 100
        self.jobs = 0
        self.gdp = 10000.0
        self.budget = 100000.0
        self.tax_rate = 0.10
        self.satisfaction = 0.7
        self.transit_share = 0.3  # share of commuters using public transit
        self.tick = 0
        self.state = {}
        self._spawn_citizens(self.population)

    # ------------------------------------------------------------------ roads

    def _path_between(self, start, end):
        """L-shaped Manhattan path of tiles from start to end (inclusive)."""
        (x1, y1), (x2, y2) = start, end
        tiles = []
        step_x = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step_x, step_x):
            tiles.append((x, y1))
        step_y = 1 if y2 >= y1 else -1
        for y in range(y1 + step_y, y2 + step_y, step_y):
            tiles.append((x2, y))
        return tiles

    def _neighbors(self, tile):
        x, y = tile
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def _is_connected(self, tiles):
        """A new road must touch the existing network (first road is exempt)."""
        if not self.roads:
            return True
        for tile in tiles:
            if tile in self.roads:
                return True
            if any(n in self.roads for n in self._neighbors(tile)):
                return True
        return False

    def build_road(self, start=None, end=None, road_type="street"):
        """Build a road with connectivity checks, hierarchy and demolition."""
        if road_type not in self.ROAD_HIERARCHY:
            return {"built": False, "reason": "unknown_road_type", "road_type": road_type}
        if start is None:
            start = (0, len(self.roads))
        if end is None:
            end = (min(start[0] + 3, self.grid_size - 1), start[1])

        tiles = self._path_between(start, end)
        spec = self.ROAD_HIERARCHY[road_type]

        # Connectivity: refuse dead-end roads that never join the network.
        if not self._is_connected(tiles):
            return {"built": False, "reason": "not_connected", "tiles": tiles}

        # Demolition: buildings standing in the way are cleared (with compensation).
        demolished = []
        for tile in tiles:
            if tile in self.zones:
                demolished.append({"tile": tile, "zone": self.zones[tile]["type"]})
                self.jobs -= self.ZONE_JOBS[self.zones[tile]["type"]]
                del self.zones[tile]
        self.demolished.extend(demolished)

        cost = len(tiles) * spec["cost"] + len(demolished) * self.DEMOLITION_COMPENSATION
        self.budget -= cost
        for tile in tiles:
            self.roads[tile] = road_type

        return {
            "built": True,
            "connected": True,
            "road_type": road_type,
            "level": spec["level"],
            "capacity": spec["capacity"],
            "tiles": tiles,
            "demolished": demolished,
            "cost": cost,
            "budget": self.budget,
        }

    # ----------------------------------------------------------------- zoning

    def _adjacent_zone_types(self, tile):
        return {self.zones[n]["type"] for n in self._neighbors(tile) if n in self.zones}

    def _max_adjacent_road_level(self, tile):
        levels = [
            self.ROAD_HIERARCHY[self.roads[n]]["level"]
            for n in self._neighbors(tile)
            if n in self.roads
        ]
        return max(levels, default=0)

    def zone_area(self, x=None, y=None, zone_type="residential", density="low", floors=1):
        """Zone a tile with demand, density and pollution checks."""
        if zone_type not in self.ZONE_TYPES:
            return {"zoned": False, "reason": "unknown_zone_type", "zone_type": zone_type}
        if density not in self.DENSITY_MAX_FLOORS:
            return {"zoned": False, "reason": "unknown_density", "density": density}
        if x is None:
            x = len(self.zones) % self.grid_size
        if y is None:
            y = len(self.zones) // self.grid_size
        tile = (x, y)
        if tile in self.roads:
            return {"zoned": False, "reason": "occupied_by_road", "tile": tile}

        # Demand: commercial needs a customer base and an existing job market.
        if zone_type == "commercial":
            if self.population < 20 or self.jobs <= 0:
                return {"zoned": False, "reason": "no_demand", "tile": tile,
                        "population": self.population, "jobs": self.jobs}
        if zone_type == "industrial" and self.population < 10:
            return {"zoned": False, "reason": "no_workforce", "tile": tile}

        # Density: floors are capped by density class; high-rises need major roads.
        max_floors = self.DENSITY_MAX_FLOORS[density]
        if floors > max_floors:
            return {"zoned": False, "reason": "density_exceeded", "tile": tile,
                    "density": density, "max_floors": max_floors, "floors": floors}
        if density == "high" and self._max_adjacent_road_level(tile) < 2:
            return {"zoned": False, "reason": "high_density_requires_major_road", "tile": tile}

        # Pollution: no housing next to industry (and vice versa).
        neighbors = self._adjacent_zone_types(tile)
        if zone_type == "residential" and "industrial" in neighbors:
            return {"zoned": False, "reason": "pollution", "tile": tile}
        if zone_type == "industrial" and "residential" in neighbors:
            return {"zoned": False, "reason": "pollution_buffer", "tile": tile}

        self.zones[tile] = {"type": zone_type, "density": density, "floors": floors}
        self.jobs += self.ZONE_JOBS[zone_type]
        return {"zoned": True, "tile": tile, "zone_type": zone_type,
                "density": density, "floors": floors, "jobs": self.jobs}

    # --------------------------------------------------------------- citizens

    def _spawn_citizens(self, count):
        for _ in range(count):
            cid = len(self.citizens)
            home = (cid % self.grid_size, (cid * 2) % self.grid_size)
            work = ((cid * 3) % self.grid_size, (cid * 5) % self.grid_size)
            self.citizens.append({
                "id": cid, "home": home, "work": work, "location": home,
                "employed": True, "satisfaction": self.satisfaction,
                "last_commute": 0,
            })

    @staticmethod
    def _step_toward(location, target):
        x, y = location
        tx, ty = target
        if x != tx:
            x += 1 if tx > x else -1
        elif y != ty:
            y += 1 if ty > y else -1
        return (x, y)

    def update_citizens(self):
        """Commute citizens, update satisfaction, grow/shrink the population."""
        self.tick += 1
        heading_to_work = self.tick % 2 == 1
        commuters = 0
        for citizen in self.citizens:
            target = citizen["work"] if heading_to_work else citizen["home"]
            if citizen["location"] != target:
                distance = abs(citizen["location"][0] - target[0]) + abs(citizen["location"][1] - target[1])
                citizen["location"] = self._step_toward(citizen["location"], target)
                citizen["last_commute"] = distance
                commuters += 1

            # Satisfaction: long commutes, pollution at home and unemployment hurt.
            value = 1.0 - 0.05 * citizen["last_commute"]
            home = citizen["home"]
            if self.zones.get(home, {}).get("type") == "residential":
                if "industrial" in self._adjacent_zone_types(home):
                    value -= 0.3
            if not citizen["employed"]:
                value -= 0.4
            citizen["satisfaction"] = max(0.0, min(1.0, value))

        if self.citizens:
            self.satisfaction = sum(c["satisfaction"] for c in self.citizens) / len(self.citizens)

        # Population growth: happy cities with jobs attract people, unhappy ones shrink.
        jobs_available = max(0, self.jobs - sum(1 for c in self.citizens if c["employed"]))
        growth_rate = 0.05 * (self.satisfaction - 0.5) + 0.01 * min(jobs_available, 10) / 10
        delta = int(round(self.population * growth_rate))
        if delta > 0:
            self._spawn_citizens(delta)
        elif delta < 0:
            del self.citizens[delta:]
        self.population = len(self.citizens)

        self.state["citizens"] = {
            "tick": self.tick,
            "commuters": commuters,
            "satisfaction": self.satisfaction,
            "population": self.population,
            "growth": delta,
        }
        return self.state["citizens"]

    # ---------------------------------------------------------------- traffic

    def _find_path(self, start, end):
        """BFS shortest path over the road network; None if unreachable."""
        if start == end:
            return [start]
        if start not in self.roads or end not in self.roads:
            return None
        frontier = [start]
        came_from = {start: None}
        while frontier:
            current = frontier.pop(0)
            if current == end:
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]
            for nxt in self._neighbors(current):
                if nxt in self.roads and nxt not in came_from:
                    came_from[nxt] = current
                    frontier.append(nxt)
        return None

    def update_traffic(self, vehicles=None):
        """Route vehicles individually, measure congestion, run public transit."""
        if vehicles is None:
            vehicles = [
                (c["home"], c["work"]) for c in self.citizens
                if c["employed"] and c["home"] != c["work"]
            ]

        # Public transit takes its share of commuters off the road.
        transit_riders = round(len(vehicles) * self.transit_share)
        car_trips = vehicles[transit_riders:]

        # Path choice: every car gets its own shortest path, not one shared route.
        paths = []
        loads = {}
        unrouted = 0
        for origin, destination in car_trips:
            path = self._find_path(origin, destination)
            if path is None:
                unrouted += 1
                continue
            paths.append(tuple(path))
            for tile in path:
                loads[tile] = loads.get(tile, 0) + 1

        # Congestion: road load vs. hierarchy capacity; more cars means more jam.
        congestion = 0.0
        for tile, load in loads.items():
            capacity = self.ROAD_HIERARCHY[self.roads[tile]]["capacity"]
            congestion = max(congestion, load / capacity)

        result = {
            "vehicles": len(vehicles),
            "cars": len(car_trips),
            "transit_riders": transit_riders,
            "transit_share": self.transit_share,
            "routes": len(paths),
            "unique_routes": len(set(paths)),
            "unrouted": unrouted,
            "congestion": congestion,
            "road_loads": loads,
        }
        self.state["traffic"] = result
        return result

    # ---------------------------------------------------------------- economy

    def calculate_economy(self):
        """Collect taxes, pay maintenance/services, grow GDP."""
        # Taxes: income tax on GDP plus per-zone land taxes.
        income_tax = self.gdp * self.tax_rate
        land_tax = sum(self.ZONE_TAX[z["type"]] for z in self.zones.values())
        revenue = income_tax + land_tax

        # Spending: road maintenance by hierarchy level plus citizen services.
        maintenance = sum(
            self.ROAD_HIERARCHY[road_type]["maintenance"]
            for road_type in self.roads.values()
        )
        services = self.population * self.SERVICE_COST_PER_CITIZEN
        expenses = maintenance + services

        # Growth: employment and satisfaction push GDP up, congestion drags it down.
        employed = sum(1 for c in self.citizens if c["employed"])
        employment_rate = employed / self.population if self.population else 0.0
        congestion = self.state.get("traffic", {}).get("congestion", 0.0)
        growth_rate = 0.03 * employment_rate + 0.02 * (self.satisfaction - 0.5) - 0.05 * congestion
        self.gdp *= 1 + growth_rate

        self.budget += revenue - expenses
        result = {
            "revenue": revenue,
            "income_tax": income_tax,
            "land_tax": land_tax,
            "expenses": expenses,
            "maintenance": maintenance,
            "services": services,
            "balance": revenue - expenses,
            "budget": self.budget,
            "gdp": self.gdp,
            "growth_rate": growth_rate,
        }
        self.state["economy"] = result
        return result
