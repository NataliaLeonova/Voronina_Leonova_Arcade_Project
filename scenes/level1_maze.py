# level1_maze.py - ИСПРАВЛЕННЫЕ КОЛЛИЗИИ (СО СПРАЙТАМИ)
import arcade
import random
import math
import time
from typing import List, Dict
from data_models import CalibrationData


class Level1MazeView(arcade.View):
    """Упрощенный и интересный хоррор-лабиринт с ПРАВИЛЬНЫМИ КОЛЛИЗИЯМИ (спрайтами)"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data

        # === ПРОСТЫЕ НАСТРОЙКИ ===
        self.tile_size = 50
        self.map_width = 15
        self.map_height = 15

        # Выход
        self.exit_x = self.map_width - 2
        self.exit_y = self.map_height - 2

        # Игрок (спрайт)
        self.player_sprite = None
        self.player_x = 1.5  # В единицах тайлов
        self.player_y = 1.5  # В единицах тайлов
        self.player_radius = 0.4  # В единицах тайлов (40% от тайла)
        self.player_speed = 5.0

        # Камера
        self.camera_x = 0
        self.camera_y = 0

        # Спрайтовые списки
        self.wall_list = None
        self.exit_list = None
        self.scare_list = None

        # Лабиринт - С ПРАВИЛЬНЫМИ СТЕНАМИ
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

        # Выход в лабиринте
        self.maze[self.exit_y][self.exit_x] = 2

        # Скримеры - УДАЛИЛ СКРИМЕРОВ В СТЕНАХ
        # Проверяем, чтобы скримеры были в проходах (0) а не в стенах (1)
        self.jumpscares = [
            # {'x': 3.5, 'y': 3.5, 'triggered': False},  # В стене! УДАЛЕНО
            {'x': 7.5, 'y': 5.5, 'triggered': False},  # В проходе ✓
            {'x': 11.5, 'y': 8.5, 'triggered': False},  # В проходе ✓
            # {'x': 5.5, 'y': 11.5, 'triggered': False},  # В стене! УДАЛЕНО
            # Добавляем новых скримеров в проходах:
            {'x': 2.5, 'y': 7.5, 'triggered': False},  # Новый скример
            {'x': 12.5, 'y': 3.5, 'triggered': False},  # Новый скример
        ]

        self.active_scare = None
        self.scare_timer = 0

        # Эффекты
        self.screen_shake = 0
        self.flash = 0
        self.stress = 30
        self.scares_triggered = 0

        # Звуки
        try:
            from sound_manager import SoundManager
            self.sound_manager = SoundManager()
        except:
            self.sound_manager = None

        # Управление
        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False
        }

        # Время старта
        self.start_time = time.time()

        # Инициализируем спрайты
        self.setup()

        print("=" * 60)
        print("ХОРРОР ЛАБИРИНТ: Найди красный выход!")
        print("=" * 60)
        print("Управление: УДЕРЖИВАЙ WASD для движения")
        print("Стены теперь работают через спрайты!")
        print(f"Скримеров: {len(self.jumpscares)} (все в проходах)")
        print("=" * 60)

    def setup(self):
        """Настройка спрайтов"""
        # Создаем спрайт-листы
        self.wall_list = arcade.SpriteList()
        self.exit_list = arcade.SpriteList()
        self.scare_list = arcade.SpriteList()

        # Создаем стены как спрайты
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.maze[y][x] == 1:  # Стена
                    wall = arcade.SpriteSolidColor(
                        self.tile_size, self.tile_size, (80, 60, 70)
                    )
                    wall.center_x = x * self.tile_size + self.tile_size // 2
                    wall.center_y = y * self.tile_size + self.tile_size // 2
                    self.wall_list.append(wall)
                elif self.maze[y][x] == 2:  # Выход
                    exit_sprite = arcade.SpriteSolidColor(
                        self.tile_size - 20, self.tile_size - 20, (150, 50, 50)
                    )
                    exit_sprite.center_x = x * self.tile_size + self.tile_size // 2
                    exit_sprite.center_y = y * self.tile_size + self.tile_size // 2
                    self.exit_list.append(exit_sprite)

        # Создаем спрайты для скримеров - ТОЛЬКО В ПРОХОДАХ
        for scare in self.jumpscares:
            # Проверяем, что скример не в стене
            x_int = int(scare['x'])
            y_int = int(scare['y'])

            if 0 <= x_int < self.map_width and 0 <= y_int < self.map_height:
                if self.maze[y_int][x_int] == 0:  # Проверяем, что это проход
                    scare_sprite = arcade.SpriteSolidColor(20, 20, (200, 50, 50))
                    scare_sprite.center_x = scare['x'] * self.tile_size
                    scare_sprite.center_y = scare['y'] * self.tile_size
                    scare['sprite'] = scare_sprite
                    self.scare_list.append(scare_sprite)
                    print(f"Скример создан на ({scare['x']}, {scare['y']}) - в проходе")
                else:
                    print(f"ОШИБКА: Скример на ({scare['x']}, {scare['y']}) в стене! Пропускаем.")
                    scare['sprite'] = None
            else:
                print(f"ОШИБКА: Координаты скримера ({scare['x']}, {scare['y']}) вне карты!")
                scare['sprite'] = None

        # Создаем спрайт игрока
        player_size = int(self.player_radius * self.tile_size * 2)
        self.player_sprite = arcade.SpriteSolidColor(
            player_size, player_size, (100, 150, 255)
        )
        self.player_sprite.center_x = self.player_x * self.tile_size
        self.player_sprite.center_y = self.player_y * self.tile_size

    def check_collisions(self, dx, dy):
        """Проверка коллизий с помощью спрайтов"""
        # Сохраняем старую позицию
        old_x = self.player_sprite.center_x
        old_y = self.player_sprite.center_y

        # Пробуем новую позицию по X
        self.player_sprite.center_x += dx
        collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)

        if collisions:
            # Есть коллизия - возвращаем X
            self.player_sprite.center_x = old_x
            # Пробуем скользить по Y
            self.player_sprite.center_y += dy
            collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            if collisions:
                # Все еще коллизия - возвращаем все
                self.player_sprite.center_y = old_y
        else:
            # Нет коллизии по X, пробуем Y
            old_x = self.player_sprite.center_x  # Обновляем старый X
            self.player_sprite.center_y += dy
            collisions = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            if collisions:
                # Коллизия по Y - возвращаем Y
                self.player_sprite.center_y = old_y

        # Обновляем координаты игрока (для других вычислений)
        self.player_x = self.player_sprite.center_x / self.tile_size
        self.player_y = self.player_sprite.center_y / self.tile_size

    def on_update(self, delta_time: float):
        """Обновление"""
        # Движение при удержании клавиш
        move_x = 0
        move_y = 0
        speed = self.player_speed * delta_time * 0.5 * self.tile_size  # Преобразуем в пиксели

        if self.keys_pressed[arcade.key.W]:
            move_y += speed
        if self.keys_pressed[arcade.key.S]:
            move_y -= speed
        if self.keys_pressed[arcade.key.A]:
            move_x -= speed
        if self.keys_pressed[arcade.key.D]:
            move_x += speed

        # Если есть движение - двигаем с проверкой коллизий
        if move_x != 0 or move_y != 0:
            self.check_collisions(move_x, move_y)

        # Обновляем камеру
        target_x = self.player_sprite.center_x - self.window.width // 2
        target_y = self.player_sprite.center_y - self.window.height // 2

        self.camera_x += (target_x - self.camera_x) * 0.2
        self.camera_y += (target_y - self.camera_y) * 0.2

        # Проверка скримеров
        self.check_scares()

        # Обновление таймера скримера
        if self.active_scare and self.scare_timer > 0:
            self.scare_timer -= delta_time
            if self.scare_timer <= 0:
                self.active_scare = None

        # Обновление эффектов
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - delta_time * 3)

        if self.flash > 0:
            self.flash = max(0, self.flash - delta_time * 5)

        # Проверка выхода (коллизия с выходом)
        exit_collisions = arcade.check_for_collision_with_list(self.player_sprite, self.exit_list)
        if exit_collisions:
            self.win_game()

        # Автоматическое снижение стресса
        if self.stress > 30:
            self.stress = max(30, self.stress - delta_time * 5)

    def check_scares(self):
        """Проверка активации скримеров"""
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite'):
                # Проверяем коллизию со спрайтом скримера
                if arcade.check_for_collision(self.player_sprite, scare['sprite']):
                    self.trigger_scare(scare)
                    break

    def trigger_scare(self, scare):
        """Активировать скример"""
        scare['triggered'] = True
        self.active_scare = scare
        self.scare_timer = 0.8
        self.scares_triggered += 1
        self.stress = min(100, self.stress + 30)

        # Эффекты
        self.screen_shake = 0.7
        self.flash = 1.0

        # Звук
        if self.sound_manager:
            self.sound_manager.play_sound('jump_scare', volume=0.8)

        print(f"ААА! Скример #{self.scares_triggered} на координатах ({scare['x']}, {scare['y']})!")

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        # Тряска камеры
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) * 20 if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) * 20 if self.screen_shake > 0 else 0

        # Фон
        arcade.set_background_color((20, 10, 30))

        # Рисуем стены (весь список сразу)
        for wall in self.wall_list:
            # Позиция с учетом камеры
            x = wall.center_x - self.camera_x + shake_x
            y = wall.center_y - self.camera_y + shake_y

            # Используем фиксированный цвет (80, 60, 70) вместо wall.color
            arcade.draw_lrbt_rectangle_filled(
                x - self.tile_size // 2, x + self.tile_size // 2,
                y - self.tile_size // 2, y + self.tile_size // 2,
                (80, 60, 70)  # ФИКСИРОВАННЫЙ ЦВЕТ СТЕН
            )

            # Тень для объема
            arcade.draw_lrbt_rectangle_filled(
                x - self.tile_size // 2, x - self.tile_size // 2 + 5,
                y - self.tile_size // 2, y + self.tile_size // 2,
                (60, 40, 50)
            )
            arcade.draw_lrbt_rectangle_filled(
                x - self.tile_size // 2, x + self.tile_size // 2,
                y - self.tile_size // 2, y - self.tile_size // 2 + 5,
                (60, 40, 50)
            )

        # Рисуем выход с пульсацией
        for exit_sprite in self.exit_list:
            pulse = (math.sin(time.time() * 5) + 1) / 2
            red = 150 + int(100 * pulse)

            # Позиция с учетом камеры
            x = exit_sprite.center_x - self.camera_x + shake_x
            y = exit_sprite.center_y - self.camera_y + shake_y

            # Рисуем выход
            arcade.draw_lrbt_rectangle_filled(
                x - (self.tile_size - 20) // 2, x + (self.tile_size - 20) // 2,
                y - (self.tile_size - 20) // 2, y + (self.tile_size - 20) // 2,
                (red, 50, 50)
            )

            # Текст ВЫХОД
            arcade.draw_text(
                "ВЫХОД",
                x, y,
                arcade.color.WHITE, 14,
                anchor_x="center", anchor_y="center"
            )

        # Рисуем скримеров (только тех, у кого есть спрайт)
        for scare in self.jumpscares:
            if not scare['triggered'] and scare.get('sprite'):
                # Позиция с учетом камеры
                x = scare['sprite'].center_x - self.camera_x + shake_x
                y = scare['sprite'].center_y - self.camera_y + shake_y

                # Индикатор скримера (мерцает)
                if random.random() < 0.2:
                    arcade.draw_circle_filled(
                        x, y,
                        15,  # Увеличил радиус для лучшей видимости
                        (200, 50, 50)
                    )
                    arcade.draw_circle_outline(
                        x, y,
                        20,  # Увеличил радиус для лучшей видимости
                        (255, 100, 100), 2
                    )

        # Рисуем активный скример
        if self.active_scare and self.scare_timer > 0:
            scare = self.active_scare
            x = scare['sprite'].center_x - self.camera_x + shake_x
            y = scare['sprite'].center_y - self.camera_y + shake_y

            # БОЛЬШОЕ СТРАШНОЕ ЛИЦО
            size = 80 + (1.0 - self.scare_timer / 0.8) * 40
            alpha = int(255 * (self.scare_timer / 0.8))

            # Лицо
            arcade.draw_circle_filled(x, y, size, (30, 30, 30, alpha))
            # Глаза
            arcade.draw_circle_filled(x - 25, y + 15, 20, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x + 25, y + 15, 20, (255, 255, 255, alpha))
            arcade.draw_circle_filled(x - 25, y + 15, 8, (0, 0, 0, alpha))
            arcade.draw_circle_filled(x + 25, y + 15, 8, (0, 0, 0, alpha))
            # Рот
            arcade.draw_ellipse_filled(x, y - 25, 50, 25, (200, 0, 0, alpha))

        # Рисуем игрока
        player_x = self.player_sprite.center_x - self.camera_x + shake_x
        player_y = self.player_sprite.center_y - self.camera_y + shake_y
        player_size = self.player_radius * self.tile_size

        arcade.draw_circle_filled(player_x, player_y, player_size, (100, 150, 255))
        arcade.draw_circle_outline(player_x, player_y, player_size, (200, 200, 255), 2)

        # Направление (маленькая точка впереди)
        arcade.draw_circle_filled(
            player_x + player_size * 0.7,
            player_y,
            player_size * 0.3,
            (255, 255, 255)
        )

        # Вспышка от скримера
        if self.flash > 0:
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                0, self.window.height,
                (255, 200, 200, int(self.flash * 100))
            )

        # Интерфейс
        self.draw_hud()

    def draw_hud(self):
        """Интерфейс"""
        # Фон HUD
        arcade.draw_lrbt_rectangle_filled(
            20, 300,
            20, 90,
            (0, 0, 0, 180)
        )

        # Стресс
        stress_width = 260 * (self.stress / 100)
        stress_color = (255, 100, 100) if self.stress > 70 else (255, 255, 100)

        arcade.draw_lrbt_rectangle_filled(
            30, 30 + stress_width,
            70, 80,
            stress_color
        )

        arcade.draw_text(
            f"СТРЕСС: {int(self.stress)}%",
            30, 50,
            arcade.color.WHITE, 18
        )

        arcade.draw_text(
            f"СКРИМЕРОВ: {self.scares_triggered}/{len(self.jumpscares)}",
            30, 25,
            (255, 100, 100), 16
        )

        # Время
        play_time = int(time.time() - self.start_time)
        arcade.draw_text(
            f"ВРЕМЯ: {play_time}с",
            self.window.width - 150, self.window.height - 30,
            arcade.color.LIGHT_GRAY, 16
        )

        # Подсказки
        arcade.draw_text(
            "ИЩИТЕ МИГАЮЩИЙ КРАСНЫЙ ВЫХОД",
            self.window.width // 2, self.window.height - 30,
            (255, 100, 100), 20,
            anchor_x="center"
        )

        arcade.draw_text(
            "УДЕРЖИВАЙТЕ WASD ДЛЯ ДВИЖЕНИЯ",
            self.window.width // 2, self.window.height - 60,
            arcade.color.LIGHT_GRAY, 16,
            anchor_x="center"
        )

        # Карта мини (в углу)
        self.draw_minimap()

    def draw_minimap(self):
        """Мини-карта в углу"""
        map_size = 120
        map_x = self.window.width - map_size - 20
        map_y = self.window.height - map_size - 20

        # Фон карты
        arcade.draw_lrbt_rectangle_filled(
            map_x, map_x + map_size,
            map_y, map_y + map_size,
            (0, 0, 0, 180)
        )

        # Рисуем клетки карты
        cell_size = map_size / max(self.map_width, self.map_height)

        for y in range(self.map_height):
            for x in range(self.map_width):
                cell_x = map_x + x * cell_size
                cell_y = map_y + (self.map_height - y - 1) * cell_size

                if self.maze[y][x] == 1:
                    arcade.draw_lrbt_rectangle_filled(
                        cell_x, cell_x + cell_size,
                        cell_y, cell_y + cell_size,
                        (100, 80, 90)
                    )
                elif self.maze[y][x] == 2:
                    arcade.draw_lrbt_rectangle_filled(
                        cell_x, cell_x + cell_size,
                        cell_y, cell_y + cell_size,
                        (255, 50, 50)
                    )

        # Игрок на карте
        player_map_x = map_x + self.player_x * cell_size
        player_map_y = map_y + (self.map_height - self.player_y - 1) * cell_size

        arcade.draw_circle_filled(
            player_map_x, player_map_y,
            cell_size * 0.4,
            (100, 150, 255)
        )

        arcade.draw_text(
            "КАРТА",
            map_x + map_size // 2, map_y - 15,
            arcade.color.LIGHT_GRAY, 12,
            anchor_x="center"
        )

    # === УПРАВЛЕНИЕ ===

    def on_key_press(self, symbol: int, modifiers: int):
        """Нажатие клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = True
        elif symbol == arcade.key.ESCAPE:
            self.back_to_menu()
        elif symbol == arcade.key.M:
            # Телепорт к выходу (для теста)
            self.player_sprite.center_x = (self.exit_x - 1) * self.tile_size + self.tile_size // 2
            self.player_sprite.center_y = self.exit_y * self.tile_size + self.tile_size // 2
            # Обновляем координаты игрока
            self.player_x = self.player_sprite.center_x / self.tile_size
            self.player_y = self.player_sprite.center_y / self.tile_size
        elif symbol == arcade.key.T:
            # Телепорт к первому скримеру (для теста коллизии)
            if self.jumpscares:
                self.player_sprite.center_x = self.jumpscares[0]['x'] * self.tile_size
                self.player_sprite.center_y = self.jumpscares[0]['y'] * self.tile_size
                self.player_x = self.player_sprite.center_x / self.tile_size
                self.player_y = self.player_sprite.center_y / self.tile_size

    def on_key_release(self, symbol: int, modifiers: int):
        """Отпускание клавиши"""
        if symbol in self.keys_pressed:
            self.keys_pressed[symbol] = False

    def win_game(self):
        """Победа"""
        play_time = time.time() - self.start_time

        print("=" * 60)
        print("ПОБЕДА! Вы нашли выход!")
        print(f"Время: {play_time:.1f} секунд")
        print(f"Активировано скримеров: {self.scares_triggered}/{len(self.jumpscares)}")
        print(f"Финальный стресс: {int(self.stress)}%")
        print("=" * 60)

        # Переходим к завершению
        from scenes.level1_complete import Level1CompleteView
        complete_view = Level1CompleteView(
            total_jumpscares=len(self.jumpscares),
            triggered_jumpscares=self.scares_triggered,
            play_time=play_time,
            final_stress=self.stress,
            final_sanity=100 - self.stress // 2,
            distance=math.sqrt((self.exit_x - self.player_x) ** 2 + (self.exit_y - self.player_y) ** 2)
        )
        self.window.show_view(complete_view)

    def back_to_menu(self):
        """Выход в меню"""
        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)