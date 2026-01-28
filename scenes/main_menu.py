import arcade
from arcade.gui import UIManager, UILabel, UIAnchorLayout, UIBoxLayout, UIFlatButton


class MainMenuView(arcade.View):
    """Главное меню с кнопкой правил"""

    def __init__(self):
        super().__init__()
        self.ui_manager = UIManager()
        self.setup_ui()

    def setup_ui(self):
        """Настроить интерфейс меню"""
        self.ui_manager.clear()

        anchor = UIAnchorLayout()
        box = UIBoxLayout(vertical=True, space_between=20)

        # Заголовок
        title = UILabel(
            text="FEAR_OS: ПЕРСОНАЛЬНЫЙ КОШМАР",
            font_size=36,
            text_color=(136, 8, 8),
            width=600,
            align="center"
        )

        # Подзаголовок
        subtitle = UILabel(
            text="Игра анализирует ваши страхи и адаптируется",
            font_size=20,
            text_color=(200, 200, 200),
            width=600,
            align="center"
        )

        # Кнопка начала
        start_btn = UIFlatButton(
            text="НАЧАТЬ ИГРУ (ЛКМ или ПРОБЕЛ)",
            width=300,
            height=50
        )

        @start_btn.event("on_click")
        def on_click_start(event):
            self.start_game()

        # Кнопка правил
        rules_btn = UIFlatButton(
            text="ПРАВИЛА ИГРЫ (R)",
            width=200,
            height=40
        )

        @rules_btn.event("on_click")
        def on_click_rules(event):
            self.show_rules()

        box.add(title)
        box.add(subtitle)
        box.add(start_btn)
        box.add(rules_btn)

        anchor.add(box)
        self.ui_manager.add(anchor)

    def on_show_view(self):
        """При показе"""
        self.ui_manager.enable()

    def on_hide_view(self):
        """При скрытии"""
        self.ui_manager.disable()

    def on_draw(self):
        """Отрисовка"""
        self.clear()
        arcade.set_background_color((0, 0, 0))

        # Добавляем атмосферные элементы
        arcade.draw_text(
            "Внимание: игра анализирует ваши реакции мыши и клавиатуры",
            self.window.width // 2,
            100,
            (100, 100, 100),
            14,
            anchor_x="center"
        )

        self.ui_manager.draw()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Клик мыши для начала"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.start_game()

    def on_key_press(self, symbol: int, modifiers: int):
        """Обработка клавиш"""
        if symbol == arcade.key.SPACE or symbol == arcade.key.ENTER:
            self.start_game()
        elif symbol == arcade.key.R:
            self.show_rules()

    def start_game(self):
        """Начать игру"""
        from scenes.fear_calibration import FearCalibrationView
        calibration_view = FearCalibrationView()
        self.window.show_view(calibration_view)

    def show_rules(self):
        """Показать правила"""
        from rules import RulesManager
        rules_view = RulesManager.show_rules(self.window, "general")
        self.window.show_view(rules_view)
