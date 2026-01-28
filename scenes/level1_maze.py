import arcade
import random
import math
import time
import os
import csv
from datetime import datetime
from data_models import CalibrationData


try:
    import pymunk

    PHYSICS_AVAILABLE = True
except ImportError:
    PHYSICS_AVAILABLE = False
    print("Pymunk не установлен. Физика будет отключена.")


class ParticleSystem:
    """Система частиц для эффектов"""

    def __init__(self):
        self.particles = []

    def create_explosion(self, x, y, color=(255, 100, 100), count=20):
        """Взрыв частиц"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 5)
            life = random.uniform(0.5, 1.5)
            size = random.uniform(2, 6)

            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': life,
                'max_life': life,
                'color': color,
                'size': size,
                'gravity': 0.2
            })

    def create_sparkle(self, x, y, color=(255, 215, 0), count=10):
        """Мерцающие частицы"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2)
            life = random.uniform(0.3, 0.8)
            size = random.uniform(1, 3)

            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': life,
                'max_life': life,
                'color': color,
                'size': size,
                'gravity': 0
            })

    def update(self, delta_time):
        """Обновить частицы"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] -= particle.get('gravity', 0)
            particle['life'] -= delta_time

            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, camera_x=0, camera_y=0, shake_x=0, shake_y=0):
        """Отрисовать частицы с учетом камеры"""
        for particle in self.particles:
            # Учитываем сдвиг камеры и тряску
            x = particle['x'] - camera_x + shake_x
            y = particle['y'] - camera_y + shake_y

            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*particle['color'], alpha)
            arcade.draw_circle_filled(
                x, y,
                particle['size'], color
            )


class AnimatedSprite:
    def __init__(self, center_x, center_y):
        self.center_x = center_x
        self.center_y = center_y
        self.animation_time = 0
        self.size = 16

    def update_animation(self, delta_time):
        """Обновить анимацию"""
        self.animation_time += delta_time

    def draw(self):
        """Отрисовать с анимацией"""
        # Пульсация размера
        pulse = (math.sin(self.animation_time * 5) + 1) / 2 * 0.3 + 0.7
        current_size = self.size * pulse

        # Изменение цвета
        color_pulse = (math.sin(self.animation_time * 3) + 1) / 2
        red = int(200 + 55 * color_pulse)
        green = int(50 + 50 * color_pulse)

        arcade.draw_circle_filled(
            self.center_x, self.center_y,
            current_size,
            (red, green, 100, 180)
        )

        # Мерцающий контур
        if int(self.animation_time * 5) % 2 == 0:
            arcade.draw_circle_outline(
                self.center_x, self.center_y,
                current_size,
                (255, 255, 255, 200),
                2
            )


class PhysicsObject:
    """Физический объект для взаимодействия"""

    def __init__(self, x, y, radius=0.3):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = 0
        self.vy = 0
        self.active = True

    def update(self, delta_time, walls):
        """Обновить физику"""
        if not self.active:
            return

        # Гравитация
        self.vy -= 0.5 * delta_time * 60

        # Движение
        new_x = self.x + self.vx * delta_time * 60
        new_y = self.y + self.vy * delta_time * 60

        # Проверка коллизий со стенами
        collision = False
        for wall in walls:
            wx = wall.center_x
            wy = wall.center_y
            w_size = wall.width / 2

            dx = abs(new_x * 50 - wx)
            dy = abs(new_y * 50 - wy)

            if dx < w_size + self.radius * 50 and dy < w_size + self.radius * 50:
                collision = True

                # Отскок
                if dx > dy:
                    self.vx *= -0.5
                else:
                    self.vy *= -0.5

                if dx < dy:
                    new_x = self.x
                else:
                    new_y = self.y

                self.vx *= 0.9
                self.vy *= 0.9

        if not collision:
            self.x = new_x
            self.y = new_y

        self.vx *= 0.99
        self.vy *= 0.99

        # Если объект остановился, деактивируем
        if abs(self.vx) < 0.01 and abs(self.vy) < 0.01:
            self.active = False

    def draw(self, camera_x=0, camera_y=0, shake_x=0, shake_y=0):
        """Отрисовать физический объект с учетом камеры"""
        if self.active:
            x = self.x * 50 - camera_x + shake_x
            y = self.y * 50 - camera_y + shake_y
            arcade.draw_circle_filled(
                x, y,
                self.radius * 50,
                (100, 200, 255, 180)
            )
            arcade.draw_circle_outline(
                x, y,
                self.radius * 50,
                (255, 255, 255, 220),
                2
            )


class GameDataSaver:
    """Сохранение игровых данных"""

    def __init__(self):
        self.filename = "game_stats.csv"
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Создать файл если его нет"""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp', 'level', 'play_time', 'scares_triggered',
                    'total_scares', 'stress', 'sanity', 'completed'
                ])

    def save_game_result(self, level, play_time, scares_triggered,
                         total_scares, stress, sanity, completed):
        """Сохранить результат игры"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp, level, round(play_time, 2), scares_triggered,
                total_scares, round(stress, 2), round(sanity, 2), completed
            ])


    def get_best_score(self, level=1):
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                best_time = float('inf')
                best_scares = 0

                for row in reader:
                    if int(row['level']) == level and row['completed'] == 'True':
                        time_val = float(row['play_time'])
                        scares = int(row['scares_triggered'])

                        if time_val < best_time:
                            best_time = time_val
                        if scares > best_scares:
                            best_scares = scares

                return best_time if best_time != float('inf') else None, best_scares
        except:
            return None, 0


class Level1InstructionView(arcade.View):
    """Экран с инструкцией перед Level 1"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data
        self.start_time = time.time()
        self.fade_alpha = 0
        self.show_controls = False
        self.show_warning = False

    def on_show_view(self):
        """При показе вида"""
        arcade.set_background_color((0, 0, 0))

    def on_update(self, delta_time: float):
        """Обновление анимации"""
        elapsed = time.time() - self.start_time

        # Анимация появления
        if elapsed < 1.0:
            self.fade_alpha = min(255, int(elapsed * 255))
        elif elapsed < 3.0:
            self.show_controls = True
        elif elapsed < 6.0:
            self.show_warning = True
        elif elapsed > 8.0:
            # Переход к уровню
            from scenes.level1_maze import Level1MazeView
            level_view = Level1MazeView(self.calibration_data)
            self.window.show_view(level_view)

    def on_draw(self):
        """Отрисовка инструкции"""
        self.clear()

        # Фон
        arcade.draw_lrbt_rectangle_filled(
            0, self.window.width,
            0, self.window.height,
            (0, 0, 0)
        )

        # Заголовок
        title_color = (255, 50, 50, self.fade_alpha)
        arcade.draw_text(
            "LEVEL 1: ТИШИНА",
            self.window.width // 2, self.window.height - 150,
            title_color, 48,
            anchor_x="center",
            bold=True
        )

        # Подзаголовок
        subtitle_color = (200, 200, 255, self.fade_alpha)
        arcade.draw_text(
            "Только скримеры...",
            self.window.width // 2, self.window.height - 220,
            subtitle_color, 24,
            anchor_x="center"
        )

        # Управление
        if self.show_controls:
            controls_alpha = min(255, int((time.time() - self.start_time - 1.0) * 255))

            # Рамка для управления
            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 200, self.window.width // 2 + 200,
                self.window.height // 2 - 150, self.window.height // 2 + 150,
                (20, 10, 30, controls_alpha // 2)
            )

            # Заголовок управления
            arcade.draw_text(
                "УПРАВЛЕНИЕ",
                self.window.width // 2, self.window.height // 2 + 100,
                (255, 200, 100, controls_alpha), 32,
                anchor_x="center",
                bold=True
            )

            # Клавиши
            key_color = (100, 200, 255, controls_alpha)
            key_bg = (50, 50, 100, controls_alpha // 2)

            # W
            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 40, self.window.width // 2 + 40,
                self.window.height // 2 + 20, self.window.height // 2 + 60,
                key_bg
            )
            arcade.draw_text(
                "W",
                self.window.width // 2, self.window.height // 2 + 40,
                key_color, 28,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            arcade.draw_text(
                "ВПЕРЕД",
                self.window.width // 2 + 80, self.window.height // 2 + 40,
                (200, 200, 200, controls_alpha), 20,
                anchor_y="center"
            )

            # A и D
            arcade.draw_text(
                "A",
                self.window.width // 2 - 100, self.window.height // 2 - 20,
                key_color, 28,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            arcade.draw_text(
                "D",
                self.window.width // 2 + 100, self.window.height // 2 - 20,
                key_color, 28,
                anchor_x="center", anchor_y="center",
                bold=True
            )

            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 140, self.window.width // 2 - 60,
                self.window.height // 2 - 40, self.window.height // 2,
                key_bg
            )
            arcade.draw_text(
                "← ВЛЕВО",
                self.window.width // 2 - 140, self.window.height // 2 - 20,
                (200, 200, 200, controls_alpha), 18,
                anchor_x="left", anchor_y="center"
            )

            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 + 60, self.window.width // 2 + 140,
                self.window.height // 2 - 40, self.window.height // 2,
                key_bg
            )
            arcade.draw_text(
                "ВПРАВО →",
                self.window.width // 2 + 140, self.window.height // 2 - 20,
                (200, 200, 200, controls_alpha), 18,
                anchor_x="right", anchor_y="center"
            )

            # S
            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 40, self.window.width // 2 + 40,
                self.window.height // 2 - 100, self.window.height // 2 - 60,
                key_bg
            )
            arcade.draw_text(
                "S",
                self.window.width // 2, self.window.height // 2 - 80,
                key_color, 28,
                anchor_x="center", anchor_y="center",
                bold=True
            )
            arcade.draw_text(
                "НАЗАД",
                self.window.width // 2 + 80, self.window.height // 2 - 80,
                (200, 200, 200, controls_alpha), 20,
                anchor_y="center"
            )

            # Подсказка
            hint_alpha = int((math.sin(time.time() * 3) + 1) / 2 * controls_alpha)
            arcade.draw_text(
                "ESC - выход в меню",
                self.window.width // 2, self.window.height // 2 - 150,
                (150, 150, 150, hint_alpha), 16,
                anchor_x="center"
            )

        # Предупреждение о скримерах
        if self.show_warning:
            warning_time = time.time() - self.start_time - 3.0
            warning_alpha = min(255, int(warning_time * 255))

            # Мигающий текст
            blink = int((math.sin(time.time() * 5) + 1) / 2 * warning_alpha)

            arcade.draw_text(
                "ВНИМАНИЕ:",
                self.window.width // 2, 300,
                (255, 50, 50, warning_alpha), 36,
                anchor_x="center",
                bold=True
            )

            arcade.draw_text(
                "В лабиринте 10 скримеров",
                self.window.width // 2, 250,
                (255, 150, 150, warning_alpha), 24,
                anchor_x="center"
            )

            arcade.draw_text(
                "4 из них скрыты и появляются при приближении",
                self.window.width // 2, 220,
                (255, 200, 200, warning_alpha), 20,
                anchor_x="center"
            )

            arcade.draw_text(
                "Будьте готовы...",
                self.window.width // 2, 150,
                (255, 100, 100, blink), 28,
                anchor_x="center",
                bold=True
            )

        # Таймер до начала
        if self.show_warning:
            time_left = max(0, 8.0 - (time.time() - self.start_time))
            arcade.draw_text(
                f"Начало через: {time_left:.1f}",
                self.window.width // 2, 50,
                (200, 200, 255, warning_alpha), 20,
                anchor_x="center"
            )

    def on_key_press(self, symbol: int, modifiers: int):
        """Пропустить инструкцию по нажатию любой клавиши"""
        if symbol == arcade.key.ESCAPE:
            from scenes.main_menu import MainMenuView
            menu_view = MainMenuView()
            self.window.show_view(menu_view)
        else:
            # Любая другая клавиша пропускает инструкцию
            from scenes.level1_maze import Level1MazeView
            level_view = Level1MazeView(self.calibration_data)
            self.window.show_view(level_view)


