import heapq

from maspy import *

from Base_Ag import Membro
from Map_Env import manhattan


def astar_explore(start, goal, known, walls):
    walls = set(walls)
    start = tuple(start)
    goal = tuple(goal)

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g = {start: 0}

    def h(p):
        return abs(goal[0] - p[0]) + abs(goal[1] - p[1])

    def neighbors(node):
        x, y = node
        return [n for n in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)] if n not in walls]

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        known_neighbors = known.get(current, set())
        unknown_neighbors = [n for n in neighbors(current) if n not in known_neighbors]

        for nxt in known_neighbors:
            new_cost = g[current] + 1
            if nxt not in g or new_cost < g[nxt]:
                g[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(open_set, (new_cost + h(nxt), nxt))

        for nxt in unknown_neighbors:
            new_cost = g[current] + 1.25
            if nxt not in g or new_cost < g[nxt]:
                g[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(open_set, (new_cost + h(nxt), nxt))

    return None


def astar_direction(ag, position, target):
    map_graph = ag.get(Belief("Path_Graph", Any))
    wall_set = ag.get(Belief("Wall_Set", Any))
    path = astar_explore(position, target, map_graph.values, wall_set.values)
    if path is None:
        path = []
    if len(path) > 1:
        target = path[1]

    dx, dy = target[0] - position[0], target[1] - position[1]
    if dx == 0 and dy == 0:
        direction = "stay"
    elif abs(dy) >= abs(dx):
        direction = "down" if dy > 0 else "up"
    else:
        direction = "right" if dx > 0 else "left"
    return direction


class Walker(Membro):
    def __init__(self, name, map: Environment):
        super().__init__(name, max_intentions=1)
        self.filter_perceptions(add, focus, self.my_name)
        self.connect_to(map)
        self.add(Belief("Path_Graph", dict()))
        self.add(Belief("Wall_Set", []))
        self.aguardando = None
        self.alvos = set()

    def objetivo(self, position):
        if not self.alvos:
            return None
        return max(self.alvos, key=lambda a: (a[2], -manhattan(position, a[:2])))

    def update_map(self, position, direction):
        map_graph = self.get(Belief("Path_Graph", Any))
        wall_list = self.get(Belief("Wall_Set", Any))
        new_pos = self.get(Belief("agt_position", (Any, Any), "Map"))
        if new_pos.values not in map_graph.values:
            graph = map_graph.values
            graph.setdefault(position, set()).add(new_pos.values)
            graph.setdefault(new_pos.values, set()).add(position)
            map_graph.change(values=graph)
        if new_pos.values == position and direction != "stay":
            dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[direction]
            wall_pos = (position[0] + dx, position[1] + dy)
            walls = wall_list.values
            if wall_pos not in walls:
                walls.append(wall_pos)
                wall_list.change(values=walls)
                self.send("Memoria", tell, Belief("parede", wall_pos))
        return new_pos.values

    @pl(gain, Belief("alvo", (Any, Any, Any)))
    def conhecer_alvo(self, src, alvo):
        self.alvos.add(alvo)
        self.print(f"{src} anunciou alvo de valor {alvo[2]} em {alvo[:2]}")

    @pl(gain, Goal("move"), Belief("agt_position", (Any, Any), "Map"))
    def mover(self, src, position):
        if self.aguardando:
            return False
        alvo = self.objetivo(position)
        if alvo is None:
            return False

        direction = astar_direction(self, position, alvo[:2])
        if direction != "stay":
            self.move(direction)
        self.perceive("Map")
        nova = self.update_map(position, direction)

        if nova == alvo[:2]:
            self.print(f"cheguei no alvo {alvo[2]} em {nova}; pedindo validacao ao Juiz")
            self.aguardando = alvo
            self.send("Juiz", achieve, Goal("validar_captura", alvo))
        return False

    @pl(gain, Belief("captura_confirmada", Any))
    def venci(self, src, valor):
        self.print(f"capturei o alvo de valor {valor}!")
        self.stop_cycle()

    @pl(gain, Belief("captura_negada", (Any, Any, Any)))
    def perdi(self, src, args):
        x, y, motivo = args
        self.print(f"captura em {(x, y)} negada pelo {src}: {motivo}")
        self.alvos = {a for a in self.alvos if a[:2] != (x, y)}
        self.aguardando = None
        self.send("Memoria", askAll, Belief("parede", (Any, Any)))

    @pl(lose, Belief("alvo", (Any, Any, Any)))
    def alvo_perdido(self, src, alvo):
        self.print(f"alvo {alvo[2]} em {alvo[:2]} saiu da disputa; replanejando com a Memoria")
        self.alvos.discard(alvo)
        self.send("Memoria", askAll, Belief("parede", (Any, Any)))

    @pl(gain, Belief("parede", (Any, Any)))
    def receber_parede(self, src, parede):
        wall_set = self.get(Belief("Wall_Set", Any))
        walls = wall_set.values
        if parede not in walls:
            walls.append(parede)
            wall_set.change(values=walls)
            self.print(f"{src} me ensinou a parede {parede}")

    @pl(gain, Belief("encerrar"))
    def encerrar(self, src):
        self.stop_cycle()
