# horror_3d.py - ИСПРАВЛЕННАЯ ВЕРСИЯ (убраны лишние надписи, исправлена инструкция)
import arcade
import random
import math
import time
from typing import List, Dict, Tuple, Optional, Deque
from collections import deque
from dataclasses import dataclass, field
import numpy as np


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
    speed: float = 0.006
    detection_range: float = 3.0
    type: str = 'stalker'
    last_sound: float = 0
    active: bool = True
    health: int = 3
    attack_cooldown: float = 0
    visible: bool = True
    aggression_level: float = 1.0
    patrol_path: List[Tuple[float, float]] = field(default_factory=list)
    patrol_index: int = 0
    last_seen_time: float = 0
    is_hunting: bool = False


@dataclass
class Objective:
    """Цель игры"""
    x: float
    y: float
    type: str  # 'key', 'exit'
    collected: bool = False
    visible: bool = True
    pulse: float = 0.0


@dataclass
class BehaviorData:
    """Данные о поведении игрока для анализа"""
    mouse_deltas: Deque[Tuple[float, float]] = field(default_factory=lambda: deque(maxlen=100))
    key_presses: Deque[Tuple[float, str]] = field(default_factory=lambda: deque(maxlen=100))
    reaction_times: List[float] = field(default_factory=list)
    stress_levels: Deque[float] = field(default_factory=lambda: deque(maxlen=50))
    inactivity_periods: List[float] = field(default_factory=list)
    scream_events: List[float] = field(default_factory=list)

    def calculate_mouse_tremor(self) -> float:
        """Рассчитать дрожание мыши"""
        if len(self.mouse_deltas) < 10:
            return 0.0

        velocities = []
        for i in range(1, len(self.mouse_deltas)):
            dx, dy = self.mouse_deltas[i]
            dist = math.sqrt(dx * dx + dy * dy)
            velocities.append(dist)

        if not velocities:
            return 0.0

        avg_vel = np.mean(velocities)
        std_vel = np.std(velocities)

        if avg_vel < 2.0:
            return min(1.0, std_vel * 3.0)
        return 0.0

    def calculate_panic_level(self) -> float:
        """Рассчитать уровень паники по нажатиям клавиш"""
        if len(self.key_presses) < 20:
            return 0.0

        recent_time = time.time() - 3.0
        recent_presses = [k for t, k in self.key_presses if t > recent_time]

        if len(recent_presses) > 15:
            return min(1.0, len(recent_presses) / 30.0)

        return 0.0

    def calculate_inactivity(self) -> float:
        """Рассчитать уровень замирания"""
        if not self.inactivity_periods:
            return 0.0

        avg_inactivity = np.mean(self.inactivity_periods[-5:]) if len(self.inactivity_periods) >= 5 else \
            self.inactivity_periods[-1]
        return min(1.0, avg_inactivity / 5.0)


