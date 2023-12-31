# Third-party imports.
from typing import List, Tuple, Optional
from pygame.locals import *
import numpy as np
import pygame
import chess
import math

# Local application imports.
from constants import WINDOW, FRAME_RATE, PIECE_ANIMATION_DURATION, CAMERA_DEFAULT_YAW, CAMERA_DEFAULT_PITCH, CAMERA_ANIMATE_AFTER_MOVE, CAMERA_ANIMATE_AFTER_MOVE_DELAY, ROTATE_CAMERA_EVENT, DISABLE_INVALID_MOVE_SQUARE_EVENT, INVALID_MOVE_SQUARE_FLASH_DURATION, DELAYED_MOVE_SOUND_EVENT, RESET_GAME_EVENT
from game.chess_game import ChessGame
# from graphics.graphics_2d import pixel_to_board_coords, board_coords_to_notation, display_endgame_message, display_turn_indicator
from graphics.graphics_3d import handle_mouse_events, create_piece_animation, start_camera_rotation_animation #, get_ray_from_mouse, intersect_ray_with_plane, determine_square_from_intersection
from util.game import notation_to_coords
from util.guiV3 import SimpleGUI
from util.gui_ext import setup_gui

pygame.mixer.init()

# Global variables.
game: Optional['ChessGame'] = None
gui: Optional['SimpleGUI'] = None
clock: Optional['pygame.time.Clock'] = None
selected_square: Optional[str] = None  # Keep track of the user-selected square.
valid_move_squares: Optional[List[Tuple[int, int]]] = None # Displays highlighted squares that the user can move to.
highlighted_square: Tuple[int, int] = notation_to_coords('d2')  # Currently highlighted square coordinates (file, rank)
last_highlighted_white: Tuple[int, int] = notation_to_coords('d2')
last_highlighted_black: Tuple[int, int] = notation_to_coords('e7')
is_selected: bool = False  # State to track if a square is selected
end_move_sound = pygame.mixer.Sound('./sounds/end_move.mp3')
start_move_sound = pygame.mixer.Sound('./sounds/start_move.mp3')
capture_sound = pygame.mixer.Sound('./sounds/capture.mp3')
side_to_rotate_to = None
invalid_move_square = None

# ~ Main
def gameplay_setup(game_settings=None):
    global game, clock, highlighted_square, last_highlighted_white, last_highlighted_black
    game = ChessGame(game_settings)
    gui = setup_gui(game)
    
    # Initialize pygame.
    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("3D Chess")
    clock = pygame.time.Clock()
    
    # Set the initial highlighted square based on the player's turn
    highlighted_square = last_highlighted_white if game.get_whos_turn() == "white" else last_highlighted_black
    
    return game, gui

# ~ Game loop
def pre_draw_gameloop():
    global clock, highlighted_square, selected_square, valid_move_squares, is_selected, invalid_move_square
    clock.tick(FRAME_RATE)
    events = pygame.event.get()
    
    # Check if awaiting a successful pawn promotion.
    pawn_promotion_selection = game.get_pawn_promotion_selection()
    if pawn_promotion_selection:
        process_move(highlighted_square, pawn_promotion_selection)
        game.set_pawn_promotion_selection(None)
        
    # Check if the game is over (has a winner).
    winner = game.get_winner()
    if winner:
        print(f"Game Over! {winner.capitalize()} wins!")
        return 'game_over'
    
    for event in events:
        if event.type == pygame.QUIT:
            return 'quit'
        
        # Use the keyboard to move the highlighted square (WASD/↑←↓→ for movement, SPACEBAR/ENTER for selection, BACKSPACE for undo selection).
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP: highlighted_square = move_highlighted_square('up')
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN: highlighted_square = move_highlighted_square('down')
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT: highlighted_square = move_highlighted_square('left')
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT: highlighted_square = move_highlighted_square('right')
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if is_selected:
                    result = process_move(highlighted_square, pawn_promotion_selection)
                    if result == 'needs_pawn_promotion': return result
                else: select_square(highlighted_square)
                is_selected = not is_selected
            elif event.key == pygame.K_BACKSPACE:
                selected_square = None
                valid_move_squares = None
                is_selected = False
                print("Selected square cleared.")
            elif event.key == pygame.K_ESCAPE:
                return 'pause'
                
        elif event.type == ROTATE_CAMERA_EVENT:
            start_camera_rotation_animation(CAMERA_DEFAULT_YAW[side_to_rotate_to], CAMERA_DEFAULT_PITCH)
            
        elif event.type == DISABLE_INVALID_MOVE_SQUARE_EVENT:
            invalid_move_square = None

        elif event.type == DELAYED_MOVE_SOUND_EVENT:
            end_move_sound.play()
            
        elif event.type == RESET_GAME_EVENT:
            highlighted_square = notation_to_coords('d2')
            last_highlighted_white = notation_to_coords('d2')
            last_highlighted_black = notation_to_coords('e7')
            selected_square = False
            is_selected = False
            invalid_move_square = None
                
    handle_mouse_events(events)
    attempt_move_ai_opponent()
    
    return { 'highlighted_square': highlighted_square, 'selected_square': selected_square, 'valid_move_squares': valid_move_squares, 'invalid_move_square': invalid_move_square }

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

def rotate_camera_to_side(side):
    global side_to_rotate_to
    side_to_rotate_to = side
    pygame.time.set_timer(ROTATE_CAMERA_EVENT, CAMERA_ANIMATE_AFTER_MOVE_DELAY, 1)
    
