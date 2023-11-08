import pygame_menu
from menu_theme import menu_theme, draw_main_menu_background

def change_elo(difficulty_name, elo, game):
    # Change the Elo of the AI opponent.
    game.set_ai_elo(elo)

def open_settings_menu(surface, game):
    settings_menu = pygame_menu.Menu(
        title='Settings',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    # Add settings menu options.
    settings_menu.add.selector(
        'Difficulty \t (Elo): \t ',
        [('Easy', 400), ('Medium', 900), ('Hard', 2200)],
        onchange=lambda selected_value, index: change_elo(selected_value[0], selected_value[1], game)
    )
    # TODO: fix this button so that it actually returns to the main menu.
    settings_menu.add.button('Return \t To \t Main \t Menu', pygame_menu.events.BACK)
    
    settings_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='settings'))
    
    return settings_menu

# Example usage:
# open_settings_menu(surface, game)