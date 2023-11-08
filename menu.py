import pygame_menu
from settings import open_settings_menu

def main_menu_interface(surface, game):
    # Define the main menu interface.
    menu = pygame_menu.Menu('Chess Game', 800, 800,
                            theme=pygame_menu.themes.THEME_DARK, enabled=False)

    # Add menu options.
    menu.add.button('Play', start_the_game, menu, game)
    menu.add.button('Settings', open_settings_menu, surface, game)
    menu.add.button('Quit', pygame_menu.events.EXIT)

    return menu

def start_the_game(menu, game):
    menu.disable()
    # game.start() # TODO: if necessary (e.g. if we wanted to add a timer / reset game functionality / etc.)