class MazeGenerator:
    """Генератор сложных лабиринтов"""

    @staticmethod
    def generate_perfect_maze(width: int, height: int) -> List[List[int]]:
        """Генерация совершенного лабиринта (1-стены, 0-проходы)"""
        maze = [[1 for _ in range(width)] for _ in range(height)]

        start_x, start_y = width // 2, height // 2
        stack = [(start_x, start_y)]
        maze[start_y][start_x] = 0

        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]

        while stack:
            x, y = stack[-1]
            random.shuffle(directions)

            found = False
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                if (1 <= nx < width - 1 and 1 <= ny < height - 1 and
                        maze[ny][nx] == 1):
                    maze[y + dy // 2][x + dx // 2] = 0
                    maze[ny][nx] = 0
                    stack.append((nx, ny))
                    found = True
                    break

            if not found:
                stack.pop()

        center_size = 3
        center_x, center_y = width // 2, height // 2
        for dy in range(-center_size, center_size + 1):
            for dx in range(-center_size, center_size + 1):
                nx, ny = center_x + dx, center_y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    maze[ny][nx] = 0

        for _ in range(width * height // 20):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            if maze[y][x] == 1:
                walls = 0
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if maze[ny][nx] == 1:
                            walls += 1
                if walls >= 3:
                    maze[y][x] = 0

        MazeGenerator._ensure_connectivity(maze, width, height)

        return maze

    @staticmethod
    def _ensure_connectivity(maze: List[List[int]], width: int, height: int):
        """Гарантировать, что лабиринт полностью проходим"""
        passages = []
        for y in range(height):
            for x in range(width):
                if maze[y][x] == 0:
                    passages.append((x, y))

        if not passages:
            return

        start = passages[0]
        visited = set()
        queue = deque([start])

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue

            visited.add((x, y))

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and
                        maze[ny][nx] == 0 and (nx, ny) not in visited):
                    queue.append((nx, ny))

        if len(visited) < len(passages):
            unvisited = [p for p in passages if p not in visited]
            for ux, uy in unvisited:
                min_dist = float('inf')
                nearest = None
                for vx, vy in visited:
                    dist = abs(ux - vx) + abs(uy - vy)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (vx, vy)

                if nearest:
                    vx, vy = nearest
                    while ux != vx or uy != vy:
                        if random.random() < 0.5 and ux != vx:
                            ux += 1 if ux < vx else -1
                        else:
                            uy += 1 if uy < vy else -1

                        if 0 <= ux < width and 0 <= uy < height:
                            maze[uy][ux] = 0
                            visited.add((ux, uy))


class FearAnalyzer:
    """Анализатор страхов игрока"""

    def __init__(self):
        self.fear_amplifiers = {
            'darkness': 1.0,
            'monsters': 1.0,
            'jump_scares': 1.0,
            'tight_spaces': 1.0,
            'sounds': 1.0,
            'atmosphere': 1.0,
            'paranoia': 1.0
        }
        self.last_analysis_time = 0
        self.analysis_interval = 5.0
        self.fear_profile = {}
        self.adaptation_log = []

    def analyze_behavior(self, behavior_data: BehaviorData, game_state: dict) -> dict:
        """Проанализировать поведение игрока и адаптировать игру"""
        current_time = time.time()
        if current_time - self.last_analysis_time < self.analysis_interval:
            return self.fear_amplifiers

        self.last_analysis_time = current_time

        mouse_tremor = behavior_data.calculate_mouse_tremor()
        panic_level = behavior_data.calculate_panic_level()
        inactivity_level = behavior_data.calculate_inactivity()
        aggression_level = len(behavior_data.scream_events) / 10.0 if behavior_data.scream_events else 0.0

        # Убрали вывод в консоль для чистоты
        if mouse_tremor > 0.3:
            self.fear_amplifiers['sounds'] = min(3.0, 1.0 + mouse_tremor * 2)
            self.fear_amplifiers['jump_scares'] = min(2.5, 1.0 + mouse_tremor * 1.5)

        if panic_level > 0.4:
            self.fear_amplifiers['monsters'] = min(2.5, 1.0 + panic_level * 1.5)

        if inactivity_level > 0.5:
            self.fear_amplifiers['darkness'] = min(2.8, 1.0 + inactivity_level * 1.8)

        if aggression_level > 0.6:
            self.fear_amplifiers['atmosphere'] = min(2.2, 1.0 + aggression_level)
            self.fear_amplifiers['paranoia'] = min(2.5, 1.0 + aggression_level * 1.5)

        stress = game_state.get('stress', 0)
        if stress > 70:
            self.fear_amplifiers['atmosphere'] = min(3.0, 1.0 + (stress - 70) / 30)

        self.adaptation_log.append({
            'time': current_time,
            'amplifiers': self.fear_amplifiers.copy(),
            'metrics': {
                'mouse_tremor': mouse_tremor,
                'panic': panic_level,
                'inactivity': inactivity_level,
                'aggression': aggression_level
            }
        })

        return self.fear_amplifiers


class Horror3DGame(arcade.View):
    """3D хоррор-лабиринт с правильным лабиринтом и звуками"""

    def __init__(self, fear_profile=None):
        super().__init__()

        # === ПЕРЕМЕННЫЕ ДЛЯ ЗВУКОВ ===
        self.sound_manager = None
        self.sound_timer = 0
        self.last_step_sound = 0
        self.step_interval = 0.5
        self.last_ambient_sound = 0
        self.ambient_interval = random.randint(5, 10)
        self.heartbeat_timer = 0
        self.heartbeat_active = False
        self.monster_sound_timer = 0
        self.step_counter = 0
        self.monster_near_counter = 0
        self.is_moving = False

        # Инициализируем звуковую систему
        self.init_sound_manager()

        # === ОСНОВНЫЕ ПЕРЕМЕННЫЕ ===
        self.fear_analyzer = FearAnalyzer()
        self.behavior_data = BehaviorData()
        self.fear_amplifiers = self.fear_analyzer.fear_amplifiers.copy()
        self.fear_profile = fear_profile or {}
        self.last_activity_time = time.time()
        self.inactivity_start = 0

        # === НАСТРОЙКИ ИГРОКА ===
        self.map_width = 31
        self.map_height = 31
        self.tile_size = 64

        # Генерация сложного лабиринта
        self.map = MazeGenerator.generate_perfect_maze(self.map_width, self.map_height)
        self.maze = self.map

        # Находим открытую центральную зону для старта
        self.player_x, self.player_y = self._find_start_position()
        self.player_angle = 0.0
        self.player_sanity = 100.0
        self.player_health = 100.0
        self.player_stress = 30.0
        self.player_fov = math.pi / 1.8

        # === КОЛЛИЗИИ ===
        self.collision_map = self._create_collision_map()
        self.walls = self._create_walls_list()
        self.exit_location = self._find_far_position(self.player_x, self.player_y)

        # === ИНТЕРФЕЙС ===
        self.show_minimap = False
        self.last_minimap_toggle = 0
        self.minimap_cooldown = 0.3
        self.minimap_scale = 0.8
        self.show_instructions = False

        # === ОБЪЕКТЫ ===
        self.objectives: List[Objective] = []
        self.keys_collected = 0
        self.keys_needed = 3
        self.total_keys = 3
        self.exit_found = False
        self._place_objects()

        # === ОСВЕЩЕНИЕ ===
        self.flashlight_on = True
        self.flashlight_battery = 150.0
        self.flashlight_flicker = 0.0
        self.ambient_light = 1.0
        self.light_level = 1.0

        # === ЭФФЕКТЫ ===
        self.screen_shake = 0.0
        self.blood_overlay = 0.0
        self.vignette = 0.4
        self.visual_distortion = 0.0
        self.paranoia_effect = 0.0
        self.camera_shake = 0.0
        self.flash_effect = 0.0
        self.walk_bob = 0.0

        # === ЧАСТИЦЫ ===
        self.particles: List[Particle] = []
        self.blood_particles: List[Particle] = []

        # === МОНСТРЫ ===
        self.monsters: List[Monster] = []
        self._init_monsters()

        # === УПРАВЛЕНИЕ ===
        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False,
            arcade.key.LEFT: False,
            arcade.key.RIGHT: False,
            arcade.key.Q: False,
            arcade.key.E: False,
        }
        self.mouse_look = True
        self.mouse_sensitivity = 0.002
        self.turn_speed = 1.8

        # === ВРЕМЯ ===
        self.game_time = 0.0
        self.time_since_last_scare = 0.0
        self.time_in_darkness = 0.0
        self.time_since_last_analysis = 0.0
        self.start_time = time.time()

        # === СОСТОЯНИЕ ===
        self.game_active = True
        self.game_won = False
        self.show_tutorial = True
        self.tutorial_time = 6.0
        self.game_over = False
        self.victory = False

        # === СТАТИСТИКА ===
        self.jump_scares_triggered = 0
        self.monsters_killed = 0

        # === АДАПТИВНЫЕ ЭФФЕКТЫ ===
        self.adaptive_music_pitch = 1.0
        self.adaptive_sound_volume = 1.0
        self.fear_induced_darkness = 0.0

        # Убрали лишний вывод в консоль
        print("Запуск 3D лабиринта...")

    # ==================== ЗВУКОВАЯ СИСТЕМА ====================

    def init_sound_manager(self):
        """Инициализировать звуки"""
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager(sound_mode="level2")
            self.sound_manager.set_volume(1.0)
        except Exception as e:
            print(f"Ошибка звуков: {e}")
            self.sound_manager = None

    def update_sounds(self, delta_time):
        """Обновление звуков"""
        if not self.sound_manager:
            return

        current_time = time.time()
        self.sound_timer += delta_time

        # 1. ЗВУКИ ШАГОВ
        if self.is_moving:
            if current_time - self.last_step_sound > self.step_interval:
                volume = 0.3 + random.random() * 0.1
                self.sound_manager.play_sound('footstep', volume=volume)
                self.last_step_sound = current_time
                self.step_counter += 1

        # 2. АТМОСФЕРНЫЕ звуки
        if current_time - self.last_ambient_sound > self.ambient_interval:
            sound_type = random.choice(['ambient', 'drip', 'wind', 'door'])
            volume = 0.2 + random.random() * 0.1
            self.sound_manager.play_sound(sound_type, volume=volume)
            self.last_ambient_sound = current_time
            self.ambient_interval = random.randint(5, 10)

        # 3. ШЕПОТЫ
        if random.random() < 0.01:
            volume = 0.15 + random.random() * 0.1
            self.sound_manager.play_sound('whisper', volume=volume)

        # 4. СЕРДЦЕБИЕНИЕ
        if self.player_stress > 60:
            self.heartbeat_timer += delta_time
            heartbeat_interval = max(0.1, 1.0 - (self.player_stress - 60) / 100)

            if self.heartbeat_timer > heartbeat_interval:
                volume = 0.3 + (self.player_stress - 60) / 200
                self.sound_manager.play_sound('heartbeat', volume=volume)
                self.heartbeat_timer = 0
                self.heartbeat_active = True
        else:
            self.heartbeat_active = False

        # 5. ЗВУКИ МОНСТРОВ
        self.monster_sound_timer += delta_time
        if self.monster_sound_timer > 2.0:
            for monster in self.monsters:
                if monster.active:
                    dx = monster.x - self.player_x
                    dy = monster.y - self.player_y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < 200:
                        if random.random() < 0.3:
                            volume = 0.4 * (1.0 - distance / 300)
                            self.sound_manager.play_sound('monster', volume=volume)
                            self.monster_near_counter += 1

            self.monster_sound_timer = 0

        # 6. ВНЕЗАПНЫЕ звуки
        if (self.light_level < 0.3 or self.player_sanity < 50) and random.random() < 0.005:
            volume = 0.4 + random.random() * 0.2
            self.sound_manager.play_sound('sudden', volume=volume)
            self.camera_shake = 0.3
            self.player_stress = min(100, self.player_stress + 10)

    def play_jumpscare_3d(self):
        """Скример"""
        if self.sound_manager:
            volume = 0.8 + random.random() * 0.2
            self.sound_manager.play_sound('scream', volume=volume)

            arcade.schedule(lambda dt: self.sound_manager.play_sound('sudden', volume=0.4), 0.2)
            arcade.schedule(lambda dt: self.sound_manager.play_sound('monster', volume=0.3), 0.5)

            self.camera_shake = 1.0
            self.flash_effect = 1.0
            self.player_stress = min(100, self.player_stress + 30)
            self.player_sanity = max(0, self.player_sanity - 20)
            self.jump_scares_triggered += 1

    # ==================== ГЕНЕРАЦИЯ КАРТЫ ====================

    def _find_start_position(self) -> Tuple[float, float]:
        """Найти открытую позицию для старта"""
        open_areas = []

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map[y][x] == 0:
                    space = 0
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < self.map_width and 0 <= ny < self.map_height and
                                    self.map[ny][nx] == 0):
                                space += 1

                    if space >= 20:
                        open_areas.append((x, y, space))

        if open_areas:
            open_areas.sort(key=lambda a: a[2], reverse=True)
            return open_areas[0][0] + 0.5, open_areas[0][1] + 0.5

        return self.map_width // 2 + 0.5, self.map_height // 2 + 0.5

    def _find_far_position(self, from_x: float, from_y: float) -> Tuple[int, int]:
        """Найти позицию далеко от заданной"""
        max_distance = 0
        far_pos = (self.map_width - 2, self.map_height - 2)

        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map[y][x] == 0:
                    distance = math.sqrt((x - from_x) ** 2 + (y - from_y) ** 2)
                    if distance > max_distance:
                        max_distance = distance
                        far_pos = (x, y)

        return far_pos

    def _create_collision_map(self):
        """Создать карту коллизий"""
        return [[cell == 1 for cell in row] for row in self.map]

    def _create_walls_list(self):
        """Создать список стен"""
        walls = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map[y][x] == 1:
                    walls.append({
                        'x': x * self.tile_size,
                        'y': y * self.tile_size,
                        'width': self.tile_size,
                        'height': self.tile_size
                    })
        return walls

    def check_collision(self, x, y):
        """Проверить коллизию"""
        ix, iy = int(x), int(y)

        if 0 <= ix < self.map_width and 0 <= iy < self.map_height:
            return self.collision_map[iy][ix]

        return True

    # ==================== РАЗМЕЩЕНИЕ ОБЪЕКТОВ ====================

    def _place_objects(self):
        """Разместить объекты на карте"""
        self.objectives.clear()

        free_cells = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map[y][x] == 0:
                    dist_to_player = math.sqrt((x - self.player_x) ** 2 + (y - self.player_y) ** 2)
                    if dist_to_player > 3:
                        free_cells.append((x, y))

        if not free_cells:
            return

        for _ in range(3):
            if not free_cells:
                break

            x, y = random.choice(free_cells)
            free_cells.remove((x, y))

            self.objectives.append(Objective(
                x=x + 0.5,
                y=y + 0.5,
                type='key',
                collected=False,
                pulse=random.random() * math.pi * 2
            ))

        exit_x, exit_y = self.exit_location
        self.objectives.append(Objective(
            x=exit_x + 0.5,
            y=exit_y + 0.5,
            type='exit',
            collected=False,
            pulse=0.0
        ))

        self.keys = []
        for i, obj in enumerate([obj for obj in self.objectives if obj.type == 'key']):
            self.keys.append({
                'x': obj.x * self.tile_size,
                'y': obj.y * self.tile_size,
                'collected': False,
                'id': i
            })

    def _init_monsters(self):
        """Инициализировать монстров"""
        dead_ends = []
        for y in range(1, self.map_height - 1):
            for x in range(1, self.map_width - 1):
                if self.map[y][x] == 0:
                    walls = 0
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        if self.map[y + dy][x + dx] == 1:
                            walls += 1
                    if walls >= 3:
                        dead_ends.append((x, y))

        for i in range(min(3, len(dead_ends))):
            x, y = dead_ends[i]

            patrol_path = []
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.map_width and 0 <= ny < self.map_height and
                        self.map[ny][nx] == 0):
                    patrol_path.append((nx + 0.5, ny + 0.5))

            if not patrol_path:
                patrol_path = [(x + 0.5, y + 0.5)]

            monster = Monster(
                x=x + 0.5,
                y=y + 0.5,
                speed=0.004 * self.fear_amplifiers['monsters'],
                detection_range=2.5,
                patrol_path=patrol_path
            )
            self.monsters.append(monster)

    # ==================== ОСНОВНАЯ ЛОГИКА ====================

    def on_update(self, delta_time: float):
        """Главный цикл"""
        if not self.game_active or self.game_won:
            return

        self.game_time += delta_time
        self.tutorial_time = max(0, self.tutorial_time - delta_time)
        self.last_minimap_toggle = max(0, self.last_minimap_toggle - delta_time)
        self.time_since_last_analysis += delta_time

        # Обновление активности игрока
        self._update_activity_tracking(delta_time)

        # Анализ поведения
        if self.time_since_last_analysis >= 2.0:
            self.time_since_last_analysis = 0
            game_state = {
                'stress': self.player_stress,
                'sanity': self.player_sanity,
                'health': self.player_health,
                'darkness': 1.0 if not self.flashlight_on else 0.0
            }
            self.fear_amplifiers = self.fear_analyzer.analyze_behavior(
                self.behavior_data, game_state
            )

            self._apply_fear_amplifiers()

        # Обновление звуков
        self.update_sounds(delta_time)

        # Обновление игрока
        self._update_player(delta_time)

        # Обновление фонарика
        self._update_flashlight(delta_time)

        # Обновление монстров
        self._update_monsters(delta_time)

        # Обновление объектов
        self._update_objects(delta_time)

        # Обновление частиц
        self._update_particles(delta_time)

        # Обновление эффектов
        self._update_effects(delta_time)

        # Проверка объектов
        self._check_objectives()

        # Проверка победы
        if self.exit_found and self.keys_collected >= self.keys_needed:
            self._win_game()

        # Проверка поражения
        if self.player_health <= 0:
            self._end_game("СМЕРТЬ")
        elif self.player_sanity <= 0:
            self._end_game("БЕЗУМИЕ")

    def _update_activity_tracking(self, delta_time: float):
        """Отслеживать активность игрока"""
        current_time = time.time()

        any_key_pressed = any(self.keys_pressed.values())
        mouse_moved = len(self.behavior_data.mouse_deltas) > 0 and self.behavior_data.mouse_deltas[-1] != (0, 0)

        if any_key_pressed or mouse_moved:
            self.last_activity_time = current_time
            if self.inactivity_start > 0:
                inactivity_duration = current_time - self.inactivity_start
                if inactivity_duration > 1.0:
                    self.behavior_data.inactivity_periods.append(inactivity_duration)
                self.inactivity_start = 0
        else:
            if self.inactivity_start == 0:
                self.inactivity_start = current_time

    def _apply_fear_amplifiers(self):
        """Применить усилители страха"""
        for monster in self.monsters:
            monster.speed = 0.004 * self.fear_amplifiers['monsters']
            monster.detection_range = 2.5 * self.fear_amplifiers['atmosphere']

        self.fear_induced_darkness = (self.fear_amplifiers['darkness'] - 1.0) * 0.3

        if self.sound_manager:
            self.adaptive_sound_volume = self.fear_amplifiers['sounds']
            self.sound_manager.set_volume(self.adaptive_sound_volume)  # ИСПРАВЛЕНО

        self.paranoia_effect = min(0.7, (self.fear_amplifiers['paranoia'] - 1.0) * 0.35)

    def _update_player(self, delta_time: float):
        """Обновить игрока"""
        move_forward = 0
        move_right = 0
        move_speed = 2.8 * delta_time

        if self.keys_pressed[arcade.key.W]:
            move_forward += move_speed
            self.behavior_data.key_presses.append((time.time(), 'W'))
            self.is_moving = True
        if self.keys_pressed[arcade.key.S]:
            move_forward -= move_speed
            self.behavior_data.key_presses.append((time.time(), 'S'))
            self.is_moving = True
        if self.keys_pressed[arcade.key.A]:
            move_right -= move_speed
            self.behavior_data.key_presses.append((time.time(), 'A'))
            self.is_moving = True
        if self.keys_pressed[arcade.key.D]:
            move_right += move_speed
            self.behavior_data.key_presses.append((time.time(), 'D'))
            self.is_moving = True

        if not any([self.keys_pressed[arcade.key.W], self.keys_pressed[arcade.key.S],
                    self.keys_pressed[arcade.key.A], self.keys_pressed[arcade.key.D]]):
            self.is_moving = False

        turn_amount = 0
        if self.keys_pressed[arcade.key.LEFT] or self.keys_pressed[arcade.key.Q]:
            turn_amount -= self.turn_speed * delta_time
            self.behavior_data.key_presses.append((time.time(), 'LEFT'))
        if self.keys_pressed[arcade.key.RIGHT] or self.keys_pressed[arcade.key.E]:
            turn_amount += self.turn_speed * delta_time
            self.behavior_data.key_presses.append((time.time(), 'RIGHT'))

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

            self._apply_movement(move_x, move_y)

            if not self.flashlight_on or self.flashlight_battery < 30:
                self.player_stress = min(100, self.player_stress + delta_time * 3)
                self.player_sanity = max(0, self.player_sanity - delta_time * 2)

            self.walk_bob += delta_time * 10
        else:
            self.walk_bob = 0

    def _apply_movement(self, move_x: float, move_y: float):
        """Применить движение"""
        speed_factor = 0.8
        new_x = self.player_x + move_x * speed_factor
        new_y = self.player_y + move_y * speed_factor

        if self.check_collision(new_x, self.player_y):
            for offset in [0.1, 0.2, 0.3]:
                if not self.check_collision(self.player_x, self.player_y + offset):
                    new_y += offset * 0.5
                    break
                elif not self.check_collision(self.player_x, self.player_y - offset):
                    new_y -= offset * 0.5
                    break
        else:
            self.player_x = new_x

        if self.check_collision(self.player_x, new_y):
            for offset in [0.1, 0.2, 0.3]:
                if not self.check_collision(self.player_x + offset, self.player_y):
                    self.player_x += offset * 0.5
                    break
                elif not self.check_collision(self.player_x - offset, self.player_y):
                    self.player_x -= offset * 0.5
                    break
        else:
            self.player_y = new_y

    def _update_flashlight(self, delta_time: float):
        """Обновить фонарик"""
        if self.flashlight_on and self.flashlight_battery > 0:
            drain_rate = 0.6 * (1.0 + self.fear_amplifiers['darkness'] * 0.3)
            self.flashlight_battery = max(0, self.flashlight_battery - delta_time * drain_rate)

            if self.flashlight_battery < 30:
                self.flashlight_flicker = math.sin(self.game_time * 15) * 0.3 + 0.7
            else:
                self.flashlight_flicker = 1.0

            if self.flashlight_battery <= 0:
                self.flashlight_on = False
                self.player_stress = min(100, self.player_stress + 25)
                if self.sound_manager:
                    self.sound_manager.play_sound('power_down', volume=0.5)
        else:
            if self.flashlight_battery < 150:
                self.flashlight_battery = min(150, self.flashlight_battery + delta_time * 0.1)

        if self.flashlight_on and self.flashlight_battery > 20:
            self.light_level = self.flashlight_flicker
        else:
            self.light_level = 0.3

    def _update_monsters(self, delta_time: float):
        """Обновить монстров"""
        for monster in self.monsters:
            if not monster.active:
                continue

            monster.attack_cooldown = max(0, monster.attack_cooldown - delta_time)
            monster.last_seen_time += delta_time

            dx = self.player_x - monster.x
            dy = self.player_y - monster.y
            distance = math.sqrt(dx * dx + dy * dy)
            monster.visible = distance < 15

            has_line_of_sight = self._check_line_of_sight(monster.x, monster.y, self.player_x, self.player_y)

            if has_line_of_sight:
                monster.last_seen_time = 0
                monster.is_hunting = True

            if monster.is_hunting:
                if distance < monster.detection_range:
                    if distance > 1.5:
                        move_x = (dx / distance) * monster.speed * delta_time * 60
                        move_y = (dy / distance) * monster.speed * delta_time * 60

                        if not self.check_collision(monster.x + move_x, monster.y):
                            monster.x += move_x
                        if not self.check_collision(monster.x, monster.y + move_y):
                            monster.y += move_y

                    if distance < 1.5 and monster.attack_cooldown <= 0:
                        self._monster_attack(monster)

                if monster.last_seen_time > 5.0:
                    monster.is_hunting = False
            else:
                if monster.patrol_path:
                    target_x, target_y = monster.patrol_path[monster.patrol_index]
                    pdx = target_x - monster.x
                    pdy = target_y - monster.y
                    pdist = math.sqrt(pdx * pdx + pdy * pdy)

                    if pdist > 0.1:
                        move_x = (pdx / pdist) * monster.speed * 0.5 * delta_time * 60
                        move_y = (pdy / pdist) * monster.speed * 0.5 * delta_time * 60

                        if not self.check_collision(monster.x + move_x, monster.y):
                            monster.x += move_x
                        if not self.check_collision(monster.x, monster.y + move_y):
                            monster.y += move_y
                    else:
                        monster.patrol_index = (monster.patrol_index + 1) % len(monster.patrol_path)

    def _check_line_of_sight(self, x1: float, y1: float, x2: float, y2: float, steps: int = 20) -> bool:
        """Проверить прямую видимость"""
        for i in range(steps + 1):
            t = i / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t

            if self.check_collision(x, y):
                return False

        return True

    def _monster_attack(self, monster: Monster):
        """Атака монстра"""
        damage = 15 * self.fear_amplifiers['monsters']
        self.player_health -= damage
        self.player_stress = min(100, self.player_stress + 25 * self.fear_amplifiers['jump_scares'])
        self.player_sanity = max(0, self.player_sanity - 10)

        monster.attack_cooldown = 3.0 / self.fear_amplifiers['monsters']
        self.screen_shake = 0.7 * self.fear_amplifiers['jump_scares']
        self.blood_overlay = 0.9
        self.visual_distortion = 0.5

        for _ in range(15):
            self.blood_particles.append(Particle(
                x=self.window.width // 2 + random.randint(-50, 50),
                y=self.window.height // 2 + random.randint(-50, 50),
                vx=random.uniform(-10, 10),
                vy=random.uniform(-10, 10),
                life=random.uniform(0.8, 1.5),
                color=(200, 20, 20),
                size=random.uniform(4, 8)
            ))

        self.play_jumpscare_3d()

    def _update_objects(self, delta_time: float):
        """Обновить анимацию объектов"""
        for obj in self.objectives:
            if not obj.collected:
                obj.pulse += delta_time * 2
                if obj.pulse > math.pi * 2:
                    obj.pulse -= math.pi * 2

    def _update_particles(self, delta_time: float):
        """Обновить частицы"""
        for particle in self.particles[:]:
            particle.x += particle.vx * delta_time * 60
            particle.y += particle.vy * delta_time * 60
            particle.life -= delta_time
            new_alpha = int(particle.alpha * (particle.life / 1.0))
            particle.alpha = max(0, new_alpha)
            if particle.life <= 0:
                self.particles.remove(particle)

        for particle in self.blood_particles[:]:
            particle.x += particle.vx * delta_time * 60
            particle.y += particle.vy * delta_time * 60
            particle.life -= delta_time
            if particle.life <= 0:
                self.blood_particles.remove(particle)

    def _update_effects(self, delta_time: float):
        """Обновить эффекты"""
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - delta_time * 2)

        if self.camera_shake > 0:
            self.camera_shake = max(0, self.camera_shake - delta_time * 2)

        if self.flash_effect > 0:
            self.flash_effect = max(0, self.flash_effect - delta_time * 3)

        if self.blood_overlay > 0:
            self.blood_overlay = max(0, self.blood_overlay - delta_time * 0.3)

        if self.visual_distortion > 0:
            self.visual_distortion = max(0, self.visual_distortion - delta_time * 0.5)

        if self.player_stress > 30:
            recovery_rate = 5 if self.flashlight_on and self.flashlight_battery > 50 else 2
            self.player_stress = max(30, self.player_stress - delta_time * recovery_rate)

        if self.player_sanity < 100 and self.player_stress < 50:
            self.player_sanity = min(100, self.player_sanity + delta_time * 1)

        if not self.flashlight_on or self.flashlight_battery < 10:
            self.time_in_darkness += delta_time
            if self.time_in_darkness > 10:
                if random.random() < 0.01:
                    self._trigger_whisper()
        else:
            self.time_in_darkness = max(0, self.time_in_darkness - delta_time * 2)

    def _trigger_whisper(self):
        """Шепот"""
        whispers = [
            "Они идут...",
            "Позади тебя...",
            "Не оглядывайся...",
            "Темнота живая...",
            "Беги...",
            "Он рядом...",
            "Ты не один...",
            "Смотри...",
            "Слушай...",
            "Бойся..."
        ]

        if self.sound_manager and random.random() < 0.7:
            whisper = random.choice(whispers)
            self.sound_manager.play_sound('whisper', volume=0.3 * self.fear_amplifiers['sounds'])

            self.visual_distortion = 0.3
            self.player_sanity = max(0, self.player_sanity - 5)

    # ==================== ВЗАИМОДЕЙСТВИЯ ====================

    def _check_objectives(self):
        """Проверить цели"""
        for obj in self.objectives:
            if obj.collected:
                continue

            dx = obj.x - self.player_x
            dy = obj.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 1.0:
                obj.collected = True

                if obj.type == 'key':
                    self.keys_collected += 1

                    for _ in range(20):
                        self.particles.append(Particle(
                            x=self.window.width // 2,
                            y=self.window.height // 2,
                            vx=random.uniform(-4, 4),
                            vy=random.uniform(-4, 4),
                            life=random.uniform(1.5, 2.5),
                            color=(255, 215, 0),
                            size=random.uniform(4, 7),
                            alpha=220
                        ))

                    if self.sound_manager:
                        volume = 0.7 * self.fear_amplifiers['sounds']
                        self.sound_manager.play_sound('coin1', volume=volume)

                    self.player_stress = min(100, self.player_stress + 10)

                elif obj.type == 'exit':
                    self.exit_found = True

                    for _ in range(25):
                        self.particles.append(Particle(
                            x=self.window.width // 2,
                            y=self.window.height // 2,
                            vx=random.uniform(-5, 5),
                            vy=random.uniform(-5, 5),
                            life=random.uniform(2, 3),
                            color=(255, 50, 50),
                            size=random.uniform(5, 9),
                            alpha=240
                        ))

                    if self.sound_manager:
                        volume = 0.8 * self.fear_amplifiers['sounds']
                        self.sound_manager.play_sound('upgrade4', volume=volume)

                    self.player_stress = min(100, self.player_stress + 20)

    # ==================== ОТРИСОВКА ====================

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        # Тряска
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.uniform(-self.screen_shake, self.screen_shake) * 25
            shake_y = random.uniform(-self.screen_shake, self.screen_shake) * 25

        # Искажение
        distortion_x = 0
        distortion_y = 0
        if self.visual_distortion > 0:
            distortion_x = math.sin(self.game_time * 20) * self.visual_distortion * 5
            distortion_y = math.cos(self.game_time * 18) * self.visual_distortion * 5

        total_offset_x = shake_x + distortion_x
        total_offset_y = shake_y + distortion_y

        # 3D вид
        self._draw_3d_view(total_offset_x, total_offset_y)

        # Эффекты
        self._draw_effects(total_offset_x, total_offset_y)

        # Интерфейс (без лишней надписи на карте)
        self._draw_hud()

        # Миникарта
        if self.show_minimap:
            self._draw_minimap()

        # Обучение
        if self.show_tutorial and self.tutorial_time > 0:
            self._draw_tutorial()

        # Инструкция (исправленная)
        if self.show_instructions:
            self._draw_instructions()

        # Эффект паранойи
        if self.paranoia_effect > 0 and random.random() < self.paranoia_effect * 0.1:
            self._draw_paranoia_effect()

    def _draw_3d_view(self, offset_x=0, offset_y=0):
        """Нарисовать 3D вид"""
        darkness_factor = 1.0 + self.fear_induced_darkness
        if self.flashlight_on and self.flashlight_battery > 20:
            base_color = (20, 15, 30)
        else:
            base_color = (5, 2, 10)

        bg_color = (
            int(base_color[0] / darkness_factor),
            int(base_color[1] / darkness_factor),
            int(base_color[2] / darkness_factor)
        )

        arcade.draw_lrbt_rectangle_filled(
            0 + offset_x, self.window.width + offset_x,
            0 + offset_y, self.window.height + offset_y,
            bg_color
        )

        self._draw_walls_raycasting(offset_x, offset_y)
        self._draw_objects_in_3d(offset_x, offset_y)
        self._draw_monsters_3d(offset_x, offset_y)

        if self.flashlight_on and self.flashlight_battery > 0:
            self._draw_flashlight_effect(offset_x, offset_y)

    def _draw_walls_raycasting(self, offset_x=0, offset_y=0):
        """Отрисовка стен"""
        num_rays = 120
        ray_step = self.player_fov / num_rays
        column_width = self.window.width / num_rays

        for i in range(num_rays):
            ray_angle = (self.player_angle - self.player_fov / 2) + i * ray_step
            distance, wall_type = self._cast_ray(ray_angle)

            if distance > 0:
                darkness = 1.0 + self.fear_induced_darkness
                if not self.flashlight_on or self.flashlight_battery < 20:
                    darkness *= 1.5

                wall_height = min(600, self.window.height / max(distance * darkness, 0.1))

                x = i * column_width + offset_x
                y_bottom = (self.window.height - wall_height) / 2 + offset_y
                y_top = y_bottom + wall_height

                darken = min(1.0, 8.0 / (distance * darkness))

                if wall_type == 'side':
                    wall_color = (
                        int(70 * darken),
                        int(60 * darken),
                        int(50 * darken)
                    )
                else:
                    wall_color = (
                        int(80 * darken),
                        int(70 * darken),
                        int(60 * darken)
                    )

                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                    y_bottom, y_top,
                    wall_color
                )

                floor_darken = darken * 0.6
                floor_color = (
                    int(40 * floor_darken),
                    int(30 * floor_darken),
                    int(20 * floor_darken)
                )
                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                       0 + offset_y, y_bottom,
                    floor_color
                )

                ceiling_darken = darken * 0.5
                ceiling_color = (
                    int(20 * ceiling_darken),
                    int(15 * ceiling_darken),
                    int(30 * ceiling_darken)
                )
                arcade.draw_lrbt_rectangle_filled(
                    x, x + column_width,
                    y_top, self.window.height + offset_y,
                    ceiling_color
                )

    def _cast_ray(self, angle: float) -> Tuple[float, str]:
        """Кастовать луч"""
        step = 0.05
        max_dist = 25.0

        x = self.player_x
        y = self.player_y
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)

        distance = 0
        last_x, last_y = x, y

        while distance < max_dist:
            distance += step
            test_x = x + dir_x * distance
            test_y = y + dir_y * distance

            if self.check_collision(test_x, test_y):
                grid_x = int(test_x)
                grid_y = int(test_y)
                last_grid_x = int(last_x)
                last_grid_y = int(last_y)

                if grid_x != last_grid_x and grid_y != last_grid_y:
                    wall_type = 'corner'
                elif grid_x != last_grid_x:
                    wall_type = 'side'
                else:
                    wall_type = 'front'

                return distance, wall_type

            last_x, last_y = test_x, test_y

        return max_dist, 'front'

    def _draw_objects_in_3d(self, offset_x=0, offset_y=0):
        """Отрисовка объектов"""
        objects_to_draw = []

        for obj in self.objectives:
            if obj.type == 'key' and not obj.collected:
                objects_to_draw.append({
                    'type': 'key',
                    'x': obj.x,
                    'y': obj.y,
                    'pulse': obj.pulse,
                    'obj': obj
                })

        for obj in self.objectives:
            if obj.type == 'exit' and not obj.collected:
                objects_to_draw.append({
                    'type': 'exit',
                    'x': obj.x,
                    'y': obj.y,
                    'pulse': obj.pulse,
                    'obj': obj
                })

        objects_to_draw.sort(
            key=lambda o: -math.sqrt((o['x'] - self.player_x) ** 2 + (o['y'] - self.player_y) ** 2)
        )

        for obj_data in objects_to_draw:
            self._draw_single_object_3d(obj_data, offset_x, offset_y)

    def _draw_single_object_3d(self, obj_data: dict, offset_x=0, offset_y=0):
        """Отрисовать один объект"""
        dx = obj_data['x'] - self.player_x
        dy = obj_data['y'] - self.player_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 0.1 or distance > 20:
            return

        angle_to_obj = math.atan2(dy, dx) - self.player_angle

        while angle_to_obj > math.pi:
            angle_to_obj -= 2 * math.pi
        while angle_to_obj < -math.pi:
            angle_to_obj += 2 * math.pi

        if abs(angle_to_obj) < self.player_fov / 2:
            screen_x = self.window.width / 2 + (angle_to_obj / (self.player_fov / 2)) * (
                    self.window.width / 2) + offset_x
            screen_y = self.window.height / 2 + offset_y

            base_size = 50
            size = max(15, min(base_size, base_size * 4 / distance))

            darken = min(1.0, 15 / distance)
            if not self.flashlight_on or self.flashlight_battery < 20:
                darken *= 0.4

            if obj_data['type'] == 'key':
                pulse = (math.sin(obj_data['pulse'] * 2) + 1.5) / 2.5
                brightness = pulse * darken * self.flashlight_flicker

                core_color = (
                    int(255 * brightness),
                    int(215 * brightness),
                    int(50 * brightness)
                )
                arcade.draw_circle_filled(screen_x, screen_y, size, core_color)

                glow_size = size * 1.5
                glow_alpha = min(255, max(0, int(100 * pulse * darken)))
                if glow_alpha > 0:
                    arcade.draw_circle_filled(
                        screen_x, screen_y, glow_size,
                        (core_color[0], core_color[1], core_color[2], glow_alpha)
                    )

                arcade.draw_circle_outline(screen_x, screen_y, size, (255, 255, 200, 200), 3)

                arcade.draw_text(
                    "K", screen_x, screen_y - 4,
                    (100, 80, 0, 200), int(size * 0.9),
                    anchor_x="center", anchor_y="center", bold=True
                )

            elif obj_data['type'] == 'exit':
                blink = int(time.time() * 2) % 2 == 0
                if blink:
                    brightness = darken * self.flashlight_flicker
                    core_color = (
                        int(255 * brightness),
                        int(50 * brightness),
                        int(50 * brightness)
                    )

                    arcade.draw_circle_filled(screen_x, screen_y, size, core_color)

                    pulse_size = size * (1.2 + 0.3 * math.sin(obj_data['pulse'] * 3))
                    pulse_alpha = min(255, max(0, int(150 * (0.5 + 0.5 * math.sin(obj_data['pulse'] * 3)) * darken)))
                    if pulse_alpha > 0:
                        arcade.draw_circle_filled(
                            screen_x, screen_y, pulse_size,
                            (core_color[0], core_color[1], core_color[2], pulse_alpha)
                        )

                    arcade.draw_circle_outline(screen_x, screen_y, size, (255, 200, 200, 200), 3)

                    arcade.draw_text(
                        "E", screen_x, screen_y - 4,
                        (150, 0, 0, 200), int(size * 0.9),
                        anchor_x="center", anchor_y="center", bold=True
                    )

    def _draw_monsters_3d(self, offset_x=0, offset_y=0):
        """Отрисовка монстров"""
        for monster in self.monsters:
            if not monster.active or not monster.visible:
                continue

            dx = monster.x - self.player_x
            dy = monster.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.1 or distance > 20:
                continue

            angle_to_monster = math.atan2(dy, dx) - self.player_angle

            while angle_to_monster > math.pi:
                angle_to_monster -= 2 * math.pi
            while angle_to_monster < -math.pi:
                angle_to_monster += 2 * math.pi

            if abs(angle_to_monster) < self.player_fov / 2:
                screen_x = self.window.width / 2 + (angle_to_monster / (self.player_fov / 2)) * (
                        self.window.width / 2) + offset_x
                screen_y = self.window.height / 2 + offset_y

                size = max(25, min(100, 200 / distance))
                darken = min(1.0, 20 / distance)

                if not self.flashlight_on or self.flashlight_battery < 20:
                    darken *= 0.3

                if self.paranoia_effect > 0 and random.random() < self.paranoia_effect:
                    size *= 1.2
                    darken *= 1.3

                body_color = (
                    int(180 * darken),
                    int(60 * darken),
                    int(60 * darken)
                )
                arcade.draw_circle_filled(screen_x, screen_y, size, body_color)

                shadow_alpha = min(255, max(0, 150))
                shadow_color = (100, 30, 30, shadow_alpha)
                arcade.draw_circle_filled(screen_x - size * 0.2, screen_y - size * 0.2, size * 0.9, shadow_color)

                eye_size = size * 0.18
                eye_offset = size * 0.35
                eye_y_offset = size * 0.1

                eye_alpha = min(255, max(0, 220))
                arcade.draw_circle_filled(
                    screen_x - eye_offset, screen_y + eye_y_offset,
                    eye_size, (255, 255, 255, eye_alpha)
                )
                arcade.draw_circle_filled(
                    screen_x + eye_offset, screen_y + eye_y_offset,
                    eye_size, (255, 255, 255, eye_alpha)
                )

                pupil_offset = eye_size * 0.3
                arcade.draw_circle_filled(
                    screen_x - eye_offset, screen_y + eye_y_offset + pupil_offset,
                    eye_size * 0.6, (255, 0, 0)
                )
                arcade.draw_circle_filled(
                    screen_x + eye_offset, screen_y + eye_y_offset + pupil_offset,
                    eye_size * 0.6, (255, 0, 0)
                )

                highlight_alpha = min(255, max(0, 200))
                highlight_size = eye_size * 0.2
                arcade.draw_circle_filled(
                    screen_x - eye_offset - eye_size * 0.2, screen_y + eye_y_offset + eye_size * 0.3,
                    highlight_size, (255, 255, 255, highlight_alpha)
                )
                arcade.draw_circle_filled(
                    screen_x + eye_offset - eye_size * 0.2, screen_y + eye_y_offset + eye_size * 0.3,
                    highlight_size, (255, 255, 255, highlight_alpha)
                )

    def _draw_flashlight_effect(self, offset_x=0, offset_y=0):
        """Эффект фонарика"""
        if self.flashlight_battery <= 0:
            return

        center_x = self.window.width // 2 + offset_x
        center_y = self.window.height // 2 + offset_y

        intensity = min(1.0, self.flashlight_battery / 150.0) * self.flashlight_flicker

        layers = [
            (220 * intensity, min(255, max(0, int(50 * intensity)))),
            (160 * intensity, min(255, max(0, int(30 * intensity)))),
            (100 * intensity, min(255, max(0, int(15 * intensity))))
        ]

        for radius, alpha in layers:
            arcade.draw_circle_filled(
                center_x, center_y, radius,
                (255, 245, 220, alpha)
            )

    def _draw_effects(self, offset_x=0, offset_y=0):
        """Эффекты"""
        for particle in self.particles:
            particle_alpha = min(255, max(0, particle.alpha))
            arcade.draw_circle_filled(
                particle.x + offset_x,
                particle.y + offset_y,
                particle.size,
                (particle.color[0], particle.color[1], particle.color[2], particle_alpha)
            )

        for particle in self.blood_particles:
            blood_alpha = min(255, max(0, 180))
            arcade.draw_circle_filled(
                particle.x + offset_x,
                particle.y + offset_y,
                particle.size,
                (particle.color[0], particle.color[1], particle.color[2], blood_alpha)
            )

        if self.blood_overlay > 0:
            alpha = min(255, max(0, int(200 * self.blood_overlay)))

            arcade.draw_lrbt_rectangle_filled(
                0 + offset_x, self.window.width + offset_x,
                0 + offset_y, self.window.height + offset_y,
                (180, 30, 30, alpha // 3)
            )

            for _ in range(int(self.blood_overlay * 10)):
                drop_x = random.randint(0, self.window.width)
                drop_y = random.randint(0, self.window.height)
                drop_size = random.randint(2, 6)
                drop_alpha = min(255, max(0, alpha // 2))
                arcade.draw_circle_filled(
                    drop_x + offset_x, drop_y + offset_y,
                    drop_size, (150, 20, 20, drop_alpha)
                )

        vignette_strength = self.vignette + self.fear_induced_darkness * 0.3
        if vignette_strength > 0:
            alpha = min(255, max(0, int(200 * vignette_strength)))
            if not self.flashlight_on:
                alpha = min(255, max(0, alpha * 2))

            gradient_height = self.window.height * 0.4
            for i in range(20):
                step_alpha = min(255, max(0, int(alpha * (i / 20))))
                y_top = self.window.height - i * (gradient_height / 20)
                y_bottom = i * (gradient_height / 20)

                arcade.draw_lrbt_rectangle_filled(
                    0 + offset_x, self.window.width + offset_x,
                    y_top - (gradient_height / 20), y_top + offset_y,
                    (0, 0, 0, step_alpha)
                )
                arcade.draw_lrbt_rectangle_filled(
                    0 + offset_x, self.window.width + offset_x,
                    y_bottom - (gradient_height / 20) + offset_y, y_bottom + offset_y,
                    (0, 0, 0, step_alpha)
                )

        if self.flash_effect > 0:
            alpha = int(self.flash_effect * 150)
            arcade.draw_lrbt_rectangle_filled(
                0 + offset_x, self.window.width + offset_x,
                0 + offset_y, self.window.height + offset_y,
                (255, 200, 200, alpha)
            )

    def _draw_paranoia_effect(self):
        """Эффект паранойи"""
        if random.random() < 0.5:
            side = random.choice(['left', 'right', 'top', 'bottom'])
            if side == 'left':
                x = random.randint(0, 50)
                y = random.randint(0, self.window.height)
                arcade.draw_lrbt_rectangle_filled(
                    x - 15, x + 15,
                    y - 75, y + 75,
                    (0, 0, 0, 100)
                )
            elif side == 'right':
                x = random.randint(self.window.width - 50, self.window.width)
                y = random.randint(0, self.window.height)
                arcade.draw_lrbt_rectangle_filled(
                    x - 15, x + 15,
                    y - 75, y + 75,
                    (0, 0, 0, 100)
                )
            elif side == 'top':
                x = random.randint(0, self.window.width)
                y = random.randint(self.window.height - 50, self.window.height)
                arcade.draw_lrbt_rectangle_filled(
                    x - 75, x + 75,
                    y - 15, y + 15,
                    (0, 0, 0, 100)
                )
            else:
                x = random.randint(0, self.window.width)
                y = random.randint(0, 50)
                arcade.draw_lrbt_rectangle_filled(
                    x - 75, x + 75,
                    y - 15, y + 15,
                    (0, 0, 0, 100)
                )

    def _draw_hud(self):
        """Интерфейс - упрощенный"""
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, 110,
            (0, 0, 0, 180)
        )

        # Здоровье
        health_width = 250 * (self.player_health / 100.0)
        if self.player_health > 60:
            health_color = (50, 200, 50)
        elif self.player_health > 30:
            health_color = (255, 150, 50)
        else:
            health_color = (255, 50, 50)
            if int(time.time() * 2) % 2 == 0:
                health_color = (255, 100, 100)

        arcade.draw_lrbt_rectangle_filled(20, 20 + health_width, 20, 40, health_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 20, 40, (255, 255, 255, 150), 2)
        arcade.draw_text(f"ЗДОРОВЬЕ: {int(self.player_health)}%", 25, 25, arcade.color.WHITE, 16)

        # Рассудок
        sanity_width = 250 * (self.player_sanity / 100.0)
        sanity_color = (100, 100, 200)
        arcade.draw_lrbt_rectangle_filled(20, 20 + sanity_width, 45, 65, sanity_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 45, 65, (255, 255, 255, 150), 2)
        arcade.draw_text(f"РАССУДОК: {int(self.player_sanity)}%", 25, 50, arcade.color.LIGHT_GRAY, 14)

        # Стресс
        stress_width = 250 * (self.player_stress / 100.0)
        if self.player_stress > 70:
            stress_color = (255, 50, 50)
        elif self.player_stress > 40:
            stress_color = (255, 150, 50)
        else:
            stress_color = (255, 200, 100)

        arcade.draw_lrbt_rectangle_filled(20, 20 + stress_width, 70, 90, stress_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 70, 90, (255, 255, 255, 150), 2)
        arcade.draw_text(f"СТРЕСС: {int(self.player_stress)}%", 25, 75, arcade.color.WHITE, 14)

        # Ключи
        progress_x = self.window.width - 280
        key_text = f"КЛЮЧИ: {self.keys_collected}/{self.keys_needed}"
        key_color = (255, 215, 0) if self.keys_collected >= self.keys_needed else arcade.color.WHITE
        if self.keys_collected >= self.keys_needed:
            if int(time.time() * 2) % 2 == 0:
                key_color = (255, 255, 150)

        arcade.draw_text(key_text, progress_x, 75, key_color, 22, bold=True)

        # Время
        time_text = f"ВРЕМЯ: {int(self.game_time)}с"
        arcade.draw_text(time_text, progress_x, 50, arcade.color.LIGHT_GRAY, 18)

        # Фонарик
        if self.flashlight_on:
            if self.flashlight_battery > 50:
                battery_color = (100, 255, 100)
            elif self.flashlight_battery > 20:
                battery_color = (255, 200, 100)
            else:
                battery_color = (255, 100, 100)
                if int(time.time()) % 2 == 0:
                    battery_color = (255, 150, 150)

            battery_text = f"ФОНАРИК: {int(self.flashlight_battery)}%"
            arcade.draw_text(
                battery_text, self.window.width // 2 - 100, 25,
                battery_color, 16
            )

        # Статус карты (убрали из мини-карты)
        if self.show_minimap:
            map_status = "КАРТА: ВКЛ"
            map_color = (100, 255, 100)
        else:
            map_status = "КАРТА: ВЫКЛ"
            map_color = (200, 200, 200)

        arcade.draw_text(
            map_status,
            self.window.width - 50, 15,
            map_color, 12,
            anchor_x="center"
        )

        # Сообщения
        if self.exit_found:
            blink = int(time.time() * 3) % 2 == 0
            if blink:
                arcade.draw_text(
                    "✓ ВЫХОД НАЙДЕН!",
                    self.window.width // 2, self.window.height - 60,
                    (255, 50, 50), 26,
                    anchor_x="center", bold=True
                )
        elif self.keys_collected >= self.keys_needed:
            arcade.draw_text(
                "ВСЕ КЛЮЧИ НАЙДЕНЫ! ИЩИТЕ ВЫХОД!",
                self.window.width // 2, self.window.height - 60,
                (255, 215, 0), 24,
                anchor_x="center", bold=True
            )

    def _draw_minimap(self):
        """Миникарта - без лишних надписей"""
        map_size = min(350, int(min(self.window.width, self.window.height) * self.minimap_scale))
        margin = 20
        cell_size = min(map_size // self.map_width, map_size // self.map_height)

        left = self.window.width - margin - map_size
        bottom = self.window.height - margin - map_size
        top = bottom + map_size
        right = left + map_size

        # Фон
        arcade.draw_lrbt_rectangle_filled(
            left - 10, right + 10, bottom - 10, top + 10,
            (0, 0, 0, 230)
        )

        # Рамка
        arcade.draw_lrbt_rectangle_outline(
            left, right, bottom, top,
            (180, 180, 180), 3
        )

        # Карта
        for y in range(self.map_height):
            for x in range(self.map_width):
                draw_x = left + (y * cell_size) + cell_size // 2
                draw_y = bottom + (x * cell_size) + cell_size // 2

                if self.map[y][x] == 1:
                    color = (80, 80, 80)
                    arcade.draw_lrbt_rectangle_filled(
                        draw_x - cell_size // 2 + 1,
                        draw_x + cell_size // 2 - 1,
                        draw_y - cell_size // 2 + 1,
                        draw_y + cell_size // 2 - 1,
                        color
                    )
                else:
                    color = (40, 40, 50)
                    arcade.draw_lrbt_rectangle_filled(
                        draw_x - cell_size // 2 + 1,
                        draw_x + cell_size // 2 - 1,
                        draw_y - cell_size // 2 + 1,
                        draw_y + cell_size // 2 - 1,
                        color
                    )

        # Игрок
        player_map_x = left + (self.player_y * cell_size)
        player_map_y = bottom + (self.player_x * cell_size)
        player_size = max(cell_size // 1.2, 8)

        arcade.draw_circle_filled(player_map_x, player_map_y, player_size, (0, 255, 0))
        arcade.draw_circle_outline(player_map_x, player_map_y, player_size, (255, 255, 255), 2)

        # Стрелка
        arrow_len = cell_size * 1.8
        map_angle = -(self.player_angle - math.pi / 2)

        arrow_x = player_map_x + math.cos(map_angle) * arrow_len
        arrow_y = player_map_y + math.sin(map_angle) * arrow_len

        arcade.draw_line(
            player_map_x, player_map_y,
            arrow_x, arrow_y,
            (0, 255, 0), 3
        )

        # Объекты
        for obj in self.objectives:
            if not obj.collected:
                obj_x = left + (obj.y * cell_size)
                obj_y = bottom + (obj.x * cell_size)
                obj_size = max(5, cell_size // 1.5)

                if obj.type == 'key':
                    arcade.draw_circle_filled(obj_x, obj_y, obj_size, (255, 215, 0))
                elif obj.type == 'exit':
                    if int(time.time() * 2) % 2 == 0:
                        arcade.draw_circle_filled(obj_x, obj_y, obj_size, (255, 50, 50))

        # Монстры
        for monster in self.monsters:
            if monster.active:
                monster_x = left + (monster.y * cell_size)
                monster_y = bottom + (monster.x * cell_size)
                monster_size = max(5, cell_size // 1.3)

                arcade.draw_circle_filled(monster_x, monster_y, monster_size, (200, 50, 50))

    def _draw_tutorial(self):
        """Обучение"""
        alpha = min(255, int(255 * (self.tutorial_time / 6.0)))

        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height,
            (0, 0, 0, alpha // 2)
        )

        texts = [
            "3D ХОРРОР ЛАБИРИНТ",
            "Найдите 3 ключа и выход",
            "",
            "Управление:",
            "WASD - движение",
            "Мышь - поворот камеры",
            "F - фонарик",
            "M - карта",
            "ПРОБЕЛ - крик",
            "I - инструкция",
            "",
            "Нажмите любую клавишу"
        ]

        center_y = self.window.height // 2 + 80
        for i, text in enumerate(texts):
            y_offset = i * 28
            if i == 0:
                size = 32
                color = (255, 50, 50)
            elif i == 1:
                size = 26
                color = (255, 215, 0)
            elif i == 3:
                size = 24
                color = (100, 200, 255)
            elif i == 11:
                size = 20
                color = (255, 255, 255)
            else:
                size = 18
                color = (200, 200, 200)

            arcade.draw_text(
                text, self.window.width // 2, center_y - y_offset,
                (*color, alpha), size,
                anchor_x="center", anchor_y="center",
                bold=(i in [0, 1, 11])
            )

    def _draw_instructions(self):
        """Инструкция - исправленная и аккуратная"""
        # Полупрозрачный фон
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height,
            (0, 0, 0, 220)
        )

        # Заголовок
        arcade.draw_text(
            "ИНСТРУКЦИЯ - 3D ЛАБИРИНТ",
            self.window.width // 2, self.window.height - 80,
            (255, 50, 50), 32,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        # Основные разделы с нормальным позиционированием
        sections = [
            ("УПРАВЛЕНИЕ", [
                "W/S - вперед/назад",
                "A/D - влево/вправо",
                "Мышь - поворот камеры",
                "F - фонарик (вкл/выкл)",
                "M - карта (вкл/выкл)",
                "ПРОБЕЛ - крик (отпугивает)",
                "I - эта инструкция",
                "ESC - выход в меню"
            ]),
            ("ЦЕЛЬ ИГРЫ", [
                "1. Найдите 3 золотых ключа",
                "2. Найдите красный выход",
                "3. Избегайте красных монстров",
                "4. Следите за здоровьем и рассудком"
            ]),
            ("ПОДСКАЗКИ", [
                "• Фонарик разряжается в темноте",
                "• Монстры преследуют по звуку",
                "• В темноте начинаются галлюцинации",
                "• Крик временно отпугивает монстров",
                "• Карта поможет ориентироваться"
            ])
        ]

        start_y = self.window.height - 150
        section_spacing = 50

        for section_index, (section_title, items) in enumerate(sections):
            y = start_y - section_index * section_spacing

            # Заголовок секции
            arcade.draw_text(
                section_title,
                self.window.width // 2, y,
                (255, 215, 0), 24,
                anchor_x="center", anchor_y="center",
                bold=True
            )

            # Элементы секции
            for item_index, item in enumerate(items):
                item_y = y - 30 - item_index * 25
                color = (200, 200, 255) if "•" in item else (255, 255, 255)
                arcade.draw_text(
                    item,
                    self.window.width // 2, item_y,
                    color, 18,
                    anchor_x="center", anchor_y="center"
                )

            start_y -= len(items) * 25 + 60

        # Кнопка закрытия
        arcade.draw_text(
            "Нажмите I или ESCAPE чтобы закрыть",
            self.window.width // 2, 60,
            (150, 255, 150), 20,
            anchor_x="center", anchor_y="center",
            bold=True
        )

    # ==================== УПРАВЛЕНИЕ ====================

    def on_key_press(self, symbol: int, modifiers: int):
        """Нажатие клавиши"""
        key_name_map = {
            arcade.key.W: 'W',
            arcade.key.S: 'S',
            arcade.key.A: 'A',
            arcade.key.D: 'D',
            arcade.key.LEFT: 'LEFT',
            arcade.key.RIGHT: 'RIGHT',
            arcade.key.Q: 'Q',
            arcade.key.E: 'E',
            arcade.key.F: 'F',
            arcade.key.M: 'M',
            arcade.key.SPACE: 'SPACE',
            arcade.key.I: 'I',
            arcade.key.ESCAPE: 'ESCAPE',
        }

        key_name = key_name_map.get(symbol, 'UNKNOWN')

        if self.show_tutorial and self.tutorial_time > 0 and symbol not in [arcade.key.ESCAPE, arcade.key.I]:
            self.show_tutorial = False
            return

        current_time = time.time()
        self.behavior_data.key_presses.append((current_time, key_name))

        if symbol == arcade.key.I:
            self.show_instructions = not self.show_instructions
            return

        if self.show_instructions and symbol == arcade.key.ESCAPE:
            self.show_instructions = False
            return

        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = True

        elif symbol == arcade.key.F:
            if self.flashlight_battery > 0:
                self.flashlight_on = not self.flashlight_on
                if self.sound_manager:
                    volume = 0.3 * self.fear_amplifiers['sounds']
                    sound = 'flashlight_on' if self.flashlight_on else 'flashlight_off'
                    self.sound_manager.play_sound(sound, volume=volume)

        elif symbol == arcade.key.M:
            current_time = time.time()
            if current_time - self.last_minimap_toggle > self.minimap_cooldown:
                self.show_minimap = not self.show_minimap
                self.last_minimap_toggle = current_time

        elif symbol == arcade.key.SPACE:
            self.behavior_data.scream_events.append(time.time())

            if self.sound_manager:
                volume = 0.6 * self.fear_amplifiers['sounds']
                self.sound_manager.play_sound('scream', volume=volume)

            self.screen_shake = 0.4
            self.player_stress = min(100, self.player_stress + 15)

            for monster in self.monsters:
                dx = monster.x - self.player_x
                dy = monster.y - self.player_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0.1 and distance < 10:
                    if random.random() < 0.7:
                        monster.x -= dx * 0.4
                        monster.y -= dy * 0.4
                        monster.attack_cooldown = 5.0
                        monster.is_hunting = False
                    else:
                        monster.detection_range *= 1.5
                        monster.is_hunting = True

        elif symbol == arcade.key.ESCAPE:
            self._end_game("ВЫХОД В МЕНЮ")

    def on_key_release(self, symbol: int, modifiers: int):
        """Отпускание клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Движение мыши"""
        if self.game_active and self.mouse_look and not self.show_instructions:
            if abs(dx) < 100 and abs(dy) < 100:
                self.behavior_data.mouse_deltas.append((dx, dy))
                self.player_angle += dx * self.mouse_sensitivity

    # ==================== КОНЕЦ ИГРЫ ====================

    def _win_game(self):
        """Победа"""
        self.game_won = True
        self.game_active = False
        self.victory = True
        self.game_over = True

        # Победный звук
        if self.sound_manager:
            self.sound_manager.play_sound('music', volume=0.4)

        self.end_game()

    def create_hud_text_objects(self):
        """Создать текстовые объекты для HUD (для производительности)"""
        # Здоровье
        self.health_text = arcade.Text(
            "ЗДОРОВЬЕ: 100%",
            25, 25,
            arcade.color.WHITE, 16
        )

        # Рассудок
        self.sanity_text = arcade.Text(
            "РАССУДОК: 100%",
            25, 50,
            arcade.color.LIGHT_GRAY, 14
        )

        # Стресс
        self.stress_text = arcade.Text(
            "СТРЕСС: 30%",
            25, 75,
            arcade.color.WHITE, 14
        )

        # Ключи
        self.keys_text = arcade.Text(
            "КЛЮЧИ: 0/3",
            self.window.width - 280, 75,
            arcade.color.WHITE, 22
        )

        # Время
        self.time_text = arcade.Text(
            "ВРЕМЯ: 0с",
            self.window.width - 280, 50,
            arcade.color.LIGHT_GRAY, 18
        )

        # Фонарик
        self.flashlight_text = arcade.Text(
            "ФОНАРИК: 100%",
            self.window.width // 2 - 100, 25,
            (100, 255, 100), 16
        )

        # Карта
        self.map_text = arcade.Text(
            "КАРТА: ВЫКЛ",
            self.window.width - 50, 15,
            (200, 200, 200), 12,
            anchor_x="center"
        )

    def update_hud_text(self):
        """Обновить текст HUD"""
        # Обновляем текст с текущими значениями
        self.health_text.text = f"ЗДОРОВЬЕ: {int(self.player_health)}%"

        if self.player_health > 60:
            self.health_text.color = arcade.color.WHITE
        elif self.player_health > 30:
            self.health_text.color = (255, 150, 50)
        else:
            self.health_text.color = (255, 50, 50)
            if int(time.time() * 2) % 2 == 0:
                self.health_text.color = (255, 100, 100)

        self.sanity_text.text = f"РАССУДОК: {int(self.player_sanity)}%"
        self.stress_text.text = f"СТРЕСС: {int(self.player_stress)}%"

        if self.player_stress > 70:
            self.stress_text.color = (255, 50, 50)
        elif self.player_stress > 40:
            self.stress_text.color = (255, 150, 50)
        else:
            self.stress_text.color = (255, 200, 100)

        self.keys_text.text = f"КЛЮЧИ: {self.keys_collected}/{self.keys_needed}"
        if self.keys_collected >= self.keys_needed:
            if int(time.time() * 2) % 2 == 0:
                self.keys_text.color = (255, 255, 150)
            else:
                self.keys_text.color = (255, 215, 0)
        else:
            self.keys_text.color = arcade.color.WHITE

        self.time_text.text = f"ВРЕМЯ: {int(self.game_time)}с"

        if self.flashlight_on:
            battery = int(self.flashlight_battery)
            if battery > 50:
                self.flashlight_text.color = (100, 255, 100)
            elif battery > 20:
                self.flashlight_text.color = (255, 200, 100)
            else:
                self.flashlight_text.color = (255, 100, 100)
                if int(time.time()) % 2 == 0:
                    self.flashlight_text.color = (255, 150, 150)
            self.flashlight_text.text = f"ФОНАРИК: {battery}%"
        else:
            self.flashlight_text.text = "ФОНАРИК: ВЫКЛ"
            self.flashlight_text.color = (200, 200, 200)

        if self.show_minimap:
            self.map_text.text = "КАРТА: ВКЛ"
            self.map_text.color = (100, 255, 100)
        else:
            self.map_text.text = "КАРТА: ВЫКЛ"
            self.map_text.color = (200, 200, 200)

    # В методе _draw_hud замените arcade.draw_text на рисование объектов:
    def _draw_hud(self):
        """Интерфейс - упрощенный"""
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, 110,
            (0, 0, 0, 180)
        )

        # Полоски здоровья, рассудка и стресса (остаются как есть)
        health_width = 250 * (self.player_health / 100.0)
        if self.player_health > 60:
            health_color = (50, 200, 50)
        elif self.player_health > 30:
            health_color = (255, 150, 50)
        else:
            health_color = (255, 50, 50)
            if int(time.time() * 2) % 2 == 0:
                health_color = (255, 100, 100)

        arcade.draw_lrbt_rectangle_filled(20, 20 + health_width, 20, 40, health_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 20, 40, (255, 255, 255, 150), 2)

        sanity_width = 250 * (self.player_sanity / 100.0)
        sanity_color = (100, 100, 200)
        arcade.draw_lrbt_rectangle_filled(20, 20 + sanity_width, 45, 65, sanity_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 45, 65, (255, 255, 255, 150), 2)

        stress_width = 250 * (self.player_stress / 100.0)
        if self.player_stress > 70:
            stress_color = (255, 50, 50)
        elif self.player_stress > 40:
            stress_color = (255, 150, 50)
        else:
            stress_color = (255, 200, 100)

        arcade.draw_lrbt_rectangle_filled(20, 20 + stress_width, 70, 90, stress_color)
        arcade.draw_lrbt_rectangle_outline(20, 270, 70, 90, (255, 255, 255, 150), 2)

        # Обновляем и рисуем текстовые объекты
        if not hasattr(self, 'health_text'):
            self.create_hud_text_objects()

        self.update_hud_text()

        # Рисуем все текстовые объекты
        self.health_text.draw()
        self.sanity_text.draw()
        self.stress_text.draw()
        self.keys_text.draw()
        self.time_text.draw()
        self.flashlight_text.draw()
        self.map_text.draw()

        # Сообщения (для них тоже можно создать Text объекты)
        if self.exit_found:
            blink = int(time.time() * 3) % 2 == 0
            if blink:
                if not hasattr(self, 'exit_found_text'):
                    self.exit_found_text = arcade.Text(
                        "✓ ВЫХОД НАЙДЕН!",
                        self.window.width // 2, self.window.height - 60,
                        (255, 50, 50), 26,
                        anchor_x="center", anchor_y="center", bold=True
                    )
                self.exit_found_text.draw()
        elif self.keys_collected >= self.keys_needed:
            if not hasattr(self, 'all_keys_text'):
                self.all_keys_text = arcade.Text(
                    "ВСЕ КЛЮЧИ НАЙДЕНЫ! ИЩИТЕ ВЫХОД!",
                    self.window.width // 2, self.window.height - 60,
                    (255, 215, 0), 24,
                    anchor_x="center", anchor_y="center", bold=True
                )
            self.all_keys_text.draw()


    def _end_game(self, reason: str):
        """Поражение - переход на экран проигрыша"""
        self.game_active = False
        self.game_over = True

        # Собираем статистику для экрана проигрыша
        game_stats = {
            'time': self.game_time,
            'keys_collected': self.keys_collected,
            'total_keys': self.keys_needed,
            'stress_level': self.player_stress,
            'sanity_level': self.player_sanity,
            'jump_scares': self.jump_scares_triggered,
            'monsters_killed': self.monsters_killed
        }

        # Импортируем и показываем экран проигрыша
        try:
            from game_over import GameOverView
            game_over_view = GameOverView(reason, game_stats)
            self.window.show_view(game_over_view)
        except ImportError:
            # Fallback: возвращаемся в меню
            from scenes.main_menu import MainMenuView
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

    def end_game(self):
        """Завершение игры"""
        if self.victory:
            try:
                from results import ResultsView

                game_stats = {
                    'time': self.game_time,
                    'keys_collected': self.keys_collected,
                    'total_keys': self.keys_needed,
                    'stress_level': self.player_stress,
                    'sanity_level': self.player_sanity,
                    'jump_scares': self.jump_scares_triggered,
                }

                results_view = ResultsView(self.fear_profile, game_stats)
                self.window.show_view(results_view)
            except ImportError:
                from scenes.main_menu import MainMenuView
                self.window.show_view(MainMenuView())