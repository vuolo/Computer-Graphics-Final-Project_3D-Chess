# Third-party imports.
import pygame_menu

# Local application imports.
from menu.theme import menu_theme, draw_main_menu_background

def change_elo(difficulty_name, elo, game):
    # Change the Elo of the AI opponent.
    if game.get_ai_elo() != elo:
        game.set_ai_elo(elo)
        print(f"Changed AI difficulty to {difficulty_name} (Elo: {elo}).")
        
def toggle_ai(enabled, game):
    # Toggle the AI opponent on or off.
    if game.get_ai_opponent_enabled() != enabled:
        game.set_ai_opponent_enabled(enabled)
        print(f"AI opponent {'enabled' if enabled else 'disabled'}.")

def open_pause_menu(surface, game):
    pause_menu = pygame_menu.Menu(
        title='Pause',
        width=surface.get_width(),
        height=surface.get_height(),
        theme=menu_theme
    )
    
    cur_elo = game.get_ai_elo()
    ai_enabled = game.get_ai_opponent_enabled()
    
    # Add pause menu options.
    pause_menu.add.button('Return To Game'.replace(" ", " \t "), pause_menu.disable)
    pause_menu.add.selector(
        'Difficulty \t (Elo): \t ',
        [('Easy', 400), ('Medium', 900), ('Hard', 1750)],
        default=0 if cur_elo <= 400 else 1 if cur_elo <= 900 else 2,
        onchange=lambda selected_value, _: change_elo(selected_value[0][0], selected_value[0][1], game)
    )
    pause_menu.add.toggle_switch(
        'Enable \t AI \t Opponent: ',
        toggleswitch_id='toggle_ai',
        default=ai_enabled,
        onchange=lambda enabled: toggle_ai(enabled, game)
    )
    pause_menu.add.label('')
    pause_menu.add.button('Return To Main Menu'.replace(" ", " \t "), lambda: return_to_main_menu(pause_menu,  game))
    
    pause_menu.mainloop(surface, bgfun=lambda: draw_main_menu_background(surface, menu_type='pause'))
    
    return pause_menu

def return_to_main_menu(pause_menu, game):
    pause_menu.disable()
    game.set_go_to_main_menu(True)
    

# Example usage:
# open_pause_menu(surface, game)