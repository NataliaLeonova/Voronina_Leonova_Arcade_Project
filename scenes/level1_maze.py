# level1_maze.py - ТОЛЬКО СКРИМЕРЫ С КАРТОЙ
import arcade
import random
import math
import time
import os
from data_models import CalibrationData


class Level1MazeView(arcade.View):
    """Level 1: ТОЛЬКО звуки скримеров, НИКАКИХ других звуков"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data

        # === НАСТРОЙКИ ===
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

        # === ЛАБИРИНТ ===
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

        # === СКРИМЕРЫ ===
        self.jumpscares = []
        # Разные типы лиц скримеров
        self.scare_types = [
            'face1',  # Обычное лицо
            'face2',  # Кривое лицо
            'face3',  # Злое лицо
            'face4',  # Глаза
            'face5',  # Демон
            'face6',  # Тень
            'face7',  # Призрак
            'face8',  # Без лица
            'face9',  # Смеющееся
            'face10'  # Шепчущее
        ]

        # Сначала найдем все свободные клетки
        self.free_cells = self.find_free_cells()

        # Создаем 10 скримеров
        self.create_jumpscares()

        self.active_scare = None
        self.scare_timer = 0

        # === ЭФФЕКТЫ ===
        self.screen_shake = 0
        self.flash = 0
        self.stress = 30
        self.sanity = 100
        self.scares_triggered = 0
        self.vignette_darkness = 0
        self.blood_overlay = 0

        # === ЗВУКИ - ТОЛЬКО СКРИМЕРЫ ===
        self.sound_manager = None
        self.init_sound_manager()

        # === УПРАВЛЕНИЕ ===
        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False
        }

        # Время
        self.start_time = time.time()

        # Настройка
        self.setup()

    def find_free_cells(self):
        """Найти все свободные клетки в лабиринте"""
        free_cells = []
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.maze[y][x] == 0:  # Свободная клетка
                    free_cells.append((x, y))
        return free_cells

    def create_jumpscares(self):
        """Создать 10 скримеров на свободных клетках"""
        if len(self.free_cells) < 10:
            print(f"ВНИМАНИЕ: Свободных клеток только {len(self.free_cells)}!")

        # Выбираем 10 случайных свободных клеток
        selected_cells = random.sample(self.free_cells, min(10, len(self.free_cells)))

        # Создаем скримеры
        for i, (x, y) in enumerate(selected_cells):
            # Определяем тип скримера
            scare_type = self.scare_types[i % len(self.scare_types)]

            # Определяем, скрытый ли это скример (первые 4 - скрытые)
            is_hidden = i < 4

            # Определяем диапазон активации для скрытых скримеров
            activation_range = random.uniform(1.2, 2.0) if is_hidden else None

            # Создаем скример
            scare = {
                'x': x + 0.5,  # Центр клетки
                'y': y + 0.5,
                'triggered': False,
                'visible': not is_hidden,  # Скрытые невидимы
                'hidden': is_hidden,
                'type': scare_type,
                'activation_range': activation_range if is_hidden else None,
                'sprite': None
            }

            self.jumpscares.append(scare)

        print(f"Создано {len(self.jumpscares)} скримеров:")
        for i, scare in enumerate(self.jumpscares):
            print(f"  {i + 1}: ({scare['x']:.1f},{scare['y']:.1f}), тип: {scare['type']}, "
                  f"скрытый: {scare['hidden']}")

    def init_sound_manager(self):
        """Инициализировать менеджер звуков ТОЛЬКО для скримеров"""
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager(sound_mode="level1")
            self.sound_manager.set_volume(1.0)
        except Exception as e:
            print(f"Ошибка загрузки звуков: {e}")
            self.sound_manager = None

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
        print("Создание спрайтов скримеров...")
        for scare in self.jumpscares:
            # Проверяем, что скример на свободной клетке
            x_int = int(scare['x'])
            y_int = int(scare['y'])

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
            print(f"Скример создан на ({scare['x']:.1f},{scare['y']:.1f}), "
                  f"тип: {scare['type']}, скрытый: {scare.get('hidden', False)}")

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
        # Движение (БЕЗ ЗВУКОВ ШАГОВ!)
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

        # Камера
        target_x = self.player_sprite.center_x - self.window.width // 2
        target_y = self.player_sprite.center_y - self.window.height // 2

        self.camera_x += (target_x - self.camera_x) * 0.2
        self.camera_y += (target_y - self.camera_y) * 0.2

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

    def update_scares(self):
        """Активация скрытых скримеров - ТОЛЬКО один раз"""
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
                    print(f"Скрытый скример {scare['type']} на ({scare['x']:.1f},{scare['y']:.1f}) активирован!")

    def check_scares(self):
        """Проверка активации скримеров"""
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite') and scare.get('visible', True):
                if arcade.check_for_collision(self.player_sprite, scare['sprite']):
                    self.trigger_scare(scare)
                    break

    def draw_scare_face(self, x, y, scare_type, size, alpha):
        """Рисуем разные лица скримеров"""
        if scare_type == 'face1':  # Обычное лицо
            arcade.draw_circle_filled(x, y, size, (255, 50, 50, alpha))
            arcade.draw_circle_filled(x - size * 0.3, y + size * 0.2, size * 0.25, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + size * 0.3, y + size * 0.2, size * 0.25, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x - size * 0.3, y + size * 0.2, size * 0.1, (0, 0, 0, alpha))
            arcade.draw_circle_filled(x + size * 0.3, y + size * 0.2, size * 0.1, (0, 0, 0, alpha))
            arcade.draw_ellipse_filled(x, y - size * 0.3, size * 0.6, size * 0.3, (200, 0, 0, alpha))

        elif scare_type == 'face2':  # Кривое лицо
            arcade.draw_circle_filled(x, y, size, (255, 100, 0, alpha))
            arcade.draw_circle_filled(x - size * 0.25, y + size * 0.3, size * 0.2, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + size * 0.35, y + size * 0.25, size * 0.2, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x - size * 0.25, y + size * 0.3, size * 0.08, (0, 0, 0, alpha))
            arcade.draw_circle_filled(x + size * 0.35, y + size * 0.25, size * 0.08, (0, 0, 0, alpha))
            arcade.draw_arc_filled(x, y - size * 0.2, size * 0.7, size * 0.4, (200, 50, 0, alpha), 0, 180)

        elif scare_type == 'face3':  # Злое лицо
            arcade.draw_circle_filled(x, y, size, (200, 0, 100, alpha))
            arcade.draw_triangle_filled(x - size * 0.4, y + size * 0.3, x - size * 0.2, y + size * 0.1, x - size * 0.6,
                                        y + size * 0.1, (255, 255, 255, alpha))
            arcade.draw_triangle_filled(x + size * 0.4, y + size * 0.3, x + size * 0.2, y + size * 0.1, x + size * 0.6,
                                        y + size * 0.1, (255, 255, 255, alpha))
            arcade.draw_line(x, y - size * 0.1, x, y - size * 0.4, (100, 0, 50, alpha), 3)

        elif scare_type == 'face4':  # Глаза
            arcade.draw_ellipse_filled(x, y, size * 1.5, size, (100, 100, 255, alpha))
            arcade.draw_circle_filled(x - size * 0.4, y, size * 0.35, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + size * 0.4, y, size * 0.35, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x - size * 0.4, y, size * 0.15, (0, 0, 0, alpha))
            arcade.draw_circle_filled(x + size * 0.4, y, size * 0.15, (0, 0, 0, alpha))

        elif scare_type == 'face5':  # Демон
            arcade.draw_circle_filled(x, y, size, (150, 0, 0, alpha))
            arcade.draw_triangle_filled(x, y + size * 1.2, x - size * 0.5, y + size * 0.5, x + size * 0.5,
                                        y + size * 0.5, (150, 0, 0, alpha))
            arcade.draw_circle_filled(x - size * 0.3, y + size * 0.1, size * 0.25, (255, 200, 200, alpha))
            arcade.draw_circle_filled(x + size * 0.3, y + size * 0.1, size * 0.25, (255, 200, 200, alpha))
            arcade.draw_ellipse_filled(x, y - size * 0.4, size * 0.8, size * 0.3, (100, 0, 0, alpha))

        elif scare_type == 'face6':  # Тень
            for i in range(3):
                shadow_size = size * (1 - i * 0.2)
                shadow_alpha = alpha * (0.7 - i * 0.2)
                arcade.draw_circle_filled(x + random.uniform(-5, 5), y + random.uniform(-5, 5),
                                          shadow_size, (50, 50, 50, int(shadow_alpha)))

        elif scare_type == 'face7':  # Призрак
            arcade.draw_circle_filled(x, y + size * 0.2, size * 0.8, (200, 200, 255, alpha))
            arcade.draw_ellipse_filled(x, y - size * 0.3, size, size * 0.6, (200, 200, 255, alpha))
            arcade.draw_circle_filled(x - size * 0.3, y + size * 0.3, size * 0.2, (100, 100, 150, alpha))
            arcade.draw_circle_filled(x + size * 0.3, y + size * 0.3, size * 0.2, (100, 100, 150, alpha))

        elif scare_type == 'face8':  # Без лица
            arcade.draw_circle_filled(x, y, size, (100, 100, 100, alpha))
            # ИСПРАВЛЕННАЯ СТРОКА: используем draw_lrbt_rectangle_filled
            arcade.draw_lrbt_rectangle_filled(
                x - size * 0.4, x + size * 0.4,
                y - size * 0.05, y + size * 0.05,
                (70, 70, 70, alpha)
            )

        elif scare_type == 'face9':  # Смеющееся
            arcade.draw_circle_filled(x, y, size, (255, 200, 0, alpha))
            arcade.draw_arc_filled(x, y, size * 0.6, size * 0.6, (200, 150, 0, alpha), 0, 180)
            arcade.draw_circle_filled(x - size * 0.3, y + size * 0.2, size * 0.15, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + size * 0.3, y + size * 0.2, size * 0.15, (255, 255, 255, alpha))

        else:  # face10 - Шепчущее
            arcade.draw_circle_filled(x, y, size, (100, 255, 100, alpha))
            arcade.draw_ellipse_filled(x, y, size * 0.5, size * 0.3, (50, 200, 50, alpha))
            arcade.draw_line(x - size * 0.2, y + size * 0.1, x - size * 0.4, y + size * 0.3, (50, 200, 50, alpha), 2)
            arcade.draw_line(x + size * 0.2, y + size * 0.1, x + size * 0.4, y + size * 0.3, (50, 200, 50, alpha), 2)

    def trigger_scare(self, scare):
        """Активировать скример"""
        scare['triggered'] = True
        self.active_scare = scare
        self.scare_timer = 0.8
        self.scares_triggered += 1

        # Стресс
        stress_increase = 30 + random.randint(0, 20)
        self.stress = min(100, self.stress + stress_increase)
        self.sanity = max(0, self.sanity - stress_increase // 2)

        # Эффекты
        self.screen_shake = 0.7 + random.random() * 0.3
        self.flash = 0.8 + random.random() * 0.2
        self.blood_overlay = 0.3 + random.random() * 0.2
        self.vignette_darkness = 0.2

        # ЗВУК СКРИМЕРА
        if self.sound_manager:
            volume = 0.8 + random.random() * 0.2
            self.sound_manager.play_sound('scream', volume=volume)

        print(f"Скример {scare['type']} активирован! Всего: {self.scares_triggered}/10")

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

        # Скримеры
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite') and scare.get('visible', True):
                x = scare['sprite'].center_x - self.camera_x + shake_x
                y = scare['sprite'].center_y - self.camera_y + shake_y

                # Рисуем индикатор скримера
                if random.random() < 0.2:  # Мигающий эффект
                    if scare.get('hidden', False):
                        arcade.draw_circle_filled(x, y, 8, (150, 50, 150, 100))
                    else:
                        arcade.draw_circle_filled(x, y, 8, (255, 100, 100, 100))

        # Активный скример
        if self.active_scare and self.scare_timer > 0:
            scare = self.active_scare
            x = scare['sprite'].center_x - self.camera_x + shake_x
            y = scare['sprite'].center_y - self.camera_y + shake_y

            size = 80 + (1.0 - self.scare_timer / 0.8) * 40
            alpha = int(255 * (self.scare_timer / 0.8))

            # Рисуем лицо скримера в зависимости от типа
            self.draw_scare_face(x, y, scare['type'], size, alpha)

        # Игрок
        player_x = self.player_sprite.center_x - self.camera_x + shake_x
        player_y = self.player_sprite.center_y - self.camera_y + shake_y
        player_size = self.player_radius * self.tile_size

        arcade.draw_circle_filled(player_x, player_y, player_size, (100, 150, 255))
        arcade.draw_circle_outline(player_x, player_y, player_size, (200, 200, 255), 2)

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

        # МИНИ-КАРТА
        self.draw_minimap()

    def draw_hud(self):
        """Интерфейс"""
        # Фон HUD
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
            "LEVEL 1: ТОЛЬКО СКРИМЕРЫ",
            "ТИШИНА - ХУДШИЙ ВРАГ",
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

    def draw_minimap(self):
        """Мини-карта"""
        map_size = 120
        map_x = self.window.width - map_size - 20
        map_y = self.window.height - map_size - 20

        # Фон карты
        arcade.draw_lrbt_rectangle_filled(
            map_x, map_x + map_size,
            map_y, map_y + map_size,
            (0, 0, 0, 180)
        )

        cell_size = map_size / max(self.map_width, self.map_height)

        # Клетки
        for y in range(self.map_height):
            for x in range(self.map_width):
                cell_x = map_x + x * cell_size
                cell_y = map_y + y * cell_size

                if self.maze[y][x] == 1:
                    arcade.draw_lrbt_rectangle_filled(
                        cell_x, cell_x + cell_size,
                        cell_y, cell_y + cell_size,
                        (100, 80, 90)
                    )
                elif self.maze[y][x] == 2:
                    if int(time.time() * 2) % 2 == 0:
                        arcade.draw_lrbt_rectangle_filled(
                            cell_x, cell_x + cell_size,
                            cell_y, cell_y + cell_size,
                            (255, 50, 50)
                        )

        # Игрок на карте
        player_map_x = map_x + self.player_x * cell_size
        player_map_y = map_y + self.player_y * cell_size

        arcade.draw_circle_filled(
            player_map_x, player_map_y,
            cell_size * 0.4,
            (100, 150, 255)
        )

        # Скримеры на карте
        for scare in self.jumpscares:
            if not scare['triggered']:
                scare_x = map_x + scare['x'] * cell_size
                scare_y = map_y + scare['y'] * cell_size

                if scare.get('visible', False):
                    # Определяем цвет в зависимости от типа
                    if scare['type'] == 'face1':
                        color = (255, 50, 50)
                    elif scare['type'] == 'face2':
                        color = (255, 100, 0)
                    elif scare['type'] == 'face3':
                        color = (200, 0, 100)
                    elif scare['type'] == 'face4':
                        color = (100, 100, 255)
                    elif scare['type'] == 'face5':
                        color = (150, 0, 0)
                    elif scare['type'] == 'face6':
                        color = (50, 50, 50)
                    elif scare['type'] == 'face7':
                        color = (200, 200, 255)
                    elif scare['type'] == 'face8':
                        color = (100, 100, 100)
                    elif scare['type'] == 'face9':
                        color = (255, 200, 0)
                    else:  # face10
                        color = (100, 255, 100)

                    arcade.draw_circle_filled(
                        scare_x, scare_y,
                        cell_size * 0.15,
                        color
                    )

        # Рамка
        arcade.draw_lrbt_rectangle_outline(
            map_x, map_x + map_size,
            map_y, map_y + map_size,
            (180, 180, 180), 2
        )

        arcade.draw_text(
            "КАРТА",
            map_x + map_size // 2, map_y - 20,
            arcade.color.LIGHT_GRAY, 12,
            anchor_x="center"
        )

    def on_key_press(self, symbol: int, modifiers: int):
        """Нажатие клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = True
        elif symbol == arcade.key.ESCAPE:
            self.back_to_menu()
        elif symbol == arcade.key.P:
            # Тест звука скримера
            if self.sound_manager:
                self.sound_manager.play_sound('scream', volume=0.5)
        elif symbol == arcade.key.T:
            # Тест: вывести информацию о скримерах
            print(f"=== ИНФОРМАЦИЯ О СКРИМЕРАХ ===")
            visible_count = sum(1 for s in self.jumpscares if s.get('visible', False))
            triggered_count = sum(1 for s in self.jumpscares if s['triggered'])
            print(f"Всего: {len(self.jumpscares)}, Видимых: {visible_count}, Активировано: {triggered_count}")
            for i, scare in enumerate(self.jumpscares):
                print(f"{i + 1}: тип={scare['type']}, ({scare['x']:.1f},{scare['y']:.1f}), "
                      f"виден={scare.get('visible', False)}, активирован={scare['triggered']}")

    def on_key_release(self, symbol: int, modifiers: int):
        """Отпускание клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = False

    def win_game(self):
        """Победа"""
        play_time = time.time() - self.start_time
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