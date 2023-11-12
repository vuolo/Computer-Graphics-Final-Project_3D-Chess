# Third-party imports.
import pygame_menu

# Local application imports.
from constants import developers, third_party_credits
from menu.theme import menu_theme, draw_main_menu_background

def open_credits_menu(surface, game):
    credits_menu = pygame_menu.Menu(
        title='credits',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add a scroll area to the menu for developers.
    credits_menu.add.label('Developers', max_char=-1, align=pygame_menu.locals.ALIGN_CENTER)
    for developer in developers: credits_menu.add.label(developer.replace(" ", " \t "), max_char=-1, align=pygame_menu.locals.ALIGN_CENTER)
    credits_menu.add.label('')
    
    # Add the third-party credits.
    credits_menu.add.label(third_party_credits.replace(" ", " \t "), max_char=-1, align=pygame_menu.locals.ALIGN_CENTER)
    credits_menu.add.label('')

    # Add a button to return to the main menu.
    credits_menu.add.button('Return To Main Menu'.replace(" ", " \t "), credits_menu.disable)
    credits_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='credits'))
    
    return credits_menu

# Example usage:
# open_credits_menu(surface, game)