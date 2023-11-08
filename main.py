import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from constants import AI_OPPONENT_ENABLED, AI_OPPONENT_ELO
from chess_game import ChessGame, chess
from menu import main_menu_interface
from graphics import setup_board, draw_board, draw_pieces, pixel_to_board_coords, board_coords_to_notation, display_endgame_message, display_turn_indicator
    
def main():
    pygame.init()
    pygame.font.init()
    display = (800, 800)
    surface = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    setup_board()  # Sets up the orthographic projection and blending.
    
    game = ChessGame()
    main_menu = main_menu_interface(surface, game)
    
    if AI_OPPONENT_ENABLED:
        game.set_ai_elo(AI_OPPONENT_ELO)
    selected_square = None  # Keep track of the selected square.
    highlight_squares = None

    # Main Loop.
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
        
        current_menu = main_menu.get_current()

        if main_menu.is_enabled():
            # Draw the menu.
            main_menu.draw(surface)
            main_menu.update(events)
        else:
            # Draw the current game.
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = pygame.mouse.get_pos()
                    board_x, board_y = pixel_to_board_coords(x, y)
                    square_notation = board_coords_to_notation(board_x, board_y)
                    if selected_square and selected_square != square_notation:
                        move = f"{selected_square}{square_notation}"
                        success, _ = game.make_move(move)
                        if success:
                            print(f"Move made: {move}")
                        else:
                            print(f"Invalid move: {move}")
                        selected_square = None
                        highlight_squares = None
                    else:
                        selected_square = square_notation
                        # Get valid moves and convert to pixel coordinates
                        valid_moves = game.get_valid_moves(selected_square)
                        highlight_squares = [(file, 7 - rank) for file, rank in valid_moves]
                        print(f"Selected square: {selected_square}")
                        
            if AI_OPPONENT_ENABLED and game.board.turn == chess.BLACK:  # Assuming the AI plays as black.
                ai_move = game.ai_make_move()
                if ai_move:
                    print(f"AI moved: {ai_move}")
                        
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            draw_board(highlight_squares)
            draw_pieces(game.get_2d_board_array())  # Use the 2D array for drawing pieces.
            display_turn_indicator(game.board.turn)  # Display whose turn it is.
            
            game_result = game.get_game_result()
            if game_result:
                display_endgame_message(game_result)
            else:
                display_turn_indicator(game.board.turn)  # Display whose turn it is if the game is still ongoing.

        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()
    quit()

if __name__ == '__main__':
    main()