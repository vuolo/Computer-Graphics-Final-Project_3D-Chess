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

PIECES = ["pawn", "rook", "knight", "bishop", "queen", "king"]
PIECE_COLORS = ["white", "black"]
PIECE_ABR_DICT = { piece: piece[0] if piece != "knight" else "n" for piece in PIECES }
PIECE_ABR_DICT.update({ v: k for k, v in PIECE_ABR_DICT.items() })

MODEL_TEMPLATE = { "obj": None, "texture": None, "vao": None, "vbo": None, "model_matrix": None }
CHESSBOARD_OBJECT_PATH = 'models/board/board.obj'
CHESSBOARD_TEXTURE_PATH = 'models/board/board.png'
PIECE_OBJECT_PATHS = { piece: f'models/pieces/{piece}/{piece}.obj' for piece in PIECES }
PIECE_TEXTURE_PATHS = { color: { piece: f'models/pieces/{piece}/{color}.png' for piece in PIECES } for color in PIECE_COLORS }
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