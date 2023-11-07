import chess
from stockfish import Stockfish
import platform

class ChessGame:
    def __init__(self):
        # Automatically detect the OS and set the appropriate path for Stockfish
        if platform.system() == 'Windows':
            stockfish_path = './stockfish/stockfish-windows-x86-64-avx2.exe'
        else:
            stockfish_path = './stockfish/stockfish'

        self.engine = Stockfish(path=stockfish_path, parameters={
                "Threads": 2, 
                "Minimum Thinking Time": 30
            })
        self.board = chess.Board()
        
    def set_ai_elo(self, elo):
        self.engine.set_skill_level(elo)
    
    def ai_make_move(self):
        best_move = self.engine.get_best_move()
        if best_move:
            self.make_move(best_move)
            return best_move
        return None
    
    def set_position(self, moves):
        # Update both the stockfish engine and python-chess board
        self.engine.set_position(moves)
        self.board = chess.Board()
        for move in moves:
            self.board.push(chess.Move.from_uci(move))

    def make_move(self, move):
        if self.engine.is_move_correct(move):
            self.engine.make_moves_from_current_position([move])
            # Update the python-chess board
            self.board.push(chess.Move.from_uci(move))
            return True, move
        return False, None

    def get_board_visual(self):
        return self.engine.get_board_visual()
    
    def get_2d_board_array(self):
        ''' Returns a 2d array representation of the board '''
        board = []
        for rank in range(1, 9):  # 1 to 8
            row = []
            for file in range(8):  # 0 to 7, corresponding to 'a' to 'h'
                square = f'{chr(97 + file)}{rank}'  # From 'a1' to 'h8'
                row.append(self.engine.get_what_is_on_square(square))
            board.insert(0, row)  # Insert rows at the beginning to start from 'a1'
        return board
    
    def get_game_result(self):
        '''Check the game result using python-chess library'''
        if self.board.is_checkmate():
            return "white" if self.board.turn == chess.BLACK else "black"
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or \
             self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition() or \
             self.board.can_claim_draw():
            return "draw"
        return None  # If none of the above, the game is still ongoing

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