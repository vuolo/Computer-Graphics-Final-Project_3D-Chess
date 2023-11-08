import pygame_menu
from menu_theme import menu_theme, draw_main_menu_background
from menu_settings import open_settings_menu

def main_menu_interface(surface, game):
    # Define the main menu interface.
    main_menu = pygame_menu.Menu(
        title='3D Chess',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme,
        enabled=True
    )

    # Add main menu buttons.
    main_menu.add.button('Play', lambda: start_the_game(main_menu, game))
    main_menu.add.button('Settings', lambda: open_settings_menu(surface, game))
    main_menu.add.button('Quit', pygame_menu.events.EXIT)
    # TODO: add a "credits" button & page to show the names of the developers and any resources used.
    
    main_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface))

    return main_menu

def start_the_game(menu, game):
    menu.disable()
    # game.start() # TODO: if necessary (e.g. if we wanted to add a timer / reset game functionality / etc.)
