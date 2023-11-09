# Third-party imports.
from typing import Optional
from pygame.locals import *
import pygame
import chess
import platform

# Local application imports.
from constants import WINDOW
from chess_game import ChessGame
from graphics_2d import pixel_to_board_coords, board_coords_to_notation, display_endgame_message, display_turn_indicator

# Global variables.
game: Optional['ChessGame'] = None
selected_square = None  # Keep track of the user-selected square.
highlight_squares = None # Displays highlight squares that the user can move to.

def gameplay_setup():
    global game
    game = ChessGame()
    
    # Initialize pygame and set up OpenGL context's major and minor version numbers.
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("3D Chess")
    pygame.display.set_mode(WINDOW["display"], DOUBLEBUF | OPENGL)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    
    # MacOS Compatability: We need to request a core profile and the flag for forward compatibility must be set.
    # (Source: https://www.khronos.org/opengl/wiki/OpenGL_Context#Forward_compatibility:~:text=Recommendation%3A%20You%20should%20use%20the%20forward%20compatibility%20bit%20only%20if%20you%20need%20compatibility%20with%20MacOS.%20That%20API%20requires%20the%20forward%20compatibility%20bit%20to%20create%20any%20core%20profile%20context.)
    if platform.system() == 'Linux':
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
    
    return game

def pre_draw_gameloop():
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            return 'quit'
        
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
                    
        if game.ai_opponent_enabled and game.board.turn == chess.BLACK:  # Assuming the AI plays as black.
            ai_move = game.ai_make_move()
            if ai_move:
                print(f"AI moved: {ai_move}")

def post_draw_gameloop():
    # Display endgame message if the game is over.
    game_result = game.get_game_result()
    if game_result:
        display_endgame_message(game_result)
    else:
        display_turn_indicator(game.board.turn)  # Display whose turn it is if the game is still ongoing.

    pygame.display.flip()
    pygame.time.wait(10)