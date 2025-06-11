"""
Chess Game Logic for Matchmaking Server

This script implements chess game logic with all standard rules.
King cannot move into check or make moves that leave king in check.
"""

import json
import sys
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

class PieceType(Enum):
    PAWN = "pawn"
    ROOK = "rook" 
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"

class Color(Enum):
    WHITE = 1
    BLACK = 2

class ChessLogic:
    """Chess game logic implementation with full rules."""
    
    def __init__(self):
        self.piece_values = {
            PieceType.PAWN: 1,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.ROOK: 5,
            PieceType.QUEEN: 9,
            PieceType.KING: 100
        }
    
    def initialize_game(self):
        """Initialize a new chess game."""
        # Standard chess starting position
        board = self._create_initial_board()
        
        return {
            "board": board,
            "current_player": 1,  # White starts
            "moves_count": 0,
            "captured_pieces": {"white": [], "black": []},
            "castling_rights": {
                "white_kingside": True,
                "white_queenside": True,
                "black_kingside": True,
                "black_queenside": True
            },
            "en_passant_target": None,  # Square where en passant capture is possible
            "king_positions": {"white": (7, 4), "black": (0, 4)},
            "check_status": {"white": False, "black": False},
            "game_status": "active",  # active, check, checkmate, stalemate, draw
            "last_move": None,
            "move_history": []
        }
    
    def _create_initial_board(self):
        """Create the initial chess board setup."""
        board = [[None for _ in range(8)] for _ in range(8)]
        
        # Place pawns
        for col in range(8):
            board[1][col] = {"type": "pawn", "color": 2}  # Black pawns
            board[6][col] = {"type": "pawn", "color": 1}  # White pawns
        
        # Place other pieces
        piece_order = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        
        for col in range(8):
            board[0][col] = {"type": piece_order[col], "color": 2}  # Black pieces
            board[7][col] = {"type": piece_order[col], "color": 1}  # White pieces
        
        return board

    def validate_move(self, state, move, player_id):
        """Validate if a move is legal"""
        try:
            # Check if it's the player's turn
            if state["current_player"] != player_id:
                return False
            
            from_pos = move.get("from")
            to_pos = move.get("to")
            
            if not from_pos or not to_pos:
                return False
            
            from_row, from_col = from_pos
            to_row, to_col = to_pos
            
            # Check bounds
            if not (0 <= from_row < 8 and 0 <= from_col < 8 and 
                0 <= to_row < 8 and 0 <= to_col < 8):
                return False
            
            board = state["board"]
            
            if not board or len(board) != 8:
                return False
            
            piece = board[from_row][from_col]
            target = board[to_row][to_col]
            
            # Check if there's a piece at the starting position
            if not piece:
                return False
                
            if piece["color"] != player_id:
                return False
            
            # Capturing the king is forbidden
            if target and target["type"] == "king":
                # Capturing a king is NEVER allowed in chess - it's illegal in chess game
                return False
            
            # Check if move is valid for the piece type
            piece_move_valid = self._is_valid_piece_move(board, from_pos, to_pos, piece, state)
            
            if not piece_move_valid:
                return False
            
            # More robust check for king safety
            # This is the CRITICAL fix - we must ensure the king is safe after ANY move
            if self._would_move_leave_king_in_check(state, from_pos, to_pos, player_id):
                return False
            
            return True
                    
        except Exception as e:
            print(f"ERROR in validate_move: {e}", file=sys.stderr)
            return False

    def _would_move_leave_king_in_check(self, state, from_pos, to_pos, player_id):
        """
        Check if making this move would leave the player's king in check.
        This is the core fix for the king safety issue.
        """
        try:
            # Create a deep copy of the state
            temp_state = self._copy_state(state)
            temp_board = temp_state["board"]
            
            from_row, from_col = from_pos
            to_row, to_col = to_pos
            
            # Get the piece being moved
            moving_piece = temp_board[from_row][from_col]
            if not moving_piece:
                return True  # No piece to move - invalid
            
            # Simulate the move
            captured_piece = temp_board[to_row][to_col]
            temp_board[to_row][to_col] = moving_piece
            temp_board[from_row][from_col] = None
            
            # Update king position if the king is moving
            if moving_piece["type"] == "king":
                color_key = "white" if player_id == 1 else "black"
                temp_state["king_positions"][color_key] = (to_row, to_col)
            
            # Check if the player's king is now in check
            return self._is_king_in_check_robust(temp_state, player_id)
            
        except Exception as e:
            print(f"ERROR in _would_move_leave_king_in_check: {e}", file=sys.stderr)
            return True  # Err on the side of caution
    
    def _is_king_in_check_robust(self, state, player_id):
        """
        Robust check if the king is in check.
        This checks ALL opponent pieces to see if any can attack the king.
        """
        try:
            # Get king position
            color_key = "white" if player_id == 1 else "black"
            king_pos = state["king_positions"].get(color_key)
            
            if not king_pos or len(king_pos) != 2:
                return True  # No king position - critical error
            
            king_row, king_col = king_pos
            
            # Verify the king is actually at this position
            board = state["board"]
            king_piece = board[king_row][king_col]
            if not king_piece or king_piece["type"] != "king" or king_piece["color"] != player_id:
                # King not where expected - find it
                king_pos = self._find_king_position(board, player_id)
                if not king_pos:
                    return True  # King not found - critical error
                king_row, king_col = king_pos
                
                # Update the state with correct king position
                state["king_positions"][color_key] = king_pos
            
            opponent_id = 1 if player_id == 2 else 2
            
            # Check every opponent piece to see if it can attack the king
            for row in range(8):
                for col in range(8):
                    piece = board[row][col]
                    if piece and piece["color"] == opponent_id:
                        if self._can_piece_attack_square(board, (row, col), (king_row, king_col), piece):
                            return True
            
            return False
            
        except Exception as e:
            print(f"ERROR in _is_king_in_check_robust: {e}", file=sys.stderr)
            return True  # Err on the side of caution

    def _find_king_position(self, board, player_id):
        """Find the king's actual position on the board."""
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece["type"] == "king" and piece["color"] == player_id:
                    return (row, col)
        return None

    def _can_piece_attack_square(self, board, piece_pos, target_pos, piece):
        """
        Check if a piece can attack a target square.
        This is more comprehensive than the previous version.
        """
        piece_type = piece["type"]
        piece_color = piece["color"]
        
        from_row, from_col = piece_pos
        to_row, to_col = target_pos
        
        # Calculate differences
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        abs_row_diff = abs(row_diff)
        abs_col_diff = abs(col_diff)
        
        if piece_type == "pawn":
            # Pawns attack diagonally
            direction = -1 if piece_color == 1 else 1  # White moves up, black moves down
            return (row_diff == direction and abs_col_diff == 1)
        
        elif piece_type == "rook":
            # Rooks move in straight lines
            if from_row != to_row and from_col != to_col:
                return False
            return self._is_path_clear(board, piece_pos, target_pos)
        
        elif piece_type == "knight":
            # Knights move in L-shape
            return (abs_row_diff == 2 and abs_col_diff == 1) or (abs_row_diff == 1 and abs_col_diff == 2)
        
        elif piece_type == "bishop":
            # Bishops move diagonally
            if abs_row_diff != abs_col_diff:
                return False
            return self._is_path_clear(board, piece_pos, target_pos)
        
        elif piece_type == "queen":
            # Queens combine rook and bishop moves
            if (from_row == to_row or from_col == to_col or abs_row_diff == abs_col_diff):
                return self._is_path_clear(board, piece_pos, target_pos)
            return False
        
        elif piece_type == "king":
            # Kings attack adjacent squares
            return abs_row_diff <= 1 and abs_col_diff <= 1 and (abs_row_diff + abs_col_diff > 0)
        
        return False
    
    def _is_valid_piece_move(self, board, from_pos, to_pos, piece, state):
        """Check if move is valid for the specific piece type."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece_type = piece["type"]
        color = piece["color"]
        
        # Can't capture own piece
        target = board[to_row][to_col]
        if target and target["color"] == color:
            return False
        
        if piece_type == "pawn":
            return self._is_valid_pawn_move(board, from_pos, to_pos, color, state)
        elif piece_type == "rook":
            return self._is_valid_rook_move(board, from_pos, to_pos)
        elif piece_type == "knight":
            return self._is_valid_knight_move(from_pos, to_pos)
        elif piece_type == "bishop":
            return self._is_valid_bishop_move(board, from_pos, to_pos)
        elif piece_type == "queen":
            return self._is_valid_queen_move(board, from_pos, to_pos)
        elif piece_type == "king":
            return self._is_valid_king_move(board, from_pos, to_pos, state)
        
        return False
    
    def _is_valid_pawn_move(self, board, from_pos, to_pos, color, state):
        """Validate pawn move"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        direction = -1 if color == 1 else 1  # White moves up (-1), Black moves down (+1)
        start_row = 6 if color == 1 else 1
        
        row_diff = to_row - from_row
        col_diff = abs(to_col - from_col)
        
        target = board[to_row][to_col]
        
        # Forward move
        if col_diff == 0:
            if target:  # Can't move forward to occupied square
                return False
            
            if row_diff == direction:  # Single step
                return True
            elif row_diff == 2 * direction and from_row == start_row:  # Double step from start
                return True
            else:
                return False
        
        # Diagonal capture
        elif col_diff == 1 and row_diff == direction:
            if target and target["color"] != color:  # Regular capture
                return True
            
            # En passant
            en_passant = state.get("en_passant_target")
            if en_passant and en_passant == [to_row, to_col]:
                return True
            
            return False
        
        return False
    
    def _is_valid_rook_move(self, board, from_pos, to_pos):
        """Validate rook move."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move in straight line
        if from_row != to_row and from_col != to_col:
            return False
        
        return self._is_path_clear(board, from_pos, to_pos)
    
    def _is_valid_knight_move(self, from_pos, to_pos):
        """Validate knight move."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
    
    def _is_valid_bishop_move(self, board, from_pos, to_pos):
        """Validate bishop move."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Must move diagonally
        if abs(to_row - from_row) != abs(to_col - from_col):
            return False
        
        return self._is_path_clear(board, from_pos, to_pos)
    
    def _is_valid_queen_move(self, board, from_pos, to_pos):
        """Validate queen move."""
        return (self._is_valid_rook_move(board, from_pos, to_pos) or 
                self._is_valid_bishop_move(board, from_pos, to_pos))
    
    def _is_valid_king_move(self, board, from_pos, to_pos, state):
        """Validate king move including castling."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        # Regular king move
        if row_diff <= 1 and col_diff <= 1:
            return True
        
        # Castling
        if row_diff == 0 and col_diff == 2:
            return self._is_valid_castling(board, from_pos, to_pos, state)
        
        return False
    
    def _is_valid_castling(self, board, from_pos, to_pos, state):
        """Validate castling move."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        color = "white" if state["current_player"] == 1 else "black"
        
        # Check if king and rook haven't moved
        if to_col > from_col:  # Kingside
            if not state["castling_rights"][f"{color}_kingside"]:
                return False
            rook_col = 7
        else:  # Queenside
            if not state["castling_rights"][f"{color}_queenside"]:
                return False
            rook_col = 0
        
        # Check if path is clear
        start_col = min(from_col, rook_col) + 1
        end_col = max(from_col, rook_col)
        for col in range(start_col, end_col):
            if board[from_row][col]:
                return False
        
        # Check if king is not in check and doesn't pass through check
        for col in range(min(from_col, to_col), max(from_col, to_col) + 1):
            temp_state = self._copy_state(state)
            temp_state["king_positions"][color] = (from_row, col)
            if self._is_king_in_check_robust(temp_state, state["current_player"]):
                return False
        
        return True
    
    def _is_path_clear(self, board, from_pos, to_pos):
        """Check if path between two positions is clear."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        row_step = 0 if from_row == to_row else (1 if to_row > from_row else -1)
        col_step = 0 if from_col == to_col else (1 if to_col > from_col else -1)
        
        current_row, current_col = from_row + row_step, from_col + col_step
        
        while (current_row, current_col) != (to_row, to_col):
            if board[current_row][current_col]:
                return False
            current_row += row_step
            current_col += col_step
        
        return True
    
    def apply_move(self, state, move, player_id):
        """Apply a move to the game state."""
        new_state = self._copy_state(state)
        board = new_state["board"]
        
        from_pos = move["from"]
        to_pos = move["to"]
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = board[from_row][from_col]
        target = board[to_row][to_col]
        
        # Handle captures
        if target:
            color_key = "white" if target["color"] == 1 else "black"
            new_state["captured_pieces"][color_key].append(target)
        
        # Handle en passant capture
        if (piece["type"] == "pawn" and 
            new_state["en_passant_target"] == [to_row, to_col] and
            not target):
            # Remove captured pawn
            captured_row = to_row + (1 if player_id == 1 else -1)
            captured_pawn = board[captured_row][to_col]
            color_key = "white" if captured_pawn["color"] == 1 else "black"
            new_state["captured_pieces"][color_key].append(captured_pawn)
            board[captured_row][to_col] = None
        
        # Move piece
        board[to_row][to_col] = piece
        board[from_row][from_col] = None
        
        # Handle special moves
        self._handle_special_moves(new_state, move, piece, from_pos, to_pos)
        
        # Update game state
        new_state["current_player"] = 1 if player_id == 2 else 2
        new_state["moves_count"] += 1
        new_state["last_move"] = move
        new_state["move_history"].append(move)
        
        # Update check status
        self._update_check_status(new_state)
        
        # Update game status
        self._update_game_status(new_state)
        
        return new_state
    
    def _handle_special_moves(self, state, move, piece, from_pos, to_pos):
        """Handle castling, en passant setup, pawn promotion."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        board = state["board"]
        
        # Update castling rights
        if piece["type"] == "king":
            color = "white" if piece["color"] == 1 else "black"
            state["castling_rights"][f"{color}_kingside"] = False
            state["castling_rights"][f"{color}_queenside"] = False
            state["king_positions"][color] = to_pos
            
            # Handle castling rook move
            if abs(to_col - from_col) == 2:
                if to_col > from_col:  # Kingside
                    board[to_row][5] = board[to_row][7]
                    board[to_row][7] = None
                else:  # Queenside
                    board[to_row][3] = board[to_row][0]
                    board[to_row][0] = None
        
        elif piece["type"] == "rook":
            # Update castling rights when rook moves
            color = "white" if piece["color"] == 1 else "black"
            if from_col == 0:  # Queenside rook
                state["castling_rights"][f"{color}_queenside"] = False
            elif from_col == 7:  # Kingside rook
                state["castling_rights"][f"{color}_kingside"] = False
        
        # Set en passant target for pawn double moves
        state["en_passant_target"] = None
        if piece["type"] == "pawn" and abs(to_row - from_row) == 2:
            state["en_passant_target"] = [(from_row + to_row) // 2, from_col]
        
        # Handle pawn promotion
        if piece["type"] == "pawn":
            if (piece["color"] == 1 and to_row == 0) or (piece["color"] == 2 and to_row == 7):
                # Auto-promote to queen for simplicity
                promotion = move.get("promotion", "queen")
                board[to_row][to_col] = {"type": promotion, "color": piece["color"]}
    
    def _copy_state(self, state):
        """Create a deep copy of the game state."""
        return json.loads(json.dumps(state))
    
    def _update_check_status(self, state):
        """Update check status for both players."""
        state["check_status"]["white"] = self._is_king_in_check_robust(state, 1)
        state["check_status"]["black"] = self._is_king_in_check_robust(state, 2)
    
    def _update_game_status(self, state):
        """Update overall game status"""
        current_player = state["current_player"]
        
        # Check if the current player is in check
        is_in_check = self._is_king_in_check_robust(state, current_player)
        
        if is_in_check:
            # In check - check if there are any legal moves to escape check
            has_legal_moves = self._has_legal_moves_to_escape_check(state, current_player)
            
            if has_legal_moves:
                state["game_status"] = "check"
            else:
                state["game_status"] = "checkmate"
        else:
            # Not in check - check for stalemate
            has_moves = self._has_any_legal_moves(state, current_player)
            
            if has_moves:
                state["game_status"] = "active"
            else:
                state["game_status"] = "stalemate"

    def _has_legal_moves_to_escape_check(self, state, player_id):
        """Check if there are any moves to escape check"""
        board = state["board"]
        
        for from_row in range(8):
            for from_col in range(8):
                piece = board[from_row][from_col]
                if piece and piece["color"] == player_id:
                    for to_row in range(8):
                        for to_col in range(8):
                            # Test if this move would be legal (including king safety)
                            move = {"from": [from_row, from_col], "to": [to_row, to_col]}
                            if self.validate_move(state, move, player_id):
                                return True
        return False
    
    def _has_any_legal_moves(self, state, player_id):
        """Check if there are any legal moves (for stalemate)"""
        board = state["board"]
        
        for from_row in range(8):
            for from_col in range(8):
                piece = board[from_row][from_col]
                if piece and piece["color"] == player_id:
                    for to_row in range(8):
                        for to_col in range(8):
                            # Test if this move would be legal (including king safety)
                            move = {"from": [from_row, from_col], "to": [to_row, to_col]}
                            if self.validate_move(state, move, player_id):
                                return True
        return False
    
    def check_winner(self, state):
        """Check if there's a winner."""
        if state["game_status"] == "checkmate":
            # Winner is the opponent of current player
            return 1 if state["current_player"] == 2 else 2
        return None
    
    def is_game_over(self, state):
        """Check if the game is over."""
        return state["game_status"] in ["checkmate", "stalemate"]
    
    def is_draw(self, state):
        """Check if the game is a draw."""
        return state["game_status"] == "stalemate"


