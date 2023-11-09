# Define the window and viewport positions and sizes.
WINDOW = {
    "width": 800,
    "height": 800,
}
WINDOW.update({"aspect_ratio": WINDOW["width"] / WINDOW["height"]})
WINDOW.update({"display": (WINDOW["width"], WINDOW["height"])})

STOCKFISH_PATH_WINDOWS = './stockfish/stockfish-windows-x86-64-avx2.exe'
STOCKFISH_PATH_LINUX = './stockfish/stockfish' # MacOS/Linux

AI_OPPONENT_DEFAULT_ENABLED = True
AI_OPPONENT_DEFAULT_ELO = 900  # Make the AI aim for an engine strength of the given Elo (i.e. from 0 to 4000).

SKIP_MAIN_MENU = False
MAIN_MENU_BACKGROUND_IMAGE = 'images/menu/3.png'
SETTINGS_MENU_BACKGROUND_IMAGE = 'images/menu/4.png'
STORE_MENU_BACKGROUND_IMAGE = 'images/menu/1.png'

CHESSBOARD_OBJECT_PATH = 'models/board/board.obj'
CHESSBOARD_TEXTURE_PATH = 'models/board/board.png'
PIECE_OBJECT_PATHS = {
    "pawn": 'models/pieces/pawn.obj',
    "rook": 'models/pieces/rook.obj',
    "knight": 'models/pieces/knight.obj',
    "bishop": 'models/pieces/bishop.obj',
    "queen": 'models/pieces/queen.obj',
    "king": 'models/pieces/king.obj'
}
PIECE_TEXTURE_PATHS = {
    "white": {
        "pawn": 'models/pieces/textures/white/pawn.png',
        "rook": 'models/pieces/textures/white/rook.png',
        "knight": 'models/pieces/textures/white/knight.png',
        "bishop": 'models/pieces/textures/white/bishop.png',
        "queen": 'models/pieces/textures/white/queen.png',
        "king": 'models/pieces/textures/white/king.png'
    },
    "black": {
        "pawn": 'models/pieces/textures/black/pawn.png',
        "rook": 'models/pieces/textures/black/rook.png',
        "knight": 'models/pieces/textures/black/knight.png',
        "bishop": 'models/pieces/textures/black/bishop.png',
        "queen": 'models/pieces/textures/black/queen.png',
        "king": 'models/pieces/textures/black/king.png'
    }
}       
SKYBOX_PATH = 'skybox/ugly'

# Credits.
developers = [
    'Jonathan Gilbert',
    'Gani Begawala',
    'Maxwell Graeser',
    'Michael Vuolo'
]
third_party_credits = """
Third-Party Resources:
- TODO: Resource 1: Description
- TODO: Resource 2: Description
"""