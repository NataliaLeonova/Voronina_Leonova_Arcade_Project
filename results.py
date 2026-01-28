import arcade
import random
from arcade.gui import UIManager, UILabel, UIAnchorLayout, UIBoxLayout, UIFlatButton


class ResultsView(arcade.View):
    """Экран результатов после прохождения 3D лабиринта"""

    def __init__(self, fear_profile=None, game_stats=None):
        super().__init__()
        self.fear_profile = fear_profile
        self.game_stats = game_stats or {}
        self.ui_manager = UIManager()

    def on_show_view(self):
        """Вызывается при показе результатов"""
        self.ui_manager.enable()
        self.setup_ui()

    def setup_ui(self):
        """Настроить интерфейс результатов"""
        self.ui_manager.clear()

        # Извлекаем статистику
        time_played = self.game_stats.get('time', 0)
        hints = self.game_stats.get('hints_collected', 0)
        total_hints = self.game_stats.get('total_hints', 0)
        keys = self.game_stats.get('keys_collected', 0)
        total_keys = self.game_stats.get('total_keys', 0)
        jump_scares = self.game_stats.get('jump_scares', 0)
        stress = self.game_stats.get('stress_level', 0)
        sanity = self.game_stats.get('sanity_level', 0)

        # Оценка
        score = self.calculate_score()

        anchor = UIAnchorLayout()
        box = UIBoxLayout(vertical=True, space_between=15)

        # Заголовок
        title = UILabel(
            text="НАСТОЯЩИЙ ЛАБИРИНТ ПРОЙДЕН!",
            font_size=32,
            text_color=(136, 8, 8),
            width=600,
            align="center"
        )

        # Оценка
        grade = UILabel(
            text=f"ОЦЕНКА: {score['grade']}",
            font_size=28,
            text_color=(255, 215, 0),
            width=600,
            align="center"
        )

        # Статистика
        stats_text = (
            f"ВРЕМЯ: {int(time_played)} сек\n"
            f"ПОДСКАЗКИ: {hints}/{total_hints}\n"
            f"КЛЮЧИ: {keys}/{total_keys}\n"
            f"СТРЕСС: {int(stress)}%\n"
            f"РАССУДОК: {int(sanity)}%\n"
            f"СКРИМЕРОВ: {jump_scares}\n"
            f"ОЧКОВ: {score['points']}"
        )

        stats = UILabel(
            text=stats_text,
            font_size=20,
            text_color=(57, 255, 20),
            width=500,
            align="center",
            multiline=True
        )

        # Комментарий
        comment = UILabel(
            text=score['comment'],
            font_size=18,
            text_color=(200, 200, 255),
            width=550,
            align="center",
            multiline=True
        )

        # Кнопки
        menu_btn = UIFlatButton(
            text="В ГЛАВНОЕ МЕНЮ",
            width=250,
            height=40
        )

        @menu_btn.event("on_click")
        def on_click_menu(event):
            from scenes.main_menu import MainMenuView
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

        box.add(title)
        box.add(grade)
        box.add(stats)
        box.add(comment)
        box.add(menu_btn)

        anchor.add(box)
        self.ui_manager.add(anchor)

    def calculate_score(self):
        """Рассчитать оценку"""
        time_score = self.game_stats.get('time', 300)
        keys = self.game_stats.get('keys_collected', 0)
        total_keys = self.game_stats.get('total_keys', 3)
        hints = self.game_stats.get('hints_collected', 0)
        total_hints = self.game_stats.get('total_hints', 8)
        stress = self.game_stats.get('stress_level', 100)

        # Баллы
        points = 0
        points += max(0, 600 - time_score)  # Быстрее = лучше (макс 600)
        points += (keys / total_keys) * 300  # Все ключи = 300
        points += (hints / total_hints) * 200  # Все подсказки = 200
        points += max(0, 100 - stress) * 2  # Меньше стресса = лучше

        # Оценка
        if points >= 900:
            grade = "SS"
            comment = "БЕЗУПРЕЧНО! Вы мастер лабиринтов страха!"
        elif points >= 800:
            grade = "S"
            comment = "ОТЛИЧНО! Вы контролировали свои страхи."
        elif points >= 700:
            grade = "A"
            comment = "ХОРОШО! Вы справились с испытанием."
        elif points >= 600:
            grade = "B"
            comment = "НЕПЛОХО! Вы пережили лабиринт."
        elif points >= 500:
            grade = "C"
            comment = "УДОВЛЕТВОРИТЕЛЬНО. Вам повезло выбраться."
        else:
            grade = "D"
            comment = "ЕЛЕ ВЫБРАЛИСЬ. Больше тренируйтесь."

        return {
            'grade': grade,
            'points': int(points),
            'comment': comment
        }

    def on_draw(self):
        """Отрисовка"""
        self.clear()
        arcade.set_background_color((15, 5, 30))

        # Рисуем мини-лабиринт на фоне
        self.draw_maze_background()

        self.ui_manager.draw()

    def draw_maze_background(self):
        """Нарисовать схему лабиринта на фоне"""
        cell_size = 30
        for x in range(0, self.window.width, cell_size):
            for y in range(0, self.window.height, cell_size):
                if random.random() < 0.2:
                    color = (
                        random.randint(30, 60),
                        random.randint(20, 40),
                        random.randint(40, 70)
                    )
                    left = x
                    right = x + cell_size
                    bottom = y
                    top = y + cell_size

                    arcade.draw_lrbt_rectangle_filled(
                        left, right, bottom, top,
                        color
                    )

    def on_hide_view(self):
        """Вызывается при скрытии"""
        self.ui_manager.disable()