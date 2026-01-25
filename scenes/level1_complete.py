# level1_complete.py - без лишнего вывода
import arcade
import json
import os
import random
import time
from game_state import GameState


class Level1CompleteView(arcade.View):
    """Экран завершения первого уровня"""

    def __init__(self, total_jumpscares, triggered_jumpscares, play_time,
                 final_stress, final_sanity, distance):
        super().__init__()

        self.data = {
            'total_jumpscares': total_jumpscares,
            'triggered_jumpscares': triggered_jumpscares,
            'play_time': play_time,
            'final_stress': final_stress,
            'final_sanity': final_sanity,
            'distance': distance
        }

        self.texts = []

        # Сохраняем результаты
        game_state = GameState()
        game_state.save_level1_results(self.data)

        self.save_level_data()

    def save_level_data(self):
        """Сохранить данные уровня"""
        os.makedirs('data', exist_ok=True)
        filename = f"data/level1_result_{int(self.data['final_stress'])}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def on_show_view(self):
        """При показе экрана"""
        analysis = self.get_analysis_text()
        lines = analysis.split('\n')

        start_y = self.window.height - 100
        line_height = 30

        for i, line in enumerate(lines):
            y = start_y - i * line_height
            color = (255, 150, 150) if i < 4 else (200, 200, 200)
            size = 24 if i < 4 else 20

            self.texts.append(arcade.Text(
                line,
                self.window.width // 2,
                y,
                color,
                size,
                anchor_x="center",
                anchor_y="center"
            ))

        # Кнопка для продолжения
        self.texts.append(arcade.Text(
            "НАЖМИТЕ ПРОБЕЛ ДЛЯ УРОВНЯ 2",
            self.window.width // 2,
            150,
            (136, 8, 8),
            28,
            anchor_x="center"
        ))

        self.texts.append(arcade.Text(
            "ESC - В главное меню",
            self.window.width // 2,
            100,
            arcade.color.GRAY,
            18,
            anchor_x="center"
        ))

    def get_analysis_text(self):
        """Получить текст анализа"""
        fear_level = self.data['final_stress'] / 100
        jump_scare_ratio = self.data['triggered_jumpscares'] / max(1, self.data['total_jumpscares'])

        if fear_level > 0.8:
            fear_desc = "ЭКСТРЕМАЛЬНЫЙ УРОВЕНЬ СТРАХА"
        elif fear_level > 0.6:
            fear_desc = "ВЫСОКИЙ УРОВЕНЬ СТРАХА"
        elif fear_level > 0.4:
            fear_desc = "СРЕДНИЙ УРОВЕНЬ СТРАХА"
        else:
            fear_desc = "НИЗКИЙ УРОВЕНЬ СТРАХА"

        if jump_scare_ratio > 0.7:
            reaction_desc = "ЧРЕЗМЕРНАЯ РЕАКЦИЯ НА СКРИМЕРЫ"
        elif jump_scare_ratio > 0.4:
            reaction_desc = "СИЛЬНАЯ РЕАКЦИЯ НА СКРИМЕРЫ"
        elif jump_scare_ratio > 0.2:
            reaction_desc = "УМЕРЕННАЯ РЕАКЦИЯ"
        else:
            reaction_desc = "СЛАБАЯ РЕАКЦИЯ НА СКРИМЕРЫ"

        return f"АНАЛИЗ ВАШИХ СТРАХОВ\n\n" \
               f"{fear_desc}\n" \
               f"{reaction_desc}\n\n" \
               f"Статистика:\n" \
               f"Время: {self.data['play_time']:.1f}с\n" \
               f"Пройдено: {self.data['distance']:.1f} тайлов\n" \
               f"Скримеров: {self.data['triggered_jumpscares']}/{self.data['total_jumpscares']}\n" \
               f"Стресс: {int(self.data['final_stress'])}%\n" \
               f"Рассудок: {int(self.data['final_sanity'])}%"

    def on_draw(self):
        """Отрисовка"""
        self.clear()
        arcade.set_background_color((20, 10, 40))

        for _ in range(5):
            x = random.randint(0, self.window.width)
            y = random.randint(0, self.window.height)
            width = random.randint(50, 200)
            height = random.randint(10, 30)
            arcade.draw_ellipse_filled(
                x, y, width, height,
                (100, 20, 20, 50)
            )

        for text in self.texts:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        """Обработка нажатия клавиш"""
        if symbol == arcade.key.SPACE:
            self.start_level2()
        elif symbol == arcade.key.ESCAPE:
            from scenes.main_menu import MainMenuView
            menu_view = MainMenuView()
            self.window.show_view(menu_view)

    def start_level2(self):
        """Запустить второй уровень"""
        game_state = GameState()
        fear_profile = game_state.get_fear_profile()

        from scenes.horror_3d import Horror3DGame
        game_view = Horror3DGame(fear_profile)
        self.window.show_view(game_view)