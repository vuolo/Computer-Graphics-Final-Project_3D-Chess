# Third-party imports.
import pygame_menu

# Local application imports.
from menu.theme import menu_theme, draw_main_menu_background
from piece_globals import game_globals


def change_elo(selected_piece_name, selected_piece_index, game):
    global piece_selection
    print("Selected Piece: ", selected_piece_index)
    game_globals.piece_selection = selected_piece_index

def open_store_menu(surface, game):
    store_menu = pygame_menu.Menu(
        title='Store',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )

    store_menu.add.selector(
        'Piece : \t ',
        [('Classic', 0), ('Wood', 1), ('Metal', 2)],
        default=game_globals.piece_selection,
        onchange=lambda value, _: change_elo(value[0], value[1], game)
    )
    
    # Add a button to return to the main menu.
    store_menu.add.button('Return To Main Menu'.replace(" ", " \t "), store_menu.disable)
    store_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='store'))
    
    return store_menu


# Example usage:
# open_store_menu(surface, game)