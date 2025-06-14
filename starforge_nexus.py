import pygame
import random
import asyncio
import platform
from typing import List, Tuple, Set
from collections import defaultdict

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starforge Nexus")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)

# Game settings
GRID_SIZE = 40
GRID_WIDTH, GRID_HEIGHT = WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE
NODE_SIZE = 15
VOID_SIZE = 20
FPS = 60
VOID_SPAWN_RATE = 0.02
ENERGY_PER_CONNECTION = 10
MAX_ENERGY = 100

class Node:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.active = False
        self.energy = 0

    def draw(self):
        color = YELLOW if self.active else GRAY
        pygame.draw.circle(screen, color, (self.x * GRID_SIZE + GRID_SIZE // 2, self.y * GRID_SIZE + GRID_SIZE // 2), NODE_SIZE)

class VoidCreature:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def move_towards(self, target_x: int, target_y: int):
        dx = 1 if target_x > self.x else -1 if target_x < self.x else 0
        dy = 1 if target_y > self.y else -1 if target_y < self.y else 0
        self.x += dx
        self.y += dy
        self.x = max(0, min(GRID_WIDTH - 1, self.x))
        self.y = max(0, min(GRID_HEIGHT - 1, self.y))

    def draw(self):
        pygame.draw.circle(screen, RED, (self.x * GRID_SIZE + GRID_SIZE // 2, self.y * GRID_SIZE + GRID_SIZE // 2), VOID_SIZE // 2)

class Game:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.nodes: List[Node] = []
        self.void_creatures: List[VoidCreature] = []
        self.connections: Set[Tuple[Tuple[int, int], Tuple[int, int]]] = set()
        self.core = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.energy = 50
        self.font = pygame.font.SysFont("arial", 24)
        self.clock = pygame.time.Clock()
        self.setup_grid()

    def setup_grid(self):
        # Place core
        self.grid[self.core[1]][self.core[0]] = 1
        # Place initial nodes
        for _ in range(5):
            while True:
                x, y = random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2)
                if self.grid[y][x] == 0 and (x, y) != self.core:
                    self.grid[y][x] = 2
                    self.nodes.append(Node(x, y))
                    break

    def get_node_at(self, x: int, y: int) -> Node | None:
        for node in self.nodes:
            if node.x == x and node.y == y:
                return node
        return None

    def add_connection(self, pos1: Tuple[int, int], pos2: Tuple[int, int]):
        if pos1 == pos2 or (pos1, pos2) in self.connections or (pos2, pos1) in self.connections:
            return
        node1, node2 = self.get_node_at(*pos1), self.get_node_at(*pos2)
        if node1 and node2 and self.energy >= ENERGY_PER_CONNECTION:
            if abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1:  # Adjacent nodes only
                self.connections.add((pos1, pos2))
                node1.active = node2.active = True
                self.energy -= ENERGY_PER_CONNECTION
                self.propagate_energy()

    def propagate_energy(self):
        # Simple BFS to check if nodes are connected to core
        visited = {self.core}
        queue = [self.core]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and (nx, ny) not in visited and
                    ((x, y), (nx, ny)) in self.connections or ((nx, ny), (x, y)) in self.connections):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                    node = self.get_node_at(nx, ny)
                    if node:
                        node.energy = 100
        # Reset energy for unconnected nodes
        for node in self.nodes:
            if (node.x, node.y) not in visited:
                node.energy = 0
                node.active = False

    def spawn_void(self):
        if random.random() < VOID_SPAWN_RATE and len(self.void_creatures) < 5:
            edges = [(0, y) for y in range(GRID_HEIGHT)] + [(GRID_WIDTH - 1, y) for y in range(GRID_HEIGHT)] + \
                    [(x, 0) for x in range(GRID_WIDTH)] + [(x, GRID_HEIGHT - 1) for x in range(GRID_WIDTH)]
            x, y = random.choice(edges)
            if self.grid[y][x] == 0:
                self.void_creatures.append(VoidCreature(x, y))

    def check_collisions(self) -> bool:
        for creature in self.void_creatures[:]:
            if (creature.x, creature.y) == self.core:
                return False
            node = self.get_node_at(creature.x, creature.y)
            if node and node.energy > 0:
                self.nodes.remove(node)
                self.grid[creature.y][creature.x] = 0
                self.void_creatures.remove(creature)
                self.connections = {(p1, p2) for p1, p2 in self.connections if p1 != (creature.x, creature.y) and p2 != (creature.x, creature.y)}
                self.propagate_energy()
        return True

    def draw(self):
        screen.fill(BLACK)
        # Draw grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(screen, GRAY, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)
        # Draw connections
        for (x1, y1), (x2, y2) in self.connections:
            pygame.draw.line(screen, YELLOW, 
                            (x1 * GRID_SIZE + GRID_SIZE // 2, y1 * GRID_SIZE + GRID_SIZE // 2),
                            (x2 * GRID_SIZE + GRID_SIZE // 2, y2 * GRID_SIZE + GRID_SIZE // 2), 3)
        # Draw nodes and core
        for node in self.nodes:
            node.draw()
        pygame.draw.rect(screen, BLUE, (self.core[0] * GRID_SIZE, self.core[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        # Draw void creatures
        for creature in self.void_creatures:
            creature.draw()
        # Draw UI
        energy_text = self.font.render(f"Energy: {self.energy}", True, WHITE)
        screen.blit(energy_text, (10, 10))

async def main():
    game = Game()
    running = True
    selected_node = None
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_x, grid_y = event.pos[0] // GRID_SIZE, event.pos[1] // GRID_SIZE
                if game.get_node_at(grid_x, grid_y):
                    if selected_node:
                        game.add_connection(selected_node, (grid_x, grid_y))
                        selected_node = None
                    else:
                        selected_node = (grid_x, grid_y)

        game.spawn_void()
        for creature in game.void_creatures:
            creature.move_towards(*game.core)
        if not game.check_collisions():
            running = False
        if game.energy <= 0 and not any(node.active for node in game.nodes):
            running = False  # Lose condition
        game.draw()
        pygame.display.flip()
        game.clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
