# horror_3d.py - НАСТОЯЩИЙ ЛАБИРИНТ С АЛГОРИТМОМ (с улучшенной картой)
import arcade
import random
import math
import time
import json
import os
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Particle:
    """Частица для эффектов"""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple
    size: float
    alpha: int = 255


@dataclass
class Monster:
    """Видимый монстр с моделью"""
    x: float
    y: float
    speed: float
    detection_range: float
    type: str
    last_sound: float = 0
    active: bool = True
    health: int = 3
    attack_cooldown: float = 0
    visible: bool = True


@dataclass
class Objective:
    """Цель игры"""
    x: float
    y: float
    type: str  # 'key', 'note', 'exit'
    collected: bool = False


@dataclass
class Hint:
    """Подсказка в мире"""
    x: float
    y: float
    text: str
    collected: bool = False


class Horror3DGame(arcade.View):
    """3D хоррор с НАСТОЯЩИМ ЛАБИРИНТОМ"""

    def __init__(self, fear_profile=None):
        super().__init__()

        print("=" * 60)
        print("FEAR_OS: НАСТОЯЩИЙ ЛАБИРИНТ СТРАХА - УРОВЕНЬ 2")
        print("=" * 60)

        # === ПРОФИЛЬ СТРАХОВ ===
        self.fear_profile = fear_profile

        # === НАСТРОЙКИ ИГРОКА ===
        self.player_x = 1.5
        self.player_y = 1.5
        self.player_angle = 0.0
        self.player_sanity = 100.0
        self.player_health = 100.0
        self.player_stress = 30.0

        # === КАРТА И КОЛЛИЗИИ ===
        self.map_width = 21  # Нечетное для алгоритма
        self.map_height = 21
        self.exit_location = (self.map_width - 2, self.map_height - 2)  # Противоположный угол
        self.map = self.generate_real_maze()  # Настоящий лабиринт
        self.collision_map = self.create_collision_map()

        # === НАСТРОЙКИ МИНИКАРТЫ ===
        self.show_minimap = False  # По умолчанию выключена
        self.minimap_toggle_key = arcade.key.M
        self.last_minimap_toggle_time = 0
        self.minimap_cooldown = 0.3  # Защита от двойного нажатия

        # === ПОДСКАЗКИ И ОБЪЕКТЫ ===
        self.hints: List[Hint] = []
        self.objectives: List[Objective] = []
        self.keys_collected = 0
        self.keys_needed = 3
        self.exit_found = False
        self.init_hints_and_objectives()

        # === ОСВЕЩЕНИЕ И АТМОСФЕРА ===
        self.flashlight_on = True
        self.flashlight_battery = 150.0
        self.flashlight_flicker = 0.0
        self.ambient_light = 0.3  # Темнее для атмосферы

        # === ЭФФЕКТЫ УЖАСА ===
        self.screen_shake = 0.0
        self.blood_overlay = 0.0
        self.distortion = 0.0
        self.vignette = 0.4

        # === ИГРОВОЕ ВРЕМЯ ===
        self.game_time = 0.0
        self.time_since_last_scare = 0.0
        self.time_in_darkness = 0.0

        # === ЧАСТИЦЫ И ЭФФЕКТЫ ===
        self.particles: List[Particle] = []
        self.blood_particles: List[Particle] = []

        # === МОНСТРЫ ===
        self.monsters: List[Monster] = []
        self.max_monsters = 2
        self.init_monsters()

        # === УПРАВЛЕНИЕ ===
        # ИСПРАВЛЕНО: правильные клавиши для движения и поворота
        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,  # ДВИЖЕНИЕ ВЛЕВО
            arcade.key.D: False,  # ДВИЖЕНИЕ ВПРАВО
            arcade.key.LEFT: False,  # ПОВОРОТ ВЛЕВО
            arcade.key.RIGHT: False,  # ПОВОРОТ ВПРАВО
            arcade.key.Q: False,  # ПОВОРОТ ВЛЕВО
            arcade.key.E: False,  # ПОВОРОТ ВПРАВО
        }
        self.mouse_look = True
        self.mouse_sensitivity = 0.002
        self.turn_speed = 1.8

        # === ЗВУКИ ===
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager()
        except:
            self.sound_manager = None

        # === СОСТОЯНИЕ ИГРЫ ===
        self.game_active = True
        self.game_won = False
        self.show_tutorial = True
        self.tutorial_time = 6.0

        # === СТАТИСТИКА ===
        self.jump_scares_triggered = 0
        self.distance_traveled = 0.0
        self.hints_collected = 0

        print("=" * 60)
        print("ЦЕЛЬ: Найдите 3 ключа и выход в противоположном углу!")
        print("Управление:")
        print("- WASD - движение (A-влево, D-вправо)")
        print("- МЫШЬ или СТРЕЛКИ (← влево, → вправо) - обзор")
        print("- Q/E - поворот (Q-влево, E-вправо)")
        print("- M - ВКЛ/ВЫКЛ карту (держите открытой для навигации)")
        print("- F - вкл/выкл фонарик")
        print("- ПРОБЕЛ - крик (отпугивает монстров)")
        print("=" * 60)

        self.play_sound('wind', volume=0.4)

    # ==================== АЛГОРИТМ ГЕНЕРАЦИИ ЛАБИРИНТА ====================

    def generate_real_maze(self):
        """Создать настоящий лабиринт с алгоритмом"""
        # 1 - стена, 0 - проход
        maze = [[1 for _ in range(self.map_width)] for _ in range(self.map_height)]

        # Алгоритм "Рекурсивный backtracking" для идеального лабиринта
        stack = []

        # Начинаем с нечетной клетки (чтобы были стены вокруг)
        start_x, start_y = 1, 1
        maze[start_y][start_x] = 0
        stack.append((start_x, start_y))

        # Все возможные направления (dx, dy)
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]

        while stack:
            x, y = stack[-1]

            # Собираем все возможные непосещенные направления
            available_dirs = []
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.map_width - 1 and 1 <= ny < self.map_height - 1:
                    if maze[ny][nx] == 1:  # Если это стена (не посещали)
                        # Проверяем что все соседи не посещены (для идеального лабиринта)
                        neighbor_visited = False
                        for ndx, ndy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nnx, nny = nx + ndx, ny + ndy
                            if 0 <= nnx < self.map_width and 0 <= nny < self.map_height:
                                if maze[nny][nnx] == 0 and (nnx != x or nny != y):
                                    neighbor_visited = True
                                    break

                        if not neighbor_visited:
                            available_dirs.append((dx, dy))

            if available_dirs:
                # Выбираем случайное направление
                dx, dy = random.choice(available_dirs)
                nx, ny = x + dx, y + dy

                # Убираем стену между текущей и новой клеткой
                maze[y + dy // 2][x + dx // 2] = 0
                maze[ny][nx] = 0

                stack.append((nx, ny))
            else:
                # Backtrack
                stack.pop()

        # Гарантируем выход
        exit_x, exit_y = self.exit_location
        maze[exit_y][exit_x] = 0

        # Делаем выход доступным (убираем стены вокруг)
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = exit_x + dx, exit_y + dy
            if 1 <= nx < self.map_width - 1 and 1 <= ny < self.map_height - 1:
                maze[ny][nx] = 0

        # Убираем некоторые тупики для лучшей связности
        for _ in range(self.map_width * self.map_height // 10):
            x = random.randint(2, self.map_width - 3)
            y = random.randint(2, self.map_height - 3)

            if maze[y][x] == 1:  # Если это стена
                # Проверяем может ли она быть убрана
                wall_count = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                        if maze[ny][nx] == 1:
                            wall_count += 1

                # Если это тонкая стена (окружена проходами)
                if wall_count <= 1:
                    maze[y][x] = 0

        return maze

    def create_collision_map(self):
        """Создать карту коллизий"""
        collision = [[False for _ in range(self.map_width)] for _ in range(self.map_height)]

        for y in range(self.map_height):
            for x in range(self.map_width):
                collision[y][x] = (self.map[y][x] == 1)

        return collision

    def check_collision(self, x, y):
        """Проверить коллизию с картой"""
        ix, iy = int(x), int(y)

        if 0 <= ix < self.map_width and 0 <= iy < self.map_height:
            return self.collision_map[iy][ix]

        return True

    def init_hints_and_objectives(self):
        """Инициализировать подсказки и цели"""
        # Находим открытые клетки для подсказок
        open_cells = []
        for y in range(1, self.map_height - 1):
            for x in range(1, self.map_width - 1):
                if self.map[y][x] == 0:
                    # Проверяем что это не тупик (есть хотя бы 2 выхода)
                    exits = 0
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                            if self.map[ny][nx] == 0:
                                exits += 1

                    if exits >= 2:  # Не тупик
                        open_cells.append((x, y))

        hint_texts = [
            "Выход в противоположном углу",
            "Ищите красный свет",
            "Ключи сверкают золотым",
            "Держитесь правой стороны",
            "Карта: M (удерживайте открытой)",
            "Монстры боятся крика",
            "Фонарик разряжается",
            "Не теряйте рассудок"
        ]

        # Размещаем подсказки в случайных открытых клетках
        for i, text in enumerate(hint_texts):
            if i < len(open_cells):
                x, y = random.choice(open_cells)
                open_cells.remove((x, y))  # Чтобы не было повторений
                self.hints.append(Hint(x=x + 0.5, y=y + 0.5, text=text))
                print(f"✓ Подсказка '{text[:15]}...' в ({x}, {y})")

        # Находим места для ключей (в тупиках или развилках)
        key_positions = []
        attempts = 0
        while len(key_positions) < 3 and attempts < 100:
            x = random.randint(1, self.map_width - 2)
            y = random.randint(1, self.map_height - 2)

            if self.map[y][x] == 0:
                # Проверяем что достаточно далеко от старта
                distance_to_start = math.sqrt((x - 1) ** 2 + (y - 1) ** 2)
                if distance_to_start > 5:
                    key_positions.append((x, y))
                    self.objectives.append(Objective(x=x + 0.5, y=y + 0.5, type='key'))
                    print(f"✓ Ключ размещен в ({x}, {y})")
            attempts += 1

        # Если не нашли достаточно ключей, размещаем в любых открытых клетках
        if len(key_positions) < 3:
            for x in range(1, self.map_width - 1):
                for y in range(1, self.map_height - 1):
                    if self.map[y][x] == 0 and (x, y) not in key_positions:
                        key_positions.append((x, y))
                        self.objectives.append(Objective(x=x + 0.5, y=y + 0.5, type='key'))
                        print(f"✓ Ключ размещен в ({x}, {y}) (запасной вариант)")
                        if len(key_positions) >= 3:
                            break
                if len(key_positions) >= 3:
                    break

        # Выход
        exit_x, exit_y = self.exit_location
        self.objectives.append(Objective(
            x=exit_x + 0.5,
            y=exit_y + 0.5,
            type='exit'
        ))
        print(f"✓ Выход размещен в ({exit_x}, {exit_y})")

    def init_monsters(self):
        """Создать монстров в тупиках"""
        monster_positions = []
        attempts = 0

        while len(monster_positions) < 2 and attempts < 50:
            x = random.randint(1, self.map_width - 2)
            y = random.randint(1, self.map_height - 2)

            if self.map[y][x] == 0:
                # Проверяем что это тупик (только 1 выход)
                exits = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                        if self.map[ny][nx] == 0:
                            exits += 1

                if exits == 1:  # Тупик - идеальное место для монстра
                    monster_positions.append((x, y))
                    self.monsters.append(Monster(
                        x=x + 0.5, y=y + 0.5,
                        speed=0.006,
                        detection_range=3.0,
                        type='stalker'
                    ))
                    print(f"✓ Монстр размещен в тупике ({x}, {y})")

            attempts += 1

        # Если не нашли тупики, размещаем в любых местах
        if len(monster_positions) < 2:
            for x in range(1, self.map_width - 1):
                for y in range(1, self.map_height - 1):
                    if self.map[y][x] == 0 and (x, y) not in monster_positions:
                        monster_positions.append((x, y))
                        self.monsters.append(Monster(
                            x=x + 0.5, y=y + 0.5,
                            speed=0.005,
                            detection_range=2.5,
                            type='stalker'
                        ))
                        print(f"✓ Монстр размещен в ({x}, {y})")
                        if len(monster_positions) >= 2:
                            break
                if len(monster_positions) >= 2:
                    break

    # ==================== ОСНОВНАЯ ЛОГИКА ====================

    def on_update(self, delta_time: float):
        """Главный цикл обновления"""
        if not self.game_active or self.game_won:
            return

        self.game_time += delta_time
        self.time_since_last_scare += delta_time
        self.tutorial_time = max(0, self.tutorial_time - delta_time)
        self.last_minimap_toggle_time = max(0, self.last_minimap_toggle_time - delta_time)

        # Обновление игрока
        self.update_player(delta_time)
        self.update_flashlight(delta_time)
        self.update_monsters(delta_time)
        self.update_particles(delta_time)

        # Проверка подсказки
        self.check_hints()
        self.check_objectives()
        self.update_horror_events(delta_time)
        self.update_ambient_sounds(delta_time)

        # Потеря рассудка в темноте
        if not self.flashlight_on or self.flashlight_battery < 20:
            self.time_in_darkness += delta_time
            if self.time_in_darkness > 3:
                self.player_sanity = max(0, self.player_sanity - delta_time)
        else:
            self.time_in_darkness = max(0, self.time_in_darkness - delta_time)

        # Победа
        if self.exit_found and self.keys_collected >= self.keys_needed:
            self.win_game()

        # Поражение
        if self.player_health <= 0:
            self.end_game("ВАС УБИЛИ")
        elif self.player_sanity <= 0:
            self.end_game("ВЫ СОШЛИ С УМА")

    def update_player(self, delta_time):
        """Обновить состояние игрока"""
        move_forward = 0
        move_right = 0
        move_speed = 3.0 * delta_time  # Медленнее для лабиринта

        if self.keys_pressed[arcade.key.W]:
            move_forward += move_speed
        if self.keys_pressed[arcade.key.S]:
            move_forward -= move_speed
        if self.keys_pressed[arcade.key.A]:  # ДВИЖЕНИЕ ВЛЕВО
            move_right -= move_speed
        if self.keys_pressed[arcade.key.D]:  # ДВИЖЕНИЕ ВПРАВО
            move_right += move_speed

        # ПОВОРОТ - ИСПРАВЛЕННЫЕ КЛАВИШИ (БЫЛО ПЕРЕПУТАНО)
        turn_amount = 0
        # ← (влево) и Q (влево) - поворот налево (УМЕНЬШАЕТ угол)
        if self.keys_pressed[arcade.key.LEFT] or self.keys_pressed[arcade.key.Q]:
            turn_amount -= self.turn_speed * delta_time
        # → (вправо) и E (вправо) - поворот направо (УВЕЛИЧИВАЕТ угол)
        if self.keys_pressed[arcade.key.RIGHT] or self.keys_pressed[arcade.key.E]:
            turn_amount += self.turn_speed * delta_time

        if turn_amount != 0:
            self.player_angle += turn_amount

        if move_forward != 0 or move_right != 0:
            cos_a = math.cos(self.player_angle)
            sin_a = math.sin(self.player_angle)

            forward_x = move_forward * cos_a
            forward_y = move_forward * sin_a

            right_x = move_right * -sin_a
            right_y = move_right * cos_a

            move_x = forward_x + right_x
            move_y = forward_y + right_y

            self.apply_movement(move_x, move_y)

            if random.random() < 0.3:
                self.play_sound('footstep', volume=0.15)

        # Восстановление стресса
        if self.player_stress > 30:
            self.player_stress = max(30, self.player_stress - delta_time * 5)

    def apply_movement(self, move_x, move_y):
        """Применить движение с проверкой коллизий"""
        new_x = self.player_x + move_x
        new_y = self.player_y + move_y

        if not self.check_collision(new_x, self.player_y):
            self.player_x = new_x

        if not self.check_collision(self.player_x, new_y):
            self.player_y = new_y

    def update_flashlight(self, delta_time):
        """Обновить состояние фонарика"""
        if self.flashlight_on and self.flashlight_battery > 0:
            self.flashlight_battery = max(0, self.flashlight_battery - delta_time * 0.6)
            if self.flashlight_battery <= 0:
                self.flashlight_on = False
        else:
            if self.flashlight_battery < 150:
                self.flashlight_battery = min(150, self.flashlight_battery + delta_time * 0.15)

    def update_monsters(self, delta_time):
        """Обновить монстров"""
        for monster in self.monsters:
            if not monster.active:
                continue

            monster.attack_cooldown = max(0, monster.attack_cooldown - delta_time)

            dx = self.player_x - monster.x
            dy = self.player_y - monster.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Защита от деления на ноль
            if distance < 0.1:
                continue

            if distance < monster.detection_range:
                if distance > 2.0:
                    move_x = (dx / distance) * monster.speed * delta_time * 60
                    move_y = (dy / distance) * monster.speed * delta_time * 60

                    # Монстр может ходить только по проходам
                    if not self.check_collision(monster.x + move_x, monster.y):
                        monster.x += move_x
                    if not self.check_collision(monster.x, monster.y + move_y):
                        monster.y += move_y

                if distance < 1.8 and monster.attack_cooldown <= 0:
                    self.monster_attack(monster)

    def monster_attack(self, monster):
        """Атака монстра"""
        damage = 10
        self.player_health -= damage
        self.player_stress = min(100, self.player_stress + 12)

        monster.attack_cooldown = 4.0

        self.screen_shake = 0.4
        self.blood_overlay = min(1.0, self.blood_overlay + 0.6)

        for _ in range(10):
            self.blood_particles.append(Particle(
                x=self.window.width // 2 + random.randint(-40, 40),
                y=self.window.height // 2 + random.randint(-40, 40),
                vx=random.uniform(-8, 8),
                vy=random.uniform(-8, 8),
                life=random.uniform(0.5, 1.0),
                color=(200, 20, 20),
                size=random.uniform(3, 6)
            ))

        self.play_sound('jump_scare', volume=0.5)
        print(f"Монстр атаковал! -{damage} здоровья")

    # ==================== УПРАВЛЕНИЕ ====================

    def on_key_press(self, symbol: int, modifiers: int):
        """Нажатие клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = True

        elif symbol == arcade.key.F:
            if self.flashlight_battery > 0:
                self.flashlight_on = not self.flashlight_on
                self.play_sound('door_creak', volume=0.3)

        elif symbol == arcade.key.M:
            # Переключаем карту с защитой от двойного нажатия
            if self.last_minimap_toggle_time <= 0:
                self.show_minimap = not self.show_minimap
                self.last_minimap_toggle_time = self.minimap_cooldown

                if self.show_minimap:
                    self.play_sound('upgrade1', volume=0.3)
                    print("Карта ВКЛЮЧЕНА (M для выключения)")
                else:
                    self.play_sound('upgrade2', volume=0.3)
                    print("Карта ВЫКЛЮЧЕНА (M для включения)")

        elif symbol == arcade.key.SPACE:
            self.play_sound('scream', volume=0.6)
            self.screen_shake = 0.3

            for monster in self.monsters:
                dx = monster.x - self.player_x
                dy = monster.y - self.player_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0.1 and distance < 8:
                    monster.x -= dx * 0.4
                    monster.y -= dy * 0.4
                    monster.attack_cooldown = 5.0

            self.player_stress = min(100, self.player_stress + 10)
            print("Крик! Монстры напуганы.")

        elif symbol == arcade.key.ESCAPE:
            self.end_game("ВЫХОД")

        # Тестовые команды
        elif symbol == arcade.key.T:
            self.player_x = self.map_width - 1.5
            self.player_y = self.map_height - 1.5
            print(f"Телепорт к выходу ({self.player_x}, {self.player_y})")

        elif symbol == arcade.key.K:
            self.keys_collected = self.keys_needed
            print("Все ключи получены")

        elif symbol == arcade.key.H:
            self.player_health = 100
            self.player_sanity = 100
            self.player_stress = 30
            print("Здоровье восстановлено")

    def on_key_release(self, symbol: int, modifiers: int):
        """Отпускание клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Движение мыши"""
        if self.game_active and self.mouse_look:
            if abs(dx) < 100:
                self.player_angle += dx * self.mouse_sensitivity

    # ==================== ПОБЕДА ====================

    def win_game(self):
        """Победа в игре"""
        self.game_won = True
        self.game_active = False

        print("=" * 60)
        print("ПОБЕДА! ВЫ ВЫБРАЛИСЬ ИЗ НАСТОЯЩЕГО ЛАБИРИНТА!")
        print("=" * 60)
        print(f"Время: {int(self.game_time)} секунд")
        print(f"Найдено подсказок: {self.hints_collected}/{len(self.hints)}")
        print(f"Финальный стресс: {int(self.player_stress)}%")
        print(f"Остаток рассудка: {int(self.player_sanity)}%")
        print("=" * 60)

        self.play_sound('coin1', volume=0.8)

        # Собираем статистику
        game_stats = {
            'time': self.game_time,
            'hints_collected': self.hints_collected,
            'total_hints': len(self.hints),
            'keys_collected': self.keys_collected,
            'total_keys': self.keys_needed,
            'jump_scares': self.jump_scares_triggered,
            'stress_level': self.player_stress,
            'sanity_level': self.player_sanity
        }

        # Переход к результатам - 2 попытки импорта
        try:
            # Попытка 1: прямой импорт
            from results import ResultsView
            results_view = ResultsView(self.fear_profile, game_stats)
            self.window.show_view(results_view)
        except ImportError:
            try:
                # Попытка 2: добавить текущую директорию в путь
                import os
                import sys
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                sys.path.append(project_root)

                from results import ResultsView
                results_view = ResultsView(self.fear_profile, game_stats)
                self.window.show_view(results_view)
            except Exception as e:
                print(f"Не удалось загрузить результаты: {e}")
                print("Возврат в главное меню...")
                try:
                    from scenes.main_menu import MainMenuView
                    menu_view = MainMenuView()
                    self.window.show_view(menu_view)
                except:
                    # Если всё сломалось, просто выходим
                    arcade.exit()

    def end_game(self, reason="КОНЕЦ"):
        """Завершить игру"""
        self.game_active = False
        print("=" * 60)
        print(f"ИГРА ОКОНЧЕНА: {reason}")
        print("=" * 60)

        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)

    # ==================== ОТРИСОВКА ====================

    def on_draw(self):
        """Отрисовка кадра"""
        self.clear()

        # Тряска экрана
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.uniform(-self.screen_shake, self.screen_shake) * 20
            shake_y = random.uniform(-self.screen_shake, self.screen_shake) * 20

        # 3D вид
        self.draw_3d_view(shake_x, shake_y)
        self.draw_effects(shake_x, shake_y)
        self.draw_hud()

        # Миникарта (теперь включается/выключается по M)
        if self.show_minimap:
            self.draw_minimap()

        # Обучение
        if self.show_tutorial and self.tutorial_time > 0:
            self.draw_tutorial()

    def draw_3d_view(self, shake_x=0, shake_y=0):
        """Нарисовать 3D вид"""
        # Фон
        if self.flashlight_on and self.flashlight_battery > 20:
            bg_color = (30, 25, 40)
        else:
            bg_color = (10, 5, 20)

        arcade.draw_lrbt_rectangle_filled(
            0 + shake_x, self.window.width + shake_x,
            0 + shake_y, self.window.height + shake_y,
            bg_color
        )

        # Стены (настоящий рейкастинг)
        self.draw_walls(shake_x, shake_y)

        # Монстры
        self.draw_monsters(shake_x, shake_y)

        # Цели и подсказки
        self.draw_objectives(shake_x, shake_y)
        self.draw_hints_in_world(shake_x, shake_y)

        # Фонарик
        if self.flashlight_on and self.flashlight_battery > 0:
            self.draw_flashlight_effect(shake_x, shake_y)

    def draw_walls(self, shake_x=0, shake_y=0):
        """Нарисовать стены через рейкастинг"""
        num_rays = 120  # Больше лучей для качества
        fov = math.pi / 1.4  # Широкое поле зрения

        ray_step = fov / num_rays
        column_width = self.window.width / num_rays

        for i in range(num_rays):
            ray_angle = (self.player_angle - fov / 2) + i * ray_step
            distance = self.cast_ray(ray_angle)

            if distance > 0:
                # Высота стены (чем дальше - тем меньше)
                wall_height = min(600, self.window.height / max(distance, 0.1))

                x = i * column_width + shake_x
                y_bottom = (self.window.height - wall_height) / 2 + shake_y
                y_top = y_bottom + wall_height

                # Цвет стены с учетом расстояния и освещения
                darken = min(1.0, 7.0 / distance)

                # Темнее без фонарика
                if not self.flashlight_on or self.flashlight_battery < 20:
                    darken *= 0.4

                # Мерцание
                if self.flashlight_flicker > 0:
                    flicker = math.sin(self.flashlight_flicker * 25) * 0.15
                    darken *= (1 + flicker)
                    self.flashlight_flicker = max(0, self.flashlight_flicker - 0.2)

                # Разные оттенки для разнообразия
                if i % 15 < 5:
                    color = (
                        int(140 * darken),
                        int(120 * darken),
                        int(100 * darken)
                    )
                else:
                    color = (
                        int(120 * darken),
                        int(100 * darken),
                        int(80 * darken)
                    )

                # Рисуем колонну стены
                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                    y_bottom, y_top,
                    color
                )

                # Пол (простой)
                floor_y = y_bottom
                floor_color = (
                    int(60 * darken),
                    int(50 * darken),
                    int(40 * darken)
                )
                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                       0 + shake_y, floor_y,
                    floor_color
                )

                # Потолок
                ceil_y = y_top
                ceil_color = (
                    int(40 * darken),
                    int(35 * darken),
                    int(50 * darken)
                )
                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                    ceil_y, self.window.height + shake_y,
                    ceil_color
                )

    def cast_ray(self, angle):
        """Кастовать луч и найти стену"""
        step = 0.05  # Более точный шаг для лабиринта
        max_dist = 30.0

        x = self.player_x
        y = self.player_y
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)

        distance = 0

        while distance < max_dist:
            distance += step

            test_x = x + dir_x * distance
            test_y = y + dir_y * distance

            if self.check_collision(test_x, test_y):
                return distance

        return max_dist

    def draw_monsters(self, shake_x=0, shake_y=0):
        """Нарисовать монстров"""
        for monster in self.monsters:
            if not monster.active:
                continue

            dx = monster.x - self.player_x
            dy = monster.y - self.player_y

            distance = math.sqrt(dx * dx + dy * dy)

            # Защита от деления на ноль
            if distance < 0.1:
                continue

            angle_to_monster = math.atan2(dy, dx) - self.player_angle

            # Нормализация угла
            while angle_to_monster > math.pi:
                angle_to_monster -= 2 * math.pi
            while angle_to_monster < -math.pi:
                angle_to_monster += 2 * math.pi

            fov = math.pi / 1.4
            if abs(angle_to_monster) < fov / 2 and distance < 20:
                screen_x = self.window.width / 2 + (angle_to_monster / (fov / 2)) * self.window.width / 2 + shake_x

                size = max(20, min(100, 200 / distance))
                screen_y = self.window.height / 2 + shake_y

                # Монстр темнее вдалеке
                darken = min(1.0, 12 / distance)
                color = (
                    int(180 * darken),
                    int(60 * darken),
                    int(60 * darken)
                )

                if not self.flashlight_on or self.flashlight_battery < 20:
                    color = (
                        color[0] // 3,
                        color[1] // 3,
                        color[2] // 3
                    )

                # Тело
                arcade.draw_circle_filled(screen_x, screen_y, size, color)

                # Глаза
                eye_size = size * 0.15
                eye_offset = size * 0.3

                arcade.draw_circle_filled(
                    screen_x - eye_offset, screen_y + eye_size * 0.7,
                    eye_size, (255, 255, 255, min(255, 180))
                )
                arcade.draw_circle_filled(
                    screen_x + eye_offset, screen_y + eye_size * 0.7,
                    eye_size, (255, 255, 255, min(255, 180))
                )

                arcade.draw_circle_filled(
                    screen_x - eye_offset, screen_y + eye_size * 0.7,
                    eye_size * 0.6, (255, 0, 0)
                )
                arcade.draw_circle_filled(
                    screen_x + eye_offset, screen_y + eye_size * 0.7,
                    eye_size * 0.6, (255, 0, 0)
                )

    def draw_objectives(self, shake_x=0, shake_y=0):
        """Нарисовать цели"""
        for obj in self.objectives:
            if obj.collected:
                continue

            dx = obj.x - self.player_x
            dy = obj.y - self.player_y

            distance = math.sqrt(dx * dx + dy * dy)

            # Защита от деления на ноль
            if distance < 0.1:
                continue

            angle_to_obj = math.atan2(dy, dx) - self.player_angle

            while angle_to_obj > math.pi:
                angle_to_obj -= 2 * math.pi
            while angle_to_obj < -math.pi:
                angle_to_obj += 2 * math.pi

            fov = math.pi / 1.4
            if abs(angle_to_obj) < fov / 2 and distance < 15:
                screen_x = self.window.width / 2 + (angle_to_obj / (fov / 2)) * self.window.width / 2 + shake_x

                size = max(10, min(40, 80 / distance))
                screen_y = self.window.height / 2 + shake_y

                if obj.type == 'key':
                    # Яркое мерцание ключа
                    pulse = (math.sin(time.time() * 4) + 1.5) / 2.5
                    color = (
                        int(255 * pulse),
                        int(215 * pulse),
                        int(50 * pulse)
                    )

                    arcade.draw_circle_filled(screen_x, screen_y, size, color)

                    # Внутренний круг
                    arcade.draw_circle_filled(
                        screen_x, screen_y,
                        size * 0.6,
                        (255, 255, 200)
                    )

                elif obj.type == 'exit':
                    # Мигающий красный выход
                    if int(time.time() * 1.5) % 2 == 0:
                        color = (255, 50, 50)
                        arcade.draw_circle_filled(screen_x, screen_y, size, color)

                        # Крест на выходе
                        cross_size = size * 0.7
                        arcade.draw_line(
                            screen_x - cross_size, screen_y,
                            screen_x + cross_size, screen_y,
                            (255, 200, 200), 3
                        )
                        arcade.draw_line(
                            screen_x, screen_y - cross_size,
                            screen_x, screen_y + cross_size,
                            (255, 200, 200), 3
                        )

    def draw_hints_in_world(self, shake_x=0, shake_y=0):
        """Нарисовать подсказки в мире"""
        for hint in self.hints:
            if hint.collected:
                continue

            dx = hint.x - self.player_x
            dy = hint.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            # Защита от деления на ноль
            if distance < 0.1:
                continue

            angle_to_hint = math.atan2(dy, dx) - self.player_angle

            while angle_to_hint > math.pi:
                angle_to_hint -= 2 * math.pi
            while angle_to_hint < -math.pi:
                angle_to_hint += 2 * math.pi

            fov = math.pi / 1.4
            if abs(angle_to_hint) < fov / 2 and distance < 12:
                screen_x = self.window.width / 2 + (angle_to_hint / (fov / 2)) * self.window.width / 2 + shake_x
                screen_y = self.window.height / 2 + shake_y

                size = max(6, min(30, 60 / distance))

                # Синее свечение подсказки
                pulse = (math.sin(time.time() * 2.5) + 1) / 2
                alpha = min(255, 120 + int(80 * pulse))  # ГАРАНТИРУЕМ < 255

                arcade.draw_circle_filled(
                    screen_x, screen_y,
                    size,
                    (80, 180, 255, alpha)
                )

                arcade.draw_circle_filled(
                    screen_x, screen_y,
                    size * 0.5,
                    (120, 220, 255, min(255, alpha + 30))
                )

    def draw_flashlight_effect(self, shake_x=0, shake_y=0):
        """Нарисовать эффект фонарика"""
        if self.flashlight_battery <= 0:
            return

        center_x = self.window.width // 2 + shake_x
        center_y = self.window.height // 2 + shake_y

        intensity = min(1.0, self.flashlight_battery / 150.0)

        layers = [
            (200 * intensity, min(255, int(40 * intensity))),
            (140 * intensity, min(255, int(25 * intensity))),
            (90 * intensity, min(255, int(12 * intensity)))
        ]

        for radius, alpha in layers:
            arcade.draw_circle_filled(
                center_x, center_y, radius,
                (255, 245, 220, alpha)
            )

    def draw_effects(self, shake_x=0, shake_y=0):
        """Нарисовать эффекты"""
        for particle in self.particles:
            alpha = min(255, particle.alpha)
            arcade.draw_circle_filled(
                particle.x + shake_x,
                particle.y + shake_y,
                particle.size,
                (*particle.color, alpha)
            )

        for particle in self.blood_particles:
            arcade.draw_circle_filled(
                particle.x + shake_x,
                particle.y + shake_y,
                particle.size,
                (*particle.color, 150)
            )

        # Кровь на экране
        if self.blood_overlay > 0:
            alpha = min(255, int(180 * self.blood_overlay))
            arcade.draw_lrbt_rectangle_filled(
                0 + shake_x, self.window.width + shake_x,
                0 + shake_y, self.window.height + shake_y,
                (180, 30, 30, alpha // 4)
            )

            self.blood_overlay = max(0, self.blood_overlay - 0.02)

        # Виньетка
        vignette_strength = self.vignette
        if not self.flashlight_on or self.flashlight_battery < 30:
            vignette_strength *= 1.5

        if vignette_strength > 0:
            alpha = min(255, int(180 * vignette_strength))

            arcade.draw_lrbt_rectangle_filled(
                0 + shake_x, self.window.width + shake_x,
                self.window.height * 0.7 + shake_y, self.window.height + shake_y,
                (0, 0, 0, alpha)
            )

            arcade.draw_lrbt_rectangle_filled(
                0 + shake_x, self.window.width + shake_x,
                0 + shake_y, self.window.height * 0.3 + shake_y,
                (0, 0, 0, alpha)
            )

    def draw_minimap(self):
        """Нарисовать миникарту (включить/выключить по клавише M)"""
        map_width = 350  # БОЛЬШЕ для лучшей видимости
        map_height = 350
        margin = 30
        cell_size = min(map_width // self.map_width, map_height // self.map_height)

        # Рассчитываем позицию для центрирования карты справа
        map_left = self.window.width - margin - map_width
        map_bottom = margin
        map_right = self.window.width - margin
        map_top = margin + map_height

        # ТЕМНЫЙ ПОЛУПРОЗРАЧНЫЙ ФОН для лучшей читаемости
        arcade.draw_lrbt_rectangle_filled(
            map_left - 10,
            map_right + 10,
            map_bottom - 10,
            map_top + 10,
            (0, 0, 0, 220)  # ОЧЕНЬ ТЕМНЫЙ
        )

        # ЯРКАЯ РАМКА КАРТЫ
        arcade.draw_lrbt_rectangle_outline(
            map_left,
            map_right,
            map_bottom,
            map_top,
            (180, 180, 180),  # СВЕТЛО-СЕРЫЙ
            3
        )

        # ЗАГОЛОВОК КАРТЫ
        arcade.draw_text(
            "КАРТА ЛАБИРИНТА",
            map_left + map_width // 2,
            map_top + 15,
            (255, 255, 255),
            18,
            anchor_x="center",
            bold=True
        )

        # ПОДСКАЗКА УПРАВЛЕНИЯ
        arcade.draw_text(
            "M - скрыть карту",
            map_left + map_width // 2,
            map_bottom - 25,
            (200, 200, 255),
            14,
            anchor_x="center"
        )

        # ЛЕГЕНДА
        legend_y = map_top - 20
        legend_items = [
            ("Игрок", (0, 255, 0)),
            ("Ключ", (255, 215, 0)),
            ("Выход", (255, 50, 50)),
            ("Монстр", (200, 50, 50)),
            ("Подсказка", (100, 200, 255))
        ]

        legend_x = map_left + 10
        for text, color in legend_items:
            # Цветной маркер
            arcade.draw_circle_filled(
                legend_x + 8,
                legend_y,
                6,
                color
            )
            # Текст
            arcade.draw_text(
                text,
                legend_x + 20,
                legend_y - 6,
                (220, 220, 220),
                12
            )
            legend_y -= 20

        # РИСУЕМ ЛАБИРИНТ
        for y in range(self.map_height):
            for x in range(self.map_width):
                screen_x = map_left + (x * cell_size) + cell_size // 2
                screen_y = map_bottom + (y * cell_size) + cell_size // 2

                if self.map[y][x] == 1:  # СТЕНА
                    # ЯРКАЯ СТЕНА с текстурой
                    wall_color = (120, 120, 120)  # СВЕТЛО-СЕРЫЙ

                    # Основная стена
                    arcade.draw_lrbt_rectangle_filled(
                        screen_x - cell_size // 2 + 1,
                        screen_x + cell_size // 2 - 1,
                        screen_y - cell_size // 2 + 1,
                        screen_y + cell_size // 2 - 1,
                        wall_color
                    )

                    # Текстура стены (кирпичики)
                    if (x + y) % 2 == 0:
                        texture_color = (100, 100, 100)
                        arcade.draw_lrbt_rectangle_filled(
                            screen_x - cell_size // 4,
                            screen_x,
                            screen_y - cell_size // 4,
                            screen_y + cell_size // 4,
                            texture_color
                        )

                    # Обводка стены
                    arcade.draw_lrbt_rectangle_outline(
                        screen_x - cell_size // 2 + 1,
                        screen_x + cell_size // 2 - 1,
                        screen_y - cell_size // 2 + 1,
                        screen_y + cell_size // 2 - 1,
                        (90, 90, 90),
                        1
                    )

                else:  # ПРОХОД
                    # Темный пол с легкой текстурой
                    if (x + y) % 3 == 0:
                        floor_color = (50, 50, 65)
                    else:
                        floor_color = (60, 60, 75)

                    arcade.draw_lrbt_rectangle_filled(
                        screen_x - cell_size // 2 + 1,
                        screen_x + cell_size // 2 - 1,
                        screen_y - cell_size // 2 + 1,
                        screen_y + cell_size // 2 - 1,
                        floor_color
                    )

                    # Легкая сетка на полу
                    arcade.draw_lrbt_rectangle_outline(
                        screen_x - cell_size // 2 + 1,
                        screen_x + cell_size // 2 - 1,
                        screen_y - cell_size // 2 + 1,
                        screen_y + cell_size // 2 - 1,
                        (40, 40, 55),
                        1
                    )

        # ИГРОК - ЯРКИЙ И БОЛЬШОЙ
        player_x = map_left + (self.player_x * cell_size)
        player_y = map_bottom + (self.player_y * cell_size)
        player_size = max(cell_size // 1.3, 8)

        # Внешний круг
        arcade.draw_circle_filled(
            player_x, player_y,
            player_size,
            (0, 255, 0)  # ЯРКО-ЗЕЛЕНЫЙ
        )

        # Внутренний круг
        arcade.draw_circle_filled(
            player_x, player_y,
            player_size * 0.6,
            (100, 255, 100)
        )

        # Обводка
        arcade.draw_circle_outline(
            player_x, player_y,
            player_size,
            (255, 255, 255),
            2
        )

        # НАПРАВЛЕНИЕ ВЗГЛЯДА
        arrow_len = cell_size * 2.5
        arrow_x = player_x + math.cos(self.player_angle) * arrow_len
        arrow_y = player_y + math.sin(self.player_angle) * arrow_len

        arcade.draw_line(
            player_x, player_y,
            arrow_x, arrow_y,
            (0, 255, 0),
            4
        )

        # Стрелка на конце
        arrow_head_size = 5
        perp_angle = self.player_angle + math.pi / 2

        # Левое крыло стрелки
        left_x = arrow_x + math.cos(perp_angle) * arrow_head_size
        left_y = arrow_y + math.sin(perp_angle) * arrow_head_size
        arcade.draw_line(arrow_x, arrow_y, left_x, left_y, (0, 255, 0), 3)

        # Правое крыло стрелки
        right_x = arrow_x - math.cos(perp_angle) * arrow_head_size
        right_y = arrow_y - math.sin(perp_angle) * arrow_head_size
        arcade.draw_line(arrow_x, arrow_y, right_x, right_y, (0, 255, 0), 3)

        # КЛЮЧИ - ЯРКИЕ И МЕРЦАЮЩИЕ
        for obj in self.objectives:
            if obj.type == 'key' and not obj.collected:
                obj_x = map_left + (obj.x * cell_size)
                obj_y = map_bottom + (obj.y * cell_size)

                # Мерцание
                pulse = (math.sin(time.time() * 3) + 1) / 2
                key_size = max(cell_size // 1.2, 6) * (0.8 + pulse * 0.4)

                # Внешний круг
                arcade.draw_circle_filled(
                    obj_x, obj_y,
                    key_size,
                    (255, 220, 50)  # ЗОЛОТОЙ
                )

                # Внутренний круг
                arcade.draw_circle_filled(
                    obj_x, obj_y,
                    key_size * 0.6,
                    (255, 240, 150)
                )

                # Контур
                arcade.draw_circle_outline(
                    obj_x, obj_y,
                    key_size,
                    (255, 255, 200),
                    2
                )

                # Буква K
                arcade.draw_text(
                    "K",
                    obj_x, obj_y - 3,
                    (100, 80, 0),
                    10,
                    anchor_x="center",
                    anchor_y="center",
                    bold=True
                )

        # ВЫХОД - КРАСНЫЙ И МИГАЮЩИЙ
        exit_obj = next((o for o in self.objectives if o.type == 'exit'), None)
        if exit_obj and not exit_obj.collected:
            exit_x = map_left + (exit_obj.x * cell_size)
            exit_y = map_bottom + (exit_obj.y * cell_size)

            # Мигание
            blink = int(time.time() * 1.5) % 2 == 0
            exit_size = max(cell_size // 1.2, 6)

            if blink:
                # Внешний круг
                arcade.draw_circle_filled(
                    exit_x, exit_y,
                    exit_size,
                    (255, 50, 50)  # КРАСНЫЙ
                )

                # Внутренний круг
                arcade.draw_circle_filled(
                    exit_x, exit_y,
                    exit_size * 0.6,
                    (255, 150, 150)
                )

                # Контур
                arcade.draw_circle_outline(
                    exit_x, exit_y,
                    exit_size,
                    (255, 200, 200),
                    2
                )

                # Буква E (Exit)
                arcade.draw_text(
                    "E",
                    exit_x, exit_y - 3,
                    (100, 0, 0),
                    10,
                    anchor_x="center",
                    anchor_y="center",
                    bold=True
                )

        # ПОДСКАЗКИ - СИНИЕ
        for hint in self.hints:
            if not hint.collected:
                hint_x = map_left + (hint.x * cell_size)
                hint_y = map_bottom + (hint.y * cell_size)

                hint_size = max(cell_size // 2.5, 4)

                arcade.draw_circle_filled(
                    hint_x, hint_y,
                    hint_size,
                    (100, 200, 255)  # СИНИЙ
                )

                arcade.draw_circle_outline(
                    hint_x, hint_y,
                    hint_size,
                    (150, 220, 255),
                    1
                )

                # Точка в центре
                arcade.draw_circle_filled(
                    hint_x, hint_y,
                    hint_size * 0.4,
                    (200, 230, 255)
                )

        # МОНСТРЫ - КРАСНЫЕ И УГРОЖАЮЩИЕ
        for monster in self.monsters:
            if monster.active:
                monster_x = map_left + (monster.x * cell_size)
                monster_y = map_bottom + (monster.y * cell_size)

                # Пульсирующий красный
                pulse = (math.sin(time.time() * 2) + 1) / 2
                monster_size = max(cell_size // 1.3, 6) * (0.7 + pulse * 0.3)

                # Тело монстра
                arcade.draw_circle_filled(
                    monster_x, monster_y,
                    monster_size,
                    (200, 50, 50)
                )

                # Обводка
                arcade.draw_circle_outline(
                    monster_x, monster_y,
                    monster_size,
                    (255, 100, 100),
                    2
                )

                # Глаза (две белые точки)
                eye_offset = monster_size * 0.3
                arcade.draw_circle_filled(
                    monster_x - eye_offset, monster_y,
                    max(2, monster_size * 0.2),
                    (255, 255, 255)
                )
                arcade.draw_circle_filled(
                    monster_x + eye_offset, monster_y,
                    max(2, monster_size * 0.2),
                    (255, 255, 255)
                )

                # Зрачки (красные точки)
                arcade.draw_circle_filled(
                    monster_x - eye_offset, monster_y,
                    max(1, monster_size * 0.1),
                    (255, 0, 0)
                )
                arcade.draw_circle_filled(
                    monster_x + eye_offset, monster_y,
                    max(1, monster_size * 0.1),
                    (255, 0, 0)
                )

                # Рот (линия)
                mouth_y = monster_y - monster_size * 0.2
                arcade.draw_line(
                    monster_x - eye_offset * 0.7, mouth_y,
                    monster_x + eye_offset * 0.7, mouth_y,
                    (100, 0, 0),
                    2
                )

    def draw_hud(self):
        """Нарисовать интерфейс"""
        # Фон HUD
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, 100,
            (0, 0, 0, 180)
        )

        # ИНДИКАТОР КАРТЫ В УГЛУ
        map_indicator_x = self.window.width - 40
        map_indicator_y = 35

        if self.show_minimap:
            # ЗЕЛЕНЫЙ когда карта видна
            arcade.draw_circle_filled(
                map_indicator_x, map_indicator_y,
                10,
                (0, 255, 0)
            )
            arcade.draw_circle_outline(
                map_indicator_x, map_indicator_y,
                10,
                (255, 255, 255),
                2
            )
            arcade.draw_text(
                "M",
                map_indicator_x, map_indicator_y - 3,
                (0, 100, 0),
                12,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
        else:
            # СЕРЫЙ когда карта скрыта
            arcade.draw_circle_outline(
                map_indicator_x, map_indicator_y,
                10,
                (150, 150, 150),
                2
            )
            arcade.draw_text(
                "M",
                map_indicator_x, map_indicator_y - 3,
                (100, 100, 100),
                12,
                anchor_x="center",
                anchor_y="center"
            )

        # Текст под индикатором
        map_status = "ВКЛ" if self.show_minimap else "ВЫКЛ"
        map_color = (100, 255, 100) if self.show_minimap else (200, 200, 200)
        arcade.draw_text(
            f"КАРТА: {map_status}",
            map_indicator_x, 15,
            map_color,
            12,
            anchor_x="center"
        )

        # Здоровье
        health_width = 250 * (self.player_health / 100.0)
        health_color = (50, 200, 50) if self.player_health > 40 else (255, 50, 50)

        arcade.draw_lrbt_rectangle_filled(
            20, 20 + health_width, 20, 35,
            health_color
        )
        arcade.draw_lrbt_rectangle_outline(
            20, 20 + 250, 20, 35,
            (255, 255, 255, 100),
            1
        )

        arcade.draw_text(
            f"ЖИЗНЬ: {int(self.player_health)}%",
            25, 22,
            arcade.color.WHITE, 16
        )

        # Рассудок
        sanity_width = 250 * (self.player_sanity / 100.0)
        sanity_color = (100, 100, 200)

        arcade.draw_lrbt_rectangle_filled(
            20, 20 + sanity_width, 40, 55,
            sanity_color
        )
        arcade.draw_lrbt_rectangle_outline(
            20, 20 + 250, 40, 55,
            (255, 255, 255, 100),
            1
        )

        arcade.draw_text(
            f"РАССУДОК: {int(self.player_sanity)}%",
            25, 42,
            arcade.color.LIGHT_GRAY, 14
        )

        # Стресс
        stress_width = 250 * (self.player_stress / 100.0)
        stress_color = (255, 100, 100) if self.player_stress > 50 else (255, 200, 100)

        arcade.draw_lrbt_rectangle_filled(
            20, 20 + stress_width, 60, 75,
            stress_color
        )
        arcade.draw_lrbt_rectangle_outline(
            20, 20 + 250, 60, 75,
            (255, 255, 255, 100),
            1
        )

        arcade.draw_text(
            f"СТРЕСС: {int(self.player_stress)}%",
            25, 62,
            arcade.color.WHITE, 14
        )

        # Прогресс
        progress_x = self.window.width - 250

        # Ключи
        keys_text = f"КЛЮЧИ: {self.keys_collected}/{self.keys_needed}"
        key_color = (255, 215, 0) if self.keys_collected >= self.keys_needed else arcade.color.WHITE
        arcade.draw_text(
            keys_text,
            progress_x, 60,
            key_color, 20
        )

        # Подсказки
        hints_text = f"ПОДСКАЗКИ: {self.hints_collected}/{len(self.hints)}"
        arcade.draw_text(
            hints_text,
            progress_x, 35,
            (100, 200, 255), 16
        )

        # Время
        arcade.draw_text(
            f"ВРЕМЯ: {int(self.game_time)}с",
            progress_x, 85,
            arcade.color.LIGHT_GRAY, 14
        )

        # Фонарик
        info_x = self.window.width // 2 - 100

        if self.flashlight_on:
            battery_text = f"ФОНАРИК: {int(self.flashlight_battery)}%"
            battery_color = (100, 255, 100) if self.flashlight_battery > 30 else (255, 100, 100)
            arcade.draw_text(
                battery_text,
                info_x, 85,
                battery_color, 14
            )

        # Сообщения
        if self.exit_found:
            arcade.draw_text(
                "✓ ВЫХОД НАЙДЕН!",
                self.window.width // 2, self.window.height - 40,
                (255, 50, 50), 24,
                anchor_x="center"
            )

        if self.keys_collected >= self.keys_needed and not self.exit_found:
            arcade.draw_text(
                "ИЩИТЕ ВЫХОД!",
                self.window.width // 2, self.window.height - 40,
                (255, 215, 0), 22,
                anchor_x="center"
            )

    def draw_tutorial(self):
        """Нарисовать обучение"""
        alpha = min(255, int(255 * (self.tutorial_time / 6.0)))

        # Затемнение
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width,
            0, self.window.height,
            (0, 0, 0, alpha // 3)
        )

        # ИСПРАВЛЕННЫЕ ПОДСКАЗКИ УПРАВЛЕНИЯ
        texts = [
            "НАСТОЯЩИЙ ЛАБИРИНТ СТРАХА",
            "НАЙДИТЕ 3 КЛЮЧА И ВЫХОД В ПРОТИВОПОЛОЖНОМ УГЛУ",
            "",
            "УПРАВЛЕНИЕ:",
            "• W/S - ВПЕРЕД/НАЗАД",
            "• A/D - ВЛЕВО/ВПРАВО (движение)",
            "• ← / →  или  Q/E - ВЛЕВО/ВПРАВО (поворот)",
            "• МЫШЬ - ОБЗОР",
            "• F - ВКЛ/ВЫКЛ ФОНАРИК",
            "• ПРОБЕЛ - КРИК (отпугивает монстров)",
            "• M - ВКЛ/ВЫКЛ КАРТУ (держите открытой для навигации)",
            "",
            "ПОДСКАЗКИ СВЕТЯТСЯ СИНИМ, КЛЮЧИ - ЗОЛОТЫМ",
            "ВЫХОД МИГАЕТ КРАСНЫМ СВЕТОМ",
            "НАЖМИТЕ ЛЮБУЮ КЛАВИШУ ДЛЯ НАЧАЛА"
        ]

        center_y = self.window.height // 2 + 100
        for i, text in enumerate(texts):
            y_offset = i * 30
            font_size = 28 if i == 0 else 20 if i == 1 else 16
            color = (255, 50, 50) if i == 0 else (255, 215, 0) if i == 1 else (255, 255, 255)

            arcade.draw_text(
                text,
                self.window.width // 2,
                center_y - y_offset,
                (*color, alpha),
                font_size,
                anchor_x="center",
                anchor_y="center"
            )

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def check_hints(self):
        """Проверить сбор подсказок"""
        for hint in self.hints:
            if hint.collected:
                continue

            dx = hint.x - self.player_x
            dy = hint.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 1.5:
                hint.collected = True
                self.hints_collected += 1
                self.create_hint_effect(hint.x, hint.y)
                self.play_sound('upgrade2', volume=0.5)
                print(f"Подсказка: {hint.text}")

    def create_hint_effect(self, world_x, world_y):
        """Создать эффект при сборе подсказки"""
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)

            self.particles.append(Particle(
                x=self.window.width // 2,
                y=self.window.height // 2,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(1, 2),
                color=(100, 200, 255),
                size=random.uniform(2, 4),
                alpha=min(255, 180)
            ))

    def check_objectives(self):
        """Проверить сбор целей"""
        for obj in self.objectives:
            if obj.collected:
                continue

            dx = obj.x - self.player_x
            dy = obj.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 1.3:
                obj.collected = True

                if obj.type == 'key':
                    self.keys_collected += 1
                    self.create_collect_effect(obj.x, obj.y, (255, 215, 0))
                    self.play_sound('coin1', volume=0.7)
                    print(f"Найден ключ! {self.keys_collected}/{self.keys_needed}")

                elif obj.type == 'exit':
                    self.exit_found = True
                    self.create_collect_effect(obj.x, obj.y, (255, 50, 50))
                    self.play_sound('upgrade4', volume=0.8)
                    print("Найден выход!")

    def create_collect_effect(self, world_x, world_y, color):
        """Создать эффект при сборе предмета"""
        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)

            self.particles.append(Particle(
                x=self.window.width // 2,
                y=self.window.height // 2,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(1, 2),
                color=color,
                size=random.uniform(3, 6),
                alpha=min(255, 200)
            ))

    def update_particles(self, delta_time):
        """Обновить частицы"""
        for particle in self.particles[:]:
            particle.x += particle.vx * delta_time * 60
            particle.y += particle.vy * delta_time * 60
            particle.life -= delta_time
            particle.alpha = min(255, int(particle.alpha * (particle.life / 2)))

            if particle.life <= 0:
                self.particles.remove(particle)

        for particle in self.blood_particles[:]:
            particle.x += particle.vx * delta_time * 60
            particle.y += particle.vy * delta_time * 60
            particle.life -= delta_time

            if particle.life <= 0:
                self.blood_particles.remove(particle)

    def update_horror_events(self, delta_time):
        """Обновить страшные события"""
        if self.time_since_last_scare > 15:
            scare_chance = 0.005 * delta_time * 60

            if not self.flashlight_on:
                scare_chance *= 3
            elif self.flashlight_battery < 30:
                scare_chance *= 2

            if random.random() < scare_chance:
                self.trigger_random_scare()

    def trigger_random_scare(self):
        """Запустить случайный испуг"""
        scares = [self.trigger_whisper, self.trigger_door_slam, self.trigger_dark_flicker]
        random.choice(scares)()
        self.jump_scares_triggered += 1
        self.time_since_last_scare = 0

    def trigger_whisper(self):
        """Шепот"""
        self.play_sound('whisper', volume=0.4)
        self.player_stress = min(100, self.player_stress + 8)
        print("*ШЕПОТ* Послышался шёпот...")

    def trigger_door_slam(self):
        """Хлопанье двери"""
        self.play_sound('door_creak', volume=0.5)
        self.screen_shake = 0.2
        self.player_stress = min(100, self.player_stress + 6)
        print("*ХЛОП* Дверь захлопнулась...")

    def trigger_dark_flicker(self):
        """Мерцание света"""
        self.flashlight_flicker = 2.0
        self.play_sound('laser2', volume=0.3)
        self.player_stress = min(100, self.player_stress + 5)
        print("*МЕРЦАНИЕ* Свет мигнул...")

    def update_ambient_sounds(self, delta_time):
        """Обновить атмосферные звуки"""
        if not self.sound_manager:
            return

        # Сердцебиение при стрессе
        if self.player_stress > 40:
            if random.random() < 0.08 + (self.player_stress - 40) / 600:
                volume = 0.1 + (self.player_stress / 100) * 0.3
                self.play_sound('heartbeat', volume=volume)

        # Фоновые звуки
        if random.random() < 0.01:
            volume = 0.15 + (self.time_in_darkness / 10) * 0.3
            self.play_sound('wind', volume=volume)

        if random.random() < 0.005 and self.time_in_darkness > 3:
            self.play_sound('drip', volume=0.2)

    def play_sound(self, sound_name, volume=1.0):
        """Воспроизвести звук"""
        if self.sound_manager:
            try:
                self.sound_manager.play_sound(sound_name, volume=volume)
            except:
                pass