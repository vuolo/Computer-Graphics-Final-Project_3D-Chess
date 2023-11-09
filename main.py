# Third-party imports.
import pygame
import sys
from pygame.locals import *

# Local application imports.
from constants import WINDOW, SKIP_MAIN_MENU
from game.gameplay import pre_draw_gameloop, post_draw_gameloop, gameplay_setup
from graphics.graphics_3d import setup_3d_graphics, graphics_draw, graphics_cleanup
from menu.menu import init_main_menu

def main():
    # Setup.
    game = gameplay_setup()
    if "-nomenu" not in sys.argv or SKIP_MAIN_MENU:
        init_main_menu(pygame.display.set_mode(WINDOW["display"]), game)
    screen = setup_3d_graphics(game)
    
    # Main Loop.
    while True:
        if pre_draw_gameloop() == 'quit': break
        graphics_draw()
        post_draw_gameloop(screen)

    # Cleanup.
    graphics_cleanup()
    
    # Close the graphics window and exit the program.
    pygame.quit()
    quit()

if __name__ == '__main__':
    main()