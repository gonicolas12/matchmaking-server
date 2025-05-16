"""
Game Client for Matchmaking Server

This script provides a GUI client for connecting to the matchmaking server
and playing games.
"""

import asyncio
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import socketio
import sys
import os

class TicTacToeBoard(tk.Frame):
    """GUI component for the Tic-Tac-Toe board."""
    
    def __init__(self, master, game_client):
        """Initialize the board GUI."""
        super().__init__(master)
        self.game_client = game_client
        self.current_match = None
        self.is_my_turn = False
        self.player_symbol = "X"  # Default
        self.opponent_symbol = "O"  # Default
        
        self.buttons = []
        for i in range(3):
            row = []
            for j in range(3):
                button = tk.Button(self, text=" ", font=('Arial', 20), width=5, height=2,
                                  command=lambda row=i, col=j: self.make_move(row, col))
                button.grid(row=i, column=j, padx=5, pady=5)
                row.append(button)
            self.buttons.append(row)
        
        self.status_label = tk.Label(self, text="Waiting for match...", font=('Arial', 12))
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)
    
    def update_board(self, state):
        """Update the board based on the game state."""
        if not state or 'board' not in state:
            return
        
        board = state['board']
        for i in range(3):
            for j in range(3):
                index = i * 3 + j
                if index < len(board) and board[index] is not None:
                    # 1 = X, 2 = O
                    symbol = "X" if board[index] == 1 else "O"
                    
                    # Déterminer si c'est le symbole du joueur ou de l'adversaire
                    is_player_symbol = (symbol == self.player_symbol)
                    
                    self.buttons[i][j].config(text=symbol)
                else:
                    self.buttons[i][j].config(text=" ")
    
    def update_status(self, message):
        """Update the status message."""
        self.status_label.config(text=message)
    
    def set_turn(self, is_my_turn):
        """Enable or disable buttons based on whose turn it is."""
        self.is_my_turn = is_my_turn
        state = 'normal' if is_my_turn else 'disabled'
        
        # Only enable empty buttons
        for i in range(3):
            for j in range(3):
                if self.buttons[i][j]['text'] == " ":
                    self.buttons[i][j].config(state=state)
                else:
                    self.buttons[i][j].config(state='disabled')
    
    def make_move(self, row, col):
        """Handle a move on the board."""
        if not self.is_my_turn or not self.current_match:
            return
        
        # Calculate position index (0-8)
        position = row * 3 + col
        
        # Send move to server
        asyncio.run_coroutine_threadsafe(
            self.game_client.make_move(self.current_match, {"position": position}),
            self.game_client.loop
        )
        
        # Disable all buttons until we get confirmation
        self.set_turn(False)
    
    def reset_board(self):
        """Reset the board for a new game."""
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text=" ", state='disabled')


