"""
Game Launcher for Matchmaking Server

This script allows users to choose between Chess and Tic-Tac-Toe
and launches the appropriate client with proper IP handling.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import sys
import os
import socket
from pathlib import Path

class GameLauncher:
    """Main launcher GUI for game selection."""
    
    def __init__(self):
        # Initialize server URL BEFORE creating widgets
        self.server_url = "http://localhost:3000"
        
        self.root = tk.Tk()
        self.root.title("Game Launcher - Matchmaking Server")
        self.root.configure(bg="#2c3e50")
        
        # Auto-resize and center window
        self.setup_window()
        
        # Create GUI
        self.create_widgets()
    
    def setup_window(self):
        """Setup window size and position."""
        # Let tkinter auto-size based on content
        self.root.update_idletasks()
        
        # Set minimum size
        self.root.minsize(600, 600)
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = max(600, self.root.winfo_reqwidth())
        height = max(500, self.root.winfo_reqheight())
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main frame with padding
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🎮 Game Matchmaking Server",
            bg="#2c3e50", 
            fg="white", 
            font=('Arial', 20, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Choose your game and connect to other players!",
            bg="#2c3e50",
            fg="#bdc3c7",
            font=('Arial', 12)
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Games frame - horizontal layout
        games_frame = tk.Frame(main_frame, bg="#2c3e50")
        games_frame.pack(pady=15, fill=tk.X)
        
        # Chess game card
        self.create_game_card(games_frame, "left", 
                             icon="♛♚♜♞♝♟", 
                             title="CHESS",
                             description="Full chess with all rules\nCastling, en passant, promotion\nCheck, checkmate, stalemate",
                             button_text="Play Chess",
                             button_color="#27ae60",
                             command=self.launch_chess)
        
        # Tic-Tac-Toe game card
        self.create_game_card(games_frame, "right",
                             icon="⭕❌⭕\n❌⭕❌\n⭕❌⭕",
                             title="TIC-TAC-TOE", 
                             description="Classic 3x3 grid game\nSimple and fast\nPerfect for quick matches",
                             button_text="Play Tic-Tac-Toe",
                             button_color="#3498db",
                             command=self.launch_tictactoe)
        
        # Server settings frame
        settings_frame = tk.LabelFrame(main_frame, text="Server Settings", 
                                      bg="#34495e", fg="white", font=('Arial', 12, 'bold'),
                                      relief=tk.RAISED, bd=2)
        settings_frame.pack(pady=20, fill=tk.X, padx=10)
        
        # Server URL input
        url_frame = tk.Frame(settings_frame, bg="#34495e")
        url_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(url_frame, text="Server URL:", bg="#34495e", fg="white", 
                font=('Arial', 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.server_entry = tk.Entry(url_frame, font=('Arial', 11), width=40)
        self.server_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.server_entry.insert(0, self.server_url)
        
        update_button = tk.Button(url_frame, text="Update", 
                                 command=self.update_server_url,
                                 bg="#f39c12", fg="white", font=('Arial', 10),
                                 padx=15, pady=2)
        update_button.pack(side=tk.RIGHT)
        
        # IP helper buttons
        ip_frame = tk.Frame(settings_frame, bg="#34495e")
        ip_frame.pack(pady=(0, 10), padx=10, fill=tk.X)
        
        tk.Button(ip_frame, text="Use Localhost", 
                 command=lambda: self.set_server_url("http://localhost:3000"),
                 bg="#95a5a6", fg="white", font=('Arial', 9),
                 padx=10, pady=3).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(ip_frame, text="Get Local IP", 
                 command=self.get_local_ip,
                 bg="#9b59b6", fg="white", font=('Arial', 9),
                 padx=10, pady=3).pack(side=tk.LEFT, padx=5)
        
        tk.Button(ip_frame, text="Enter Remote IP", 
                 command=self.enter_remote_ip,
                 bg="#e67e22", fg="white", font=('Arial', 9),
                 padx=10, pady=3).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#2c3e50")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to launch games!",
            bg="#2c3e50",
            fg="#95a5a6",
            font=('Arial', 10)
        )
        self.status_label.pack()
    
    def create_game_card(self, parent, side, icon, title, description, button_text, button_color, command):
        """Create a game card widget."""
        # Main card frame
        card_frame = tk.Frame(parent, bg="#34495e", relief=tk.RAISED, bd=3)
        card_frame.pack(side=tk.LEFT if side == "left" else tk.RIGHT, 
                       fill=tk.BOTH, expand=True, padx=10 if side == "left" else (10, 0))
        
        # Icon
        icon_label = tk.Label(card_frame, text=icon, bg="#34495e", fg="white", 
                             font=('Arial', 20 if "\n" not in icon else 14))
        icon_label.pack(pady=15)
        
        # Title
        title_label = tk.Label(card_frame, text=title, bg="#34495e", fg="white", 
                              font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = tk.Label(card_frame, text=description, bg="#34495e", fg="#bdc3c7", 
                             font=('Arial', 10), justify=tk.CENTER)
        desc_label.pack(pady=(0, 15))
        
        # Play button
        play_button = tk.Button(card_frame, text=button_text, command=command,
                               bg=button_color, fg="white", font=('Arial', 11, 'bold'),
                               padx=20, pady=10, cursor="hand2")
        play_button.pack(pady=(0, 20))
    
    def set_server_url(self, url):
        """Set server URL in entry field."""
        self.server_entry.delete(0, tk.END)
        self.server_entry.insert(0, url)
        self.update_server_url()
    
    def get_local_ip(self):
        """Get and set local IP address."""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            self.set_server_url(f"http://{local_ip}:3000")
            self.status_label.config(text=f"Local IP found: {local_ip}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not determine local IP: {str(e)}")
            self.status_label.config(text="Error getting local IP")
    
    def enter_remote_ip(self):
        """Prompt user to enter a remote IP address."""
        ip = simpledialog.askstring("Remote IP", 
                                    "Enter the server IP address:",
                                    parent=self.root)
        if ip:
            # Validate IP format (basic)
            try:
                parts = ip.split('.')
                if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
                    self.set_server_url(f"http://{ip}:3000")
                else:
                    messagebox.showerror("Error", "Invalid IP address format")
            except ValueError:
                messagebox.showerror("Error", "Invalid IP address format")
    
    def update_server_url(self):
        """Update the server URL from entry field."""
        new_url = self.server_entry.get().strip()
        if new_url:
            self.server_url = new_url
            self.status_label.config(text=f"Server URL: {new_url}")
        else:
            messagebox.showerror("Error", "Please enter a valid server URL")
    
    def launch_chess(self):
        """Launch the chess client."""
        try:
            self.status_label.config(text="Launching Chess client...")
            self.root.update()
            
            # Check if chess_client.py exists
            chess_script = self.find_script("chess_client.py")
            if not chess_script:
                messagebox.showerror(
                    "Error", 
                    "chess_client.py not found!\n\nPlease make sure the chess client script is available."
                )
                self.status_label.config(text="Error: Chess client not found")
                return
            
            # Launch chess client with server URL
            subprocess.Popen([
                sys.executable, 
                str(chess_script), 
                self.server_url
            ])
            
            self.status_label.config(text=f"Chess client launched! Server: {self.server_url}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch chess client:\n{str(e)}")
            self.status_label.config(text="Error launching chess client")
    
    def launch_tictactoe(self):
        """Launch the tic-tac-toe client."""
        try:
            self.status_label.config(text="Launching Tic-Tac-Toe client...")
            self.root.update()
            
            # Check if game_client.py exists
            ttt_script = self.find_script("game_client.py")
            if not ttt_script:
                messagebox.showerror(
                    "Error", 
                    "game_client.py not found!\n\nPlease make sure the tic-tac-toe client script is available."
                )
                self.status_label.config(text="Error: Tic-Tac-Toe client not found")
                return
            
            # Launch tic-tac-toe client with server URL
            subprocess.Popen([
                sys.executable, 
                str(ttt_script), 
                self.server_url
            ])
            
            self.status_label.config(text=f"Tic-Tac-Toe client launched! Server: {self.server_url}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch tic-tac-toe client:\n{str(e)}")
            self.status_label.config(text="Error launching tic-tac-toe client")
    
    def find_script(self, script_name):
        """Find script in various possible locations."""
        possible_paths = [
            Path(script_name),  # Current directory
            Path("python") / script_name,  # python subdirectory
            Path("..") / script_name,  # Parent directory
            Path("..") / "python" / script_name,  # Parent/python
            Path(".") / "python" / script_name,  # ./python
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def run(self):
        """Start the launcher GUI."""
        self.root.mainloop()


def main():
    """Main function to run the game launcher."""
    print("🎮 Starting Game Launcher...")
    
    # Check for dependencies
    try:
        import tkinter
        import subprocess
        import socket
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install the required dependencies.")
        return
    
    # Create and run launcher
    launcher = GameLauncher()
    launcher.run()


if __name__ == "__main__":
    main()