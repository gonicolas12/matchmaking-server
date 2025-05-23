"""
Game Logic for Matchmaking Server

This script implements the game logic for different board games.
It is called by the Node.js server through python-shell.
"""

import json
import sys

class TicTacToeLogic:
    """Tic-Tac-Toe game logic implementation."""
    
    def initialize_game(self):
        """Initialize a new game of Tic-Tac-Toe."""
        return {
            "board": [None, None, None, None, None, None, None, None, None],
            "current_player": 1,  # Player 1 starts
            "moves_count": 0
        }
    
    def validate_move(self, state, move, player_id):
        """Validate if a move is legal."""
        # Check if it's the player's turn
        if state["current_player"] != player_id:
            return False
        
        # Check if the position is valid
        position = move.get("position")
        if position is None or position < 0 or position > 8:
            return False
        
        # Check if the position is empty
        if state["board"][position] is not None:
            return False
        
        return True
    
    def apply_move(self, state, move, player_id):
        """Apply a move to the game state."""
        position = move["position"]
        new_state = state.copy()
        new_state["board"] = state["board"].copy()
        
        # Update board
        new_state["board"][position] = player_id
        
        # Update current player
        new_state["current_player"] = 1 if player_id == 2 else 2
        
        # Increment move count
        new_state["moves_count"] += 1
        
        return new_state
    
    def check_winner(self, state):
        """Check if there's a winner."""
        board = state["board"]
        
        # Check rows
        for i in range(0, 9, 3):
            if board[i] is not None and board[i] == board[i+1] == board[i+2]:
                return board[i]
        
        # Check columns
        for i in range(3):
            if board[i] is not None and board[i] == board[i+3] == board[i+6]:
                return board[i]
        
        # Check diagonals
        if board[0] is not None and board[0] == board[4] == board[8]:
            return board[0]
        if board[2] is not None and board[2] == board[4] == board[6]:
            return board[2]
        
        return None
    
    def is_game_over(self, state):
        """Check if the game is over (win or draw)."""
        # Check if there's a winner
        if self.check_winner(state) is not None:
            return True
        
        # Check if it's a draw (all positions filled)
        if state["moves_count"] >= 9:
            return True
            
        return False
    
    def is_draw(self, state):
        """Check if the game is a draw."""
        return self.is_game_over(state) and self.check_winner(state) is None


class GameLogicFactory:
    """Factory for creating game logic instances."""
    
    @staticmethod
    def create_game_logic(game_type):
        """Create and return a game logic instance based on game type."""
        if game_type == "tic-tac-toe":
            return TicTacToeLogic()
        else:
            raise ValueError(f"Unknown game type: {game_type}")


def handle_request():
    """Handle incoming requests from the Node.js server."""
    # Read input from stdin (from PythonShell)
    input_data = sys.stdin.readline().strip()
    
    try:
        request = json.loads(input_data)
        action = request.get("action")
        game_type = request.get("game_type", "tic-tac-toe")
        
        # Create game logic instance
        game_logic = GameLogicFactory.create_game_logic(game_type)
        
        # Process based on action
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
        
        # Return result as JSON
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    handle_request()