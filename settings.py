import pygame_menu

def change_elo(difficulty_name, elo, game):
    # Change the Elo of the AI opponent.
    # Assuming there's a method in the game class to update AI difficulty.
    game.set_ai_elo(elo)

def open_settings_menu(surface, game):
    # Create a settings menu
    settings = pygame_menu.Menu('Settings', 800, 800, theme=pygame_menu.themes.THEME_DARK)
    settings.add.selector('Difficulty (Elo): ', [('Easy', 400), ('Medium', 900), ('Hard', 2200)], onchange=change_elo(game=game))
    settings.add.button('Return to main menu', pygame_menu.events.BACK)
    settings.mainloop(surface)