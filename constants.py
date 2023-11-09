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

SKYBOX_PATH = 'skybox/set_in_space'
# TODO: Add other constants like colors, sizes, etc.
