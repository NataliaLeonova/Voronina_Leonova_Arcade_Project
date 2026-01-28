import arcade


class RulesManager:
    """Менеджер правил игры"""

    RULES = {
        "general": [
            "ПЕРЕД НАЧАЛОМ: Вам нужно кликать левой кнопкой мыши",
            "ЦЕЛЬ: Найдите выход из лабиринта",
            "Игра анализирует ваши реакции",
            "Чем дольше играете, тем страшнее становится"
        ],
        "level1": [
            "УРОВЕНЬ 1: Простой лабиринт",
            "Ищите красный выход",
            "Избегайте скримеров",
            "Удерживайте WASD для движения"
        ],
        "level2": [
            "УРОВЕНЬ 2: 3D Лабиринт",
            "Найдите 3 ключа и выход",
            "M - карта (держите открытой)",
            "F - фонарик (разряжается)",
            "ПРОБЕЛ - крик (отпугивает монстров)",
            "Используйте мышь для обзора"
        ]
    }

    @staticmethod
    def show_rules(window, level_type="general"):
        """Показать окно с правилами"""
        rules_view = RulesView(window, level_type)
        return rules_view


class RulesView(arcade.View):
    """Вид окна с правилами"""

    def __init__(self, parent_window, level_type="general"):
        super().__init__()
        self.parent_window = parent_window
        self.level_type = level_type
        self.previous_view = parent_window.current_view  # Сохраняем текущий вид

    def on_draw(self):
        """Отрисовка"""
        self.clear()

        # Полупрозрачный фон
        arcade.draw_lrbt_rectangle_filled(
            0, self.parent_window.width,
            0, self.parent_window.height,
            (0, 0, 0, 220)
        )

        # Заголовок
        arcade.draw_text(
            "ПРАВИЛА ИГРЫ",
            self.parent_window.width // 2,
            self.parent_window.height - 100,
            (136, 8, 8), 36,
            anchor_x="center", anchor_y="center",
            bold=True
        )

        # Правила
        rules = RulesManager.RULES.get(self.level_type, RulesManager.RULES["general"])

        start_y = self.parent_window.height - 180
        line_height = 30

        for i, rule in enumerate(rules):
            y = start_y - i * line_height
            color = (220, 220, 220)
            size = 20

            # Первая строка особенная
            if i == 0 and "ПЕРЕД НАЧАЛОМ" in rule:
                color = (255, 215, 0)  # Золотой цвет для важного сообщения

            arcade.draw_text(
                f"• {rule}",
                self.parent_window.width // 2, y,
                color, size,
                anchor_x="center", anchor_y="center"
            )

        # Кнопка закрытия
        arcade.draw_text(
            "Нажмите ESC для возврата",
            self.parent_window.width // 2, 100,
            (150, 255, 150), 22,
            anchor_x="center", anchor_y="center",
            bold=True
        )

    def on_key_press(self, symbol, modifiers):
        """Закрыть по ESC"""
        if symbol == arcade.key.ESCAPE:
            # Возвращаемся к предыдущему виду
            if self.previous_view:
                self.parent_window.show_view(self.previous_view)
            else:
                # Если предыдущий вид не сохранился, возвращаемся в меню
                from scenes.main_menu import MainMenuView
                menu_view = MainMenuView()
                self.parent_window.show_view(menu_view)