class GameLogicFactory:
    """Factory for creating game logic instances."""
    
    @staticmethod
    def create_game_logic(game_type):
        """Create and return a game logic instance based on game type."""
        if game_type == "chess":
            return ChessLogic()
        else:
            raise ValueError(f"Unknown game type: {game_type}")


def handle_request():
    """Handle incoming requests from the Node.js server."""
    input_data = sys.stdin.readline().strip()
    
    try:
        request = json.loads(input_data)
        action = request.get("action")
        game_type = request.get("game_type", "chess")
        
        game_logic = GameLogicFactory.create_game_logic(game_type)
        
        if action == "initialize":
            result = game_logic.initialize_game()
        elif action == "validate":
            state = request.get("state")
            move = request.get("move")
            player_id = request.get("player_id")
            result = {"valid": game_logic.validate_move(state, move, player_id)}
        elif action == "apply":
            state = request.get("state")
            move = request.get("move")
            player_id = request.get("player_id")
            result = game_logic.apply_move(state, move, player_id)
        elif action == "check_winner":
            state = request.get("state")
            result = {"winner": game_logic.check_winner(state)}
        elif action == "is_game_over":
            state = request.get("state")
            result = {"game_over": game_logic.is_game_over(state)}
        elif action == "is_draw":
            state = request.get("state")
            result = {"is_draw": game_logic.is_draw(state)}
        else:
            result = {"error": f"Invalid action: {action}"}
        
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    handle_request()