class Level1MazeView(arcade.View):
    """Level 1"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data

        self.tile_size = 50
        self.map_width = 15
        self.map_height = 15
        self.exit_x = self.map_width - 2
        self.exit_y = self.map_height - 2

        # Игрок
        self.player_sprite = None
        self.player_x = 1.5
        self.player_y = 1.5
        self.player_radius = 0.4
        self.player_speed = 5.0

        # Камера
        self.camera_x = 0
        self.camera_y = 0

        # Спрайты
        self.wall_list = None
        self.exit_list = None
        self.scare_list = None

        #Анимированные спрайты
        self.animated_scares = []

        #Система частиц
        self.particle_system = ParticleSystem()

        #Физические объекты
        self.physics_objects = []

        #Сохранение данных
        self.data_saver = GameDataSaver()
        self.best_time, self.best_scares = self.data_saver.get_best_score(level=1)

        #ЛАБИРИНТ
        self.maze = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
            [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
            [1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
            [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]

        # Выход
        self.maze[self.exit_y][self.exit_x] = 2

        #СКРИМЕРЫ
        self.jumpscares = []
        self.scare_types = [
            'face1', 'face2', 'face3', 'face4', 'face5',
            'face6', 'face7', 'face8', 'face9', 'face10'
        ]

        self.free_cells = self.find_free_cells()
        self.create_jumpscares()

        self.active_scare = None
        self.scare_timer = 0

        #ЭФФЕКТЫ
        self.screen_shake = 0
        self.flash = 0
        self.stress = 30
        self.sanity = 100
        self.scares_triggered = 0
        self.vignette_darkness = 0
        self.blood_overlay = 0

        #Физический щит
        self.has_shield = False
        self.shield_timer = 0
        self.shield_active = False

        #Звуки
        self.sound_manager = None
        self.init_sound_manager()

        #УПРАВЛЕНИЕ
        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False,
            arcade.key.SPACE: False  # Использование щита
        }

        # Время
        self.start_time = time.time()
        self.show_hint_time = time.time() + 2.0

        # Настройка
        self.setup()

        # Создаем физические объекты на карте
        self.create_physics_objects()

    def find_free_cells(self):
        """Найти все свободные клетки в лабиринте"""
        free_cells = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.maze[y][x] == 0:  # Свободная клетка
                    free_cells.append((x, y))
        return free_cells

    def create_jumpscares(self):
        """Создание 10 скримеров на свободных клетках"""
        selected_cells = random.sample(self.free_cells, min(10, len(self.free_cells)))

        # Создаем скримеры
        for i, (x, y) in enumerate(selected_cells):
            # Определяем тип скримера
            scare_type = self.scare_types[i % len(self.scare_types)]

            # Определяем, скрытый ли это скример
            is_hidden = i < 4

            # Определяем диапазон активации для скрытых скримеров
            activation_range = random.uniform(1.2, 2.0) if is_hidden else None

            # Создаем скример
            scare = {
                'x': x + 0.5,
                'y': y + 0.5,
                'triggered': False,
                'visible': not is_hidden,
                'hidden': is_hidden,
                'type': scare_type,
                'activation_range': activation_range if is_hidden else None,
                'sprite': None,
                'animation_time': random.random() * 2
            }

            self.jumpscares.append(scare)

    def init_sound_manager(self):
        """Инициализируем менеджер звуков для скримеров"""
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager(sound_mode="level1")
            self.sound_manager.set_volume(1.0)
        except Exception:
            self.sound_manager = None

    def create_physics_objects(self):
        """Создать физические объекты на карте"""
        available_cells = [cell for cell in self.free_cells
                           if (cell[0] + 0.5, cell[1] + 0.5) not in
                           [(s['x'], s['y']) for s in self.jumpscares]]

        if len(available_cells) < 3:
            return

        physics_cells = random.sample(available_cells, min(3, len(available_cells)))

        for x, y in physics_cells:
            phys_obj = PhysicsObject(x + 0.5, y + 0.5, radius=0.2)
            self.physics_objects.append(phys_obj)

            # Добавляем частицы вокруг объекта
            self.particle_system.create_sparkle(
                (x + 0.5) * self.tile_size,
                (y + 0.5) * self.tile_size,
                color=(100, 200, 255),
                count=8
            )

    def setup(self):
        """Настройка спрайтов"""
        self.wall_list = arcade.SpriteList()
        self.exit_list = arcade.SpriteList()
        self.scare_list = arcade.SpriteList()

        # Стены
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.maze[y][x] == 1:
                    wall = arcade.SpriteSolidColor(
                        self.tile_size, self.tile_size, (80, 60, 70)
                    )
                    wall.center_x = x * self.tile_size + self.tile_size // 2
                    wall.center_y = y * self.tile_size + self.tile_size // 2
                    self.wall_list.append(wall)
                elif self.maze[y][x] == 2:
                    exit_sprite = arcade.SpriteSolidColor(
                        self.tile_size - 20, self.tile_size - 20, (150, 50, 50)
                    )
                    exit_sprite.center_x = x * self.tile_size + self.tile_size // 2
                    exit_sprite.center_y = y * self.tile_size + self.tile_size // 2
                    self.exit_list.append(exit_sprite)

        # Скримеры
        for scare in self.jumpscares:
            # Определяем цвет в зависимости от типа
            if scare['type'] == 'face1':
                color = (255, 50, 50)  # Красный
            elif scare['type'] == 'face2':
                color = (255, 100, 0)  # Оранжевый
            elif scare['type'] == 'face3':
                color = (200, 0, 100)  # Пурпурный
            elif scare['type'] == 'face4':
                color = (100, 100, 255)  # Синий
            elif scare['type'] == 'face5':
                color = (150, 0, 0)  # Темно-красный
            elif scare['type'] == 'face6':
                color = (50, 50, 50)  # Темный
            elif scare['type'] == 'face7':
                color = (200, 200, 255)  # Светло-синий
            elif scare['type'] == 'face8':
                color = (100, 100, 100)  # Серый
            elif scare['type'] == 'face9':
                color = (255, 200, 0)  # Желтый
            else:  # face10
                color = (100, 255, 100)  # Зеленый

            # Определяем прозрачность
            if scare.get('hidden', False):
                color_with_alpha = (color[0], color[1], color[2], 0)  # Полностью прозрачный
            else:
                color_with_alpha = (color[0], color[1], color[2], 150)  # Полу-прозрачный

            scare_sprite = arcade.SpriteSolidColor(20, 20, color_with_alpha)
            scare_sprite.center_x = scare['x'] * self.tile_size
            scare_sprite.center_y = scare['y'] * self.tile_size
            scare['sprite'] = scare_sprite
            self.scare_list.append(scare_sprite)

        # Игрок
        player_size = int(self.player_radius * self.tile_size * 2)
        self.player_sprite = arcade.SpriteSolidColor(
            player_size, player_size, (100, 150, 255)
        )
        self.player_sprite.center_x = self.player_x * self.tile_size
        self.player_sprite.center_y = self.player_y * self.tile_size

    def check_collisions(self, dx, dy):
        """Проверка коллизий"""
        old_x = self.player_sprite.center_x
        old_y = self.player_sprite.center_y

        self.player_sprite.center_x += dx
        collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)

        if collisions:
            self.player_sprite.center_x = old_x
            self.player_sprite.center_y += dy
            collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            if collisions:
                self.player_sprite.center_y = old_y
        else:
            old_x = self.player_sprite.center_x
            self.player_sprite.center_y += dy
            collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            if collisions:
                self.player_sprite.center_y = old_y

        self.player_x = self.player_sprite.center_x / self.tile_size
        self.player_y = self.player_sprite.center_y / self.tile_size

    def on_update(self, delta_time: float):
        """Обновление игры"""
        move_x = 0
        move_y = 0
        speed = self.player_speed * delta_time * 0.5 * self.tile_size

        if self.keys_pressed[arcade.key.W]:
            move_y += speed
        if self.keys_pressed[arcade.key.S]:
            move_y -= speed
        if self.keys_pressed[arcade.key.A]:
            move_x -= speed
        if self.keys_pressed[arcade.key.D]:
            move_x += speed

        if move_x != 0 or move_y != 0:
            self.check_collisions(move_x, move_y)

            # Создаем частицы при движении
            if random.random() < 0.3:
                self.particle_system.create_sparkle(
                    self.player_sprite.center_x + random.randint(-10, 10),
                    self.player_sprite.center_y + random.randint(-10, 10),
                    color=(100, 150, 255),
                    count=2
                )

        # Камера
        target_x = self.player_sprite.center_x - self.window.width // 2
        target_y = self.player_sprite.center_y - self.window.height // 2

        self.camera_x += (target_x - self.camera_x) * 0.2
        self.camera_y += (target_y - self.camera_y) * 0.2

        # Обновление анимации скримеров
        for scare in self.jumpscares:
            scare['animation_time'] += delta_time

        # Обновление системы частиц
        self.particle_system.update(delta_time)

        # Обновление физических объектов
        for phys_obj in self.physics_objects[:]:
            phys_obj.update(delta_time, self.wall_list)

            dx = phys_obj.x - self.player_x
            dy = phys_obj.y - self.player_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 0.5 and phys_obj.active:
                self.collect_shield(phys_obj)

        if self.shield_active:
            self.shield_timer -= delta_time
            if self.shield_timer <= 0:
                self.shield_active = False
                self.has_shield = False

        # Скримеры
        self.update_scares()
        self.check_scares()

        # Таймер скримера
        if self.active_scare and self.scare_timer > 0:
            self.scare_timer -= delta_time
            if self.scare_timer <= 0:
                self.active_scare = None

        # Эффекты
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - delta_time * 3)

        if self.flash > 0:
            self.flash = max(0, self.flash - delta_time * 5)

        if self.vignette_darkness > 0:
            self.vignette_darkness = max(0, self.vignette_darkness - delta_time * 0.5)

        if self.blood_overlay > 0:
            self.blood_overlay = max(0, self.blood_overlay - delta_time * 0.5)

        # Авто снижение стресса
        if self.stress > 30:
            self.stress = max(30, self.stress - delta_time * 2)

        # Восстановление рассудка
        if self.sanity < 100:
            self.sanity = min(100, self.sanity + delta_time * 0.5)

        # Выход
        exit_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.exit_list)
        if exit_collisions:
            self.win_game()

    def collect_shield(self, phys_obj):
        phys_obj.active = False
        self.physics_objects.remove(phys_obj)
        self.has_shield = True
        self.shield_timer = 10.0  # 10 секунд защиты
        self.shield_active = True

        # Эффект при сборе щита
        self.particle_system.create_explosion(
            self.player_sprite.center_x,
            self.player_sprite.center_y,
            color=(100, 200, 255),
            count=30
        )

        if self.sound_manager:
            self.sound_manager.play_sound('coin1', volume=0.7)


    def update_scares(self):
        """Активация скрытых скримеров"""
        for scare in self.jumpscares:
            if (scare.get('hidden', False) and
                    not scare['triggered'] and
                    scare.get('sprite') and
                    not scare['visible']):  # Только если еще не виден

                dx = scare['sprite'].center_x - self.player_sprite.center_x
                dy = scare['sprite'].center_y - self.player_sprite.center_y
                distance = math.sqrt(dx * dx + dy * dy) / self.tile_size

                activation_range = scare.get('activation_range', 1.5)

                if distance < activation_range:
                    scare['visible'] = True
                    scare['sprite'].alpha = 150  # Делаем видимым

                    # ффект при активации скримера
                    self.particle_system.create_explosion(
                        scare['sprite'].center_x,
                        scare['sprite'].center_y,
                        color=(255, 50, 50),
                        count=15
                    )

    def check_scares(self):
        """Проверка активации скримеров"""
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite') and scare.get('visible', True):
                if arcade.check_for_collision(self.player_sprite, scare['sprite']):
                    self.trigger_scare(scare)
                    break

    def draw_scare_face(self, x, y, scare_type, size, alpha):
        """Рисуем разные лица скримеров с анимацией"""
        # Добавляем пульсацию к размеру
        pulse = (math.sin(time.time() * 10) + 1) / 2 * 0.2 + 0.8
        size = size * pulse

        if scare_type == 'face1':  # Обычное лицо
            # Анимированный цвет лица
            color_pulse = (math.sin(time.time() * 5) + 1) / 2
            red = int(200 + 55 * color_pulse)
            arcade.draw_circle_filled(x, y, size, (red, 50, 50, alpha))

            # Анимированные глаза
            eye_size = size * 0.25
            eye_offset_x = size * 0.3
            eye_offset_y = size * 0.2

            # Мерцание глаз
            eye_alpha = alpha * (0.7 + 0.3 * math.sin(time.time() * 8))

            arcade.draw_circle_filled(
                x - eye_offset_x, y + eye_offset_y,
                eye_size, (255, 255, 255, int(eye_alpha))
            )
            arcade.draw_circle_filled(
                x + eye_offset_x, y + eye_offset_y,
                eye_size, (255, 255, 255, int(eye_alpha))
            )

            # Зрачки с движением
            pupil_move = math.sin(time.time() * 3) * 0.1
            arcade.draw_circle_filled(
                x - eye_offset_x, y + eye_offset_y + pupil_move * eye_size,
                eye_size * 0.4, (0, 0, 0, alpha)
            )
            arcade.draw_circle_filled(
                x + eye_offset_x, y + eye_offset_y + pupil_move * eye_size,
                eye_size * 0.4, (0, 0, 0, alpha)
            )

            # Анимированный рот
            mouth_open = (math.sin(time.time() * 4) + 1) / 2
            mouth_height = size * 0.15 * mouth_open
            arcade.draw_ellipse_filled(
                x, y - size * 0.3,
                   size * 0.6, mouth_height,
                (200, 0, 0, alpha)
            )

        elif scare_type == 'face2':  # Кривое лицо
            # Анимированное лицо
            face_pulse = (math.sin(time.time() * 3) + 1) / 2
            arcade.draw_circle_filled(x, y, size, (255, 100, 0, alpha))

            # Двигающиеся глаза
            eye_move_x = math.sin(time.time() * 2) * 0.1
            eye_move_y = math.cos(time.time() * 1.5) * 0.1

            arcade.draw_circle_filled(
                x - size * 0.25 + eye_move_x * size,
                y + size * 0.3 + eye_move_y * size,
                size * 0.2, (255, 255, 255, alpha)
            )
            arcade.draw_circle_filled(
                x + size * 0.35 - eye_move_x * size,
                y + size * 0.25 - eye_move_y * size,
                size * 0.2, (255, 255, 255, alpha)
            )

            # Мерцающие зрачки
            if int(time.time() * 3) % 2 == 0:
                arcade.draw_circle_filled(
                    x - size * 0.25 + eye_move_x * size,
                    y + size * 0.3 + eye_move_y * size,
                    size * 0.08, (0, 0, 0, alpha)
                )
                arcade.draw_circle_filled(
                    x + size * 0.35 - eye_move_x * size,
                    y + size * 0.25 - eye_move_y * size,
                    size * 0.08, (0, 0, 0, alpha)
                )

            # Анимированный рот
            mouth_pulse = (math.sin(time.time() * 5) + 1) / 2
            arcade.draw_arc_filled(
                x, y - size * 0.2,
                   size * 0.7, size * 0.4 * mouth_pulse,
                (200, 50, 0, alpha), 0, 180
            )

        elif scare_type == 'face3':  # Злое лицо
            # Пульсирующее лицо
            pulse = (math.sin(time.time() * 6) + 1) / 2
            red = int(150 + 50 * pulse)
            arcade.draw_circle_filled(x, y, size, (red, 0, 100, alpha))

            # Мерцающие глаза-треугольники
            eye_alpha = alpha * (0.5 + 0.5 * math.sin(time.time() * 4))
            arcade.draw_triangle_filled(
                x - size * 0.4, y + size * 0.3,
                x - size * 0.2, y + size * 0.1,
                x - size * 0.6, y + size * 0.1,
                (255, 255, 255, int(eye_alpha))
            )
            arcade.draw_triangle_filled(
                x + size * 0.4, y + size * 0.3,
                x + size * 0.2, y + size * 0.1,
                x + size * 0.6, y + size * 0.1,
                (255, 255, 255, int(eye_alpha))
            )

            # Пульсирующая линия рта
            mouth_pulse = (math.sin(time.time() * 8) + 1) / 2
            arcade.draw_line(
                x - size * 0.3, y - size * 0.25,
                x + size * 0.3, y - size * 0.25,
                (100, 0, 50, alpha),
                3 * mouth_pulse
            )

        else:  # Упрощенные остальные типы
            # Базовое лицо для остальных типов
            color_pulse = (math.sin(time.time() * 3) + 1) / 2
            base_color = (200, 100, 100, alpha)
            arcade.draw_circle_filled(x, y, size, base_color)

            # Простые глаза
            arcade.draw_circle_filled(
                x - size * 0.3, y + size * 0.2,
                size * 0.15, (255, 255, 255, alpha)
            )
            arcade.draw_circle_filled(
                x + size * 0.3, y + size * 0.2,
                size * 0.15, (255, 255, 255, alpha)
            )

            # Мигающие зрачки
            if int(time.time() * 2) % 2 == 0:
                arcade.draw_circle_filled(
                    x - size * 0.3, y + size * 0.2,
                    size * 0.07, (0, 0, 0, alpha)
                )
                arcade.draw_circle_filled(
                    x + size * 0.3, y + size * 0.2,
                    size * 0.07, (0, 0, 0, alpha)
                )

    def trigger_scare(self, scare):
        """Активировать скример"""
        if self.shield_active:

            # Эффект отражения
            self.particle_system.create_explosion(
                scare['sprite'].center_x,
                scare['sprite'].center_y,
                color=(100, 200, 255),
                count=25
            )

            # Деактивируем скример
            scare['triggered'] = True
            scare['sprite'].alpha = 50

            if self.sound_manager:
                self.sound_manager.play_sound('shield', volume=0.5)

            return

        # Стандартная активация скримера
        scare['triggered'] = True
        self.active_scare = scare
        self.scare_timer = 0.8
        self.scares_triggered += 1

        stress_increase = 30 + random.randint(0, 20)
        self.stress = min(100, self.stress + stress_increase)
        self.sanity = max(0, self.sanity - stress_increase // 2)

        self.screen_shake = 0.7 + random.random() * 0.3
        self.flash = 0.8 + random.random() * 0.2
        self.blood_overlay = 0.3 + random.random() * 0.2
        self.vignette_darkness = 0.2

        # Эффект частиц при скримере
        self.particle_system.create_explosion(
            scare['sprite'].center_x,
            scare['sprite'].center_y,
            color=(255, 50, 50),
            count=40
        )

        if self.sound_manager:
            volume = 0.8 + random.random() * 0.2
            self.sound_manager.play_sound('scream', volume=volume)

    def on_draw(self):
        """Отрисовка"""
        self.clear()
        arcade.set_background_color((20, 10, 30))

        # Тряска
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) * 20 if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) * 20 if self.screen_shake > 0 else 0

        # Стены
        for wall in self.wall_list:
            x = wall.center_x - self.camera_x + shake_x
            y = wall.center_y - self.camera_y + shake_y

            arcade.draw_lrbt_rectangle_filled(
                x - self.tile_size // 2, x + self.tile_size // 2,
                y - self.tile_size // 2, y + self.tile_size // 2,
                (80, 60, 70)
            )

        # Выход
        for exit_sprite in self.exit_list:
            pulse = (math.sin(time.time() * 5) + 1) / 2
            red = 150 + int(100 * pulse)

            x = exit_sprite.center_x - self.camera_x + shake_x
            y = exit_sprite.center_y - self.camera_y + shake_y

            arcade.draw_lrbt_rectangle_filled(
                x - (self.tile_size - 20) // 2, x + (self.tile_size - 20) // 2,
                y - (self.tile_size - 20) // 2, y + (self.tile_size - 20) // 2,
                (red, 50, 50)
            )

            arcade.draw_text(
                "ВЫХОД",
                x, y,
                arcade.color.WHITE, 14,
                anchor_x="center", anchor_y="center"
            )

        # НОВОЕ: Физические объекты
        for phys_obj in self.physics_objects:
            phys_obj.draw(self.camera_x, self.camera_y, shake_x, shake_y)

        # Скримеры
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite') and scare.get('visible', True):
                x = scare['sprite'].center_x - self.camera_x + shake_x
                y = scare['sprite'].center_y - self.camera_y + shake_y

                # Анимированные скримеры
                pulse = (math.sin(scare['animation_time'] * 3) + 1) / 2 * 0.3 + 0.7
                size = 10 * pulse

                # Цвет в зависимости от типа
                if scare['type'] == 'face1':
                    color = (255, 50, 50, 150)
                elif scare['type'] == 'face2':
                    color = (255, 100, 0, 150)
                elif scare['type'] == 'face3':
                    color = (200, 0, 100, 150)
                elif scare['type'] == 'face4':
                    color = (100, 100, 255, 150)
                elif scare['type'] == 'face5':
                    color = (150, 0, 0, 150)
                elif scare['type'] == 'face6':
                    color = (50, 50, 50, 150)
                elif scare['type'] == 'face7':
                    color = (200, 200, 255, 150)
                elif scare['type'] == 'face8':
                    color = (100, 100, 100, 150)
                elif scare['type'] == 'face9':
                    color = (255, 200, 0, 150)
                else:  # face10
                    color = (100, 255, 100, 150)

                arcade.draw_circle_filled(x, y, size, color)

                # Мерцающий контур
                if int(scare['animation_time'] * 5) % 2 == 0:
                    arcade.draw_circle_outline(
                        x, y, size,
                        (255, 255, 255, 200), 2
                    )

        # Система частиц
        self.particle_system.draw(self.camera_x, self.camera_y, shake_x, shake_y)

        # Активный скример
        if self.active_scare and self.scare_timer > 0:
            scare = self.active_scare
            x = scare['sprite'].center_x - self.camera_x + shake_x
            y = scare['sprite'].center_y - self.camera_y + shake_y

            size = 80 + (1.0 - self.scare_timer / 0.8) * 40
            alpha = int(255 * (self.scare_timer / 0.8))

            self.draw_scare_face(x, y, scare['type'], size, alpha)

        # Игрок
        player_x = self.player_sprite.center_x - self.camera_x + shake_x
        player_y = self.player_sprite.center_y - self.camera_y + shake_y
        player_size = self.player_radius * self.tile_size

        arcade.draw_circle_filled(player_x, player_y, player_size, (100, 150, 255))
        arcade.draw_circle_outline(player_x, player_y, player_size, (200, 200, 255), 2)

        # Щит игрока
        if self.shield_active:
            shield_size = player_size * 1.5
            shield_alpha = int(150 * (0.7 + 0.3 * math.sin(time.time() * 8)))

            arcade.draw_circle_outline(
                player_x, player_y,
                shield_size,
                (100, 200, 255, shield_alpha),
                3
            )

            # Частицы щита
            if random.random() < 0.3:
                angle = random.uniform(0, math.pi * 2)
                dist = shield_size + random.uniform(-5, 5)
                part_x = player_x + math.cos(angle) * dist
                part_y = player_y + math.sin(angle) * dist

                arcade.draw_circle_filled(
                    part_x, part_y,
                    3,
                    (100, 200, 255, 150)
                )

        # Вспышка
        if self.flash > 0:
            flash_color = (255, 200, 200, int(self.flash * 100))
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                0, self.window.height,
                flash_color
            )

        # Кровь
        if self.blood_overlay > 0:
            blood_alpha = int(self.blood_overlay * 100)
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                0, self.window.height,
                (150, 20, 20, blood_alpha // 3)
            )

        # Интерфейс
        self.draw_hud()

        # Подсказка об управлении (показывается первые 5 секунд)
        if time.time() - self.start_time < 5.0:
            hint_alpha = min(255, int((5.0 - (time.time() - self.start_time)) * 255))
            hint_bg_alpha = hint_alpha // 3

            # Фон подсказки
            arcade.draw_lrbt_rectangle_filled(
                self.window.width // 2 - 250, self.window.width // 2 + 250,
                self.window.height - 100, self.window.height - 20,
                (0, 0, 0, hint_bg_alpha)
            )

            # Текст подсказки
            arcade.draw_text(
                "Управление: W A S D  |  ПРОБЕЛ - щит  |  ESC - меню",
                self.window.width // 2, self.window.height - 60,
                (255, 255, 200, hint_alpha), 20,
                anchor_x="center", anchor_y="center",
                bold=True
            )


    def draw_hud(self):
        """Интерфейс"""
        arcade.draw_lrbt_rectangle_filled(
            20, 350,
            20, 120,
            (0, 0, 0, 180)
        )

        # Стресс
        stress_width = 320 * (self.stress / 100)
        if self.stress > 80:
            pulse = (math.sin(time.time() * 8) + 1) / 2
            stress_color = (255, 50 + int(50 * pulse), 50)
        elif self.stress > 60:
            stress_color = (255, 150, 50)
        else:
            stress_color = (255, 255, 100)

        arcade.draw_lrbt_rectangle_filled(
            30, 30 + stress_width,
            100, 110,
            stress_color
        )

        # Рассудок
        sanity_width = 320 * (self.sanity / 100)
        sanity_color = (100, 200, 255) if self.sanity > 50 else (255, 150, 100)

        arcade.draw_lrbt_rectangle_filled(
            30, 30 + sanity_width,
            70, 80,
            sanity_color
        )

        arcade.draw_text(
            f"СТРЕСС: {int(self.stress)}%",
            30, 80,
            arcade.color.WHITE, 20
        )

        arcade.draw_text(
            f"РАССУДОК: {int(self.sanity)}%",
            30, 50,
            arcade.color.WHITE, 20
        )

        arcade.draw_text(
            f"СКРИМЕРОВ: {self.scares_triggered}/10",
            30, 25,
            (255, 100, 100) if self.scares_triggered > 0 else (200, 200, 200), 16
        )

        # Статус щита
        if self.shield_active:
            shield_text = f"ЩИТ: {int(self.shield_timer)}с"
            shield_color = (100, 200, 255)

            # Мигание при заканчивающемся щите
            if self.shield_timer < 3:
                if int(time.time() * 2) % 2 == 0:
                    shield_color = (255, 100, 100)

            arcade.draw_text(
                shield_text,
                self.window.width - 150, 25,
                shield_color, 16
            )

        # Лучший результат
        if self.best_time:
            arcade.draw_text(
                f"ЛУЧШЕЕ ВРЕМЯ: {int(self.best_time)}с",
                self.window.width - 200, 50,
                (255, 215, 0), 14
            )

        if self.best_scares > 0:
            arcade.draw_text(
                f"ЛУЧШИЙ РЕЗУЛЬТАТ: {self.best_scares}/10",
                self.window.width - 200, 70,
                (255, 100, 100), 14
            )

        # Время
        play_time = int(time.time() - self.start_time)
        arcade.draw_text(
            f"ВРЕМЯ: {play_time}с",
            self.window.width - 150, self.window.height - 30,
            arcade.color.LIGHT_GRAY, 16
        )

        # Подсказка
        hints = [
            "ИЩИТЕ КРАСНЫЙ ВЫХОД",
            "СКРИМЕРОВ: 10 ШТУК",
            "СИНИЕ СФЕРЫ - ЩИТЫ",
            "LEVEL 1: ТОЛЬКО СКРИМЕРЫ",
            f"Найдено скримеров: {self.scares_triggered}/10"
        ]

        hint_index = (play_time // 10) % len(hints)
        hint_color = (255, 100, 100) if self.stress > 70 else (255, 200, 100) if self.stress > 50 else (200, 200, 255)

        arcade.draw_text(
            hints[hint_index],
            self.window.width // 2, self.window.height - 30,
            hint_color, 22,
            anchor_x="center",
            bold=True
        )

    def on_key_press(self, symbol: int, modifiers: int):
        """Нажатие клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = True

            # Активация щита
            if symbol == arcade.key.SPACE and self.has_shield and not self.shield_active:
                self.shield_active = True
                self.shield_timer = 10.0

                # Эффект активации
                self.particle_system.create_explosion(
                    self.player_sprite.center_x,
                    self.player_sprite.center_y,
                    color=(100, 200, 255),
                    count=40
                )

                if self.sound_manager:
                    self.sound_manager.play_sound('shield', volume=0.7)

        elif symbol == arcade.key.ESCAPE:
            self.back_to_menu()
        elif symbol == arcade.key.P:
            # Тест звука скримера
            if self.sound_manager:
                self.sound_manager.play_sound('scream', volume=0.5)
        elif symbol == arcade.key.T:
            visible_count = sum(1 for s in self.jumpscares if s.get('visible', False))
            triggered_count = sum(1 for s in self.jumpscares if s['triggered'])

    def on_key_release(self, symbol: int, modifiers: int):
        """Отпускание клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = False

    def win_game(self):
        """Победа"""
        play_time = time.time() - self.start_time

        # Сохранение результата
        self.data_saver.save_game_result(
            level=1,
            play_time=play_time,
            scares_triggered=self.scares_triggered,
            total_scares=len(self.jumpscares),
            stress=self.stress,
            sanity=self.sanity,
            completed=True
        )

        # Переход
        from scenes.level1_complete import Level1CompleteView
        complete_view = Level1CompleteView(
            total_jumpscares=len(self.jumpscares),
            triggered_jumpscares=self.scares_triggered,
            play_time=play_time,
            final_stress=self.stress,
            final_sanity=self.sanity,
            distance=math.sqrt((self.exit_x - self.player_x) ** 2 + (self.exit_y - self.player_y) ** 2)
        )
        self.window.show_view(complete_view)

    def back_to_menu(self):
        """Выход в меню"""
        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)