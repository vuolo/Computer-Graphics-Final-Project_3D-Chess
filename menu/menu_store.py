# Third-party imports.
import pygame_menu

# Local application imports.
from menu.theme import menu_theme, draw_main_menu_background


def change_selected_piece(selected_piece_name, selected_piece_index, game):
    game.set_piece_selection(selected_piece_index)

def change_selected_board(selected_board_name, selected_board_index, game):
    game.set_board_selection(selected_board_index)

def change_selected_ambience(selected_board_name, selected_board_index, game):
    game.set_ambience_selection(selected_board_index)

def open_store_menu(surface, game):
    store_menu = pygame_menu.Menu(
        title='Store',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )

    store_menu.add.selector(
        'Board : \t ',
        [('Wood', 0), ('Classic', 1), ('RGB', 2)],
        default=game.get_board_selection(),
        onchange=lambda value, _: change_selected_board(value[0], value[1], game)
    )

    store_menu.add.selector(
        'Piece : \t ',
        [('Classic', 0), ('Wood', 1), ('Metal', 2)],
        default=game.get_piece_selection(),
        onchange=lambda value, _: change_selected_piece(value[0], value[1], game)
    )

    store_menu.add.selector(
        'Game Ambience : \t ',
        [('Chill', 0), ('Orchestra', 1), ('Beats', 2), ('Off', 3)],
        default=game.get_ambience_selection(),
        onchange=lambda value, _: change_selected_ambience(value[0], value[1], game)
    )
    
    # Add a button to return to the main menu.
    store_menu.add.label('')
    store_menu.add.button('Return To Main Menu'.replace(" ", " \t "), store_menu.disable)
    store_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='store'))
    
    return store_menu


# Example usage:
# open_store_menu(surface, game)