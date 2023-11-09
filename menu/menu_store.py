# Third-party imports.
import pygame_menu

# Local application imports.
from menu.menu_theme import menu_theme, draw_main_menu_background

# TODO: show the names of the developers and any resources used.

def open_store_menu(surface, game):
    store_menu = pygame_menu.Menu(
        title='Store',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add store menu options.
    store_menu.add.button('Return \t To \t Main \t Menu', store_menu.disable)
    
    store_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='store'))
    
    return store_menu

# Example usage:
# open_store_menu(surface, game)