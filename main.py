import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from chess_game import ChessGame, chess

AI_OPPONENT_ENABLED = False  # Set to False to disable the AI opponent
AI_OPPONENT_ELO = 1350  # elo_rating: Aim for an engine strength of the given Elo (from 0 to 4000)

# Initialize the game
game = ChessGame()
# game.engine.set_fen_position("7k/5Q2/5K2/8/8/8/8/8 b - - 0 1")
# game.board = chess.Board(game.engine.get_fen_position())

def draw_board(highlight_squares):
    # Set the background color to light brown
    glClearColor(0.82, 0.71, 0.55, 1.0)  # RGBA for light brown
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Highlight the squares if any
    if highlight_squares:
        glColor3f(0.5, 0.76, 0.82)  # A light blue color for highlighting
        glBegin(GL_QUADS)
        for square in highlight_squares:
            x, y = square
            y = 7 - y
            glVertex2fv((x, y))
            glVertex2fv((x + 1, y))
            glVertex2fv((x + 1, y + 1))
            glVertex2fv((x, y + 1))
        glEnd()

    # Draw the grid lines for the board
    glColor3f(0, 0, 0)  # Black lines for the board grid
    glBegin(GL_LINES)
    for i in range(9):
        glVertex2fv((i, 0))
        glVertex2fv((i, 8))
        glVertex2fv((0, i))
        glVertex2fv((8, i))
    glEnd()

def draw_text(text, x, y, color):
    """ Render text at the given position using Pygame and OpenGL. """
    font_size = 48
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    text_width, text_height = text_surface.get_size()
    text_data = pygame.image.tostring(text_surface, "RGBA", True)

    # Calculate the position to center the text
    centered_x = x - (text_width / 2) / 800 * 8
    centered_y = y - (text_height / 2) / 800 * 8

    glWindowPos2d(centered_x, centered_y)
    glDrawPixels(text_width, text_height, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    
def draw_pieces(board_array):
    """ Render pieces on the board using the 2D board array.
    
    `piece.value` is one of the following:
        • WHITE_PAWN = "P"
        • BLACK_PAWN = "p"
        • WHITE_KNIGHT = "N"
        • BLACK_KNIGHT = "n"
        • WHITE_BISHOP = "B"
        • BLACK_BISHOP = "b"
        • WHITE_ROOK = "R"
        • BLACK_ROOK = "r"
        • WHITE_QUEEN = "Q"
        • BLACK_QUEEN = "q"
        • WHITE_KING = "K"
        • BLACK_KING = "k"
    """
    square_size = 100
    for row in range(8):
        for col in range(8):
            piece = board_array[row][col]
            if piece:
                piece_char = piece.value
                # Determine the color of the text based on the piece's case
                color = (0, 0, 0, 255) if piece_char.islower() else (255, 255, 255, 255)
                x = (col + 0.5) * square_size  # Center in the square
                y = (7 - row + 0.5) * square_size  # Center in the square
                draw_text(piece_char, x, y, color)
                
def pixel_to_board_coords(x, y):
    return x // 100, 7 - y // 100

def board_coords_to_notation(x, y):
    return f"{chr(ord('a') + x)}{y + 1}"

def display_endgame_message(result):
    message = "Draw!" if result == "draw" else f"{result.capitalize()} wins!"
    draw_text(message, 400, 400, (255, 0, 0, 255))  # Red color for the endgame message
    
def display_turn_indicator(turn):
    indicator_text = "White's Turn" if turn == chess.WHITE else "Black's Turn"
    # Choose a visible color for the text, like blue
    draw_text(indicator_text, 400, 750, (0, 0, 255, 255))

def main():
    pygame.init()
    pygame.font.init()
    display = (800, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    # Setup orthographic projection
    glOrtho(0.0, 8, 0.0, 8, -1.0, 1.0)

    # Enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    selected_square = None  # Keep track of the selected square
    highlight_squares = None
    
    if AI_OPPONENT_ENABLED:
        game.set_ai_elo(AI_OPPONENT_ELO)
    
    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
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
                    
        if AI_OPPONENT_ENABLED and game.board.turn == chess.BLACK:  # Assuming the AI plays as black
            ai_move = game.ai_make_move()
            if ai_move:
                print(f"AI moved: {ai_move}")
                    
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # draw_board()
        draw_board(highlight_squares=highlight_squares)
        draw_pieces(game.get_2d_board_array())  # Use the 2D array for drawing pieces
        display_turn_indicator(game.board.turn)  # Display whose turn it is
        
        game_result = game.get_game_result()
        if game_result:
            display_endgame_message(game_result)
        else:
            display_turn_indicator(game.board.turn)  # Display whose turn it is if the game is still ongoing
        
        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == '__main__':
    main()