from typing import Tuple

def notation_to_coords(square_notation: str) -> Tuple[int, int]:
    rank = int(square_notation[1]) - 1  # Convert '1'-'8' to 0-7
    file = ord(square_notation[0]) - ord('a')  # Convert 'a'-'h' to 0-7
    return (file, rank)