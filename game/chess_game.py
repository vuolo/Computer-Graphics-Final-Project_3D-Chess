# Third-party imports.
import chess
from stockfish import Stockfish
import platform

# Local application imports.
from constants import STOCKFISH_PATH_WINDOWS, STOCKFISH_PATH_LINUX, AI_OPPONENT_DEFAULT_ENABLED, AI_OPPONENT_DEFAULT_ELO, DEFAULT_SELECTION, PIECE_ABR_DICT

class ChessGame:
    def __init__(self, game_settings=None):
        # Automatically detect the OS and set the appropriate path for Stockfish.
        if platform.system() == 'Windows': stockfish_path = STOCKFISH_PATH_WINDOWS
        else: stockfish_path = STOCKFISH_PATH_LINUX

        # Initialize the Stockfish engine and python-chess board.
        self.engine = Stockfish(path=stockfish_path, parameters={
                "Threads": 2, 
                "Minimum Thinking Time": 30
            }) # (using the `stockfish` library)
        self.board = chess.Board() # (using the `python-chess` library)
        
        # AI opponent settings.
        if game_settings:
            self.ai_opponent_enabled = game_settings["ai_opponent_enabled"]
            self.engine.set_skill_level(game_settings["ai_elo"])
            self.piece_selection = game_settings["selected_piece"]
            self.board_selection = game_settings["selected_board"]
        else:
            self.ai_opponent_enabled = AI_OPPONENT_DEFAULT_ENABLED
            self.engine.set_skill_level(AI_OPPONENT_DEFAULT_ELO)
            self.piece_selection = DEFAULT_SELECTION
            self.board_selection = DEFAULT_SELECTION
        
        # Menu settings.
        self.go_to_main_menu = False
        
        # Promote pawn settings.
        self.pawn_promotion_selection = None
        
    # ~ Settings
    def get_settings(self):
        return {
            "ai_opponent_enabled": self.get_ai_opponent_enabled(),
            "ai_elo": self.get_ai_elo(),
            "selected_piece": self.get_piece_selection(),
            "selected board": self.get_board_selection()
        }
        
    # ~ Pawn Promotion
    def set_pawn_promotion_selection(self, piece):
        self.pawn_promotion_selection = PIECE_ABR_DICT[piece.lower()] if piece else None
        
    def get_pawn_promotion_selection(self):
        return self.pawn_promotion_selection
    
    # ~ Piece Selection
    def set_piece_selection(self, piece_selection):
        self.piece_selection = piece_selection
        
    def get_piece_selection(self):
        return self.piece_selection
       
    # ~ Board Selection
    def set_board_selection(self, board_selection):
        self.board_selection = board_selection
        
    def get_board_selection(self):
        return self.board_selection
        
    # ~ Menu
    def set_go_to_main_menu(self, go_to_main_menu):
        self.go_to_main_menu = go_to_main_menu
        
    def get_go_to_main_menu(self):
        return self.go_to_main_menu

    # ~ AI opponent
    def set_ai_elo(self, elo):
        self.engine.set_skill_level(elo)
        
    def get_ai_elo(self):
        return self.engine.get_parameters()["Skill Level"]
    
    def set_ai_opponent_enabled(self, enabled):
        self.ai_opponent_enabled = enabled
        
    def get_ai_opponent_enabled(self):
        return self.ai_opponent_enabled
    
    def make_ai_move(self):
        best_move = self.engine.get_best_move()
        if best_move:
            self.make_move(best_move)
            return best_move
        
        return None
    
    # ~ Game State
    def set_position(self, moves):
        # Update both the `stockfish` engine and `python-chess` board.
        self.engine.set_position(moves)
        self.board = chess.Board()
        for move in moves: self.board.push(chess.Move.from_uci(move))

    def make_move(self, move):
        if not self.engine.is_move_correct(move):
            # Check if the move needs pawn promotion.
            try:
                if chess.Move.from_uci(move + 'q') in self.board.legal_moves:
                    if self.pawn_promotion_selection:
                        move += self.pawn_promotion_selection
                        self.pawn_promotion_selection = None
                    else: return 'needs_pawn_promotion' # Ask the user to pick from [q, r, b, n] (queen, rook, bishop, knight).
            except ValueError:
                pass
            
            return False
        
        # Update both the `stockfish` engine and `python-chess` board.
        self.engine.make_moves_from_current_position([move])
        self.board.push(chess.Move.from_uci(move))
        
        return True
    
    def get_game_result(self):
        '''Check the game result using python-chess library'''
        if self.board.is_checkmate(): return "white" if self.board.turn == chess.BLACK else "black"
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or \
             self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition() or \
             self.board.can_claim_draw(): return "draw"
             
        return None  # If none of the above, the game is still ongoing.
    
    def get_whos_turn(self):
        return "white" if self.board.turn == chess.WHITE else "black"
    
    def display_whos_turn(self):
        print("[White's Turn]" if self.board.turn == chess.WHITE else "[Black's Turn]")

    # ~ Board
    def get_board_visual(self):
        return self.engine.get_board_visual()
    
    def get_2d_board_array(self):
            ''' 
            Returns a 2d array representation of the board.
            
            Example:
            >>> game = ChessGame()
            >>> game.get_2d_board_array()
               a    b    c    d    e    f    g    h
            [['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],  8
             ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],  7
             [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],  6
             [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],  5
             [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],  4
             [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],  3
             ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],  2
             ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']]  1
            '''
            board = []
            for rank in range(1, 9):  # 1 to 8 ("ranks" are rows)
                row = []
                for file in range(8):  # 0 to 7, corresponding to 'a' to 'h' ("files" are columns)
                    square = f'{chr(97 + file)}{rank}'  # From 'a1' to 'h8'
                    row.append(self.engine.get_what_is_on_square(square))
                    
                board.insert(0, row)  # Insert rows at the beginning to start from 'a1'
                
            return board
    
    def get_valid_moves(self, square):
        ''' Returns a list of valid moves for the piece on the given square.
        The moves will be in the format of coordinate pairs. '''
        
        moves = []
        try:
            piece = self.board.piece_at(chess.parse_square(square))
            if piece:  # If there is a piece on the given square
                for move in self.board.legal_moves:
                    if move.from_square == chess.parse_square(square):
                        moves.append((chess.square_file(move.to_square), chess.square_rank(move.to_square)))
        except ValueError:
            pass
        return moves
    
    def get_winner(self):
        '''Check the game's winner or if it's a draw using python-chess library'''
        if self.board.is_checkmate():
            return "white" if self.board.turn == chess.BLACK else "black"
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or \
            self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition() or \
            self.board.can_claim_draw():
            return "draw"
            
        return None  # If none of the above, the game is still ongoing.

    # ~ Cleanup
    def __del__(self):
        ''' Properly terminate the Stockfish engine process when the ChessGame object is deleted '''
        self.engine.__del__()

if __name__ == "__main__":
    # Example usage:
    game = ChessGame()
    success, move_made = game.make_move("e2e4")
    print("Move made:", move_made)
    print(game.get_board_visual())
    print(game.get_2d_board_array())
    
    # Check the game result
    result = game.get_game_result()
    if result:
        print(f"The game is over: {result}")

    # Cleanup.
    del game