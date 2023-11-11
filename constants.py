# ~ Window
WINDOW = {
    "width": 1200,
    "height": 800,
}
WINDOW.update({"aspect_ratio": WINDOW["width"] / WINDOW["height"]})
WINDOW.update({"display": (WINDOW["width"], WINDOW["height"])})
FRAME_RATE = 244 # FPS

# ~ Stockfish
STOCKFISH_PATH_WINDOWS = './stockfish/stockfish-windows-x86-64-avx2.exe'
STOCKFISH_PATH_LINUX = './stockfish/stockfish' # MacOS/Linux

# ~ AI opponent
AI_OPPONENT_DEFAULT_ENABLED = False
AI_OPPONENT_DEFAULT_ELO = 900  # Make the AI aim for an engine strength of the given Elo (i.e. from 0 to 4000).

# ~ Menu
SKIP_MAIN_MENU = False
MAIN_MENU_BACKGROUND_IMAGE = 'images/menu/3.png'
SETTINGS_MENU_BACKGROUND_IMAGE = 'images/menu/4.png'
STORE_MENU_BACKGROUND_IMAGE = 'images/menu/1.png'

# ~ Pieces
PIECES = ["pawn", "rook", "knight", "bishop", "queen", "king"]
PIECE_COLORS = ["white", "black"]
PIECE_ABR_DICT = { piece: piece[0] if piece != "knight" else "n" for piece in PIECES }
PIECE_ABR_DICT.update({ v: k for k, v in PIECE_ABR_DICT.items() })

# ~ Objects and textures
MODEL_TEMPLATE = { "obj": None, "texture": None, "vao": None, "vbo": None, "model_matrix": None }
CHESSBOARD_OBJECT_PATH = 'models/board/board.obj'
CHESSBOARD_TEXTURE_PATH = 'models/board/board.png'
SQUARE_OBJECT_PATH = 'models/square.obj'
HIGHLIGHTED_SQUARE_TEXTURE_PATH = 'models/highlighted_square.png'
SELECTED_SQUARE_TEXTURE_PATH = 'models/selected_square.png'
VALID_MOVES_SQUARE_TEXTURE_PATH = 'models/valid_moves_square.png'
PIECE_OBJECT_PATHS = { piece: f'models/pieces/{piece}/{piece}.obj' for piece in PIECES }
PIECE_TEXTURE_PATHS = { color: { piece: f'models/pieces/{piece}/{color}.png' for piece in PIECES } for color in PIECE_COLORS }
SKYBOX_PATH = 'skybox/set_in_space'

# ~ Camera
CAMERA_MOUSE_DRAG_SENSITIVITY = 0.1
CAMERA_DEFAULT_YAW = {
    "white": 90,
    "black": 360 - 90
}
CAMERA_DEFAULT_PITCH = 25 # i.e. 1 := top-down, 90 := side-view
CAMERA_MIN_DISTANCE = 0.75
CAMERA_MAX_DISTANCE = 5
CAMERA_ZOOM_SCROLL_SENSITIVITY = 0.25

# ~ Camera animation
CAMERA_DEFAULT_ANIMATION_SPEED = 10
CAMERA_USE_INTRO_ANIMATION = True
CAMERA_ANIMATE_AFTER_MOVE = True

MOUSE_POSITION_DELTA = 2.1 # Delta that determines a click, in pixels

# Credits.
developers = [
    'Jonathan Gilbert',
    'Gani Begawala',
    'Maxwell Graeser',
    'Michael Vuolo'
]
third_party_credits = """
Third-Party Resources:
- skybox.blockadelabs.com
"""