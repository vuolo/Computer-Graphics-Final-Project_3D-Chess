# Third-party imports.
import pygame_menu

# Local application imports.
from menu.theme import menu_theme, draw_main_menu_background

def open_game_over_menu(surface, game):
    game_over_menu = pygame_menu.Menu(
        title='Game Over',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add game_over menu options.
    game_over_menu.add.label('GAME OVER'.replace(' ', ' \t '))
    game_over_menu.add.label('')
    
    winner = game.get_winner()
    if winner == 'draw': game_over_menu.add.label('Draw'.replace(' ', ' \t '))
    else: game_over_menu.add.label(f'{winner.capitalize()} wins!'.replace(' ', ' \t '))
    game_over_menu.add.label('')
    
    game_over_menu.add.button('Return To Main Menu'.replace(" ", " \t "), lambda: return_to_main_menu(game_over_menu,  game))
    
    game_over_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='game_over'))
    
    return game_over_menu

def return_to_main_menu(pause_menu, game):
    pause_menu.disable()
    game.set_go_to_main_menu(True)