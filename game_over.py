import arcade
import random
import time
import math


class GameOverView(arcade.View):
    """Экран проигрыша (смерть или безумие)"""

    def __init__(self, reason="СМЕРТЬ", game_stats=None):
        super().__init__()
        self.reason = reason
        self.game_stats = game_stats or {}
        self.particles = []
        self.blood_drops = []
        self.flash_alpha = 255
        self.shake_intensity = 1.0
        self.start_time = time.time()

        # Текстовые объекты для производительности
        self.title_text = None
        self.reason_text = None
        self.stats_texts = []
        self.message_text = None
        self.instruction_text = None

        # Создаем начальные эффекты
        self.create_effects()
        self.create_text_objects()

    def create_text_objects(self):
        """Создать текстовые объекты для производительности"""
        # Заголовок
        self.title_text = arcade.Text(
            "ПОРАЖЕНИЕ",
            self.window.width // 2,
            self.window.height - 150,
            (255, 50, 50) if self.reason == "СМЕРТЬ" else (200, 50, 200),
            72,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        # Причина
        self.reason_text = arcade.Text(
            self.reason,
            self.window.width // 2,
            self.window.height - 220,
            (255, 100, 100) if self.reason == "СМЕРТЬ" else (220, 100, 220),
            48,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        # Статистика
        if self.game_stats:
            stats_y = self.window.height - 320
            stats = [
                f"Время: {int(self.game_stats.get('time', 0))}с",
                f"Ключи: {self.game_stats.get('keys_collected', 0)}/{self.game_stats.get('total_keys', 3)}",
                f"Стресс: {int(self.game_stats.get('stress_level', 0))}%",
                f"Рассудок: {int(self.game_stats.get('sanity_level', 0))}%",
                f"Скримеров: {self.game_stats.get('jump_scares', 0)}"
            ]

            for i, stat in enumerate(stats):
                y = stats_y - i * 40
                text = arcade.Text(
                    stat,
                    self.window.width // 2,
                    y,
                    (220, 220, 220),
                    24,
                    anchor_x="center",
                    anchor_y="center"
                )
                self.stats_texts.append(text)

        # Инструкция
        self.instruction_text = arcade.Text(
            "Нажмите ПРОБЕЛ для повтора или ESC для выхода в меню",
            self.window.width // 2,
            100,
            (150, 255, 150),
            22,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

    def create_effects(self):
        """Создать эффекты для экрана проигрыша"""
        # Кровавые капли
        for _ in range(50):
            self.blood_drops.append({
                'x': random.randint(0, self.window.width),
                'y': random.randint(0, self.window.height),
                'size': random.randint(2, 8),
                'alpha': random.randint(100, 200)
            })

        # Частицы крови
        for _ in range(100):
            self.particles.append({
                'x': self.window.width // 2,
                'y': self.window.height // 2,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'life': random.uniform(1.0, 3.0),
                'size': random.uniform(3, 10),
                'color': (180 + random.randint(0, 50),
                          20 + random.randint(0, 30),
                          20 + random.randint(0, 30))
            })

    def on_draw(self):
        """Отрисовка экрана проигрыша"""
        self.clear()

        # Тряска экрана
        shake_x = random.uniform(-self.shake_intensity, self.shake_intensity) * 10
        shake_y = random.uniform(-self.shake_intensity, self.shake_intensity) * 10

        elapsed = time.time() - self.start_time

        # Фон - красный градиент
        for i in range(20):
            alpha = 50 + i * 10
            height = self.window.height // 20
            y = i * height

            if self.reason == "БЕЗУМИЕ":
                # Безумие - фиолетовые тона
                color = (
                    80 + i * 8,
                    20 + i * 2,
                    60 + i * 6,
                    alpha
                )
            else:
                # Смерть - красные тона
                color = (
                    60 + i * 8,
                    10 + i * 2,
                    10 + i * 2,
                    alpha
                )

            arcade.draw_lrbt_rectangle_filled(
                0 + shake_x, self.window.width + shake_x,
                y + shake_y, y + height + shake_y,
                color
            )

        # Кровавые капли на фоне
        for drop in self.blood_drops:
            # ИСПРАВЛЕНИЕ: ограничиваем alpha 0-255
            alpha = max(0, min(255, drop['alpha'] // 2))
            arcade.draw_circle_filled(
                drop['x'] + shake_x,
                drop['y'] + shake_y,
                drop['size'],
                (150, 20, 20, alpha)
            )

        # Частицы крови
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = max(0, min(255, int(particle['life'] * 100)))
                arcade.draw_circle_filled(
                    particle['x'] + shake_x,
                    particle['y'] + shake_y,
                    particle['size'],
                    (*particle['color'], alpha)
                )

        # Вспышка
        if self.flash_alpha > 0:
            flash_alpha = max(0, min(255, self.flash_alpha))
            flash_color = (255, 200, 200) if self.reason == "СМЕРТЬ" else (200, 150, 255)
            arcade.draw_lrbt_rectangle_filled(
                0, self.window.width,
                0, self.window.height,
                (*flash_color, flash_alpha)
            )

        # Текст проигрыша (с использованием Text объектов)
        # Обновляем позиции с учетом тряски
        if self.title_text:
            # Пульсация заголовка
            pulse = (math.sin(elapsed * 3) + 1) / 2
            original_color = self.title_text.color
            pulsating_color = (
                min(255, original_color[0] + int(pulse * 20)),
                min(255, original_color[1] + int(pulse * 20)),
                min(255, original_color[2] + int(pulse * 20))
            )

            # Временно изменяем цвет и позицию
            self.title_text.x = self.window.width // 2 + shake_x
            self.title_text.y = self.window.height - 150 + shake_y
            original_color = self.title_text.color
            self.title_text.color = pulsating_color
            self.title_text.draw()
            self.title_text.color = original_color

        # Причина
        if self.reason_text:
            self.reason_text.x = self.window.width // 2 + shake_x
            self.reason_text.y = self.window.height - 220 + shake_y
            self.reason_text.draw()

        # Статистика
        for i, text in enumerate(self.stats_texts):
            text.x = self.window.width // 2 + shake_x
            text.y = self.window.height - 320 - i * 40 + shake_y
            text.draw()

        # Сообщение (меняется со временем)
        if self.reason == "БЕЗУМИЕ":
            messages = [
                "Темнота поглотила ваш разум...",
                "Голоса в голове стали реальностью...",
                "Вы больше не отличаете кошмар от яви...",
                "Страх стал вашим единственным спутником..."
            ]
        else:
            messages = [
                "Монстры нашли свою жертву...",
                "Лабиринт забрал свою дань...",
                "Тени сомкнулись над вами...",
                "Кошмар закончился, но не для вас..."
            ]

        message_index = int(elapsed * 0.5) % len(messages)

        # Создаем или обновляем текст сообщения
        if not hasattr(self, 'current_message') or self.current_message != messages[message_index]:
            self.current_message = messages[message_index]
            self.message_text = arcade.Text(
                self.current_message,
                self.window.width // 2,
                200,
                (255, 150, 150),
                28,
                anchor_x="center",
                anchor_y="center"
            )

        if self.message_text:
            self.message_text.x = self.window.width // 2 + shake_x
            self.message_text.y = 200 + shake_y
            self.message_text.draw()

        # Инструкция (мигает)
        if self.instruction_text:
            blink = int(elapsed * 2) % 2 == 0
            if blink:
                self.instruction_text.x = self.window.width // 2 + shake_x
                self.instruction_text.y = 100 + shake_y
                self.instruction_text.draw()

    def on_update(self, delta_time):
        """Обновление эффектов"""
        elapsed = time.time() - self.start_time

        # Уменьшаем тряску
        if self.shake_intensity > 0:
            self.shake_intensity = max(0, self.shake_intensity - delta_time * 0.2)

        # Уменьшаем вспышку
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - delta_time * 100)

        # Обновляем частицы
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= delta_time

            # Гравитация
            particle['vy'] -= 0.1

            # Если частица умерла, респавним ее
            if particle['life'] <= 0:
                particle['x'] = self.window.width // 2
                particle['y'] = self.window.height // 2
                particle['vx'] = random.uniform(-5, 5)
                particle['vy'] = random.uniform(-5, 5)
                particle['life'] = random.uniform(1.0, 3.0)

        # Мерцание кровавых капель
        for drop in self.blood_drops:
            # ИСПРАВЛЕНИЕ: ограничиваем alpha 0-255
            new_alpha = 100 + int((math.sin(elapsed * 2 + drop['x'] * 0.01) + 1) * 50)
            drop['alpha'] = max(0, min(255, new_alpha))

    def on_key_press(self, symbol: int, modifiers: int):
        """Обработка нажатия клавиш"""
        if symbol == arcade.key.SPACE:
            self.restart_game()
        elif symbol == arcade.key.ESCAPE:
            self.back_to_menu()

    def restart_game(self):
        """Перезапустить игру"""
        from scenes.main_menu import MainMenuView
        from scenes.fear_calibration import FearCalibrationView

        # Начать с калибровки
        calibration_view = FearCalibrationView()
        self.window.show_view(calibration_view)

    def back_to_menu(self):
        """Вернуться в главное меню"""
        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)