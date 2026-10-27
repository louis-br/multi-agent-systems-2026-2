from maspy import *
from collections import deque
from random import randint
import random


def generate_map_with_walls(width, height, alvos, wall_prob=0.1, max_attempts=2000):
    def neighbors(x, y):
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    for _ in range(max_attempts):
        walls = {(x, y) for x in range(width) for y in range(height)
                 if random.random() < wall_prob and (x, y) not in alvos}

        queue = deque([alvos[0]])
        reachable = {alvos[0]}
        while queue:
            cx, cy = queue.popleft()
            for nx, ny in neighbors(cx, cy):
                if (nx, ny) not in walls and (nx, ny) not in reachable:
                    reachable.add((nx, ny))
                    queue.append((nx, ny))

        total_open = width * height - len(walls)
        if len(reachable) == total_open:
            return walls, sorted(reachable)

    raise RuntimeError("Failed to generate a valid map.")


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Map(Environment):
    def __init__(self, map_size=(10, 10), walls_prob=0.1, valores=(10, 50)):
        super().__init__()
        self.moves = {
            "up": (0, -1), "down": (0, 1),
            "right": (1, 0), "left": (-1, 0),
        }
        self.map_size = map_size
        alvos = self._sortear_alvos(len(valores))
        walls, _ = generate_map_with_walls(map_size[0], map_size[1], alvos, walls_prob, 2000)

        for (x, y), valor in zip(alvos, valores):
            self.print(f"Alvo de valor {valor} em {(x, y)}")
            self.create(Percept("alvo", (x, y, valor, None)))
        for wall in walls:
            self.create(Percept("wall", wall))

    def _sortear_alvos(self, n):
        w, h = self.map_size
        alvos = []
        while len(alvos) < n:
            pos = (randint(0, w-1), randint(0, h-1))
            if all(manhattan(pos, a) >= (w + h) // 4 for a in alvos):
                alvos.append(pos)
        return alvos

    def _alvos(self):
        return [p.values for p in self.get(Percept("alvo", (Any, Any, Any, Any)), all=True)]

    def on_connect(self, agt):
        if not agt.startswith("Walker"):
            return
        alvos = [a[:2] for a in self._alvos()]
        w, h = self.map_size
        for tentativa in range(1000):
            start_pos = (randint(0, w-1), randint(0, h-1))
            longe = min(manhattan(start_pos, a) for a in alvos) > w / 3 or tentativa > 500
            if not self.has(Percept("wall", start_pos)) and start_pos not in alvos and longe:
                break
        self.create(Percept("agt_position", start_pos, agt))

    def moviment(self, position, direction):
        dx, dy = self.moves[direction]
        new_x = max(0, min(position[0] + dx, self.map_size[0] - 1))
        new_y = max(0, min(position[1] + dy, self.map_size[1] - 1))
        return new_x, new_y

    def move(self, agt, direction):
        position = self.get(Percept("agt_position", (Any, Any), agt), ck_group=True)
        assert isinstance(position, Percept)

        pos = position.values
        if direction == "stay":
            return
        new_pos = self.moviment(pos, direction)
        if self.has(Percept("wall", new_pos)):
            self.print(f"{agt} in {pos} moves {direction} but hits a wall")
        else:
            position.change(values=new_pos)
            self.print(f"{agt} in {pos} moves {direction} to {new_pos}")

    def listar_alvos(self, agt):
        return [(x, y, valor) for x, y, valor, dono in self._alvos() if dono is None]

    def capturar(self, agt, walker, x, y, valor):
        alvo = self.get(Percept("alvo", (x, y, Any, Any)))
        pos = self.get(Percept("agt_position", (Any, Any), walker), ck_group=True)
        if not isinstance(alvo, Percept) or alvo.values[2] != valor:
            return False, "alvo inexistente"
        if alvo.values[3] is not None:
            return False, f"ja capturado por {alvo.values[3]}"
        if not isinstance(pos, Percept) or pos.values != (x, y):
            return False, f"{walker} nao esta em {(x, y)}"
        alvo.change(values=(x, y, valor, walker))
        self.print(f"{walker} capturou o alvo {valor} em {(x, y)}")
        return True, walker
