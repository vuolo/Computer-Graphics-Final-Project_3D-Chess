# Third-party imports.
import pygame_menu
import pygame

# Local application imports.
from menu.menu_theme import menu_theme, draw_main_menu_background
from menu.menu_settings import open_settings_menu
from menu.menu_store import open_store_menu
from menu.menu_credits import open_credits_menu

def init_main_menu(surface, game):
    # Define the main menu interface.
    main_menu = pygame_menu.Menu(
        title='3D Chess',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme,
        enabled=True
    )

    pygame.mixer.music.load('./sounds/menu.mp3')
    pygame.mixer.music.set_volume(0.5)  # Set the volume to 50%
    pygame.mixer.music.play(-1)  # -1 means the music will loop indefinitely

    # Add main menu buttons.
    main_menu.add.button('Play', lambda: start_the_game(main_menu, game))
    main_menu.add.button('Settings', lambda: open_settings_menu(surface, game))
    main_menu.add.button('Store', lambda: open_store_menu(surface, game))
    main_menu.add.button('Credits', lambda: open_credits_menu(surface, game))
    main_menu.add.button('Quit', pygame_menu.events.EXIT)
    
    main_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface))

    return main_menu

def start_the_game(menu, game):
    menu.disable()
    pygame.mixer.music.stop()  # Stop the music

    # game.start() # TODO: if necessary (e.g. if we wanted to add a timer / reset game functionality / etc.)
