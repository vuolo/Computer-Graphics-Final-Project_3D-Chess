# Third-party imports.
import pygame
import sys
from pygame.locals import *

# Local application imports.
from constants import WINDOW
from gameplay import pre_draw_gameloop, post_draw_gameloop, gameplay_setup
from graphics import graphics_setup, graphics_draw, graphics_cleanup
from menu.menu import init_main_menu

def main():
    # Setup.
    game = gameplay_setup()
    if "-nomenu" not in sys.argv:
        init_main_menu(pygame.display.set_mode(WINDOW["display"]), game)
    graphics_setup(game)
    
    # Main Loop.
    while True:
        if pre_draw_gameloop() == 'quit':
            break

        # Draw all the graphics
        graphics_draw()

        post_draw_gameloop()

    # Cleanup.
    graphics_cleanup()
    
    # Close the graphics window and exit the program.
    pygame.quit()
    quit()

if __name__ == '__main__':
    main()