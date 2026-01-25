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
        self.jumpscares = [
            {'x': 7.5, 'y': 5.5, 'triggered': False, 'visible': True},
            {'x': 11.5, 'y': 8.5, 'triggered': False, 'visible': True},
            {'x': 2.5, 'y': 7.5, 'triggered': False, 'visible': True},
            {'x': 12.5, 'y': 3.5, 'triggered': False, 'visible': True},
            {'x': 13.5, 'y': 12.5, 'triggered': False, 'visible': False},
            {'x': 4.5, 'y': 2.5, 'triggered': False, 'visible': True},
            {'x': 10.5, 'y': 11.5, 'triggered': False, 'visible': True},
            {'x': 5.5, 'y': 12.5, 'triggered': False, 'visible': True},
            {'x': 13.5, 'y': 5.5, 'triggered': False, 'visible': True},
            {'x': 7.5, 'y': 9.5, 'triggered': False, 'visible': True},
            {'x': 3.5, 'y': 11.5, 'triggered': False, 'visible': False, 'hidden': True, 'activation_range': 2.0},
            {'x': 8.5, 'y': 2.5, 'triggered': False, 'visible': False, 'hidden': True, 'activation_range': 1.5},
        ]

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

    def init_sound_manager(self):
        """Инициализировать менеджер звуков ТОЛЬКО для скримеров"""
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager(sound_mode="level1")
            self.sound_manager.set_volume(1.0)
        except Exception as e:
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
        valid_scares = 0
        for scare in self.jumpscares:
            x_int = int(scare['x'])
            y_int = int(scare['y'])

            if 0 <= x_int < self.map_width and 0 <= y_int < self.map_height:
                if self.maze[y_int][x_int] == 0:
                    if scare.get('hidden', False):
                        color = (200, 50, 50, 0)
                    else:
                        color = (200, 50, 50, 150 if scare.get('visible', True) else 0)

                    scare_sprite = arcade.SpriteSolidColor(20, 20, color)
                    scare_sprite.center_x = scare['x'] * self.tile_size
                    scare_sprite.center_y = scare['y'] * self.tile_size
                    scare['sprite'] = scare_sprite
                    self.scare_list.append(scare_sprite)
                    valid_scares += 1
                else:
                    self.jumpscares.remove(scare)
            else:
                self.jumpscares.remove(scare)

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
        current_time = time.time()

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
        """Активация скрытых скримеров"""
        for scare in self.jumpscares:
            if scare.get('hidden', False) and not scare['triggered'] and scare.get('sprite'):
                dx = scare['sprite'].center_x - self.player_sprite.center_x
                dy = scare['sprite'].center_y - self.player_sprite.center_y
                distance = math.sqrt(dx * dx + dy * dy) / self.tile_size

                activation_range = scare.get('activation_range', 2.0)

                if distance < activation_range:
                    scare['visible'] = True
                    scare['sprite'].alpha = 255

    def check_scares(self):
        """Проверка активации скримеров"""
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite') and scare.get('visible', True):
                if arcade.check_for_collision(self.player_sprite, scare['sprite']):
                    self.trigger_scare(scare)
                    break

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

        # ЗВУК СКРИМЕРА (единственный звук в Level 1)
        if self.sound_manager:
            volume = 0.8 + random.random() * 0.2
            success = self.sound_manager.play_sound('scream', volume=volume)

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

                if scare.get('hidden', False):
                    if random.random() < 0.1:
                        arcade.draw_circle_filled(x, y, 12, (150, 50, 150, 100))
                else:
                    if random.random() < 0.15:
                        arcade.draw_circle_filled(x, y, 10, (200, 50, 50))

        # Активный скример
        if self.active_scare and self.scare_timer > 0:
            scare = self.active_scare
            x = scare['sprite'].center_x - self.camera_x + shake_x
            y = scare['sprite'].center_y - self.camera_y + shake_y

            size = 80 + (1.0 - self.scare_timer / 0.8) * 40
            alpha = int(255 * (self.scare_timer / 0.8))

            arcade.draw_circle_filled(x, y, size, (150, 0, 0, alpha))
            arcade.draw_circle_filled(x - 25, y + 15, 20, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + 25, y + 15, 20, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x - 25, y + 15, 8, (0, 0, 0, alpha))
            arcade.draw_circle_filled(x + 25, y + 15, 8, (0, 0, 0, alpha))
            arcade.draw_ellipse_filled(x, y - 25, 50, 25, (200, 0, 0, alpha))

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

        # МИНИ-КАРТА (добавляем в конце)
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
            f"СКРИМЕРОВ: {self.scares_triggered}",
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
            "СКРИМЕРЫ ВСЮДУ...",
            "LEVEL 1: ТОЛЬКО СКРИМЕРЫ",
            "ТИШИНА - ХУДШИЙ ВРАГ"
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
            if not scare['triggered'] and scare.get('visible', False):
                scare_x = map_x + scare['x'] * cell_size
                scare_y = map_y + scare['y'] * cell_size

                if scare.get('hidden', False):
                    if int(time.time() * 3) % 2 == 0:
                        arcade.draw_circle_filled(
                            scare_x, scare_y,
                            cell_size * 0.2,
                            (255, 100, 100, 150)
                        )
                else:
                    arcade.draw_circle_filled(
                        scare_x, scare_y,
                        cell_size * 0.2,
                        (255, 50, 50)
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
