# Third-party imports.
from typing import Optional
from pygame.locals import *
import pygame
import chess

# Local application imports.
from constants import WINDOW
from game.chess_game import ChessGame
from graphics.graphics_2d import pixel_to_board_coords, board_coords_to_notation, display_endgame_message, display_turn_indicator

# Global variables.
game: Optional['ChessGame'] = None
clock: Optional['pygame.time.Clock'] = None
selected_square: Optional[str] = None  # Keep track of the user-selected square.
highlight_squares: Optional[list[tuple[int, int]]] = None # Displays highlighted squares that the user can move to.

def gameplay_setup():
    global game, clock
    game = ChessGame()
    
    # Initialize pygame.
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("3D Chess")
    clock = pygame.time.Clock()
    
    return game

def pre_draw_gameloop():
    global game, clock, selected_square, highlight_squares
    clock.tick(100)
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
    global game
    game_result = game.get_game_result()
    # TODO: Fix text render whilst using 3d graphics. (pyOpenGL)
    # if game_result: display_endgame_message(game_result)
    # else: display_turn_indicator(game.board.turn)  # Display whose turn it is if the game is still ongoing.

    # Draw everything to the screen.
    pygame.display.flip()
    pygame.time.wait(10)