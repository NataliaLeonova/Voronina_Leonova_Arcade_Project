# main_menu.py
import arcade


class MainMenuView(arcade.View):
    """Главное меню - просто чёрный экран"""

    def __init__(self):
        super().__init__()
        # Используем arcade.Text для лучшей производительности
        self.title_text = None
        self.subtitle_text = None

    def on_show_view(self):
        """При показе меню"""
        print("FEAR_OS: Нажмите ЛКМ для начала")

        # Создаем объекты текста
        self.title_text = arcade.Text(
            "FEAR_OS",
            self.window.width // 2,
            self.window.height // 2,
            (136, 8, 8),
            48,
            anchor_x="center",
            anchor_y="center"
        )

        self.subtitle_text = arcade.Text(
            "НАЖМИТЕ ЛКМ ДЛЯ НАЧАЛА",
            self.window.width // 2,
            self.window.height // 2 - 70,
            arcade.color.WHITE,
            28,
            anchor_x="center",
            anchor_y="center"
        )

    def on_draw(self):
        """Отрисовка"""
        self.clear()
        arcade.set_background_color((0, 0, 0))

        # Рисуем текст
        if self.title_text and self.subtitle_text:
            self.title_text.draw()
            self.subtitle_text.draw()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Обработка клика мыши"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start_calibration()

    def start_calibration(self):
        """Начать калибровку"""
        print("Запуск калибровки...")

        from scenes.fear_calibration import FearCalibrationView
        calibration_view = FearCalibrationView()
        self.window.show_view(calibration_view)