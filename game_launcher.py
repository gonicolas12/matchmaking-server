#!/usr/bin/env python3
"""
Game Launcher for Matchmaking Server

This script allows users to choose between Chess and Tic-Tac-Toe
and launches the appropriate client.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from pathlib import Path

class GameLauncher:
    """Main launcher GUI for game selection."""
    
    def __init__(self):
        # Initialize server URL BEFORE creating widgets
        self.server_url = "http://localhost:3000"
        
        self.root = tk.Tk()
        self.root.title("Game Launcher - Matchmaking Server")
        self.root.geometry("500x400")
        self.root.configure(bg="#2c3e50")
        
        # Center window
        self.center_window()
        
        # Create GUI
        self.create_widgets()
    
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2c3e50", padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🎮 Game Matchmaking Server",
            bg="#2c3e50", 
            fg="white", 
            font=('Arial', 20, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Choose your game and connect to other players!",
            bg="#2c3e50",
            fg="#bdc3c7",
            font=('Arial', 12)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Games frame
        games_frame = tk.Frame(main_frame, bg="#2c3e50")
        games_frame.pack(pady=20)
        
        # Chess button
        chess_frame = tk.Frame(games_frame, bg="#34495e", relief=tk.RAISED, bd=3)
        chess_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        chess_icon = tk.Label(
            chess_frame,
            text="♛♚♜♞♝♟",
            bg="#34495e",
            fg="white",
            font=('Arial', 24)
        )
        chess_icon.pack(pady=10)
        
        chess_title = tk.Label(
            chess_frame,
            text="CHESS",
            bg="#34495e",
            fg="white",
            font=('Arial', 16, 'bold')
        )
        chess_title.pack()
        
        chess_desc = tk.Label(
            chess_frame,
            text="Full chess with all rules\nCastling, en passant, promotion\nCheck, checkmate, stalemate",
            bg="#34495e",
            fg="#bdc3c7",
            font=('Arial', 10),
            justify=tk.CENTER
        )
        chess_desc.pack(pady=10)
        
        chess_button = tk.Button(
            chess_frame,
            text="Play Chess",
            command=self.launch_chess,
            bg="#27ae60",
            fg="white",
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        chess_button.pack(pady=(10, 20))
        
        # Tic-Tac-Toe button
        ttt_frame = tk.Frame(games_frame, bg="#34495e", relief=tk.RAISED, bd=3)
        ttt_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        ttt_icon = tk.Label(
            ttt_frame,
            text="⭕❌⭕\n❌⭕❌\n⭕❌⭕",
            bg="#34495e",
            fg="white",
            font=('Arial', 16)
        )
        ttt_icon.pack(pady=10)
        
        ttt_title = tk.Label(
            ttt_frame,
            text="TIC-TAC-TOE",
            bg="#34495e",
            fg="white",
            font=('Arial', 16, 'bold')
        )
        ttt_title.pack()
        
        ttt_desc = tk.Label(
            ttt_frame,
            text="Classic 3x3 grid game\nSimple and fast\nPerfect for quick matches",
            bg="#34495e",
            fg="#bdc3c7",
            font=('Arial', 10),
            justify=tk.CENTER
        )
        ttt_desc.pack(pady=10)
        
        ttt_button = tk.Button(
            ttt_frame,
            text="Play Tic-Tac-Toe",
            command=self.launch_tictactoe,
            bg="#3498db",
            fg="white",
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        ttt_button.pack(pady=(10, 20))
        
        # Server settings frame
        settings_frame = tk.Frame(main_frame, bg="#2c3e50")
        settings_frame.pack(pady=30, fill=tk.X)
        
        server_label = tk.Label(
            settings_frame,
            text="Server URL:",
            bg="#2c3e50",
            fg="white",
            font=('Arial', 12)
        )
        server_label.pack()
        
        self.server_entry = tk.Entry(
            settings_frame,
            font=('Arial', 11),
            justify=tk.CENTER,
            width=30
        )
        self.server_entry.pack(pady=5)
        self.server_entry.insert(0, self.server_url)
        
        # Update button
        update_button = tk.Button(
            settings_frame,
            text="Update Server URL",
            command=self.update_server_url,
            bg="#f39c12",
            fg="white",
            font=('Arial', 10),
            padx=15,
            pady=5
        )
        update_button.pack(pady=10)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#2c3e50")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to launch games!",
            bg="#2c3e50",
            fg="#95a5a6",
            font=('Arial', 10)
        )
        self.status_label.pack()
    
    def update_server_url(self):
        """Update the server URL from entry field."""
        new_url = self.server_entry.get().strip()
        if new_url:
            self.server_url = new_url
            self.status_label.config(text=f"Server URL updated: {new_url}")
        else:
            messagebox.showerror("Error", "Please enter a valid server URL")
    
    def launch_chess(self):
        """Launch the chess client."""
        try:
            self.status_label.config(text="Launching Chess client...")
            self.root.update()
            
            # Check if chess_client.py exists
            chess_script = Path("chess_client.py")
            if not chess_script.exists():
                # Try relative paths
                possible_paths = [
                    Path("python/chess_client.py"),
                    Path("../python/chess_client.py"),
                    Path("./python/chess_client.py")
                ]
                
                chess_script = None
                for path in possible_paths:
                    if path.exists():
                        chess_script = path
                        break
                
                if not chess_script:
                    messagebox.showerror(
                        "Error", 
                        "chess_client.py not found!\n\nPlease make sure the chess client script is in the same directory."
                    )
                    self.status_label.config(text="Error: Chess client not found")
                    return
            
            # Launch chess client
            subprocess.Popen([
                sys.executable, 
                str(chess_script), 
                self.server_url
            ])
            
            self.status_label.config(text="Chess client launched successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch chess client:\n{str(e)}")
            self.status_label.config(text="Error launching chess client")
    
    def launch_tictactoe(self):
        """Launch the tic-tac-toe client."""
        try:
            self.status_label.config(text="Launching Tic-Tac-Toe client...")
            self.root.update()
            
            # Check if game_client.py exists
            ttt_script = Path("game_client.py")
            if not ttt_script.exists():
                # Try relative paths
                possible_paths = [
                    Path("python/game_client.py"),
                    Path("../python/game_client.py"),
                    Path("./python/game_client.py")
                ]
                
                ttt_script = None
                for path in possible_paths:
                    if path.exists():
                        ttt_script = path
                        break
                
                if not ttt_script:
                    messagebox.showerror(
                        "Error", 
                        "game_client.py not found!\n\nPlease make sure the tic-tac-toe client script is in the same directory."
                    )
                    self.status_label.config(text="Error: Tic-Tac-Toe client not found")
                    return
            
            # Launch tic-tac-toe client
            subprocess.Popen([
                sys.executable, 
                str(ttt_script), 
                self.server_url
            ])
            
            self.status_label.config(text="Tic-Tac-Toe client launched successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch tic-tac-toe client:\n{str(e)}")
            self.status_label.config(text="Error launching tic-tac-toe client")
    
    def run(self):
        """Start the launcher GUI."""
        self.root.mainloop()


class ServerManager:
    """Simple server management utilities."""
    
    @staticmethod
    def check_server_status(url):
        """Check if the server is running."""
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(url, method='HEAD')
            urllib.request.urlopen(req, timeout=5)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False
    
    @staticmethod
    def start_local_server():
        """Start the local Node.js server."""
        try:
            # Check if we're in the right directory
            if not Path("package.json").exists():
                return False, "package.json not found. Please run from the project root directory."
            
            # Try to start the server
            process = subprocess.Popen([
                "npm", "start"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True, "Server started successfully!"
        except FileNotFoundError:
            return False, "npm not found. Please install Node.js and npm."
        except Exception as e:
            return False, f"Failed to start server: {str(e)}"


def main():
    """Main function to run the game launcher."""
    print("🎮 Starting Game Launcher...")
    
    # Check for dependencies
    try:
        import tkinter
        import subprocess
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install the required dependencies.")
        return
    
    # Create and run launcher
    launcher = GameLauncher()
    launcher.run()


if __name__ == "__main__":
    main()