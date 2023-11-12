# Third-party imports.
import pygame_menu

# Local application imports.
from menu.theme import menu_theme, draw_main_menu_background

def open_promote_pawn_menu(surface, game):
    promote_pawn_menu = pygame_menu.Menu(
        title='Promote Pawn',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add promote_pawn menu options.
    promote_pawn_menu.add.label('Promote pawn to:'.replace(' ', ' \t '))
    promote_pawn_menu.add.button('Queen', lambda: return_to_game(game, promote_pawn_menu, 'Queen'))
    promote_pawn_menu.add.button('Rook', lambda: return_to_game(game, promote_pawn_menu, 'Rook'))
    promote_pawn_menu.add.button('Bishop', lambda: return_to_game(game, promote_pawn_menu, 'Bishop'))
    promote_pawn_menu.add.button('Knight', lambda: return_to_game(game, promote_pawn_menu, 'Knight'))
    
    promote_pawn_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='promote_pawn'))
    
    return promote_pawn_menu

def return_to_game(game, promote_pawn_menu, pawn_selection="Queen"):
    game.set_pawn_promotion_selection(pawn_selection)
    promote_pawn_menu.disable()