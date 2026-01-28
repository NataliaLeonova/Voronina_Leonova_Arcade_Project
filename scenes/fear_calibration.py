import arcade
import time
import random
from data_models import CalibrationData


class FearCalibrationView(arcade.View):
    """Калибровочный экран"""

    def __init__(self):
        super().__init__()

        # Данные калибровки
        self.calibration_data = CalibrationData()
        self.calibration_data.start_time = time.time()

        # Состояние
        self.screen_white = False
        self.click_count = 0
        self.total_clicks_needed = 10
        self.calibration_completed = False

        # Текст
        self.progress_text = None

    def on_show_view(self):
        """При показе экрана"""
        self.screen_white = False

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        if self.screen_white:
            arcade.set_background_color((255, 255, 255))
        else:
            arcade.set_background_color((0, 0, 0))

        if self.click_count > 0 and not self.calibration_completed:
            if not self.progress_text:
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
                self.progress_text.text = f"Прогресс: {self.click_count}/{self.total_clicks_needed}"
                self.progress_text.color = (100, 100, 100) if self.screen_white else (200, 200, 200)

            self.progress_text.draw()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Нажатие мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT and not self.calibration_completed:
            timestamp = time.time() - self.calibration_data.start_time
            self.calibration_data.add_click(timestamp, (x, y))
            self.screen_white = True

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Отпускание мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT and not self.calibration_completed:
            timestamp = time.time() - self.calibration_data.start_time
            self.calibration_data.add_release(timestamp)
            self.screen_white = False
            self.click_count += 1

            if self.click_count >= self.total_clicks_needed:
                self.calibration_completed = True

                if hasattr(arcade, 'unschedule'):
                    try:
                        arcade.unschedule(self.go_to_next)
                    except:
                        pass

                arcade.schedule(self.go_to_next, 0.5)

    def go_to_next(self, dt):
        """Перейти к следующему экрану"""
        try:
            arcade.unschedule(self.go_to_next)
        except:
            pass

        from scenes.level_select import LevelSelectView
        level_view = LevelSelectView(self.calibration_data)
        self.window.show_view(level_view)