def set_invalid_move_square(square):
    global invalid_move_square
    invalid_move_square = square
    pygame.time.set_timer(DISABLE_INVALID_MOVE_SQUARE_EVENT, INVALID_MOVE_SQUARE_FLASH_DURATION, 1)

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
def handle_mouse_click(x, y): 
    # print(f"Accessed handle_mouse_click with: {x}, {y}")
    pass

# ~ Movement
def move_highlighted_square(direction: str) -> Tuple[int, int]:
    global highlighted_square, last_highlighted_white, last_highlighted_black
    file, rank = highlighted_square
    turn = game.get_whos_turn()

    # Invert controls for black (since they are playing on the other side).
    if not game.get_ai_opponent_enabled() and turn == "black":
        if direction == 'up': rank -= 1
        elif direction == 'down': rank += 1
        elif direction == 'left': file += 1
        elif direction == 'right': file -= 1
    else:
        if direction == 'up': rank += 1
        elif direction == 'down': rank -= 1
        elif direction == 'left': file -= 1
        elif direction == 'right': file += 1
        
    # Ensure the new position is within the board boundaries.
    file = max(0, min(7, file))
    rank = max(0, min(7, rank))

    if highlighted_square != (file, rank): print(f"Highlighted square: {chess.SQUARE_NAMES[rank * 8 + file]}")

    return (file, rank)
    
def process_move(target_square: Tuple[int, int], pawn_promotion_selection=None):
    global selected_square, valid_move_squares
    
    if selected_square:
        from_square_name = chess.SQUARE_NAMES[selected_square[1] * 8 + selected_square[0]]
        to_square_name = chess.SQUARE_NAMES[target_square[1] * 8 + target_square[0]]
        move = f"{from_square_name}{to_square_name}{pawn_promotion_selection if pawn_promotion_selection else ''}"

        # Capture the piece object before making the move
        piece = game.board.piece_at(chess.parse_square(from_square_name))
        piece_after = game.board.piece_at(chess.parse_square(to_square_name))
        piece_symbol = piece.symbol() if piece else None
       
        result = game.make_move(move)
        if result == 'needs_pawn_promotion': return result
        elif result == True:
            # Use the captured piece object for the animation
            start_time = pygame.time.get_ticks() / 1000.0
            create_piece_animation(from_square_name, to_square_name, piece_symbol, start_time, PIECE_ANIMATION_DURATION)
            post_successful_move_processing(move, target_square)
            if piece and piece_after and piece.color != piece_after.color:
                capture_sound.play()

        elif result == False:
            print(f"Invalid move: {move}")
            set_invalid_move_square(target_square)
    
    selected_square = None
    valid_move_squares = None
    
def post_successful_move_processing(move=None, target_square=None):
    global is_selected, highlighted_square, last_highlighted_white, last_highlighted_black
    
    print(f"~ You moved: {move}")
    is_selected = False
    game.display_whos_turn()
    play_move_sound()
    
    if game.get_ai_opponent_enabled(): return
    if CAMERA_ANIMATE_AFTER_MOVE: rotate_camera_to_side(game.get_whos_turn())
    
    # Update the last highlighted square for the side that made the move and restore the highlighted square for the other side.
    if game.get_whos_turn() == "black":
        last_highlighted_white = target_square
        highlighted_square = last_highlighted_black
    else:
        last_highlighted_black = target_square
        highlighted_square = last_highlighted_white

def play_move_sound():
    start_move_sound.play()
    pygame.time.set_timer(DELAYED_MOVE_SOUND_EVENT, int(math.floor(PIECE_ANIMATION_DURATION * 1000)), 1)

def select_square(square_to_select: Tuple[int, int]):
    global selected_square, valid_move_squares, highlighted_square, last_highlighted_white, last_highlighted_black
    
    # Convert the highlighted square to the standard chess square notation.
    from_square_index = square_to_select[1] * 8 + square_to_select[0]
    from_square_name = chess.SQUARE_NAMES[from_square_index]
    
    # Retrieve the piece at the selected square
    piece = game.board.piece_at(chess.parse_square(from_square_name))
    
    # Retrieve the color of the piece
    piece_color = None if not piece else "white" if piece.color == chess.WHITE else "black"
    
    # Check if the piece color matches the current player's turn.
    if piece is not None and game.get_whos_turn() == piece_color:
        selected_square = square_to_select
        valid_moves = game.get_valid_moves(from_square_name)
        valid_move_squares = [(file, rank) for file, rank in valid_moves]
        print(f"Selected square: {from_square_name}")
    else:
        print(f"Cannot select this square. {'Not your piece' if piece else 'Select a piece'}.")
        set_invalid_move_square(square_to_select)
    
    # Save the highlighted square for the current player.
    if game.get_whos_turn() == "white": last_highlighted_white = square_to_select
    else: last_highlighted_black = square_to_select
    
# ~ AI opponent
def attempt_move_ai_opponent():
    if game.ai_opponent_enabled and game.board.turn == chess.BLACK:
        play_move_sound()
        ai_move = game.make_ai_move()
        if ai_move:
            # Parse the move to get from and to squares
            from_square = chess.SQUARE_NAMES[chess.parse_square(ai_move[:2])]
            to_square = chess.SQUARE_NAMES[chess.parse_square(ai_move[2:4])]
            # Get the piece symbol
            piece = game.board.piece_at(chess.parse_square(to_square))
            piece_symbol = piece.symbol() if piece else None

            # # Create the animation
            start_time = pygame.time.get_ticks() / 1000.0
            create_piece_animation(from_square, to_square, piece_symbol, start_time, PIECE_ANIMATION_DURATION)

            print(f"~ AI moved: {ai_move}")
            game.display_whos_turn()
