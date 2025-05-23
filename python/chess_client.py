"""
Chess Client for Matchmaking Server

This script provides a beautiful GUI client for playing chess
against other players through the matchmaking server.
"""

import asyncio
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import socketio
import sys
import os
from typing import Dict, List, Tuple, Optional

# Chess piece Unicode symbols
PIECE_SYMBOLS = {
    1: {  # White pieces
        "king": "♔", "queen": "♕", "rook": "♖", 
        "bishop": "♗", "knight": "♘", "pawn": "♙"
    },
    2: {  # Black pieces
        "king": "♚", "queen": "♛", "rook": "♜",
        "bishop": "♝", "knight": "♞", "pawn": "♟"
    }
}

# Alternative ASCII pieces for compatibility
ASCII_PIECES = {
    1: {  # White pieces
        "king": "K", "queen": "Q", "rook": "R",
        "bishop": "B", "knight": "N", "pawn": "P"
    },
    2: {  # Black pieces
        "king": "k", "queen": "q", "rook": "r",
        "bishop": "b", "knight": "n", "pawn": "p"
    }
}

class ChessBoard(tk.Frame):
    """GUI component for the chess board."""
    
    def __init__(self, master, game_client):
        super().__init__(master, bg="#2c3e50")
        self.game_client = game_client
        self.current_match = None
        self.is_my_turn = False
        self.player_color = 1  # 1 = white, 2 = black
        self.selected_square = None
        self.legal_moves = []
        self.use_unicode = True
        
        # Colors
        self.light_square = "#f0d9b5"
        self.dark_square = "#b58863"
        self.selected_color = "#ffff00"
        self.legal_move_color = "#90ee90"
        self.last_move_color = "#ffd700"
        
        # Game state - INITIALIZE BEFORE CREATING BOARD
        self.current_state = None
        self.last_move = None
        
        self.buttons = []
        self.create_board()
        
        # Status and info panels
        self.create_info_panel()
    
    def create_board(self):
        """Create the chess board GUI."""
        # Board frame
        board_frame = tk.Frame(self, bg="#2c3e50")
        board_frame.pack(pady=20)
        
        # Column labels
        col_frame = tk.Frame(board_frame, bg="#2c3e50")
        col_frame.pack()
        tk.Label(col_frame, text="  ", bg="#2c3e50", fg="white", font=('Arial', 12)).pack(side=tk.LEFT)
        for col in "abcdefgh":
            tk.Label(col_frame, text=col, bg="#2c3e50", fg="white", 
                    font=('Arial', 12, 'bold'), width=4).pack(side=tk.LEFT)
        
        # Board with row labels
        main_board_frame = tk.Frame(board_frame, bg="#2c3e50")
        main_board_frame.pack()
        
        self.buttons = []
        for row in range(8):
            button_row = []
            row_frame = tk.Frame(main_board_frame, bg="#2c3e50")
            row_frame.pack()
            
            # Row label
            tk.Label(row_frame, text=str(8-row), bg="#2c3e50", fg="white",
                    font=('Arial', 12, 'bold'), width=2).pack(side=tk.LEFT)
            
            for col in range(8):
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                button = tk.Button(
                    row_frame,
                    text="",
                    font=('Arial', 24),
                    width=4,
                    height=2,
                    bg=color,
                    relief=tk.FLAT,
                    command=lambda r=row, c=col: self.on_square_click(r, c)
                )
                button.pack(side=tk.LEFT, padx=1, pady=1)
                button_row.append(button)
            
            # Right row label
            tk.Label(row_frame, text=str(8-row), bg="#2c3e50", fg="white",
                    font=('Arial', 12, 'bold'), width=2).pack(side=tk.LEFT)
            
            self.buttons.append(button_row)
        
        # Bottom column labels
        col_frame2 = tk.Frame(board_frame, bg="#2c3e50")
        col_frame2.pack()
        tk.Label(col_frame2, text="  ", bg="#2c3e50", fg="white", font=('Arial', 12)).pack(side=tk.LEFT)
        for col in "abcdefgh":
            tk.Label(col_frame2, text=col, bg="#2c3e50", fg="white",
                    font=('Arial', 12, 'bold'), width=4).pack(side=tk.LEFT)
        
        # Initialize board with starting position
        self.setup_initial_position()
    
    def setup_initial_position(self):
        """Set up the initial chess position for display."""
        # Create a sample initial state for display
        initial_board = self.create_initial_board()
        self.current_state = {
            "board": initial_board,
            "current_player": 1,
            "captured_pieces": {"white": [], "black": []}
        }
        self.update_board_display()
    
    def create_initial_board(self):
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
    
    def create_info_panel(self):
        """Create information and control panels."""
        # Main info frame
        info_frame = tk.Frame(self, bg="#2c3e50")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Left panel - Game status
        left_panel = tk.Frame(info_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(left_panel, text="Game Status", bg="#34495e", fg="white",
                font=('Arial', 14, 'bold')).pack(pady=5)
        
        self.status_label = tk.Label(left_panel, text="Waiting for match...", 
                                    bg="#34495e", fg="white", font=('Arial', 12))
        self.status_label.pack(pady=5)
        
        self.turn_label = tk.Label(left_panel, text="", bg="#34495e", fg="white",
                                  font=('Arial', 11))
        self.turn_label.pack(pady=2)
        
        # Right panel - Captured pieces
        right_panel = tk.Frame(info_frame, bg="#34495e", relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right_panel, text="Captured Pieces", bg="#34495e", fg="white",
                font=('Arial', 14, 'bold')).pack(pady=5)
        
        self.captured_white_label = tk.Label(right_panel, text="White: ", 
                                           bg="#34495e", fg="white", font=('Arial', 11))
        self.captured_white_label.pack(pady=2)
        
        self.captured_black_label = tk.Label(right_panel, text="Black: ",
                                           bg="#34495e", fg="white", font=('Arial', 11))
        self.captured_black_label.pack(pady=2)
        
        # Controls frame
        controls_frame = tk.Frame(self, bg="#2c3e50")
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Toggle Unicode/ASCII pieces
        self.unicode_button = tk.Button(
            controls_frame, text="Toggle Pieces (Unicode/ASCII)",
            command=self.toggle_piece_style,
            bg="#3498db", fg="white", font=('Arial', 10)
        )
        self.unicode_button.pack(side=tk.LEFT, padx=5)
        
        # Resign button
        self.resign_button = tk.Button(
            controls_frame, text="Resign",
            command=self.resign_game,
            bg="#e74c3c", fg="white", font=('Arial', 10)
        )
        self.resign_button.pack(side=tk.RIGHT, padx=5)
    
    def toggle_piece_style(self):
        """Toggle between Unicode and ASCII piece display."""
        self.use_unicode = not self.use_unicode
        self.update_board_display()
    
    def resign_game(self):
        """Resign the current game."""
        if self.current_match and messagebox.askyesno("Resign", "Are you sure you want to resign?"):
            asyncio.run_coroutine_threadsafe(
                self.game_client.resign_match(self.current_match),
                self.game_client.loop
            )
    
    def on_square_click(self, row, col):
        """Handle square click events."""
        if not self.is_my_turn or not self.current_match:
            print(f"Click ignored - My turn: {self.is_my_turn}, Match: {self.current_match}")
            return
        
        if self.selected_square is None:
            # Select a piece
            if self.current_state and self.current_state["board"][row][col]:
                piece = self.current_state["board"][row][col]
                if piece["color"] == self.player_color:
                    self.selected_square = (row, col)
                    self.highlight_legal_moves(row, col)
                    print(f"Selected piece at {row},{col}: {piece}")
        else:
            # Make a move
            from_row, from_col = self.selected_square
            
            if (row, col) == self.selected_square:
                # Deselect
                self.selected_square = None
                self.legal_moves = []
                self.update_board_display()
                print("Deselected piece")
            else:
                # Attempt move
                move = {
                    "from": [from_row, from_col],
                    "to": [row, col]
                }
                
                print(f"Attempting move: {move}")
                
                # Check for pawn promotion
                piece = self.current_state["board"][from_row][from_col]
                if (piece["type"] == "pawn" and 
                    ((piece["color"] == 1 and row == 0) or (piece["color"] == 2 and row == 7))):
                    promotion = self.get_promotion_choice()
                    if promotion:
                        move["promotion"] = promotion
                
                asyncio.run_coroutine_threadsafe(
                    self.game_client.make_move(self.current_match, move),
                    self.game_client.loop
                )
                
                self.selected_square = None
                self.legal_moves = []
                self.set_turn(False)  # Disable board until response
    
    def get_promotion_choice(self):
        """Get user's choice for pawn promotion."""
        promotion_window = tk.Toplevel(self)
        promotion_window.title("Pawn Promotion")
        promotion_window.geometry("300x150")
        promotion_window.configure(bg="#2c3e50")
        promotion_window.transient(self)
        promotion_window.grab_set()
        
        choice = {"value": "queen"}  # Default
        
        tk.Label(promotion_window, text="Choose promotion piece:",
                bg="#2c3e50", fg="white", font=('Arial', 12)).pack(pady=10)
        
        button_frame = tk.Frame(promotion_window, bg="#2c3e50")
        button_frame.pack(pady=10)
        
        pieces = ["queen", "rook", "bishop", "knight"]
        symbols = PIECE_SYMBOLS[self.player_color] if self.use_unicode else ASCII_PIECES[self.player_color]
        
        for piece in pieces:
            symbol = symbols[piece]
            btn = tk.Button(
                button_frame, text=f"{symbol}\n{piece.title()}",
                command=lambda p=piece: self.set_promotion_and_close(choice, p, promotion_window),
                bg="#3498db", fg="white", font=('Arial', 10),
                width=8, height=3
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        promotion_window.wait_window()
        return choice["value"]
    
    def set_promotion_and_close(self, choice_dict, piece, window):
        """Set promotion choice and close window."""
        choice_dict["value"] = piece
        window.destroy()
    
    def highlight_legal_moves(self, row, col):
        """Highlight legal moves for the selected piece."""
        if not self.current_state:
            return
        
        self.legal_moves = []
        
        # Check all possible moves for this piece
        for to_row in range(8):
            for to_col in range(8):
                piece = self.current_state["board"][row][col]
                target = self.current_state["board"][to_row][to_col]
                
                if self.is_potentially_legal_move(piece, (row, col), (to_row, to_col), target):
                    self.legal_moves.append((to_row, to_col))
        
        self.update_board_display()
    
    def is_potentially_legal_move(self, piece, from_pos, to_pos, target):
        """Basic move validation for highlighting (not comprehensive)."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Can't capture own piece
        if target and target["color"] == piece["color"]:
            return False
        
        # Basic piece movement patterns
        piece_type = piece["type"]
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        if piece_type == "pawn":
            direction = -1 if piece["color"] == 1 else 1
            if to_col == from_col:  # Forward move
                if to_row == from_row + direction:
                    return not target
                elif to_row == from_row + 2 * direction and from_row in [1, 6]:
                    return not target
            elif col_diff == 1 and to_row == from_row + direction:
                return target is not None  # Capture
        elif piece_type == "rook":
            return from_row == to_row or from_col == to_col
        elif piece_type == "knight":
            return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)
        elif piece_type == "bishop":
            return row_diff == col_diff
        elif piece_type == "queen":
            return (from_row == to_row or from_col == to_col or row_diff == col_diff)
        elif piece_type == "king":
            return row_diff <= 1 and col_diff <= 1
        
        return False
    
    def update_board_display(self):
        """Update the visual display of the board."""
        if not self.current_state:
            return
        
        board = self.current_state["board"]
        symbols = PIECE_SYMBOLS if self.use_unicode else ASCII_PIECES
        
        for row in range(8):
            for col in range(8):
                button = self.buttons[row][col]
                piece = board[row][col]
                
                # Set piece text
                if piece:
                    symbol = symbols[piece["color"]][piece["type"]]
                    button.config(text=symbol)
                else:
                    button.config(text="")
                
                # Set background color
                base_color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                
                if (row, col) == self.selected_square:
                    button.config(bg=self.selected_color)
                elif (row, col) in self.legal_moves:
                    button.config(bg=self.legal_move_color)
                elif (self.last_move and 
                      ((row, col) == tuple(self.last_move.get("from", [])) or 
                       (row, col) == tuple(self.last_move.get("to", [])))):
                    button.config(bg=self.last_move_color)
                else:
                    button.config(bg=base_color)
    
    def update_status(self, message):
        """Update the status message."""
        self.status_label.config(text=message)
        print(f"Status: {message}")
    
    def update_turn_info(self, is_my_turn, current_player_color):
        """Update turn information display."""
        self.is_my_turn = is_my_turn
        
        if is_my_turn:
            self.turn_label.config(text="Your turn", fg="#2ecc71")
        else:
            color_name = "White" if current_player_color == 1 else "Black"
            self.turn_label.config(text=f"{color_name}'s turn", fg="#e74c3c")
    
    def set_turn(self, is_my_turn):
        """Enable or disable the board based on whose turn it is."""
        self.is_my_turn = is_my_turn
        print(f"Turn set to: {is_my_turn}")
    
    def reset_board(self):
        """Reset the board for a new game."""
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.current_state = None
        
        # Reset to initial position
        self.setup_initial_position()
    
    def update_captured_pieces(self, captured):
        """Update the display of captured pieces."""
        symbols = PIECE_SYMBOLS if self.use_unicode else ASCII_PIECES
        
        white_pieces = ""
        black_pieces = ""
        
        for piece in captured.get("white", []):
            white_pieces += symbols[piece["color"]][piece["type"]] + " "
        
        for piece in captured.get("black", []):
            black_pieces += symbols[piece["color"]][piece["type"]] + " "
        
        self.captured_white_label.config(text=f"White: {white_pieces}")
        self.captured_black_label.config(text=f"Black: {black_pieces}")


class ChessGameClient:
    """Main client class for chess matchmaking."""
    
    def __init__(self, server_url):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.player_id = None
        self.username = None
        self.current_match = None
        self.root = None
        self.game_board = None
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('registered', self.on_registered)
        self.sio.on('queue_joined', self.on_queue_joined)
        self.sio.on('match_found', self.on_match_found)
        self.sio.on('game_update', self.on_game_update)
        self.sio.on('opponent_disconnected', self.on_opponent_disconnected)
        self.sio.on('error', self.on_error)
    
    async def connect(self):
        """Connect to the matchmaking server."""
        try:
            await self.sio.connect(self.server_url)
            print(f"Connected to server: {self.server_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the server."""
        await self.sio.disconnect()
    
    async def register(self, username):
        """Register with the server."""
        if not username:
            return False
        
        self.username = username
        await self.sio.emit('register', {'username': username})
        return True
    
    async def join_queue(self):
        """Join the matchmaking queue."""
        if not self.player_id or not self.username:
            print("Player ID or username not set")
            return False
        
        await self.sio.emit('join_queue', {
            'player_id': self.player_id,
            'username': self.username,
            'game_type': 'chess'  # Specify chess game type
        })
        return True
    
    async def make_move(self, match_id, move):
        """Make a move in the current game."""
        print(f"Sending move: {move} for match {match_id}")
        await self.sio.emit('make_move', {
            'match_id': match_id,
            'player_id': self.player_id,
            'move': move
        })
    
    async def resign_match(self, match_id):
        """Resign the current match."""
        await self.sio.emit('resign_match', {
            'match_id': match_id,
            'player_id': self.player_id
        })
    
    # Event handlers
    async def on_connect(self):
        """Handle successful connection to server."""
        print("Connected to chess matchmaking server")
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Connected to server"))
    
    async def on_disconnect(self):
        """Handle disconnection from server."""
        print("Disconnected from chess matchmaking server")
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Disconnected from server"))
    
    async def on_registered(self, data):
        """Handle registration confirmation."""
        self.player_id = data.get('player_id')
        print(f"Registered as {self.username} (ID: {self.player_id})")
        
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status(f"Registered as {self.username}"))
    
    async def on_queue_joined(self, data):
        """Handle confirmation of joining the queue."""
        position = data.get('position', 0)
        print(f"Joined chess matchmaking queue. Position: {position}")
        
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status(f"In chess queue. Position: {position}"))
    
    async def on_match_found(self, data):
        """Handle a successful match."""
        self.current_match = data.get('match_id')
        opponent = data.get('opponent', 'Unknown')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        
        print(f"Chess match found! Playing against: {opponent}")
        print(f"Match ID: {self.current_match}")
        print(f"Your turn: {your_turn}")
        print(f"State: {state}")
        
        # Determine player color (player 1 = white, player 2 = black)
        is_player1 = your_turn  # First player starts, so if it's your turn, you're white
        
        if self.root and self.game_board:
            self.game_board.player_color = 1 if is_player1 else 2
            self.game_board.current_match = self.current_match
            self.game_board.current_state = state
            
            color_name = "White" if is_player1 else "Black"
            self.root.after(0, lambda: self.game_board.update_board_display())
            self.root.after(0, lambda: self.game_board.update_turn_info(your_turn, state.get('current_player', 1)))
            self.root.after(0, lambda: self.game_board.update_status(
                f"Playing as {color_name} vs {opponent}"
            ))
            
            if state.get("captured_pieces"):
                self.root.after(0, lambda: self.game_board.update_captured_pieces(state["captured_pieces"]))
    
    async def on_game_update(self, data):
        """Handle game state updates."""
        match_id = data.get('match_id')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        winner = data.get('winner')
        game_over = data.get('game_over', False)
        is_draw = data.get('is_draw', False)
        
        if match_id != self.current_match:
            return
        
        print(f"Chess game update received. Your turn: {your_turn}")
        print(f"Game over: {game_over}, Winner: {winner}")
        
        if self.root and self.game_board:
            self.game_board.current_state = state
            self.game_board.last_move = state.get('last_move')
            
            self.root.after(0, lambda: self.game_board.update_board_display())
            self.root.after(0, lambda: self.game_board.set_turn(your_turn and not game_over))
            
            if state.get("captured_pieces"):
                self.root.after(0, lambda: self.game_board.update_captured_pieces(state["captured_pieces"]))
            
            if game_over:
                if is_draw:
                    result_msg = "Game ended in a draw!"
                    self.root.after(0, lambda: self.game_board.update_status("Game over - Draw!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
                elif winner == self.player_id:
                    result_msg = "Congratulations! You won!"
                    self.root.after(0, lambda: self.game_board.update_status("You won!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
                else:
                    result_msg = "You lost. Better luck next time!"
                    self.root.after(0, lambda: self.game_board.update_status("You lost!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
            else:
                self.root.after(0, lambda: self.game_board.update_turn_info(your_turn, state.get('current_player', 1)))
                
                # Check for check status
                if state.get("game_status") == "check":
                    check_msg = "Check!" if your_turn else "You're in check!"
                    self.root.after(0, lambda: messagebox.showwarning("Check", check_msg))
    
    async def on_opponent_disconnected(self, data):
        """Handle opponent disconnection."""
        match_id = data.get('match_id')
        
        if match_id != self.current_match:
            return
        
        print("Opponent disconnected from chess match")
        
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Opponent disconnected. You win!"))
            self.root.after(0, lambda: messagebox.showinfo("Game Over", "Opponent disconnected. You win!"))
    
    async def on_error(self, data):
        """Handle error messages from the server."""
        message = data.get('message', 'Unknown error')
        print(f"Error: {message}")
        
        if self.root:
            self.root.after(0, lambda: messagebox.showerror("Error", message))
    
    def start_gui(self):
        """Start the GUI application."""
        self.root = tk.Tk()
        self.root.title("Chess Client - Matchmaking Server")
        self.root.configure(bg="#2c3e50")
        
        # Set window size and center it - INCREASED HEIGHT
        window_width = 900
        window_height = 1000  # Increased from 900
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Get username
        self.username = simpledialog.askstring("Username", "Enter your username:", parent=self.root)
        if not self.username:
            self.username = f"ChessPlayer_{hash(os.urandom(4)) % 1000}"
        
        # Main container with scrollbar if needed
        main_canvas = tk.Canvas(self.root, bg="#2c3e50", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg="#2c3e50")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = tk.Label(scrollable_frame, text="♔ Chess Matchmaking ♛", 
                              bg="#2c3e50", fg="white", font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        # Username display
        username_label = tk.Label(scrollable_frame, text=f"Playing as: {self.username}", 
                                 bg="#2c3e50", fg="white", font=('Arial', 14))
        username_label.pack(pady=5)
        
        # Game board
        self.game_board = ChessBoard(scrollable_frame, self)
        self.game_board.pack(pady=10)
        
        # Connection buttons
        button_frame = tk.Frame(scrollable_frame, bg="#2c3e50")
        button_frame.pack(pady=15)
        
        connect_button = tk.Button(
            button_frame, text="Connect to Server",
            command=lambda: asyncio.run_coroutine_threadsafe(self.connect_and_register(), self.loop),
            bg="#27ae60", fg="white", font=('Arial', 12, 'bold'),
            padx=20, pady=5
        )
        connect_button.grid(row=0, column=0, padx=10)
        
        queue_button = tk.Button(
            button_frame, text="Join Chess Queue",
            command=lambda: asyncio.run_coroutine_threadsafe(self.join_queue(), self.loop),
            bg="#3498db", fg="white", font=('Arial', 12, 'bold'),
            padx=20, pady=5
        )
        queue_button.grid(row=0, column=1, padx=10)
        
        disconnect_button = tk.Button(
            button_frame, text="Disconnect",
            command=lambda: asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop),
            bg="#e74c3c", fg="white", font=('Arial', 12, 'bold'),
            padx=20, pady=5
        )
        disconnect_button.grid(row=0, column=2, padx=10)
        
        # Add some padding at the bottom
        tk.Label(scrollable_frame, text="", bg="#2c3e50", height=2).pack()
        
        # Start asyncio event loop
        self.loop = asyncio.new_event_loop()
        
        def run_async_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        import threading
        threading.Thread(target=run_async_loop, daemon=True).start()
        
        # Connect automatically
        asyncio.run_coroutine_threadsafe(self.connect_and_register(), self.loop)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Start Tkinter main loop
        self.root.mainloop()
        
        # Cleanup
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
            self.loop.stop()
    
    async def connect_and_register(self):
        """Connect to server and register user."""
        connected = await self.connect()
        if connected:
            await self.register(self.username)


if __name__ == "__main__":
    # Use localhost for development
    SERVER_URL = "http://localhost:3000"
    
    if len(sys.argv) > 1:
        SERVER_URL = sys.argv[1]
    
    client = ChessGameClient(SERVER_URL)
    client.start_gui()