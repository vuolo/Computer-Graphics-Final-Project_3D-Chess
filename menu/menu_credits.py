# Third-party imports.
import pygame_menu

# Local application imports.
from menu.menu_theme import menu_theme, draw_main_menu_background

def open_credits_menu(surface, game):
    credits_menu = pygame_menu.Menu(
        title='credits',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add credits menu options.
    credits_menu.add.button('Return \t To \t Main \t Menu', credits_menu.disable)
    
    credits_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='credits'))
    
    return credits_menu

# Example usage:
# open_credits_menu(surface, game)