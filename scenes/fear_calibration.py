# fear_calibration.py
import arcade
import time
import random
from data_models import CalibrationData


class FearCalibrationView(arcade.View):
    """Калибровочный экран - клик = белый, отпуск = чёрный"""

    def __init__(self):
        super().__init__()

        # Данные калибровки
        self.calibration_data = CalibrationData()
        self.calibration_data.start_time = time.time()

        # Состояние
        self.screen_white = False
        self.click_count = 0
        self.total_clicks_needed = 10
        self.calibration_completed = False  # ДОБАВИЛ ЭТУ СТРОЧКУ!

        # Текст для отображения прогресса
        self.progress_text = None

        print("=" * 50)
        print("КАЛИБРОВКА: Просто кликайте ЛКМ")
        print(f"Нужно сделать {self.total_clicks_needed} кликов")
        print("Нажали = белый экран, отпустили = чёрный")
        print("=" * 50)

    def on_show_view(self):
        """При показе экрана"""
        # Начинаем с чёрного экрана
        self.screen_white = False

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        # Только цвет фона
        if self.screen_white:
            arcade.set_background_color((255, 255, 255))
        else:
            arcade.set_background_color((0, 0, 0))

        # Прогресс внизу экрана (только если есть прогресс)
        if self.click_count > 0 and not self.calibration_completed:
            if not self.progress_text:
                # Создаем текст один раз
                self.progress_text = arcade.Text(
                    f"Прогресс: {self.click_count}/{self.total_clicks_needed}",
                    self.window.width // 2,
                    50,
                    (100, 100, 100) if self.screen_white else (200, 200, 200),
                    20,
                    anchor_x="center",
                    anchor_y="center"
                )
            else:
                # Обновляем текст
                self.progress_text.text = f"Прогресс: {self.click_count}/{self.total_clicks_needed}"
                self.progress_text.color = (100, 100, 100) if self.screen_white else (200, 200, 200)

            self.progress_text.draw()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Нажатие мыши - делаем экран белым"""
        if button == arcade.MOUSE_BUTTON_LEFT and not self.calibration_completed:
            timestamp = time.time() - self.calibration_data.start_time
            self.calibration_data.add_click(timestamp, (x, y))

            # Включаем белый экран
            self.screen_white = True

            print(f"Нажатие #{len(self.calibration_data.click_times)}")

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Отпускание мыши - делаем экран чёрным"""
        if button == arcade.MOUSE_BUTTON_LEFT and not self.calibration_completed:
            timestamp = time.time() - self.calibration_data.start_time
            self.calibration_data.add_release(timestamp)

            # Выключаем белый экран
            self.screen_white = False

            # Считаем клик
            self.click_count += 1
            if self.calibration_data.reaction_intervals:
                hold_time = self.calibration_data.reaction_intervals[-1]
            else:
                hold_time = 0

            print(f"Клик #{self.click_count}/{self.total_clicks_needed} - удержание: {hold_time:.3f}с")

            # Проверяем завершение
            if self.click_count >= self.total_clicks_needed:
                self.calibration_completed = True
                print("=" * 50)
                print("КАЛИБРОВКА ЗАВЕРШЕНА!")
                print("=" * 50)

                # Отключаем дальнейшие клики
                if hasattr(arcade, 'unschedule'):
                    try:
                        arcade.unschedule(self.go_to_next)
                    except:
                        pass

                # Переходим дальше через 0.5 секунды
                arcade.schedule(self.go_to_next, 0.5)

    def go_to_next(self, dt):
        """Перейти к следующему экрану"""
        # Отписываемся от таймера
        try:
            arcade.unschedule(self.go_to_next)
        except:
            pass

        from scenes.level_select import LevelSelectView
        level_view = LevelSelectView(self.calibration_data)
        self.window.show_view(level_view)