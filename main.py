# Third-party imports.
import pygame
import sys

# Local application imports.
from constants import WINDOW, SKIP_MAIN_MENU
from game.gameplay import pre_draw_gameloop, post_draw_gameloop, gameplay_setup
from menu.menu import init_main_menu
from graphics.graphics_3d import setup_3d_graphics, draw_graphics, cleanup_graphics

def main():
    # Setup.
    game = gameplay_setup()
    if "-nomenu" not in sys.argv or SKIP_MAIN_MENU:
        init_main_menu(pygame.display.set_mode(WINDOW["display"]), game)
    setup_3d_graphics(game)
    
    last_time = pygame.time.get_ticks()
    
    # Main Loop.
    while True:
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # Convert milliseconds to seconds
        last_time = current_time
        
        if pre_draw_gameloop() == 'quit': break
        draw_graphics(delta_time)
        post_draw_gameloop()

    # Cleanup.
    cleanup_graphics()
    
    # Close the graphics window and exit the program.
    pygame.quit()
    quit()

if __name__ == '__main__':
    main()