# main.py
import arcade
import os
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scenes.main_menu import MainMenuView


def main():
    """Главная функция"""
    # Создаем директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('saves', exist_ok=True)

    # Создаем окно
    window = arcade.Window(
        width=1280,
        height=720,
        title="FEAR_OS: Персональный кошмар",
        fullscreen=False,
        resizable=True
    )

    menu_view = MainMenuView()
    window.show_view(menu_view)

    # Запускаем игру
    arcade.run()


if __name__ == "__main__":
    main()