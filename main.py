# Third-party imports.
import pygame
import sys

# Local application imports.
from constants import WINDOW, SKIP_MAIN_MENU, RESET_GAME_EVENT
from game.gameplay import pre_draw_gameloop, post_draw_gameloop, gameplay_setup
from menu.menu import init_main_menu
from menu.menu_pause import open_pause_menu
from menu.menu_promote_pawn import open_promote_pawn_menu
from menu.menu_game_over import open_game_over_menu
from graphics.graphics_3d import setup_3d_graphics, draw_graphics, cleanup_graphics

pygame.mixer.init()

def main(game_settings=None):

    game, gui = gameplay_setup(game_settings)
    if "-nomenu" not in sys.argv and not SKIP_MAIN_MENU:
        init_main_menu(pygame.display.set_mode(WINDOW["display"]), game)
    
    # Setup.
    if(game.ambience_selection == 0):
        pygame.mixer.music.load('sounds/chill.mp3')
        pygame.mixer.music.set_volume(0.2)  
        pygame.mixer.music.play(-1)  
    elif(game.ambience_selection == 1):
        pygame.mixer.music.load('sounds/orchestra.mp3')
        pygame.mixer.music.set_volume(0.1) 
        pygame.mixer.music.play(-1)  
    elif(game.ambience_selection == 2):
        pygame.mixer.music.load('sounds/beats.mp3')
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

    setup_3d_graphics(game, gui)
    
    # Reset the game after the main menu is closed.
    pygame.time.set_timer(RESET_GAME_EVENT, 1, 1)
    
    notify_sound = pygame.mixer.Sound('sounds/notify.mp3')
    game_over_sound = pygame.mixer.Sound('sounds/game-end.mp3')
    
    # Main Loop.
    last_time = pygame.time.get_ticks()
    while True:
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - last_time) / 1000.0  # Convert milliseconds to seconds
        last_time = current_time
        
        result = pre_draw_gameloop()
        if result == 'quit': break
        elif result == 'pause':
            pause_game_and_continue(lambda: open_pause_menu(pygame.display.set_mode(WINDOW["display"]), game), game, gui)
            continue
        elif result == 'needs_pawn_promotion':
            notify_sound.play()
            pause_game_and_continue(lambda: open_promote_pawn_menu(pygame.display.set_mode(WINDOW["display"]), game), game, gui)
            continue
        elif result == 'game_over':
            game_over_sound.play()
            restart_game(game, display_menu_first_func=lambda: open_game_over_menu(pygame.display.set_mode(WINDOW["display"]), game))
            return
        elif result == 'play_bowling_animation':
            # pause_game_and_continue(lambda: play_bowling_animation(pygame.display.set_mode(WINDOW["display"]), game, use_random_animation=True), game, gui)
            continue
        if game.get_go_to_main_menu():
            restart_game(game)
            return
            
        draw_graphics(delta_time, result['highlighted_square'], result['selected_square'], result['valid_move_squares'], result['invalid_move_square'])
        post_draw_gameloop()

    cleanup(quitting=True)
    
def restart_game(game, display_menu_first_func=None):
    if display_menu_first_func: display_menu_first_func()
    cleanup()
    main(game_settings=game.get_settings())
    
def pause_game_and_continue(menu_func, game, gui):
    menu_func()
    setup_3d_graphics(game, gui, is_resume=True)

def cleanup(quitting=False):
    # Cleanup.
    cleanup_graphics()
    
    # Close the graphics window and exit the program.
    if quitting:
        pygame.quit()
        quit()

if __name__ == '__main__':
    main()