class GameClient:
    """Main client class for connecting to the matchmaking server."""
    
    def __init__(self, server_url):
        """Initialize the client with the server URL."""
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
        await self.sio.emit('register', {
            'username': username
        })
        return True
    
    async def join_queue(self):
        """Join the matchmaking queue."""
        if not self.player_id or not self.username:
            print("Player ID or username not set")
            return False
        
        await self.sio.emit('join_queue', {
            'player_id': self.player_id,
            'username': self.username
        })
        return True
    
    async def make_move(self, match_id, move):
        """Make a move in the current game."""
        await self.sio.emit('make_move', {
            'match_id': match_id,
            'player_id': self.player_id,
            'move': move
        })
    
    # Event handlers
    async def on_connect(self):
        """Handle successful connection to server."""
        print("Connected to matchmaking server")
        
        # If we're in a GUI, update status
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Connected to server"))
    
    async def on_disconnect(self):
        """Handle disconnection from server."""
        print("Disconnected from matchmaking server")
        
        # If we're in a GUI, update status
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Disconnected from server"))
    
    async def on_registered(self, data):
        """Handle registration confirmation."""
        self.player_id = data.get('player_id')
        print(f"Registered as {self.username} (ID: {self.player_id})")
        
        # If we're in a GUI, update status
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status(f"Registered as {self.username}"))
    
    async def on_queue_joined(self, data):
        """Handle confirmation of joining the queue."""
        position = data.get('position', 0)
        print(f"Joined matchmaking queue. Position: {position}")
        
        # If we're in a GUI, update status
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status(f"In queue. Position: {position}"))
    
    async def on_match_found(self, data):
        """Handle a successful match."""
        self.current_match = data.get('match_id')
        opponent = data.get('opponent', 'Unknown')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        
        print(f"Match found! Playing against: {opponent}")
        print(f"Your player_id: {self.player_id}")
        print(f"Current player in state: {state.get('current_player')}")
        print(f"Your turn (from server): {your_turn}")
        
        # Determine if the player is the first player (player1) or the second player (player2)
        # The first player uses X, the second uses O
        is_player1 = your_turn  # If it's your turn, you're player 1
        
        # If we're in a GUI, update the board
        if self.root and self.game_board:
            # Set symbols based on whether the player is player 1 or 2
            if is_player1:
                self.game_board.player_symbol = "X"  # Player 1 = X
                self.game_board.opponent_symbol = "O"  # Player 2 = O
            else:
                self.game_board.player_symbol = "O"  # Player 2 = O
                self.game_board.opponent_symbol = "X"  # Player 1 = X
                
            self.game_board.current_match = self.current_match
            self.root.after(0, lambda: self.game_board.reset_board())
            self.root.after(0, lambda: self.game_board.update_board(state))
            self.root.after(0, lambda: self.game_board.set_turn(your_turn))
            
            turn_message = "Your turn" if your_turn else "Opponent's turn"
            self.root.after(0, lambda: self.game_board.update_status(
                f"Playing against {opponent}. {turn_message}"
            ))
        
    async def on_game_update(self, data):
        """Handle game state updates."""
        match_id = data.get('match_id')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        winner = data.get('winner')
        
        # Ensure this is for our current match
        if match_id != self.current_match:
            return
        
        print(f"Game update received.")
        print(f"Your player_id: {self.player_id}")
        print(f"Current player in state: {state.get('current_player')}")
        print(f"Your turn (from server): {your_turn}")
        
        # If we're in a GUI, update the board
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_board(state))
            self.root.after(0, lambda: self.game_board.set_turn(your_turn))
            
            if winner is not None:
                winner_text = "You won!" if winner == self.player_id else "You lost!"
                self.root.after(0, lambda: self.game_board.update_status(winner_text))
                self.root.after(0, lambda: messagebox.showinfo("Game Over", winner_text))
            elif your_turn:
                self.root.after(0, lambda: self.game_board.update_status("Your turn"))
            else:
                self.root.after(0, lambda: self.game_board.update_status("Opponent's turn"))
    
    async def on_opponent_disconnected(self, data):
        """Handle opponent disconnection."""
        match_id = data.get('match_id')
        
        # Ensure this is for our current match
        if match_id != self.current_match:
            return
        
        print("Opponent disconnected")
        
        # If we're in a GUI, update status
        if self.root and self.game_board:
            self.root.after(0, lambda: self.game_board.update_status("Opponent disconnected. You win!"))
            self.root.after(0, lambda: messagebox.showinfo("Game Over", "Opponent disconnected. You win!"))
    
    async def on_error(self, data):
        """Handle error messages from the server."""
        message = data.get('message', 'Unknown error')
        print(f"Error: {message}")
        
        # If we're in a GUI, show error
        if self.root:
            self.root.after(0, lambda: messagebox.showerror("Error", message))
    
    def start_gui(self):
        """Start the GUI application."""
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe Client")
        
        # Get username
        self.username = simpledialog.askstring("Username", "Enter your username:", parent=self.root)
        if not self.username:
            self.username = f"Player_{hash(os.urandom(4)) % 1000}"
        
        # Create main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack()
        
        # Title
        title_label = tk.Label(main_frame, text="Tic-Tac-Toe Game", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Username display
        username_label = tk.Label(main_frame, text=f"Playing as: {self.username}", font=('Arial', 12))
        username_label.pack(pady=5)
        
        # Game board
        self.game_board = TicTacToeBoard(main_frame, self)
        self.game_board.pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        # Connect button
        connect_button = tk.Button(
            buttons_frame, text="Connect", 
            command=lambda: asyncio.run_coroutine_threadsafe(self.connect_and_register(), self.loop)
        )
        connect_button.grid(row=0, column=0, padx=5)
        
        # Queue button
        queue_button = tk.Button(
            buttons_frame, text="Join Queue", 
            command=lambda: asyncio.run_coroutine_threadsafe(self.join_queue(), self.loop)
        )
        queue_button.grid(row=0, column=1, padx=5)
        
        # Disconnect button
        disconnect_button = tk.Button(
            buttons_frame, text="Disconnect", 
            command=lambda: asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
        )
        disconnect_button.grid(row=0, column=2, padx=5)
        
        # Start asyncio event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        
        def run_async_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        import threading
        threading.Thread(target=run_async_loop, daemon=True).start()
        
        # Connect automatically
        asyncio.run_coroutine_threadsafe(self.connect_and_register(), self.loop)
        
        # Start Tkinter main loop
        self.root.mainloop()
        
        # Cleanup when window is closed
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
            self.loop.stop()
    
    async def connect_and_register(self):
        """Connect to server and register user."""
        connected = await self.connect()
        if connected:
            await self.register(self.username)


if __name__ == "__main__":
    # Use localhost for development, change to server IP for production
    SERVER_URL = "http://localhost:3000"
    
    if len(sys.argv) > 1:
        SERVER_URL = sys.argv[1]
    
    client = GameClient(SERVER_URL)
    client.start_gui()