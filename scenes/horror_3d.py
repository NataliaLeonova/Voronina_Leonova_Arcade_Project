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
    move_timer: float = 0
    move_delay: float = random.uniform(3.0, 8.0)  # УВЕЛИЧЕНА ЧАСТОТА ПЕРЕМЕЩЕНИЙ
    idle_timer: float = 0
    idle_duration: float = random.uniform(2.0, 5.0)
    is_idle: bool = False
    wander_range: float = 15.0  # РАДИУС БЛУЖДАНИЯ
    spawn_x: float = 0
    spawn_y: float = 0
    next_wander_target: Optional[Tuple[float, float]] = None


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
    """Генератор сложных лабиринтов с улучшенным алгоритмом"""

    @staticmethod
    def generate_perfect_maze(width: int, height: int) -> List[List[int]]:
        """Генерация совершенного лабиринта (1-стены, 0-проходы)"""
        # Убедимся, что размеры нечетные для правильного лабиринта
        if width % 2 == 0:
            width += 1
        if height % 2 == 0:
            height += 1

        # Инициализируем полностью заполненный лабиринт
        maze = [[1 for _ in range(width)] for _ in range(height)]

        # Начальная точка - центр лабиринта
        start_x, start_y = width // 2, height // 2
        if start_x % 2 == 0:
            start_x -= 1
        if start_y % 2 == 0:
            start_y -= 1

        maze[start_y][start_x] = 0

        # Стек для алгоритма
        stack = [(start_x, start_y)]
        visited = set()
        visited.add((start_x, start_y))

        # Все возможные направления (шаг 2 клетки)
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]

        while stack:
            x, y = stack[-1]

            # Получаем непосещенных соседей
            neighbors = []
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                # Проверяем границы
                if 0 <= nx < width and 0 <= ny < height:
                    # Проверяем, что это потенциальная проходимая клетка
                    if maze[ny][nx] == 1 and (nx, ny) not in visited:
                        # Проверяем, что вокруг есть стены
                        wall_count = 0
                        for wx, wy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            cx, cy = nx + wx, ny + wy
                            if 0 <= cx < width and 0 <= cy < height and maze[cy][cx] == 1:
                                wall_count += 1
                        if wall_count >= 3:  # Должно быть окружено стенами
                            neighbors.append((nx, ny, dx, dy))

            if neighbors:
                # Выбираем случайного соседа
                nx, ny, dx, dy = random.choice(neighbors)

                # Убираем стену между текущей клеткой и соседом
                maze[y + dy // 2][x + dx // 2] = 0
                maze[ny][nx] = 0

                # Добавляем в посещенные и стек
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                # Возвращаемся назад
                stack.pop()

        MazeGenerator._ensure_perfect_connectivity(maze, width, height)

        # Создаем несколько дополнительных проходов для лучшей проходимости
        MazeGenerator._add_extra_passages(maze, width, height)

        # Гарантируем, что все мертвые зоны соединены
        MazeGenerator._connect_dead_ends(maze, width, height)

        return maze

    @staticmethod
    def _ensure_perfect_connectivity(maze: List[List[int]], width: int, height: int):
        """Гарантировать, что лабиринт полностью проходим"""
        # Находим все проходимые клетки
        passages = []
        for y in range(height):
            for x in range(width):
                if maze[y][x] == 0:
                    passages.append((x, y))

        if not passages:
            return

        # Проверяем связность через поиск в ширину
        start = passages[0]
        visited = set()
        queue = deque([start])

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue

            visited.add((x, y))

            # Проверяем всех соседей
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and
                        maze[ny][nx] == 0 and (nx, ny) not in visited):
                    queue.append((nx, ny))

        # Если есть непосещенные проходы, соединяем их
        unvisited = [p for p in passages if p not in visited]
        if unvisited:
            for ux, uy in unvisited:
                # Ищем ближайший посещенный проход
                min_dist = float('inf')
                nearest = None
                for vx, vy in visited:
                    dist = abs(ux - vx) + abs(uy - vy)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (vx, vy)

                if nearest:
                    vx, vy = nearest
                    # Прокладываем путь
                    cx, cy = ux, uy
                    while (cx, cy) != (vx, vy):
                        if random.random() < 0.5 and cx != vx:
                            cx += 1 if cx < vx else -1
                        else:
                            cy += 1 if cy < vy else -1

                        if 0 <= cx < width and 0 <= cy < height:
                            maze[cy][cx] = 0
                            visited.add((cx, cy))

        # Убедимся, что нет изолированных областей
        MazeGenerator._check_and_fix_islands(maze, width, height)

    @staticmethod
    def _check_and_fix_islands(maze: List[List[int]], width: int, height: int):
        """Проверить и исправить изолированные области"""
        visited_all = set()
        islands = []

        for y in range(height):
            for x in range(width):
                if maze[y][x] == 0 and (x, y) not in visited_all:
                    # Новая область
                    island = []
                    queue = deque([(x, y)])
                    visited_island = set()

                    while queue:
                        cx, cy = queue.popleft()
                        if (cx, cy) in visited_island:
                            continue

                        visited_island.add((cx, cy))
                        island.append((cx, cy))

                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nx, ny = cx + dx, cy + dy
                            if (0 <= nx < width and 0 <= ny < height and
                                    maze[ny][nx] == 0 and (nx, ny) not in visited_island):
                                queue.append((nx, ny))

                    islands.append(island)
                    visited_all.update(visited_island)

        # Если больше одного острова, соединяем их
        if len(islands) > 1:
            for i in range(1, len(islands)):
                # Соединяем текущий остров с предыдущим
                island1 = islands[i - 1]
                island2 = islands[i]

                # Находим ближайшие точки
                min_dist = float('inf')
                point1 = None
                point2 = None

                for x1, y1 in island1:
                    for x2, y2 in island2:
                        dist = abs(x1 - x2) + abs(y1 - y2)
                        if dist < min_dist:
                            min_dist = dist
                            point1 = (x1, y1)
                            point2 = (x2, y2)

                if point1 and point2:
                    x1, y1 = point1
                    x2, y2 = point2

                    # Прокладываем путь
                    cx, cy = x1, y1
                    while (cx, cy) != (x2, y2):
                        if random.random() < 0.5 and cx != x2:
                            cx += 1 if cx < x2 else -1
                        else:
                            cy += 1 if cy < y2 else -1

                        if 0 <= cx < width and 0 <= cy < height:
                            maze[cy][cx] = 0

                            # Также убираем стены вокруг для плавности
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                nx, ny = cx + dx, cy + dy
                                if 0 <= nx < width and 0 <= ny < height and random.random() < 0.3:
                                    maze[ny][nx] = 0

    @staticmethod
    def _add_extra_passages(maze: List[List[int]], width: int, height: int):
        """Добавить дополнительные проходы для лучшей проходимости"""
        # Добавляем случайные проходы
        extra_passages = (width * height) // 30  # Примерно 3% клеток

        for _ in range(extra_passages):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)

            # Проверяем, что это стена
            if maze[y][x] == 1:
                # Считаем соседние стены
                wall_count = 0
                passable_count = 0

                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if maze[ny][nx] == 1:
                            wall_count += 1
                        else:
                            passable_count += 1

                # Если стена окружена проходами, делаем проход
                if passable_count >= 2 and wall_count <= 2:
                    maze[y][x] = 0

                    # С небольшим шансом делаем дополнительные проходы вокруг
                    if random.random() < 0.2:
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < width and 0 <= ny < height and
                                    maze[ny][nx] == 1 and random.random() < 0.5):
                                maze[ny][nx] = 0

    @staticmethod
    def _connect_dead_ends(maze: List[List[int]], width: int, height: int):
        """Соединить тупики для лучшей проходимости"""
        dead_ends = []

        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if maze[y][x] == 0:
                    # Считаем соседние проходы
                    passable_neighbors = 0
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 0:
                            passable_neighbors += 1

                    # Если это тупик (только 1 проход)
                    if passable_neighbors == 1:
                        dead_ends.append((x, y))

        # Соединяем некоторые тупики
        for x, y in dead_ends:
            if random.random() < 0.3:  # 30% шанс соединения
                # Ищем направление для нового прохода
                directions = []
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1:
                        # Проверяем, что за стеной есть проход
                        nx2, ny2 = x + dx * 2, y + dy * 2
                        if (0 <= nx2 < width and 0 <= ny2 < height and
                                maze[ny2][nx2] == 0):
                            directions.append((dx, dy))

                if directions:
                    dx, dy = random.choice(directions)
                    maze[y + dy][x + dx] = 0


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
    """3D хоррор-лабиринт"""

    def __init__(self, fear_profile=None):
        super().__init__()

        # Переменные для звуков
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
        self.music_playing = False
        self.current_music = None
        self.music_volume = 0.4  # Общая громкость музыки
        self.sfx_volume = 1.0  # Громкость звуковых эффектов
        self.jumpscare_volume = 1.5  # Увеличенная громкость для скримеров

        # Таймеры для звуков
        self.sudden_sound_timer = 0
        self.sudden_sound_interval = random.uniform(20.0, 40.0)  # Резкие звуки реже

        # Инициализируем звуковую систему
        self.init_sound_manager()

        # Основные переменные
        self.fear_analyzer = FearAnalyzer()
        self.behavior_data = BehaviorData()
        self.fear_amplifiers = self.fear_analyzer.fear_amplifiers.copy()
        self.fear_profile = fear_profile or {}
        self.last_activity_time = time.time()
        self.inactivity_start = 0

        # Настройка игрока
        self.map_width = 31
        self.map_height = 31
        self.tile_size = 64

        # Генерация лабиринта
        self.map = MazeGenerator.generate_perfect_maze(self.map_width, self.map_height)
        self.maze = self.map

        # Находим открытую центральную зону для старта
        self.player_x, self.player_y = self._find_start_position()
        self.player_angle = 0.0
        self.player_sanity = 100.0
        self.player_health = 100.0
        self.player_stress = 30.0
        self.player_fov = math.pi / 1.8

        # Время игры
        self.game_time = 0.0
        self.max_game_time = 600.0
        self.time_warning_timer = 0.0
        self.show_time_warning = False
        self.time_since_last_scare = 0.0
        self.time_in_darkness = 0.0
        self.time_since_last_analysis = 0.0
        self.start_time = time.time()

        # Коллизии
        self.collision_map = self._create_collision_map()
        self.walls = self._create_walls_list()
        self.exit_location = self._find_far_position(self.player_x, self.player_y)

        # ИНТЕРФЕЙС
        self.show_minimap = False
        self.last_minimap_toggle = 0
        self.minimap_cooldown = 0.3
        self.minimap_scale = 0.8
        self.show_instructions = False
        self.show_i_hint = True  # Флаг для показа подсказки про клавишу I
        self.i_hint_timer = 5.0  # 5 секунд показываем подсказку

        # ОБЪЕКТЫ
        self.objectives: List[Objective] = []
        self.keys_collected = 0
        self.keys_needed = 3  # Возвращаем 3 ключа
        self.total_keys = 3
        self.exit_found = False
        self._place_objects()

        # ОСВЕЩЕНИЕ
        self.flashlight_on = True
        self.flashlight_battery = 200.0
        self.flashlight_flicker = 0.0
        self.ambient_light = 1.0
        self.light_level = 1.0

        # ЭФФЕКТЫ ОСВЕЩЕНИЯ
        self.darkness_timer = 0.0
        self.darkness_stage = 0  # 0-нормально, 1-средняя темнота, 2-темно
        self.darkness_target = 0.0
        self.darkness_speed = 0.08  # Медленнее увеличение темноты

        # Мерцание света
        self.light_flicker_active = False
        self.light_flicker_timer = 0.0
        self.light_flicker_duration = random.uniform(2.0, 6.0)
        self.light_flicker_intensity = 0.0

        # Землетрясение
        self.earthquake_active = False
        self.earthquake_timer = 0.0
        self.earthquake_duration = random.uniform(3.0, 8.0)
        self.earthquake_intensity = 0.0

        # === ЭФФЕКТЫ ===
        self.screen_shake = 0.0
        self.blood_overlay = 0.0
        self.vignette = 0.4
        self.visual_distortion = 0.0
        self.paranoia_effect = 0.0
        self.camera_shake = 0.0
        self.flash_effect = 0.0
        self.walk_bob = 0.0

        # ЖУТКИЕ ВИЗУАЛЬНЫЕ ЭФФЕКТЫ
        self.hallucination_timer = 0.0
        self.hallucination_active = False
        self.shadow_figures = []  # Теневые фигуры для галлюцинаций
        self.blood_veins = []  # Кровавые прожилки на экране
        self.whisper_effects = []  # Эффекты шепотов

        # ЧАСТИЦЫ
        self.particles: List[Particle] = []
        self.blood_particles: List[Particle] = []

        # МОНСТРЫ
        self.monsters: List[Monster] = []
        self._init_monsters()

        # ЭФФЕКТЫ ПРИБЛИЖЕНИЯ К МОНСТРАМ
        self.near_monster_effect = 0.0
        self.monster_proximity_timer = 0.0

        # УПРАВЛЕНИЕ
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

        # Таймеры для случайных событий
        self.random_event_timer = 0.0
        self.next_event_time = random.uniform(30.0, 60.0)

        # СОСТОЯНИЕ
        self.game_active = True
        self.game_won = False
        self.show_tutorial = True
        self.tutorial_time = 6.0
        self.game_over = False
        self.victory = False
        self.time_out = False  # Флаг окончания времени

        # СТАТИСТИКА
        self.jump_scares_triggered = 0
        self.monsters_killed = 0

        # АДАПТИВНЫЕ ЭФФЕКТЫ
        self.adaptive_music_pitch = 1.0
        self.adaptive_sound_volume = 1.0
        self.fear_induced_darkness = 0.0

        # Инициализируем визуальные эффекты
        self._init_visual_effects()

    def _init_visual_effects(self):
        """Инициализировать визуальные эффекты"""
        # Создаем теневы фигуры для галлюцинаций
        self.shadow_figures = []
        for _ in range(3):
            self.shadow_figures.append({
                'x': random.uniform(0, self.window.width),
                'y': random.uniform(0, self.window.height),
                'life': 0,
                'max_life': random.uniform(1.0, 3.0),
                'size': random.uniform(30, 60),
                'speed': random.uniform(10, 30)
            })

        # Создаем кровавые прожилки
        self.blood_veins = []
        for _ in range(10):
            self.blood_veins.append({
                'x1': random.uniform(0, self.window.width),
                'y1': random.uniform(0, self.window.height),
                'x2': random.uniform(0, self.window.width),
                'y2': random.uniform(0, self.window.height),
                'thickness': random.uniform(1, 3),
                'alpha': 0,
                'pulse': random.random() * math.pi * 2
            })

        # Создаем эффекты шепотов
        self.whisper_effects = []
        for _ in range(5):
            self.whisper_effects.append({
                'x': random.uniform(0, self.window.width),
                'y': random.uniform(0, self.window.height),
                'text': random.choice(["...", "смотри...", "иди...", "нельзя...", "там..."]),
                'alpha': 0,
                'life': 0,
                'max_life': random.uniform(2.0, 4.0)
            })

    # ЗВУКОВАЯ СИСТЕМА

    def init_sound_manager(self):
        """Инициализировать звуки"""
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager(sound_mode="level2")
            self.sound_manager.set_volume(1.0)
            self.start_background_music()
        except Exception:
            self.sound_manager = None

    def start_background_music(self):
        """Запустить фоновую музыку"""
        if not self.sound_manager:
            return

        if not self.music_playing and self.sound_manager.sounds.get('music'):
            # Выбираем случайную музыку из папки music
            music_list = self.sound_manager.sounds.get('music', [])
            if music_list:
                music_data = random.choice(music_list)
                self.current_music = music_data['sound']
                # Запускаем музыку с циклом
                self.current_music.play(volume=self.music_volume, loop=True)
                self.music_playing = True

    def stop_background_music(self):
        """Остановить фоновую музыку"""
        if self.music_playing and self.current_music:
            self.current_music.stop()
            self.music_playing = False

    def play_jumpscare_3d(self):
        """Скример"""
        if self.sound_manager:
            # Останавливаем музыку на время скримера
            if self.music_playing and self.current_music:
                self.current_music.stop()
                self.music_playing = False

            # Ищем звук в папке jumpscare
            jumpscare_sounds = []
            for category, sounds in self.sound_manager.sounds.items():
                for sound_data in sounds:
                    if 'jumpscare' in sound_data.get('name', '').lower() or 'scare' in sound_data.get('name',
                                                                                                      '').lower():
                        jumpscare_sounds.append(sound_data)

            # Если нет специальных звуков скримеров, используем обычные scream
            if not jumpscare_sounds:
                jumpscare_sounds = self.sound_manager.sounds.get('scream', [])

            if jumpscare_sounds:
                sound_data = random.choice(jumpscare_sounds)
                # ОЧЕНЬ ГРОМКИЙ звук
                sound_data['sound'].play(volume=self.jumpscare_volume * 1.5)

                # Добавляем резкие звуки с задержкой
                arcade.schedule(lambda dt: self.play_sudden_sound(volume=0.7), 0.2)
                arcade.schedule(lambda dt: self.play_sudden_sound(volume=0.5), 0.5)

                # Перезапускаем музыку через 2 секунды
                arcade.schedule(lambda dt: self.start_background_music(), 2.0)

                self.camera_shake = 1.0
                self.flash_effect = 1.0
                self.player_stress = min(100, self.player_stress + 40)  # Больше стресса
                self.player_sanity = max(0, self.player_sanity - 25)  # Больше потери рассудка
                self.jump_scares_triggered += 1

    def play_sudden_sound(self, volume=0.5):
        """Воспроизвести резкий звук"""
        if self.sound_manager:
            try:
                # Выбираем случайный резкий звук
                sound_types = ['sudden', 'impact', 'glass', 'metal', 'break', 'clang']
                for sound_type in sound_types:
                    if self.sound_manager.sounds.get(sound_type):
                        self.sound_manager.play_sound(sound_type, volume=volume * self.sfx_volume)
                        break
            except:
                pass

    def update_sounds(self, delta_time):
        """Обновление звуков с новой логикой"""
        if not self.sound_manager:
            return

        current_time = time.time()
        self.sound_timer += delta_time
        self.sudden_sound_timer += delta_time

        # ЗВУКИ ШАГОВ
        if self.is_moving:
            if current_time - self.last_step_sound > self.step_interval:
                volume = 0.3 + random.random() * 0.1
                self.sound_manager.play_sound('footstep', volume=volume * self.sfx_volume)
                self.last_step_sound = current_time
                self.step_counter += 1

        # Тихие звуки
        if current_time - self.last_ambient_sound > self.ambient_interval:
            sound_type = random.choice(['ambient', 'drip', 'wind'])
            volume = 0.1 + random.random() * 0.1  # Очень тихо
            self.sound_manager.play_sound(sound_type, volume=volume * self.sfx_volume)
            self.last_ambient_sound = current_time
            self.ambient_interval = random.randint(10, 20)  # Реже

        # Шепот
        if random.random() < 0.005:  # Реже
            volume = 0.08 + random.random() * 0.05  # Очень тихо
            self.sound_manager.play_sound('whisper', volume=volume * self.sfx_volume)

            # Активируем эффект шепота
            for effect in self.whisper_effects:
                if effect['life'] <= 0:
                    effect['x'] = random.uniform(0, self.window.width)
                    effect['y'] = random.uniform(0, self.window.height)
                    effect['text'] = random.choice(["...", "смотри...", "иди...", "нельзя...", "там...", "за тобой..."])
                    effect['alpha'] = 255
                    effect['life'] = effect['max_life']
                    break

        # СЕРДЦЕБИЕНИЕ
        if self.player_stress > 60 or self.near_monster_effect > 0.5:
            self.heartbeat_timer += delta_time
            heartbeat_interval = max(0.1, 1.0 - max(self.player_stress - 60, self.near_monster_effect * 50) / 100)

            if self.heartbeat_timer > heartbeat_interval:
                volume = 0.3 + max((self.player_stress - 60) / 200, self.near_monster_effect * 0.5)
                self.sound_manager.play_sound('heartbeat', volume=volume * self.sfx_volume)
                self.heartbeat_timer = 0
                self.heartbeat_active = True
        else:
            self.heartbeat_active = False

        # ЗВУКИ МОНСТРОВ - ТОЛЬКО КОГДА БЛИЗКО
        self.monster_sound_timer += delta_time
        if self.monster_sound_timer > 3.0:  # Реже
            for monster in self.monsters:
                if monster.active:
                    dx = monster.x - self.player_x
                    dy = monster.y - self.player_y
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Только если очень близко
                    if distance < 100:
                        if random.random() < 0.4:
                            volume = 0.6 * (1.0 - distance / 200)
                            self.sound_manager.play_sound('monster', volume=volume * self.sfx_volume)
                            self.monster_near_counter += 1

            self.monster_sound_timer = 0

        # ВНЕЗАПНЫЕ звуки
        if self.sudden_sound_timer > self.sudden_sound_interval:
            # Проверяем условия для резкого звука
            should_play = False

            # Условия для резкого звука:
            if self.light_level < 0.3 and random.random() < 0.7:
                should_play = True
            elif self.player_sanity < 40 and random.random() < 0.6:
                should_play = True
            elif self.earthquake_active and random.random() < 0.8:
                should_play = True
            elif self.light_flicker_active and random.random() < 0.5:
                should_play = True
            elif self.near_monster_effect > 0.7 and random.random() < 0.9:
                should_play = True

            if should_play:
                volume = 0.6 + random.random() * 0.3
                self.play_sudden_sound(volume=volume)
                self.camera_shake = 0.4
                self.player_stress = min(100, self.player_stress + 15)

                # Сбрасываем таймер
                self.sudden_sound_timer = 0
                self.sudden_sound_interval = random.uniform(15.0, 30.0)

    def update_hallucinations(self, delta_time):
        """Обновление галлюцинаций"""
        self.hallucination_timer += delta_time

        # Галлюцинации при низком рассудке
        if self.player_sanity < 50 and random.random() < 0.01:
            self.hallucination_active = True

        if self.hallucination_active:
            # Активируем теневые фигуры
            for figure in self.shadow_figures:
                if figure['life'] <= 0 and random.random() < 0.1:
                    figure['life'] = figure['max_life']
                    figure['x'] = random.uniform(0, self.window.width)
                    figure['y'] = random.uniform(0, self.window.height)

            # Обновляем жизнь фигур
            for figure in self.shadow_figures:
                if figure['life'] > 0:
                    figure['life'] -= delta_time
                    # Двигаем фигуры
                    figure['x'] += random.uniform(-1, 1) * figure['speed'] * delta_time
                    figure['y'] += random.uniform(-1, 1) * figure['speed'] * delta_time

        # Кровавые прожилки при стрессе
        if self.player_stress > 70:
            for vein in self.blood_veins:
                vein['pulse'] += delta_time * 2
                vein['alpha'] = int((math.sin(vein['pulse']) + 1) / 2 * 100 * (self.player_stress - 70) / 30)

        # Эффекты шепотов
        for effect in self.whisper_effects:
            if effect['life'] > 0:
                effect['life'] -= delta_time
                effect['alpha'] = int((effect['life'] / effect['max_life']) * 255)
                # Двигаем текст
                effect['x'] += random.uniform(-10, 10) * delta_time
                effect['y'] += random.uniform(-10, 10) * delta_time

    def update_darkness(self, delta_time):
        """Постепенное увеличение темноты"""
        self.darkness_timer += delta_time

        # Каждые 90 секунд увеличиваем темноту
        if self.darkness_timer > 90.0:
            self.darkness_timer = 0
            self.darkness_stage = min(2, self.darkness_stage + 1)

            # Новый уровень темноты
            if self.darkness_stage == 1:
                self.darkness_target = 0.3
                # Резкий звук при изменении темноты
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.4)
            elif self.darkness_stage == 2:
                self.darkness_target = 0.6
                # Громкий звук при сильной темноте
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.6)

        # Плавное изменение темноты
        if self.fear_induced_darkness < self.darkness_target:
            self.fear_induced_darkness = min(self.darkness_target,
                                             self.fear_induced_darkness + delta_time * self.darkness_speed)
        elif self.fear_induced_darkness > self.darkness_target:
            self.fear_induced_darkness = max(self.darkness_target,
                                             self.fear_induced_darkness - delta_time * self.darkness_speed)

    def update_light_flicker(self, delta_time):
        """Обновление мерцания света"""
        if not self.light_flicker_active:
            # Случайный шанс начать мерцание
            if random.random() < 0.001 * (self.player_stress / 100):
                self.light_flicker_active = True
                self.light_flicker_timer = 0
                self.light_flicker_duration = random.uniform(2.0, 6.0)
                self.light_flicker_intensity = random.uniform(0.3, 0.8)
                # Громкий звук при мерцании
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.5)
        else:
            self.light_flicker_timer += delta_time
            if self.light_flicker_timer > self.light_flicker_duration:
                self.light_flicker_active = False
                self.light_flicker_intensity = 0.0

    def update_earthquake(self, delta_time):
        """Обновление землетрясения"""
        if not self.earthquake_active:
            # Случайный шанс начать землетрясение
            if random.random() < 0.0005 * (self.player_stress / 100):
                self.earthquake_active = True
                self.earthquake_timer = 0
                self.earthquake_duration = random.uniform(3.0, 8.0)
                self.earthquake_intensity = random.uniform(0.5, 1.0)
                # ОЧЕНЬ ГРОМКИЕ звуки при землетрясении
                if self.sound_manager:
                    self.play_jumpscare_3d()  # Полноценный скример
        else:
            self.earthquake_timer += delta_time
            if self.earthquake_timer > self.earthquake_duration:
                self.earthquake_active = False
                self.earthquake_intensity = 0.0
            else:
                # Интенсивность уменьшается со временем
                self.earthquake_intensity = max(0, self.earthquake_intensity - delta_time * 0.1)

    def update_random_events(self, delta_time):
        """Обновление случайных событий"""
        self.random_event_timer += delta_time

        if self.random_event_timer > self.next_event_time:
            self.random_event_timer = 0
            self.next_event_time = random.uniform(30.0, 90.0)

            # Случайное событие
            event = random.choice(['light_flicker', 'whisper', 'camera_shake', 'paranoia_boost', 'hallucination'])

            if event == 'light_flicker' and not self.light_flicker_active:
                self.light_flicker_active = True
                self.light_flicker_timer = 0
                self.light_flicker_duration = random.uniform(3.0, 7.0)
                self.light_flicker_intensity = random.uniform(0.4, 0.9)
                # Звук при мерцании
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.4)

            elif event == 'whisper':
                if self.sound_manager:
                    whispers = ["Они смотрят...", "Ты не уйдешь...", "Здесь...", "Прямо за тобой..."]
                    whisper = random.choice(whispers)
                    self.sound_manager.play_sound('whisper', volume=0.2)  # Тихо
                    self.player_sanity = max(0, self.player_sanity - 5)

            elif event == 'camera_shake':
                self.camera_shake = random.uniform(0.3, 0.7)
                # Резкий звук при тряске
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.3)

            elif event == 'paranoia_boost':
                self.paranoia_effect = min(0.8, self.paranoia_effect + 0.3)

            elif event == 'hallucination':
                self.hallucination_active = True
                print("Начинаются галлюцинации...")

    def update_monster_proximity_effect(self, delta_time):
        """Эффект при приближении к монстрам"""
        nearest_distance = float('inf')
        for monster in self.monsters:
            if monster.active:
                dx = monster.x - self.player_x
                dy = monster.y - self.player_y
                distance = math.sqrt(dx * dx + dy * dy)
                nearest_distance = min(nearest_distance, distance)

        # Обновление эффекта
        if nearest_distance < 10:
            proximity = 1.0 - (nearest_distance / 10.0)
            self.near_monster_effect = proximity * 1.5
            self.monster_proximity_timer += delta_time

            # Моргание при близости
            if self.monster_proximity_timer > 0.3:
                self.light_flicker_intensity = max(self.light_flicker_intensity, proximity * 0.5)
                self.monster_proximity_timer = 0

            # Увеличение стресса
            if proximity > 0.7:
                self.player_stress = min(100, self.player_stress + delta_time * 10)

                # Громкие звуки при очень близком монстре
                if proximity > 0.9 and random.random() < 0.05:
                    if self.sound_manager:
                        volume = 0.8 * (1.0 + proximity)
                        self.sound_manager.play_sound('monster', volume=volume)
        else:
            self.near_monster_effect = max(0, self.near_monster_effect - delta_time * 2)


    def on_update(self, delta_time: float):
        """Главный цикл"""
        if not self.game_active or self.game_won:
            return

        self.game_time += delta_time

        # ПРОВЕРКА ВРЕМЕНИ
        self.time_warning_timer += delta_time
        if self.game_time > self.max_game_time:
            self.time_out = True
            self._end_game("ВРЕМЯ ВЫШЛО")
            return

        # Предупреждение за 60 секунд до конца
        if self.game_time > self.max_game_time - 60 and self.time_warning_timer > 10:
            self.show_time_warning = True
            self.time_warning_timer = 0
            # Звуковое предупреждение
            if self.sound_manager:
                self.sound_manager.play_sound('sudden', volume=0.4)

        self.tutorial_time = max(0, self.tutorial_time - delta_time)
        self.last_minimap_toggle = max(0, self.last_minimap_toggle - delta_time)
        self.time_since_last_analysis += delta_time

        # Обновление подсказки про клавишу I
        if self.show_i_hint:
            self.i_hint_timer -= delta_time
            if self.i_hint_timer <= 0:
                self.show_i_hint = False

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

        # Новые эффекты
        self.update_hallucinations(delta_time)
        self.update_darkness(delta_time)
        self.update_light_flicker(delta_time)
        self.update_earthquake(delta_time)
        self.update_random_events(delta_time)
        self.update_monster_proximity_effect(delta_time)

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
            self.sfx_volume = self.fear_amplifiers['sounds']
            self.sound_manager.set_volume(self.sfx_volume)

        self.paranoia_effect = min(0.7, (self.fear_amplifiers['paranoia'] - 1.0) * 0.35)

    def _update_player(self, delta_time: float):
        """Обновить игрока"""
        move_forward = 0
        move_right = 0

        # Замедление при низком рассудке
        speed_multiplier = 1.0
        if self.player_sanity < 40:
            speed_multiplier = 0.7
        elif self.player_sanity < 20:
            speed_multiplier = 0.5

        # Замедление при землетрясении
        if self.earthquake_active:
            speed_multiplier *= 0.6

        move_speed = 3.0 * delta_time * speed_multiplier  # УВЕЛИЧЕНА СКОРОСТЬ (было 2.8)

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
            turn_amount -= self.turn_speed * delta_time * speed_multiplier
            self.behavior_data.key_presses.append((time.time(), 'LEFT'))
        if self.keys_pressed[arcade.key.RIGHT] or self.keys_pressed[arcade.key.E]:
            turn_amount += self.turn_speed * delta_time * speed_multiplier
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
        speed_factor = 0.9
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
            # Увеличенный расход при мерцании
            drain_multiplier = 1.0
            if self.light_flicker_active:
                drain_multiplier = 1.5

            drain_rate = 0.5 * (
                    1.0 + self.fear_amplifiers['darkness'] * 0.3) * drain_multiplier  # МЕНЬШЕ РАСХОД (было 0.6)
            self.flashlight_battery = max(0, self.flashlight_battery - delta_time * drain_rate)

            if self.flashlight_battery < 30:
                self.flashlight_flicker = math.sin(self.game_time * 15) * 0.3 + 0.7
            else:
                self.flashlight_flicker = 1.0

            if self.flashlight_battery <= 0:
                self.flashlight_on = False
                self.player_stress = min(100, self.player_stress + 25)
                # Громкий звук при отключении фонарика
                if self.sound_manager:
                    self.play_sudden_sound(volume=0.6)
        else:
            if self.flashlight_battery < 200:  # Соответственно увеличенному максимуму
                self.flashlight_battery = min(200, self.flashlight_battery + delta_time * 0.15)  # БЫСТРЕЕ ЗАРЯДКА

        # Учет мерцания
        if self.flashlight_on and self.flashlight_battery > 20:
            base_level = self.flashlight_flicker
            if self.light_flicker_active:
                flicker = (math.sin(self.game_time * 30) + 1) / 2
                flicker = flicker * 0.5 + 0.5  # От 0.5 до 1.0
                base_level *= flicker
            self.light_level = base_level
        else:
            self.light_level = max(0.1, 0.3 - self.fear_induced_darkness)

    def _update_monsters(self, delta_time: float):
        """Обновить монстров"""
        for monster in self.monsters:
            if not monster.active:
                continue

            monster.attack_cooldown = max(0, monster.attack_cooldown - delta_time)
            monster.last_seen_time += delta_time
            monster.move_timer += delta_time
            monster.idle_timer += delta_time

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

                if monster.last_seen_time > 8.0:  # УВЕЛИЧЕНО ВРЕМЯ ПРЕСЛЕДОВАНИЯ (было 5.0)
                    monster.is_hunting = False
                    monster.next_wander_target = None
            else:
                # ЦИКЛ: БЛУЖДАНИЕ -> ОЖИДАНИЕ -> БЛУЖДАНИЕ
                if monster.is_idle:
                    monster.idle_timer += delta_time
                    if monster.idle_timer > monster.idle_duration:
                        monster.is_idle = False
                        monster.idle_timer = 0
                        monster.move_timer = 0
                        monster.idle_duration = random.uniform(2.0, 5.0)

                        # Выбираем новую цель для блуждания
                        self._set_monster_wander_target(monster)
                else:
                    monster.move_timer += delta_time

                    if monster.next_wander_target:
                        target_x, target_y = monster.next_wander_target
                        pdx = target_x - monster.x
                        pdy = target_y - monster.y
                        pdist = math.sqrt(pdx * pdx + pdy * pdy)

                        if pdist > 0.1:
                            move_x = (pdx / pdist) * monster.speed * 0.7 * delta_time * 60  # БЫСТРЕЕ БЛУЖДАНИЕ
                            move_y = (pdy / pdist) * monster.speed * 0.7 * delta_time * 60

                            if not self.check_collision(monster.x + move_x, monster.y):
                                monster.x += move_x
                            if not self.check_collision(monster.x, monster.y + move_y):
                                monster.y += move_y
                        else:
                            # Достигли цели - переходим в режим ожидания
                            monster.is_idle = True
                            monster.idle_timer = 0
                    else:
                        # Если нет цели, выбираем новую
                        self._set_monster_wander_target(monster)

                # Случайные быстрые перемещения
                if monster.move_timer > monster.move_delay:
                    monster.move_timer = 0
                    monster.move_delay = random.uniform(2.0, 6.0)  # БОЛЬШЕ ЧАСТОТА

                    # 30% шанс на быстрое перемещение
                    if random.random() < 0.3:
                        angle = random.random() * math.pi * 2
                        move_dist = random.uniform(1.0, 3.0)  # БОЛЬШЕ ДИСТАНЦИЯ
                        new_x = monster.x + math.cos(angle) * move_dist
                        new_y = monster.y + math.sin(angle) * move_dist

                        # Проверяем, можно ли переместиться
                        if not self.check_collision(new_x, new_y):
                            monster.x = new_x
                            monster.y = new_y
                            # После быстрого перемещения - ожидание
                            monster.is_idle = True
                            monster.idle_timer = 0

    def _set_monster_wander_target(self, monster: Monster):
        """Установить цель для блуждания монстра"""
        # Ищем случайную точку в пределах радиуса блуждания
        for _ in range(10):  # 10 попыток найти валидную позицию
            angle = random.random() * math.pi * 2
            distance = random.uniform(3.0, monster.wander_range)
            target_x = monster.spawn_x + math.cos(angle) * distance
            target_y = monster.spawn_y + math.sin(angle) * distance

            # Проверяем, что позиция доступна
            if not self.check_collision(target_x, target_y):
                # Проверяем путь к цели
                if self._check_line_of_sight(monster.x, monster.y, target_x, target_y, steps=10):
                    monster.next_wander_target = (target_x, target_y)
                    return

        # Если не нашли хорошую цель, выбираем случайную из патрульного пути
        if monster.patrol_path:
            monster.patrol_index = (monster.patrol_index + 1) % len(monster.patrol_path)
            monster.next_wander_target = monster.patrol_path[monster.patrol_index]

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

        self.play_jumpscare_3d()  # ГРОМКИЙ скример при атаке

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
            self.sound_manager.play_sound('whisper', volume=0.2 * self.fear_amplifiers['sounds'])  # Тихо

            self.visual_distortion = 0.3
            self.player_sanity = max(0, self.player_sanity - 5)


    def _check_objectives(self):
        """Проверить цели"""
        for obj in self.objectives:
            if obj.collected:
                continue

            dx = obj.x - self.player_x
            dy = obj.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 1.2:
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

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        # Тряска
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            shake_x = random.uniform(-self.screen_shake, self.screen_shake) * 25
            shake_y = random.uniform(-self.screen_shake, self.screen_shake) * 25

        # Дополнительная тряска от землетрясения
        if self.earthquake_active:
            shake_x += math.sin(self.game_time * 20) * self.earthquake_intensity * 15
            shake_y += math.cos(self.game_time * 18) * self.earthquake_intensity * 15

        # Искажение
        distortion_x = 0
        distortion_y = 0
        if self.visual_distortion > 0:
            distortion_x = math.sin(self.game_time * 20) * self.visual_distortion * 5
            distortion_y = math.cos(self.game_time * 18) * self.visual_distortion * 5

        total_offset_x = shake_x + distortion_x + self.camera_shake * random.uniform(-10, 10)
        total_offset_y = shake_y + distortion_y + self.camera_shake * random.uniform(-10, 10)

        # 3D вид с учетом всех эффектов
        self._draw_3d_view(total_offset_x, total_offset_y)

        # Эффекты
        self._draw_effects(total_offset_x, total_offset_y)

        # Новые жуткие визуальные эффекты
        self._draw_hallucinations(total_offset_x, total_offset_y)
        self._draw_blood_veins(total_offset_x, total_offset_y)
        self._draw_whisper_effects(total_offset_x, total_offset_y)

        # Интерфейс
        self._draw_hud()

        # Миникарта
        if self.show_minimap:
            self._draw_minimap()

        # Обучение
        if self.show_tutorial and self.tutorial_time > 0:
            self._draw_tutorial()

        # Подсказка про клавишу I
        if self.show_i_hint and not self.show_tutorial:
            self._draw_i_hint()

        # Инструкция
        if self.show_instructions:
            self._draw_instructions()

        # Эффект паранойи
        if self.paranoia_effect > 0 and random.random() < self.paranoia_effect * 0.1:
            self._draw_paranoia_effect()

        # Предупреждение о времени
        if self.show_time_warning:
            self._draw_time_warning()

    def _draw_3d_view(self, offset_x=0, offset_y=0):
        """Нарисовать 3D вид с новыми эффектами"""
        # Общая темнота
        total_darkness = 1.0 + self.fear_induced_darkness + self.near_monster_effect * 0.5

        if self.flashlight_on and self.flashlight_battery > 20:
            base_color = (20, 15, 30)
        else:
            base_color = (5, 2, 10)

        bg_color = (
            int(base_color[0] / total_darkness),
            int(base_color[1] / total_darkness),
            int(base_color[2] / total_darkness)
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
        """Отрисовка стен с эффектами"""
        num_rays = 120
        ray_step = self.player_fov / num_rays
        column_width = self.window.width / num_rays

        # Эффект мерцания для всех стен
        flicker_multiplier = 1.0
        if self.light_flicker_active:
            flicker = (math.sin(self.game_time * 40) + 1) / 2
            flicker = flicker * self.light_flicker_intensity + (1 - self.light_flicker_intensity)
            flicker_multiplier = flicker

        for i in range(num_rays):
            ray_angle = (self.player_angle - self.player_fov / 2) + i * ray_step
            distance, wall_type = self._cast_ray(ray_angle)

            if distance > 0:
                darkness = 1.0 + self.fear_induced_darkness + self.near_monster_effect * 0.3
                if not self.flashlight_on or self.flashlight_battery < 20:
                    darkness *= 1.5

                wall_height = min(600, self.window.height / max(distance * darkness, 0.1))

                x = i * column_width + offset_x
                y_bottom = (self.window.height - wall_height) / 2 + offset_y
                y_top = y_bottom + wall_height

                darken = min(1.0, 8.0 / (distance * darkness)) * flicker_multiplier

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

            # Эффект мерцания
            if self.light_flicker_active:
                darken *= (math.sin(self.game_time * 30) + 1) / 2

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
        """Отрисовка монстров с эффектами"""
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

                # Эффект мерцания при приближении
                if distance < 5 and self.near_monster_effect > 0.5:
                    flicker = (math.sin(self.game_time * 40) + 1) / 2
                    darken *= (0.5 + flicker * 0.5)

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
        """Эффект фонарика с мерцанием"""
        if self.flashlight_battery <= 0:
            return

        center_x = self.window.width // 2 + offset_x
        center_y = self.window.height // 2 + offset_y

        # Базовая интенсивность
        intensity = min(1.0, self.flashlight_battery / 200.0) * self.flashlight_flicker

        # Эффект мерцания
        if self.light_flicker_active:
            flicker = (math.sin(self.game_time * 30) + 1) / 2
            intensity *= (0.5 + flicker * 0.5)

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

        # Усиленная виньетка при темноте
        vignette_strength = self.vignette + self.fear_induced_darkness * 0.5 + self.near_monster_effect * 0.2
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

    def _draw_hallucinations(self, offset_x=0, offset_y=0):
        """Отрисовка галлюцинаций"""
        if self.hallucination_active:
            for figure in self.shadow_figures:
                if figure['life'] > 0:
                    alpha = int((figure['life'] / figure['max_life']) * 100)
                    if alpha > 0:
                        arcade.draw_circle_filled(
                            figure['x'] + offset_x,
                            figure['y'] + offset_y,
                            figure['size'],
                            (0, 0, 0, alpha)
                        )

    def _draw_blood_veins(self, offset_x=0, offset_y=0):
        """Отрисовка кровавых прожилок"""
        if self.player_stress > 70:
            for vein in self.blood_veins:
                if vein['alpha'] > 0:
                    arcade.draw_line(
                        vein['x1'] + offset_x, vein['y1'] + offset_y,
                        vein['x2'] + offset_x, vein['y2'] + offset_y,
                        (150, 20, 20, vein['alpha']),
                        vein['thickness']
                    )

    def _draw_whisper_effects(self, offset_x=0, offset_y=0):
        """Отрисовка эффектов шепотов"""
        for effect in self.whisper_effects:
            if effect['alpha'] > 0:
                arcade.draw_text(
                    effect['text'],
                    effect['x'] + offset_x, effect['y'] + offset_y,
                    (255, 255, 255, effect['alpha']), 16,
                    anchor_x="center", anchor_y="center"
                )

    def _draw_i_hint(self):
        """Подсказка про клавишу I"""
        alpha = min(255, int(self.i_hint_timer * 50))  # Плавное исчезновение

        arcade.draw_lrbt_rectangle_filled(
            self.window.width // 2 - 200, self.window.width // 2 + 200,
            self.window.height - 80, self.window.height - 40,
            (0, 0, 0, alpha // 2)
        )

        arcade.draw_text(
            "Нажмите I для инструкции по управлению",
            self.window.width // 2, self.window.height - 60,
            (255, 255, 200, alpha), 18,
            anchor_x="center", anchor_y="center",
            bold=True
        )

    def _draw_time_warning(self):
        """Предупреждение о времени"""
        if int(time.time() * 2) % 2 == 0:  # Мигающий эффект
            remaining_time = self.max_game_time - self.game_time
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)

            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 250, self.window.width // 2 + 250,
                self.window.height - 180, self.window.height - 120,
                (0, 0, 0, 180)
            )

            arcade.draw_text(
                f"ВНИМАНИЕ! ОСТАЛОСЬ {minutes:02d}:{seconds:02d}",
                self.window.width // 2, self.window.height - 150,
                (255, 100, 100), 28,
                anchor_x="center", anchor_y="center",
                bold=True
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
        """Интерфейс"""
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

        # Время с индикацией прогресса
        time_text = f"ВРЕМЯ: {int(self.game_time)}с"
        remaining_time = self.max_game_time - self.game_time
        time_percent = remaining_time / self.max_game_time

        # Цвет времени в зависимости от оставшегося времени
        if time_percent > 0.5:
            time_color = arcade.color.LIGHT_GRAY
        elif time_percent > 0.25:
            time_color = (255, 200, 100)
        else:
            time_color = (255, 100, 100)
            if int(time.time()) % 2 == 0:  # Мигание при малом времени
                time_color = (255, 150, 150)

        arcade.draw_text(time_text, progress_x, 50, time_color, 18)

        # Прогресс-бар времени
        time_bar_width = 250 * time_percent
        time_bar_color = time_color
        arcade.draw_lrbt_rectangle_filled(progress_x - 130, progress_x - 130 + time_bar_width, 15, 25, time_bar_color)
        arcade.draw_lrbt_rectangle_outline(progress_x - 130, progress_x - 130 + 250, 15, 25, (255, 255, 255, 150), 2)

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

        # Индикатор темноты
        if self.darkness_stage > 0:
            darkness_texts = ["СРЕДНЯЯ ТЕМНОТА", "СИЛЬНАЯ ТЕМНОТА"]
            darkness_colors = [(255, 200, 100), (255, 150, 50)]

            blink = int(time.time() * 2) % 2 == 0
            if blink:
                arcade.draw_text(
                    darkness_texts[self.darkness_stage - 1],
                    self.window.width // 2, 90,
                    darkness_colors[self.darkness_stage - 1], 14,
                    anchor_x="center"
                )

        # Статус карты
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
        """Миникарта"""
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
            f"ВРЕМЯ: {int(self.max_game_time / 60)} минут",
            f"ЛАБИРИНТ: {self.map_width}x{self.map_height}",
            "",
            "ГЛАВНОЕ: Нажмите I для инструкции!",
            "",
            "УПРАВЛЕНИЕ:",
            "WASD - движение",
            "Мышь - поворот камеры",
            "F - фонарик",
            "M - карта",
            "ПРОБЕЛ - крик",
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
            elif i == 3:  # Время
                size = 24
                color = (100, 255, 100)
            elif i == 4:  # Размер лабиринта
                size = 20
                color = (150, 200, 255)
            elif i == 6:  # Важная подсказка про I
                size = 24
                color = (255, 255, 100)
                if int(time.time() * 2) % 2 == 0:
                    color = (255, 255, 150)
            elif i == 8:
                size = 24
                color = (100, 200, 255)
            elif i == 15:
                size = 20
                color = (255, 255, 255)
            else:
                size = 18
                color = (200, 200, 200)

            arcade.draw_text(
                text, self.window.width // 2, center_y - y_offset,
                (*color, alpha), size,
                anchor_x="center", anchor_y="center",
                bold=(i in [0, 1, 3, 6, 15])
            )

    def _draw_instructions(self):
        """Инструкция"""
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width, 0, self.window.height,
            (0, 0, 0, 220)
        )

        arcade.draw_text(
            "ИНСТРУКЦИЯ - 3D ХОРРОР ЛАБИРИНТ",
            self.window.width // 2, self.window.height - 80,
            (255, 50, 50), 32,
            anchor_x="center", anchor_y="center",
            bold=True
        )

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
            ("НОВЫЕ ОПАСНОСТИ", [
                f"• Время: {int(self.max_game_time / 60)} минут на прохождение",
                f"• Лабиринт: {self.map_width}x{self.map_height} клеток",
                "• Монстры активно перемещаются",
                "• Темнота усиливается со временем",
                "• Свет может начать мерцать"
            ]),
            ("ПОДСКАЗКИ", [
                "• Ищите 3 золотых ключа",
                "• Найдите красный выход",
                "• Избегайте красных монстров",
                "• В темноте начинаются галлюцинации",
                "• Следите за здоровьем и рассудком"
            ])
        ]

        start_y = self.window.height - 150
        section_spacing = 50

        for section_index, (section_title, items) in enumerate(sections):
            y = start_y - section_index * section_spacing

            arcade.draw_text(
                section_title,
                self.window.width // 2, y,
                (255, 215, 0), 24,
                anchor_x="center", anchor_y="center",
                bold=True
            )

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

        arcade.draw_text(
            "Нажмите I или ESCAPE чтобы закрыть",
            self.window.width // 2, 60,
            (150, 255, 150), 20,
            anchor_x="center", anchor_y="center",
            bold=True
        )


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
            # Сбрасываем таймер подсказки про I
            self.show_i_hint = True
            self.i_hint_timer = 5.0
            return

        current_time = time.time()
        self.behavior_data.key_presses.append((current_time, key_name))

        if symbol == arcade.key.I:
            self.show_instructions = not self.show_instructions
            # Скрываем подсказку при нажатии I
            self.show_i_hint = False
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

    # КОНЕЦ ИГРЫ

    def _win_game(self):
        """Победа"""
        self.game_won = True
        self.game_active = False
        self.victory = True
        self.game_over = True

        # Останавливаем музыку
        self.stop_background_music()

        if self.sound_manager:
            self.sound_manager.play_sound('music', volume=0.4)

        self.end_game()

    def _end_game(self, reason: str):
        """Поражение"""
        self.game_active = False
        self.game_over = True

        # Останавливаем музыку
        self.stop_background_music()

        game_stats = {
            'time': self.game_time,
            'keys_collected': self.keys_collected,
            'total_keys': self.keys_needed,
            'stress_level': self.player_stress,
            'sanity_level': self.player_sanity,
            'jump_scares': self.jump_scares_triggered,
            'monsters_killed': self.monsters_killed,
            'time_out': self.time_out
        }

        try:
            from game_over import GameOverView
            game_over_view = GameOverView(reason, game_stats)
            self.window.show_view(game_over_view)
        except ImportError:
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

        for _ in range(self.keys_needed):
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

        for i in range(min(3, len(dead_ends))):  # 3 монстра
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
                patrol_path=patrol_path,
                spawn_x=x + 0.5,
                spawn_y=y + 0.5,
                move_delay=random.uniform(2.0, 5.0),  # БОЛЬШЕ ЧАСТОТА
                wander_range=random.uniform(10.0, 15.0)  # БОЛЬШЕ РАДИУС
            )
            self.monsters.append(monster)
