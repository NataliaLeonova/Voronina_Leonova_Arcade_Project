import math
import random
from typing import List, Tuple


class MazeGenerator:
    """Генератор лабиринтов"""

    @staticmethod
    def generate_perfect_maze(width: int, height: int) -> List[List[int]]:
        """Сгенерировать идеальный лабиринт"""
        # Все стены
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # Начальная точка
        start_x, start_y = 1, 1
        maze[start_y][start_x] = 0

        # Стек для DFS
        stack = [(start_x, start_y)]
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]

        while stack:
            x, y = stack[-1]
            random.shuffle(directions)

            moved = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                    if maze[ny][nx] == 1:
                        # Убираем стену между
                        maze[y + dy // 2][x + dx // 2] = 0
                        maze[ny][nx] = 0
                        stack.append((nx, ny))
                        moved = True
                        break

            if not moved:
                stack.pop()

        return maze

    @staticmethod
    def add_exit_path(maze: List[List[int]], exit_pos: Tuple[int, int]) -> List[List[int]]:
        """Добавить гарантированный путь к выходу"""
        width = len(maze[0])
        height = len(maze)

        # Простой путь от центра к выходу
        center_x, center_y = width // 2, height // 2
        exit_x, exit_y = exit_pos

        # Соединяем по прямой
        x, y = center_x, center_y
        while x != exit_x or y != exit_y:
            if x < exit_x:
                x += 1
            elif x > exit_x:
                x -= 1
            elif y < exit_y:
                y += 1
            elif y > exit_y:
                y -= 1

            if 0 <= x < width and 0 <= y < height:
                maze[y][x] = 0
                # Убираем соседние клетки для ширины пути
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        maze[ny][nx] = 0

        return maze