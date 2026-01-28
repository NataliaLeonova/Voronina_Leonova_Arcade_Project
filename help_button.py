import arcade


class HelpButton:
    """Плавающая кнопка помощи"""

    def __init__(self, window, level_type):
        self.window = window
        self.level_type = level_type
        self.visible = True
        self.button_x = window.width - 60
        self.button_y = 60
        self.button_radius = 25
        self.hovered = False

    def draw(self):
        """Нарисовать кнопку помощи"""
        if not self.visible:
            return

        # Фон кнопки
        color = (100, 100, 200, 180) if self.hovered else (80, 80, 160, 150)
        arcade.draw_circle_filled(
            self.button_x, self.button_y,
            self.button_radius,
            color
        )

        # Знак вопроса
        arcade.draw_text(
            "?",
            self.button_x, self.button_y - 5,
            arcade.color.WHITE,
            24,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )

        # Текст при наведении
        if self.hovered:
            arcade.draw_text(
                "Помощь (H)",
                self.button_x - 100, self.button_y + 40,
                arcade.color.LIGHT_GRAY,
                16
            )

    def check_click(self, x, y):
        """Проверить клик по кнопке"""
        if not self.visible:
            return False

        distance = ((x - self.button_x) ** 2 + (y - self.button_y) ** 2) ** 0.5
        if distance <= self.button_radius:
            self.show_help()
            return True
        return False

    def check_hover(self, x, y):
        """Проверить наведение мыши"""
        if not self.visible:
            self.hovered = False
            return

        distance = ((x - self.button_x) ** 2 + (y - self.button_y) ** 2) ** 0.5
        self.hovered = distance <= self.button_radius

    def show_help(self):
        """Показать справку"""
        from rules import RulesManager
        # Сохраняем текущий вид
        self.window.current_view = self.window.current_view

        # Показываем правила
        rules_view = RulesManager.show_rules(self.window, self.level_type)
        self.window.show_view(rules_view)
