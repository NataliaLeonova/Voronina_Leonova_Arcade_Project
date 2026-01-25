# main.py - улучшенная версия (без лишнего вывода)
import arcade
import os
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scenes.main_menu import MainMenuView
from game_state import GameState


def main():
    """"Главная функция"""
    # Создаем директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('saves', exist_ok=True)
    os.makedirs('custom_sounds', exist_ok=True)
    os.makedirs('custom_sounds/music', exist_ok=True)

    # Загружаем предыдущее состояние (без вывода)
    game_state = GameState()
    game_state.load_from_file()

    # Создаем окно
    window = arcade.Window(
        width=1280,
        height=720,
        title="FEAR_OS: Персональный кошмар",
        fullscreen=False,
        resizable=True
    )

    # Запускаем с главного меню
    menu_view = MainMenuView()
    window.show_view(menu_view)

    # Запускаем игру
    arcade.run()


if __name__ == "__main__":
    main()