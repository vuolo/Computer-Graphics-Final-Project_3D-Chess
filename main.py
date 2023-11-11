# Third-party imports.
import pygame
import sys

# Local application imports.
from constants import WINDOW, SKIP_MAIN_MENU
from game.gameplay import pre_draw_gameloop, post_draw_gameloop, gameplay_setup
from menu.menu import init_main_menu
from menu.menu_pause import open_pause_menu
from graphics.graphics_3d import setup_3d_graphics, draw_graphics, cleanup_graphics

def main(game_settings=None):
    # Setup.
    game = gameplay_setup(game_settings)
    if "-nomenu" not in sys.argv and not SKIP_MAIN_MENU:
        init_main_menu(pygame.display.set_mode(WINDOW["display"]), game)
    setup_3d_graphics(game)
    
    last_time = pygame.time.get_ticks()
    
    # Main Loop.
    while True:
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # Convert milliseconds to seconds
        last_time = current_time
        
        result = pre_draw_gameloop()
        if result == 'quit': break
        if result == 'pause':
            open_pause_menu(pygame.display.set_mode(WINDOW["display"]), game)
            setup_3d_graphics(game)
            continue
        if game.get_go_to_main_menu():
            cleanup()
            main(game_settings=game.get_settings())
            return
            
        draw_graphics(delta_time, game, result['highlighted_square'], result['selected_square'], result['valid_move_squares'], result['invalid_move_square'])
        post_draw_gameloop()

    cleanup(quitting=True)

def cleanup(quitting=False):
    # Cleanup.
    cleanup_graphics()
    
    # Close the graphics window and exit the program.
    if quitting:
        pygame.quit()
        quit()

if __name__ == '__main__':
    main()