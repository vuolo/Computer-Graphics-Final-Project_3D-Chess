# Third-party imports.
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pygame
import chess
    
def setup_2d_graphics():
    glOrtho(0.0, 8, 0.0, 8, -1.0, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def draw_board(highlight_squares=None):
    # Set the background color to light brown
    glClearColor(0.82, 0.71, 0.55, 1.0)  # RGBA for light brown
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Set the color to black for the grid lines
    glColor3f(0.0, 0.0, 0.0)  # RGB for black

    # Draw the grid lines
    glBegin(GL_LINES)
    for i in range(9):  # There are 8 squares + 1 to close the grid
        # Vertical lines
        glVertex2f(i, 0)
        glVertex2f(i, 8)
        
        # Horizontal lines
        glVertex2f(0, i)
        glVertex2f(8, i)
    glEnd()

    # Highlight the squares (if any).
    if highlight_squares:
        glColor3f(0.5, 0.76, 0.82)  # A light blue color for highlighting.
        glBegin(GL_QUADS)
        for square in highlight_squares:
            x, y = square
            y = 7 - y  # Flip the y-coordinate since OpenGL's origin is at the bottom-left
            glVertex2f(x, y)
            glVertex2f(x + 1, y)
            glVertex2f(x + 1, y + 1)
            glVertex2f(x, y + 1)
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