# Third-party imports.
from typing import List, Tuple, Optional
from pygame.locals import *
import numpy as np
import pygame
import chess

# Local application imports.
from constants import WINDOW
from game.chess_game import ChessGame
# from graphics.graphics_2d import pixel_to_board_coords, board_coords_to_notation, display_endgame_message, display_turn_indicator
from graphics.graphics_3d import handle_mouse_events#, get_ray_from_mouse, intersect_ray_with_plane, determine_square_from_intersection

# Global variables.
game: Optional['ChessGame'] = None
clock: Optional['pygame.time.Clock'] = None
selected_square: Optional[str] = None  # Keep track of the user-selected square.
valid_move_squares: Optional[List[Tuple[int, int]]] = None # Displays highlighted squares that the user can move to.
hovered_square: Tuple[int, int] = (0, 0)  # Hovered square coordinates (file, rank)
is_selected: bool = False  # State to track if a square is selected

# ~ Main
def gameplay_setup():
    global game, clock
    game = ChessGame()
    
    # Initialize pygame.
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("3D Chess")
    clock = pygame.time.Clock()
    
    return game

# ~ Game loop
def pre_draw_gameloop():
    global clock, hovered_square, is_selected
    clock.tick(100)
    events = pygame.event.get()
    
    for event in events:
        if event.type == pygame.QUIT:
            return 'quit'
        
        # Use the keyboard to move the hovered square (WASD/↑←↓→ for movement, SPACEBAR for selection).
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP: hovered_square = move_hovered_square('up')
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN: hovered_square = move_hovered_square('down')
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT: hovered_square = move_hovered_square('left')
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT: hovered_square = move_hovered_square('right')
            elif event.key == pygame.K_SPACE:
                if is_selected: process_move(hovered_square)
                else: select_square(hovered_square)
                is_selected = not is_selected
            elif event.key == pygame.K_BACKSPACE:
                selected_square = None
                valid_move_squares = None
                is_selected = False
                print("Selected square cleared.")
                
    handle_mouse_events(events)
    # TODO: Handle mouse click movement for 3D graphics (needs raycasting).
    # handle_mouse_click(events)
    
    attempt_move_ai_opponent()

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

# ~ Click detection (for 2D graphics)
# def handle_mouse_click_2d(events):
#     global selected_square, valid_move_squares
#     for event in events:
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             x, y = pygame.mouse.get_pos()
#             board_x, board_y = pixel_to_board_coords(x, y)
#             clicked_square = board_coords_to_notation(board_x, board_y)
#             if selected_square and selected_square != clicked_square: process_move(clicked_square)
#             else: select_square(clicked_square)

# ~ TODO: Click detection (for 3D graphics)
# def handle_mouse_click(events):
#     global selected_square, valid_move_squares
#     for event in events:
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             x, y = pygame.mouse.get_pos()
#             ray_origin, ray_direction = get_ray_from_mouse(x, y)
#             print("~ Mouse Clicked:")
#             print(f"Ray Origin: {ray_origin}, Ray Direction: {ray_direction}")  # Logging

#             plane_origin = np.array([0, 0, 0])  # The chessboard is centered at the origin.
#             plane_normal = np.array([0, 1, -3])  # The chessboard plane is horizontal.
#             intersection_point = intersect_ray_with_plane(ray_origin, ray_direction, plane_origin, plane_normal)

#             if intersection_point is not None:
#                 print(f"Intersection Point: {intersection_point}")  # Logging
#                 clicked_square = determine_square_from_intersection(intersection_point)
#                 print(f"Clicked Square: {clicked_square}")  # Logging
#                 if selected_square and selected_square != clicked_square: process_move(clicked_square)
#                 else: select_square(clicked_square)
#             else:
#                 print("No intersection with the chessboard plane.")  # Logging

# ~ Movement
def move_hovered_square(direction: str) -> Tuple[int, int]:
    file, rank = hovered_square
    
    if direction == 'up' and rank < 7: rank += 1
    elif direction == 'down' and rank > 0: rank -= 1
    elif direction == 'left' and file > 0: file -= 1
    elif direction == 'right' and file < 7: file += 1

    print(f"Hovered square: {chess.SQUARE_NAMES[rank * 8 + file]}")

    return (file, rank)

def process_move(target_square: Tuple[int, int]):
    """ Process a move from the currently selected square to the specified square. """
    global selected_square, valid_move_squares, hovered_square, is_selected
    
    if selected_square:
        from_square = chess.SQUARE_NAMES[selected_square[1] * 8 + selected_square[0]]
        to_square = chess.SQUARE_NAMES[target_square[1] * 8 + target_square[0]]
        move = f"{from_square}{to_square}"
        if game.make_move(move):
            print(f"~ You moved: {move}")
            is_selected = False
            hovered_square = target_square  # Move hovered square to the last moved position
        else:
            print(f"Invalid move: {move}")
    
    selected_square = None
    valid_move_squares = None

def select_square(square_to_select: Tuple[int, int]):
    global selected_square, valid_move_squares, hovered_square
    selected_square = square_to_select
    
    # Get valid moves and convert to board coordinates.
    from_square = chess.SQUARE_NAMES[selected_square[1] * 8 + selected_square[0]]
    valid_moves = game.get_valid_moves(from_square)
    valid_move_squares = [(file, rank) for file, rank in valid_moves]
    
    print(f"Selected square: {chess.SQUARE_NAMES[square_to_select[1] * 8 + square_to_select[0]]}")

# ~ AI opponent
def attempt_move_ai_opponent():
    if game.ai_opponent_enabled and game.board.turn == chess.BLACK:
        ai_move = game.make_ai_move()
        if ai_move: print(f"~ AI moved: {ai_move}")