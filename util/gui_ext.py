# Third-party imports.
import tkinter as tk

# Local application imports.
from constants import WINDOW, ENABLE_GUI, GUI_WIDTH, GUI_HEIGHT
from game.chess_game import ChessGame
from util.guiV3 import SimpleGUI

# Define an add_text method for the SimpleGUI class
def __SimpleGUI__add_text(self, name, text, **kwargs):
    """
    Adds a text widget to the GUI.

    Args:
        name (str): The name of the widget.
        text (str): The text to display.
        **kwargs: Additional keyword arguments to pass to the tkinter Label constructor.
    """
    self.widgets[name] = tk.Label(self.root, text=text, **kwargs)
    self.widgets[name].pack()
    return self.widgets[name]

def __SimpleGUI__hide(self):
    self.root.withdraw()

def __SimpleGUI__show(self):
    self.root.deiconify()

# Apply our SimpleGUI extensions.
SimpleGUI.widgets = {}
SimpleGUI.game_state = {
    "whos_turn": None,
}
SimpleGUI.add_text = __SimpleGUI__add_text
SimpleGUI.hide = __SimpleGUI__hide
SimpleGUI.show = __SimpleGUI__show

def setup_gui(game: ChessGame):
    gui = SimpleGUI("")
    gui.hide()
    resize_gui(gui)
    return gui

def prepare_gui(gui, game: ChessGame):
    auto_position_gui(gui)
    
    # Add a plaintext title drawn to the top of the gui with a padding of 20 pixels.
    gui.add_text("title", "3D Chess HUD", font=("Helvetica", 16, "bold"), anchor="n", pady=20)
    
    # Add a label to placehold the current turn.
    gui.add_text("whos_turn", "Turn: ", font=("Helvetica", 12, "bold"), anchor="w", pady=5)
    
def update_gui(gui, game: ChessGame):
    # If the gui is hidden, show it.
    if not gui.root.winfo_viewable() and ENABLE_GUI:
        gui.show()
    elif not ENABLE_GUI:
        gui.hide()
        return
        
    # If the gui is not the correct size, resize it.
    if gui.root.winfo_width() != GUI_WIDTH or gui.root.winfo_height() != GUI_HEIGHT:
        resize_gui(gui)
        
    # If the gui is not in the correct position, reposition it.
    x, y = calc_gui_position(gui)
    if gui.root.winfo_x() != x or gui.root.winfo_y() != y:
        auto_position_gui(gui)
    
    # ~ Game state
    # Display whose turn it is.
    whos_turn = game.get_whos_turn()
    if whos_turn != gui.game_state["whos_turn"]:
        # Update the gui.
        gui.game_state["whos_turn"] = whos_turn
        gui.widgets["whos_turn"].config(text=f"Turn: {whos_turn.capitalize()}")
    
    # Update the gui.
    gui.root.update_idletasks()
        

def resize_gui(gui, width=GUI_WIDTH, height=GUI_HEIGHT):
    # 1. Set the width to 1px less than the desired width to force update the new dimensions (idk why, but this is a functioning workaround).
    gui.root.geometry(f"{width - 1}x{height}")
    gui.root.update_idletasks()
    
    # 2. Set the width to the desired width.
    gui.root.geometry(f"{width}x{height}")
    gui.root.update_idletasks()
    
    # print(f"GUI size set to ({gui.root.winfo_width()}, {gui.root.winfo_height()})")

def auto_position_gui(gui):
    x, y = calc_gui_position(gui)
    gui.root.geometry(f"{gui.root.winfo_width()}x{gui.root.winfo_height()}+{x}+{y}")
    # print(f"GUI position set to ({x}, {y})")
    
def calc_gui_position(gui):
    GUI_MARGIN_RIGHT = 20  # px
    TITLE_BAR_HEIGHT = 28  # px
    
    x = (gui.root.winfo_screenwidth() - WINDOW["width"]) // 2 - gui.root.winfo_width() - GUI_MARGIN_RIGHT
    y = (gui.root.winfo_screenheight() - WINDOW["height"]) // 2 - TITLE_BAR_HEIGHT
    
    return x, y