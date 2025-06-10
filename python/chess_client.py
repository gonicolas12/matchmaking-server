"""
Chess Client for Matchmaking Server - ALIGNMENT & BLOCKING FIXED

This script provides a beautiful fullscreen GUI client for playing chess
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
        self.pending_move = None
        
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
    
    def create_board(self):
        """Create the chess board GUI"""
        # Board container avec padding adaptatif
        board_container = tk.Frame(self, bg="#2c3e50")
        board_container.pack(expand=True, fill=tk.BOTH, padx=15, pady=15)  # Augmenté : 10 → 15
        
        # Calculer une taille VRAIMENT ADAPTATIVE
        def calculate_adaptive_size():
            # Forcer une mise à jour pour obtenir les vraies dimensions
            self.master.update_idletasks()
            
            # Obtenir les dimensions de la fenêtre parente
            try:
                root_widget = self.master
                while root_widget.master:
                    root_widget = root_widget.master
                
                window_width = root_widget.winfo_width()
                window_height = root_widget.winfo_height()
                
                if window_width <= 1 or window_height <= 1:
                    window_width = root_widget.winfo_screenwidth()
                    window_height = root_widget.winfo_screenheight()
                    
            except:
                window_width = 1200
                window_height = 800
            
            print(f"SIZING DEBUG: Window size: {window_width}x{window_height}")
                        
            # Calculer l'espace disponible (panneau droit plus petit)
            panel_width = max(270, min(320, int(window_width * 0.20)))  # Augmenté : 18% → 20%
            available_width = window_width - panel_width - 80   # Marge légèrement augmentée : 60 → 80
            available_height = window_height - 140              # Marge légèrement augmentée : 120 → 140
            
            # Prendre plus d'espace disponible
            available_size = min(available_width, available_height) * 0.88  # Réduit : 95% → 88%
            
            # Limites augmentées pour des échiquiers plus grands
            min_size = max(480, int(window_width * 0.32))   # Légèrement réduit : 35% → 32%
            max_size = max(850, int(window_width * 0.60))   # Légèrement réduit : 65% → 60%
            
            board_size = max(min_size, min(max_size, available_size))
            
            # Calculer les dimensions des boutons (plus grands)
            button_size = max(48, int(board_size / 9.5))    # Légèrement réduit : /9 → /9.5
            font_size_large = max(18, int(button_size / 2.1)) # Légèrement réduit : /2 → /2.1
            font_size_small = max(11, int(button_size / 4))
            
            print(f"SIZING DEBUG: Board size: {board_size}, Button size: {button_size}")
            
            return int(button_size), int(font_size_large), int(font_size_small)
        
        # Calculer les tailles adaptatives
        button_size, font_large, font_small = calculate_adaptive_size()
        
        # Configuration EXACTE pour l'alignement parfait
        BUTTON_PIXEL_WIDTH = button_size
        ROW_LABEL_PIXEL_WIDTH = max(30, int(button_size * 0.6))  # Proportionnel
        PADDING_BETWEEN = max(1, int(button_size / 40))  # Proportionnel
        
        # Style pour les labels de coordonnées
        label_style = {
            'bg': "#2c3e50",
            'fg': "#ecf0f1", 
            'font': ('Arial', font_small, 'bold'),
            'width': 0,
            'anchor': 'center'
        }
        
        # Top column labels
        top_col_frame = tk.Frame(board_container, bg="#2c3e50")
        top_col_frame.pack(pady=(20, 6))  # Augmenté : (15, 4) → (20, 6)
        
        # Espacement gauche
        left_spacer = tk.Frame(top_col_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=1)
        left_spacer.pack(side=tk.LEFT)
        left_spacer.pack_propagate(False)
        
        # Labels des colonnes a-h
        for col in "abcdefgh":
            label_frame = tk.Frame(top_col_frame, bg="#2c3e50", width=BUTTON_PIXEL_WIDTH, height=30)  # Augmenté : 25 → 30
            label_frame.pack(side=tk.LEFT, padx=PADDING_BETWEEN)
            label_frame.pack_propagate(False)
            
            label = tk.Label(label_frame, text=col, **label_style)
            label.pack(expand=True, fill=tk.BOTH)
        
        # Espacement droit
        right_spacer = tk.Frame(top_col_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=1)
        right_spacer.pack(side=tk.LEFT)
        right_spacer.pack_propagate(False)
        
        # Frame principal pour l'échiquier
        main_board_frame = tk.Frame(board_container, bg="#2c3e50")
        main_board_frame.pack()
        
        self.buttons = []
        for row in range(8):
            row_frame = tk.Frame(main_board_frame, bg="#2c3e50")
            row_frame.pack(pady=PADDING_BETWEEN)
            
            # Label de rangée gauche
            left_label_frame = tk.Frame(row_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=BUTTON_PIXEL_WIDTH)
            left_label_frame.pack(side=tk.LEFT)
            left_label_frame.pack_propagate(False)
            
            left_label = tk.Label(left_label_frame, text=str(8-row), **label_style)
            left_label.pack(expand=True, fill=tk.BOTH)
            
            button_row = []
            for col in range(8):
                # Couleur alternée des cases
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                
                # Bouton avec taille EXACTE en pixels
                button_frame = tk.Frame(row_frame, width=BUTTON_PIXEL_WIDTH, height=BUTTON_PIXEL_WIDTH)
                button_frame.pack(side=tk.LEFT, padx=PADDING_BETWEEN)
                button_frame.pack_propagate(False)
                
                button = tk.Button(
                    button_frame,
                    text="",
                    font=('Arial', font_large, 'bold'),
                    bg=color,
                    relief=tk.FLAT,
                    bd=2,
                    activebackground=color,
                    command=lambda r=row, c=col: self.on_square_click(r, c)
                )
                button.pack(expand=True, fill=tk.BOTH)
                button_row.append(button)
            
            # Label de rangée droit
            right_label_frame = tk.Frame(row_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=BUTTON_PIXEL_WIDTH)
            right_label_frame.pack(side=tk.LEFT)
            right_label_frame.pack_propagate(False)
            
            right_label = tk.Label(right_label_frame, text=str(8-row), **label_style)
            right_label.pack(expand=True, fill=tk.BOTH)
            
            self.buttons.append(button_row)
        
        # Bottom column labels
        bottom_col_frame = tk.Frame(board_container, bg="#2c3e50")
        bottom_col_frame.pack(pady=(6, 20))  # Augmenté : (4, 15) → (6, 20)
        
        # Espacement gauche
        left_spacer_bottom = tk.Frame(bottom_col_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=1)
        left_spacer_bottom.pack(side=tk.LEFT)
        left_spacer_bottom.pack_propagate(False)
        
        # Labels colonnes
        for col in "abcdefgh":
            label_frame_bottom = tk.Frame(bottom_col_frame, bg="#2c3e50", width=BUTTON_PIXEL_WIDTH, height=30)
            label_frame_bottom.pack(side=tk.LEFT, padx=PADDING_BETWEEN)
            label_frame_bottom.pack_propagate(False)
            
            label_bottom = tk.Label(label_frame_bottom, text=col, **label_style)
            label_bottom.pack(expand=True, fill=tk.BOTH)
        
        # Espacement droit
        right_spacer_bottom = tk.Frame(bottom_col_frame, bg="#2c3e50", width=ROW_LABEL_PIXEL_WIDTH, height=1)
        right_spacer_bottom.pack(side=tk.LEFT)
        right_spacer_bottom.pack_propagate(False)
        
        # Stocker les dimensions
        self.button_size = button_size
        self.font_large = font_large
        
        # Initialiser l'échiquier
        self.setup_initial_position()
        
        print(f"SIZING DEBUG: Final - Button: {button_size}px, Font: {font_large}")

    def on_board_resize(self, event=None):
        """Handle board resize to maintain proportions."""
        # Cette méthode peut être appelée lors du redimensionnement
        # Pour l'instant, on ne fait rien, mais on pourrait recalculer les tailles
        pass
    
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
        """Handle square click events"""
        print(f"CLICK DEBUG: Square clicked at {row},{col}")
        print(f"CLICK DEBUG: is_my_turn = {self.is_my_turn}")
        print(f"CLICK DEBUG: current_match = {self.current_match}")
        print(f"CLICK DEBUG: player_color = {self.player_color}")
        
        # Vérifications de base
        if not self.is_my_turn:
            print(f"CLICK IGNORED - Not my turn")
            return
            
        if not self.current_match:
            print(f"CLICK IGNORED - No active match")
            return
            
        if not self.current_state:
            print(f"CLICK IGNORED - No current state")
            return
        
        print(f"CLICK DEBUG: All checks passed")
        
        # DEBUG : Afficher l'état du plateau
        piece_at_square = self.current_state["board"][row][col]
        print(f"CLICK DEBUG: Piece at {row},{col} = {piece_at_square}")
        
        if self.selected_square is None:
            # Mode sélection
            print(f"CLICK DEBUG: Trying to select piece at {row},{col}")
            
            if piece_at_square and piece_at_square["color"] == self.player_color:
                self.selected_square = (row, col)
                self.highlight_legal_moves(row, col)
                print(f"SELECTED piece at {row},{col}: {piece_at_square}")
                
                if hasattr(self.game_client, 'right_panel') and self.game_client.right_panel:
                    self.game_client.right_panel.update_status(f"Selected {piece_at_square['type']} at {chr(97+col)}{8-row}")
            else:
                if piece_at_square:
                    print(f"Cannot select: piece color {piece_at_square['color']} != my color {self.player_color}")
                else:
                    print(f"Cannot select: no piece at {row},{col}")
        
        else:
            # Mode mouvement
            from_row, from_col = self.selected_square
            print(f"CLICK DEBUG: Attempting move from {from_row},{from_col} to {row},{col}")
            
            if (row, col) == self.selected_square:
                # Désélectionner
                self.selected_square = None
                self.legal_moves = []
                self.update_board_display()
                print("DESELECTED piece")
                
                if hasattr(self.game_client, 'right_panel') and self.game_client.right_panel:
                    self.game_client.right_panel.update_status("Piece deselected")
            
            else:
                # Vérifier que la pièce de départ existe toujours
                from_piece = self.current_state["board"][from_row][from_col]
                if not from_piece or from_piece["color"] != self.player_color:
                    print(f"ERROR: Selected piece no longer exists or wrong color!")
                    self.selected_square = None
                    self.legal_moves = []
                    self.update_board_display()
                    return
                
                # Tenter un mouvement
                move = {
                    "from": [from_row, from_col],
                    "to": [row, col]
                }
                
                print(f"ATTEMPTING MOVE: {move}")
                
                # Vérifier la promotion des pions
                if (from_piece["type"] == "pawn" and 
                    ((from_piece["color"] == 1 and row == 0) or (from_piece["color"] == 2 and row == 7))):
                    promotion = self.get_promotion_choice()
                    if promotion:
                        move["promotion"] = promotion
                
                # NETTOYER la sélection AVANT d'envoyer
                self.selected_square = None
                self.legal_moves = []
                self.update_board_display()
                
                if hasattr(self.game_client, 'right_panel') and self.game_client.right_panel:
                    self.game_client.right_panel.update_status("Sending move...")
                
                # NOUVELLE STRATÉGIE : Marquer la case comme "tentative de mouvement"
                self.pending_move = move
                
                try:
                    # Envoyer le mouvement
                    asyncio.run_coroutine_threadsafe(
                        self.game_client.make_move(self.current_match, move),
                        self.game_client.loop
                    )
                    print(f"MOVE SENT successfully")
                    
                except Exception as e:
                    print(f"ERROR SENDING MOVE: {e}")
                    # Nettoyer l'état en cas d'erreur
                    self.pending_move = None
                    if hasattr(self.game_client, 'right_panel') and self.game_client.right_panel:
                        self.game_client.right_panel.update_status(f"Error: {e}")
    
    def get_promotion_choice(self):
        """Get user's choice for pawn promotion."""
        promotion_window = tk.Toplevel(self)
        promotion_window.title("Pawn Promotion")
        promotion_window.geometry("400x200")
        promotion_window.configure(bg="#2c3e50")
        promotion_window.transient(self)
        promotion_window.grab_set()
        
        # Center the promotion window
        promotion_window.update_idletasks()
        x = (promotion_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (promotion_window.winfo_screenheight() // 2) - (200 // 2)
        promotion_window.geometry(f"400x200+{x}+{y}")
        
        choice = {"value": "queen"}  # Default
        
        tk.Label(promotion_window, text="Choose promotion piece:",
                bg="#2c3e50", fg="white", font=('Arial', 14)).pack(pady=20)
        
        button_frame = tk.Frame(promotion_window, bg="#2c3e50")
        button_frame.pack(pady=15)
        
        pieces = ["queen", "rook", "bishop", "knight"]
        symbols = PIECE_SYMBOLS[self.player_color] if self.use_unicode else ASCII_PIECES[self.player_color]
        
        for piece in pieces:
            symbol = symbols[piece]
            btn = tk.Button(
                button_frame, text=f"{symbol}\n{piece.title()}",
                command=lambda p=piece: self.set_promotion_and_close(choice, p, promotion_window),
                bg="#3498db", fg="white", font=('Arial', 11),
                width=10, height=4
            )
            btn.pack(side=tk.LEFT, padx=8)
        
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
        """Basic move validation for highlighting (not comprehensive)"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Can't capture own piece
        if target and target["color"] == piece["color"]:
            return False
        
        # *** CORRECTION : Supprimer cette règle problématique ***
        # Le serveur gère déjà cette validation correctement
        # if target and target["type"] == "king":
        #     return False
        
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
                return target is not None  # Capture normale
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
        # This will be handled by the right panel
        print(f"Status: {message}")
    
    def update_turn_info(self, is_my_turn, current_player_color):
        """Update turn information display."""
        self.is_my_turn = is_my_turn
        # This will be handled by the right panel
    
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
        # This will be handled by the right panel
        pass


class RightPanel(tk.Frame):
    """Right panel with game controls and information"""
    
    def __init__(self, master, game_client):
        screen_width = master.winfo_screenwidth()
        
        if screen_width < 1200:
            panel_width = 240  # Augmenté : 220 → 240
        elif screen_width < 1600:
            panel_width = 280  # Augmenté : 260 → 280  
        else:
            panel_width = 320  # Augmenté : 300 → 320
            
        super().__init__(master, bg="#34495e", width=panel_width)
        self.game_client = game_client
        self.pack_propagate(False)
        
        print(f"PANEL DEBUG: Screen {screen_width}px -> Panel {panel_width}px")
        
        self.create_panels()
    
    def create_panels(self):
        """Create all panels in the right sidebar"""
        # Title avec police plus grande
        title_label = tk.Label(self, text="♔ Chess Control Panel ♛", 
                              bg="#34495e", fg="white", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(25, 15), padx=25)
        
        # Game Status Panel
        self.create_status_panel()
        
        # Connection Panel  
        self.create_connection_panel()
        
        # Game Controls Panel
        self.create_controls_panel()
        
        # Captured Pieces Panel
        self.create_captured_panel()
        
        # Spacer to push everything up
        spacer = tk.Frame(self, bg="#34495e", height=50)
        spacer.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_status_panel(self):
        """Create the game status panel - VERSION PLUS GRANDE."""
        status_frame = tk.LabelFrame(self, text="Game Status", 
                                   bg="#2c3e50", fg="white", font=('Arial', 14, 'bold'),
                                   relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, padx=25, pady=(0, 20))
        
        self.status_label = tk.Label(status_frame, text="Waiting for match...", 
                                   bg="#2c3e50", fg="white", font=('Arial', 12),
                                   wraplength=350, justify=tk.LEFT)
        self.status_label.pack(pady=15, padx=15)
        
        self.turn_label = tk.Label(status_frame, text="", bg="#2c3e50", fg="white",
                                 font=('Arial', 14, 'bold'))
        self.turn_label.pack(pady=(0, 15), padx=15)
    
    def create_connection_panel(self):
        """Create the connection controls panel - VERSION PLUS COMPACTE."""
        conn_frame = tk.LabelFrame(self, text="Connection", 
                                bg="#2c3e50", fg="white", font=('Arial', 12, 'bold'),
                                relief=tk.RAISED, bd=2)
        conn_frame.pack(fill=tk.X, padx=20, pady=(0, 15))  # padding réduit
        
        # Connect button - PLUS COMPACT
        self.connect_button = tk.Button(
            conn_frame, text="Connect to Server",
            command=lambda: asyncio.run_coroutine_threadsafe(
                self.game_client.connect_and_register(), self.game_client.loop),
            bg="#27ae60", fg="white", font=('Arial', 10, 'bold'),  # police plus petite
            padx=15, pady=8, height=1  # height=1 au lieu de 2
        )
        self.connect_button.pack(fill=tk.X, padx=15, pady=10)  # padding réduit
        
        # Queue button - PLUS COMPACT
        self.queue_button = tk.Button(
            conn_frame, text="Join Chess Queue",
            command=lambda: asyncio.run_coroutine_threadsafe(
                self.game_client.join_queue(), self.game_client.loop),
            bg="#3498db", fg="white", font=('Arial', 10, 'bold'),  # police plus petite
            padx=15, pady=8, height=1  # height=1 au lieu de 2
        )
        self.queue_button.pack(fill=tk.X, padx=15, pady=(0, 10))  # padding réduit
        
        # Disconnect button - PLUS COMPACT
        self.disconnect_button = tk.Button(
            conn_frame, text="Disconnect",
            command=lambda: asyncio.run_coroutine_threadsafe(
                self.game_client.disconnect(), self.game_client.loop),
            bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'),  # police plus petite
            padx=15, pady=8, height=1  # height=1 au lieu de 2
        )
        self.disconnect_button.pack(fill=tk.X, padx=15, pady=(0, 10))  # padding réduit
    
    def create_controls_panel(self):
        """Create the game controls panel - SANS BOUTON FORCE ENABLE."""
        controls_frame = tk.LabelFrame(self, text="Game Controls", 
                                    bg="#2c3e50", fg="white", font=('Arial', 12, 'bold'),
                                    relief=tk.RAISED, bd=2)
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 15))  # padding réduit
        
        # Toggle pieces button - PLUS COMPACT
        self.unicode_button = tk.Button(
            controls_frame, text="Toggle Pieces (Unicode/ASCII)",
            command=self.toggle_pieces,
            bg="#9b59b6", fg="white", font=('Arial', 10),  # police plus petite
            padx=15, pady=8, height=1  # height=1 au lieu de 2
        )
        self.unicode_button.pack(fill=tk.X, padx=15, pady=10)  # padding réduit
        
        # Resign button - PLUS COMPACT (PAS DE BOUTON FORCE ENABLE)
        self.resign_button = tk.Button(
            controls_frame, text="Resign Game",
            command=self.resign_game,
            bg="#e67e22", fg="white", font=('Arial', 10),  # police plus petite
            padx=15, pady=8, height=1  # height=1 au lieu de 2
        )
        self.resign_button.pack(fill=tk.X, padx=15, pady=(0, 10))  # padding réduit

    def force_enable_turn(self):
        """Force enable turn if the player is stuck."""
        if hasattr(self.game_client, 'game_board') and self.game_client.game_board:
            self.game_client.game_board.is_my_turn = True
            self.update_status("🔓 Turn force-enabled!")
            print("🔧 MANUAL TURN FORCE-ENABLED by user")
    
    def create_captured_panel(self):
        """Create the captured pieces panel - VERSION PLUS GRANDE."""
        captured_frame = tk.LabelFrame(self, text="Captured Pieces", 
                                     bg="#2c3e50", fg="white", font=('Arial', 14, 'bold'),
                                     relief=tk.RAISED, bd=2)
        captured_frame.pack(fill=tk.X, padx=25, pady=(0, 20))
        
        self.captured_white_label = tk.Label(captured_frame, text="White: ", 
                                           bg="#2c3e50", fg="white", font=('Arial', 12),
                                           wraplength=350, justify=tk.LEFT)
        self.captured_white_label.pack(pady=(15, 8), padx=20, anchor=tk.W)
        
        self.captured_black_label = tk.Label(captured_frame, text="Black: ",
                                           bg="#2c3e50", fg="white", font=('Arial', 12),
                                           wraplength=350, justify=tk.LEFT)
        self.captured_black_label.pack(pady=(0, 15), padx=20, anchor=tk.W)
    
    def toggle_pieces(self):
        """Toggle piece display style."""
        if hasattr(self.game_client, 'game_board') and self.game_client.game_board:
            self.game_client.game_board.toggle_piece_style()
    
    def resign_game(self):
        """Resign the current game."""
        if hasattr(self.game_client, 'game_board') and self.game_client.game_board:
            self.game_client.game_board.resign_game()
    
    def update_status(self, message):
        """Update the status message."""
        self.status_label.config(text=message)
    
    def update_turn_info(self, is_my_turn, current_player_color):
        """Update turn information display."""
        if is_my_turn:
            self.turn_label.config(text="🔥 YOUR TURN", fg="#2ecc71")
        else:
            color_name = "White" if current_player_color == 1 else "Black"
            self.turn_label.config(text=f"⏳ {color_name}'s turn", fg="#e74c3c")
    
    def update_captured_pieces(self, captured):
        """Update the display of captured pieces."""
        symbols = PIECE_SYMBOLS  # Always use Unicode for captured pieces
        
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
        self.right_panel = None
        
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
        """Make a move in the current game - VERSION AVEC DEBUG."""
        print(f"🚀 SENDING MOVE: {move} for match {match_id}")
        print(f"🚀 PLAYER ID: {self.player_id}")
        
        try:
            await self.sio.emit('make_move', {
                'match_id': match_id,
                'player_id': self.player_id,
                'move': move
            })
            print(f"MOVE SENT SUCCESSFULLY")
        except Exception as e:
            print(f"ERROR SENDING MOVE: {e}")
            # Update status in UI
            if self.root and self.right_panel:
                self.root.after(0, lambda: self.right_panel.update_status(f"Error sending move: {e}"))
    
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
        if self.root and self.right_panel:
            self.root.after(0, lambda: self.right_panel.update_status("Connected to server"))
    
    async def on_disconnect(self):
        """Handle disconnection from server."""
        print("Disconnected from chess matchmaking server")
        if self.root and self.right_panel:
            self.root.after(0, lambda: self.right_panel.update_status("Disconnected from server"))
    
    async def on_registered(self, data):
        """Handle registration confirmation."""
        self.player_id = data.get('player_id')
        print(f"Registered as {self.username} (ID: {self.player_id})")
        
        if self.root and self.right_panel:
            self.root.after(0, lambda: self.right_panel.update_status(f"Registered as {self.username}"))
    
    async def on_queue_joined(self, data):
        """Handle confirmation of joining the queue."""
        position = data.get('position', 0)
        print(f"Joined chess matchmaking queue. Position: {position}")
        
        if self.root and self.right_panel:
            self.root.after(0, lambda: self.right_panel.update_status(f"In chess queue. Position: {position}"))
    

    async def on_match_found(self, data):
        """Handle a successful match"""
        self.current_match = data.get('match_id')
        opponent = data.get('opponent', 'Unknown')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        
        print(f"🎮 MATCH DEBUG: Chess match found!")
        print(f"🎮 MATCH DEBUG: Match ID: {self.current_match}")
        print(f"🎮 MATCH DEBUG: Your turn: {your_turn}")
        print(f"🎮 MATCH DEBUG: Opponent: {opponent}")
        print(f"🎮 MATCH DEBUG: Current player in state: {state.get('current_player', 'UNKNOWN')}")
        
        # CORRECTION IMPORTANTE : Déterminer la couleur du joueur
        # Le premier joueur (player1) est toujours blanc (1)
        # Le deuxième joueur (player2) est toujours noir (2)
        
        if self.root and self.game_board and self.right_panel:
            # CORRECTION : Déterminer la couleur en fonction de your_turn et current_player
            if your_turn and state.get('current_player') == 1:
                # Si c'est mon tour et current_player = 1, je suis le joueur 1 (blanc)
                self.game_board.player_color = 1
            elif not your_turn and state.get('current_player') == 1:
                # Si ce n'est pas mon tour et current_player = 1, je suis le joueur 2 (noir)
                self.game_board.player_color = 2
            else:
                # Fallback basé sur l'état initial
                self.game_board.player_color = 1 if your_turn else 2
            
            self.game_board.current_match = self.current_match
            self.game_board.current_state = state
            
            # CORRECTION : Ne forcer le tour qu'UNE SEULE FOIS
            self.game_board.is_my_turn = your_turn
            
            color_name = "White" if self.game_board.player_color == 1 else "Black"
            
            print(f"🎮 MATCH DEBUG: Player color set to {self.game_board.player_color} ({color_name})")
            print(f"🎮 MATCH DEBUG: Turn set to {your_turn}")
            
            # Update display
            self.root.after(0, lambda: self.game_board.update_board_display())
            self.root.after(0, lambda: self.right_panel.update_turn_info(your_turn, state.get('current_player', 1)))
            self.root.after(0, lambda: self.right_panel.update_status(
                f"Playing as {color_name} vs {opponent} - {'YOUR TURN' if your_turn else 'WAITING'}"
            ))
            
            if state.get("captured_pieces"):
                self.root.after(0, lambda: self.right_panel.update_captured_pieces(state["captured_pieces"]))

    async def on_game_update(self, data):
        """Handle game state updates"""
        match_id = data.get('match_id')
        state = data.get('state', {})
        your_turn = data.get('your_turn', False)
        winner = data.get('winner')
        game_over = data.get('game_over', False)
        is_draw = data.get('is_draw', False)
        
        if match_id != self.current_match:
            return
        
        print(f"GAME UPDATE DEBUG: Your turn: {your_turn}")
        print(f"GAME UPDATE DEBUG: Current player in state: {state.get('current_player', 'UNKNOWN')}")
        print(f"GAME UPDATE DEBUG: Game over: {game_over}")
        print(f"GAME UPDATE DEBUG: My player_color: {getattr(self.game_board, 'player_color', 'UNKNOWN')}")
        
        if self.root and self.game_board and self.right_panel:
            # MISE À JOUR CRITIQUE : S'assurer que l'état du jeu est cohérent
            self.game_board.current_state = state
            self.game_board.last_move = state.get('last_move')
            
            # Nettoyer le mouvement en attente s'il y en a un
            if hasattr(self.game_board, 'pending_move'):
                self.game_board.pending_move = None
            
            # *** CORRECTION ABSOLUE: FORCER LA MISE À JOUR DU TOUR ***
            def update_turn():
                old_turn = self.game_board.is_my_turn
                new_turn = your_turn and not game_over
                
                # FORCER ABSOLUMENT la mise à jour du tour
                self.game_board.is_my_turn = new_turn
                
                print(f"🔄 ABSOLUTE TURN UPDATE: {old_turn} -> {new_turn}")
                
                if new_turn:
                    print(f"✅ TURN ABSOLUTELY ENABLED: It's my turn! I am player color {self.game_board.player_color}")
                    print(f"✅ TURN ABSOLUTELY ENABLED: Current game player is {state.get('current_player')}")
                else:
                    print(f"❌ TURN DISABLED: Not my turn")
            
            # Exécuter IMMÉDIATEMENT la mise à jour du tour
            self.root.after(0, update_turn)
            self.root.after(0, lambda: self.game_board.update_board_display())
            
            if state.get("captured_pieces"):
                self.root.after(0, lambda: self.right_panel.update_captured_pieces(state["captured_pieces"]))
            
            if game_over:
                if is_draw:
                    result_msg = "Game ended in a draw!"
                    self.root.after(0, lambda: self.right_panel.update_status("Game over - Draw!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
                elif winner == self.player_id:
                    result_msg = "Congratulations! You won!"
                    self.root.after(0, lambda: self.right_panel.update_status("You won!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
                else:
                    result_msg = "You lost. Better luck next time!"
                    self.root.after(0, lambda: self.right_panel.update_status("You lost!"))
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", result_msg))
            else:
                self.root.after(0, lambda: self.right_panel.update_turn_info(your_turn, state.get('current_player', 1)))
                
                # Simplifier la gestion des échecs
                if your_turn:
                    self.root.after(0, lambda: self.right_panel.update_status("🔥 YOUR TURN"))
                else:
                    self.root.after(0, lambda: self.right_panel.update_status("⏳ Opponent's turn"))
    
    async def on_opponent_disconnected(self, data):
        """Handle opponent disconnection."""
        match_id = data.get('match_id')
        
        if match_id != self.current_match:
            return
        
        print("Opponent disconnected from chess match")
        
        if self.root and self.right_panel:
            self.root.after(0, lambda: self.right_panel.update_status("🏆 Opponent disconnected. You win!"))
            self.root.after(0, lambda: messagebox.showinfo("Game Over", "Opponent disconnected. You win!"))
    
    async def on_error(self, data):
        """Handle error messages from the server - VERSION AVEC DÉBLOCAGE."""
        message = data.get('message', 'Unknown error')
        print(f"SERVER ERROR: {message}")
        
        if self.root:
            # Re-enable turn if it was a move error
            if "move" in message.lower() and self.game_board:
                def re_enable_turn():
                    self.game_board.is_my_turn = True
                    self.game_board.set_turn(True)
                    print(f"🔧 RE-ENABLED TURN after error")
                
                self.root.after(0, re_enable_turn)
            
            self.root.after(0, lambda: messagebox.showerror("Error", message))
            
            # Update status in right panel
            if self.right_panel:
                self.root.after(0, lambda: self.right_panel.update_status(f"Error: {message}"))
    
    def start_gui(self):
        """Start the GUI application"""
        self.root = tk.Tk()
        self.root.title("Chess Client - Matchmaking Server")
        self.root.configure(bg="#2c3e50")
        
        # FORCER LE PLEIN ÉCRAN AUTOMATIQUE
        try:
            # Essayer plusieurs méthodes selon l'OS
            self.root.state('zoomed')  # Windows
        except:
            try:
                self.root.attributes('-zoomed', True)  # Linux
            except:
                try:
                    self.root.attributes('-fullscreen', True)  # Alternative
                except:
                    # Fallback : taille maximale manuelle
                    self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        # FORCER LA FENÊTRE AU PREMIER PLAN
        self.root.lift()  # Mettre au premier plan
        self.root.attributes('-topmost', True)  # Toujours au dessus
        self.root.after(100, lambda: self.root.attributes('-topmost', False))  # Désactiver après 100ms
        self.root.focus_force()  # Forcer le focus
        
        # Get username before setup
        self.username = tk.simpledialog.askstring("Username", "Enter your username:", parent=self.root)
        if not self.username:
            self.username = f"ChessPlayer_{hash(os.urandom(4)) % 1000}"
        
        # Main container
        main_container = tk.Frame(self.root, bg="#2c3e50")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        title_frame = tk.Frame(main_container, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text=f"♔ Chess Matchmaking - {self.username} ♛", 
                            bg="#2c3e50", fg="white", font=('Arial', 18, 'bold'))
        title_label.pack(expand=True)
        
        # Content area with proper proportions
        content_frame = tk.Frame(main_container, bg="#2c3e50")
        content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Board frame (LEFT side) - takes most of the width
        board_frame = tk.Frame(content_frame, bg="#2c3e50")
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5))
        
        self.game_board = ChessBoard(board_frame, self)
        self.game_board.pack(expand=True, fill=tk.BOTH)
        
        # Right panel (RIGHT side) - fixed width
        self.right_panel = RightPanel(content_frame, self)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 10), pady=10)
        
        # Start asyncio event loop
        self.loop = asyncio.new_event_loop()
        
        def run_async_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        import threading
        threading.Thread(target=run_async_loop, daemon=True).start()
        
        # Connect automatically
        asyncio.run_coroutine_threadsafe(self.connect_and_register(), self.loop)
        
        # Keyboard shortcuts
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # ASSURER QUE LA FENÊTRE RESTE AU PREMIER PLAN AU DÉMARRAGE
        self.root.after(200, self.ensure_foreground)
        
        # Start main loop
        self.root.mainloop()
        
        # Cleanup
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
            self.loop.stop()

    def on_window_resize(self, event=None):
        """Handle window resize events."""
        if event and event.widget == self.root:
            # La fenêtre a été redimensionnée, on pourrait recalculer les tailles
            if hasattr(self, 'game_board') and self.game_board:
                # Planifier une mise à jour du board après un court délai
                self.root.after(100, self.update_board_size)

    def update_board_size(self):
        """Update board size based on current window size."""
        # Cette méthode peut être appelée pour recalculer les tailles du board
        # Pour l'instant, le redimensionnement automatique se fait via le layout
        pass

    def reset_board_size(self):
        """Reset board to optimal size (Ctrl+R shortcut)."""
        if hasattr(self, 'game_board') and self.game_board:
            # Forcer une recreation du board avec nouvelles dimensions
            print("🔄 Resetting board size...")
            # On pourrait implémenter une recreation complète ici si nécessaire

    def toggle_fullscreen(self):
        """Toggle fullscreen mode (F11 shortcut)."""
        try:
            current_state = self.root.attributes('-fullscreen')
            if current_state:
                self.root.attributes('-fullscreen', False)
                self.root.state('zoomed')  # Passer en mode fenêtré maximisé
            else:
                self.root.attributes('-fullscreen', True)
        except:
            # Fallback pour les systèmes qui ne supportent pas -fullscreen
            if self.root.state() == 'zoomed':
                self.root.state('normal')
            else:
                self.root.state('zoomed')

    def ensure_foreground(self):
        """S'assurer que la fenêtre reste au premier plan."""
        self.root.lift()
        self.root.focus_force()
        # Répéter une fois de plus après 500ms pour être sûr
        self.root.after(500, lambda: self.root.lift())
    
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