import express from 'express';
import http from 'http';
import { Server, Socket } from 'socket.io';
import path from 'path';
import cors from 'cors';
import { DatabaseService } from './services/database';
import { GameLogicService } from './services/gamelogic';
import { networkInterfaces } from 'os';


// Initialize Express
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// Middleware
app.use(cors());
app.use(express.json());

// Home route
app.get('/', (req, res) => {
    res.send(`
    <html>
      <head>
        <title>Chess & Tic-Tac-Toe Matchmaking Server</title>
        <style>
          body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            max-width: 1000px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
          }
          .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
          }
          h1 { color: #fff; text-align: center; margin-bottom: 30px; }
          .game-card {
            background: rgba(255,255,255,0.15);
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            border-left: 4px solid #ffd700;
          }
          .status { color: #4ade80; font-weight: bold; }
          .feature-list { margin: 15px 0; }
          .feature-list li { margin: 8px 0; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>♔ Chess & Tic-Tac-Toe Matchmaking Server ♛</h1>
          
          <div class="game-card">
            <h2>🏆 Available Games</h2>
            <div class="feature-list">
              <h3>♟️ Chess</h3>
              <ul>
                <li>Full chess rules implementation</li>
                <li>Castling, en passant, pawn promotion</li>
                <li>Check, checkmate, and stalemate detection</li>
                <li>Beautiful Unicode piece display</li>
                <li>Move highlighting and validation</li>
              </ul>
              
              <h3>⭕ Tic-Tac-Toe</h3>
              <ul>
                <li>Classic 3x3 grid gameplay</li>
                <li>Simple and fast matches</li>
                <li>Perfect for quick games</li>
              </ul>
            </div>
          </div>
          
          <div class="game-card">
            <h2>📊 Server Status</h2>
            <p>Status: <span class="status">Online</span></p>
            <p>Port: ${PORT}</p>
            <p>Started: ${new Date().toLocaleString()}</p>
            <p>Active Players: <span id="playerCount">0</span></p>
            <p>Active Matches: <span id="matchCount">0</span></p>
          </div>
          
          <div class="game-card">
            <h2>🎮 How to Play</h2>
            <ol>
              <li>Run the Python client: <code>python chess_client.py</code> or <code>python game_client.py</code></li>
              <li>Enter your username</li>
              <li>Connect to the server</li>
              <li>Join the matchmaking queue</li>
              <li>Wait for an opponent and enjoy the game!</li>
            </ol>
          </div>
        </div>
      </body>
    </html>
  `);
});

// Initialize services
const db = new DatabaseService();
const gameLogic = new GameLogicService();

// In-memory storage for active players and their sockets
interface Player {
    id: number;
    username: string;
    socketId: string;
    joinedAt: Date;
    gameType?: string; // 'chess' or 'tic-tac-toe'
}

// In-memory storage for active matches
interface ActiveMatch {
    id: number;
    player1Id: number;
    player2Id: number;
    gameState: any;
    currentPlayer: number;
    isFinished: boolean;
    gameType: string;
    playerMapping?: Record<number, number>;
}

// Separate queues for different game types
let chessQueue: Player[] = [];
let ticTacToeQueue: Player[] = [];
let activeMatches: Map<number, ActiveMatch> = new Map();
let playerSockets: Map<number, Socket> = new Map();
let socketPlayers: Map<string, number> = new Map();

// Express routes
app.get('/api/games', async (req, res) => {
    try {
        const games = await db.getGames();
        res.json(games);
    } catch (error) {
        console.error("Error getting games:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

app.get('/api/stats', (req, res) => {
    res.json({
        chess_queue: chessQueue.length,
        tictactoe_queue: ticTacToeQueue.length,
        active_matches: activeMatches.size,
        total_players: playerSockets.size
    });
});

app.get('/api/players/:id', async (req, res) => {
    try {
        const player = await db.getPlayer(parseInt(req.params.id));
        if (!player) {
            return res.status(404).json({ error: "Player not found" });
        }
        res.json(player);
    } catch (error) {
        console.error("Error getting player:", error);
        res.status(500).json({ error: "Internal server error" });
    }
});

// Socket.IO handling
io.on('connection', (socket: Socket) => {
    console.log(`New connection: ${socket.id}`);

    // Handle player registration
    socket.on('register', async (data: { username: string }) => {
        try {
            const { username } = data;

            // Create or get player
            let player = await db.getPlayerByUsername(username);
            if (!player) {
                player = await db.createPlayer(username, socket.handshake.address, 0);
            }

            // Update player's last active timestamp
            await db.updatePlayerLastActive(player.player_id);

            // Store socket associations
            playerSockets.set(player.player_id, socket);
            socketPlayers.set(socket.id, player.player_id);

            socket.emit('registered', {
                player_id: player.player_id,
                username: player.username
            });

            console.log(`Player registered: ${player.username} (ID: ${player.player_id})`);
        } catch (error) {
            console.error("Error registering player:", error);
            socket.emit('error', { message: "Failed to register player" });
        }
    });

    // Handle queue joining with game type
    socket.on('join_queue', async (data: { player_id: number, username: string, game_type?: string }) => {
        try {
            const { player_id, username, game_type = 'tic-tac-toe' } = data;

            // Validate player
            if (!player_id) {
                return socket.emit('error', { message: "Invalid player ID" });
            }

            // Validate game type
            if (!['chess', 'tic-tac-toe'].includes(game_type)) {
                return socket.emit('error', { message: "Invalid game type. Choose 'chess' or 'tic-tac-toe'" });
            }

            // Remove player from all queues first
            chessQueue = chessQueue.filter(p => p.id !== player_id);
            ticTacToeQueue = ticTacToeQueue.filter(p => p.id !== player_id);

            // Add player to database queue
            await db.addPlayerToQueue(player_id, username);

            // Add player to appropriate in-memory queue
            const player: Player = {
                id: player_id,
                username,
                socketId: socket.id,
                joinedAt: new Date(),
                gameType: game_type
            };

            if (game_type === 'chess') {
                chessQueue.push(player);
                socket.emit('queue_joined', { 
                    position: chessQueue.length,
                    game_type: 'chess'
                });
                console.log(`Player ${username} joined chess queue. Queue size: ${chessQueue.length}`);
                processChessQueue();
            } else {
                ticTacToeQueue.push(player);
                socket.emit('queue_joined', { 
                    position: ticTacToeQueue.length,
                    game_type: 'tic-tac-toe'
                });
                console.log(`Player ${username} joined tic-tac-toe queue. Queue size: ${ticTacToeQueue.length}`);
                processTicTacToeQueue();
            }

        } catch (error) {
            console.error("Error joining queue:", error);
            socket.emit('error', { message: "Failed to join queue" });
        }
    });

    // Handle game moves
    socket.on('make_move', async (data) => {
        try {
            const { match_id, player_id, move } = data;
            
            console.log(`🎯 MOVE DEBUG: Player ${player_id} attempting move in match ${match_id}`);
            console.log(`🎯 MOVE DEBUG: Move data:`, move);

            // Get match from memory or database
            let match = activeMatches.get(match_id);
            if (!match) {
                const dbMatch = await db.getMatch(match_id);
                if (!dbMatch || dbMatch.is_finished) {
                    console.log(`❌ MOVE ERROR: Match ${match_id} not found or finished`);
                    return socket.emit('error', { message: "Match not found or already finished" });
                }

                // Create in-memory match object
                match = {
                    id: dbMatch.match_id,
                    player1Id: dbMatch.player1_id,
                    player2Id: dbMatch.player2_id,
                    gameState: dbMatch.game_state,
                    currentPlayer: dbMatch.game_state.current_player,
                    isFinished: dbMatch.is_finished,
                    gameType: determineGameTypeFromState(dbMatch.game_state)
                };

                activeMatches.set(match_id, match);
            }

            // Check if player is in the match
            const isPlayer1 = player_id === match.player1Id;
            const isPlayer2 = player_id === match.player2Id;
            
            if (!isPlayer1 && !isPlayer2) {
                console.log(`❌ MOVE ERROR: Player ${player_id} not in match ${match_id}`);
                return socket.emit('error', { message: "You are not in this match" });
            }

            // Map player ID to game player ID (1 or 2)
            const gamePlayerId = isPlayer1 ? 1 : 2;
            
            console.log(`🎯 MOVE DEBUG: Player ${player_id} -> Game Player ${gamePlayerId}`);
            console.log(`🎯 MOVE DEBUG: Current game player: ${match.gameState.current_player}`);

            // Check if it's the player's turn
            if (match.gameState.current_player !== gamePlayerId) {
                console.log(`❌ TURN ERROR: Not player ${gamePlayerId}'s turn (current: ${match.gameState.current_player})`);
                return socket.emit('error', { message: "Not your turn" });
            }

            // Validate move with game logic
            const isValidMove = await gameLogic.validateMove(match.gameState, move, gamePlayerId);
            if (!isValidMove) {
                console.log(`❌ VALIDATION ERROR: Invalid move for player ${gamePlayerId}`);
                return socket.emit('error', { message: "Invalid move" });
            }

            // Apply move to game state
            const newState = await gameLogic.applyMove(match.gameState, move, gamePlayerId);
            
            console.log(`✅ MOVE APPLIED: New current player: ${newState.current_player}`);

            // Record turn in database
            await db.recordTurn(match_id, player_id, move);

            // Update match state in database
            await db.updateMatchState(match_id, newState);

            // Check for game over
            const winner = await gameLogic.checkWinner(newState);
            const isGameOver = await gameLogic.isGameOver(newState);
            const isDraw = await gameLogic.isDraw(newState);

            console.log(`SERVER DEBUG: Winner: ${winner}, Game Over: ${isGameOver}, Draw: ${isDraw}`);
            console.log(`SERVER DEBUG: Game status: ${newState.game_status}`);

            // Update in-memory match
            match.gameState = newState;
            match.currentPlayer = newState.current_player;

            if (isGameOver) {
                match.isFinished = true;
                const realWinnerId = winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null;
                await db.finishMatch(match_id, realWinnerId);
            }

            activeMatches.set(match_id, match);

            // Notify players of the move
            console.log(`📤 NOTIFYING PLAYERS: Match ${match_id}, Winner: ${winner}, Game Over: ${isGameOver}`);
            notifyMatchPlayers(match, winner, isGameOver, isDraw);

            console.log(`✅ MOVE COMPLETED: Match ${match_id}, Player ${player_id} -> Game Player ${gamePlayerId}`);

        } catch (error: unknown) {
            console.error("❌ CRITICAL ERROR in make_move:", error);
            
            // Send error message to client
            let errorMessage = "Unknown error occurred";
            
            if (error instanceof Error) {
                errorMessage = error.message;
            } else if (typeof error === 'string') {
                errorMessage = error;
            } else if (error && typeof error === 'object' && 'message' in error) {
                errorMessage = String((error as any).message);
            }
            
            socket.emit('error', { message: "Failed to process move: " + errorMessage });
        }
    });

    // Handle resignation
    socket.on('resign_match', async (data) => {
        try {
            const { match_id, player_id } = data;
            
            const match = activeMatches.get(match_id);
            if (!match || match.isFinished) {
                return socket.emit('error', { message: "Match not found or already finished" });
            }

            // Determine winner (opponent)
            const winnerId = match.player1Id === player_id ? match.player2Id : match.player1Id;
            
            // Finish match
            match.isFinished = true;
            await db.finishMatch(match_id, winnerId);
            activeMatches.set(match_id, match);

            // Notify both players
            const socket1 = playerSockets.get(match.player1Id);
            const socket2 = playerSockets.get(match.player2Id);

            if (socket1) {
                socket1.emit('game_update', {
                    match_id: match.id,
                    state: match.gameState,
                    your_turn: false,
                    winner: winnerId,
                    game_over: true,
                    resignation: true,
                    resigned_player: player_id
                });
            }

            if (socket2) {
                socket2.emit('game_update', {
                    match_id: match.id,
                    state: match.gameState,
                    your_turn: false,
                    winner: winnerId,
                    game_over: true,
                    resignation: true,
                    resigned_player: player_id
                });
            }

            console.log(`Player ${player_id} resigned from match ${match_id}`);
        } catch (error) {
            console.error("Error handling resignation:", error);
            socket.emit('error', { message: "Failed to process resignation" });
        }
    });

    // Handle disconnect
    socket.on('disconnect', () => {
        const playerId = socketPlayers.get(socket.id);
        if (playerId) {
            handlePlayerDisconnect(playerId, socket.id);
        }

        console.log(`Socket disconnected: ${socket.id}`);
    });
});

// Process chess matchmaking queue
async function processChessQueue() {
    if (chessQueue.length < 2) return;

    // Sort queue by join time
    chessQueue.sort((a, b) => a.joinedAt.getTime() - b.joinedAt.getTime());

    // Match first two players
    const player1 = chessQueue.shift();
    const player2 = chessQueue.shift();

    if (!player1 || !player2) return;

    await createMatch(player1, player2, 'chess');
}

// Process tic-tac-toe matchmaking queue
async function processTicTacToeQueue() {
    if (ticTacToeQueue.length < 2) return;

    // Sort queue by join time
    ticTacToeQueue.sort((a, b) => a.joinedAt.getTime() - b.joinedAt.getTime());

    // Match first two players
    const player1 = ticTacToeQueue.shift();
    const player2 = ticTacToeQueue.shift();

    if (!player1 || !player2) return;

    await createMatch(player1, player2, 'tic-tac-toe');
}

// Create a match between two players
async function createMatch(player1: Player, player2: Player, gameType: string) {
    try {
        // Create match in database
        const match = await db.createMatch(player1.id, player2.id);

        // Initialize game state
        const gameState = await gameLogic.initializeGame(gameType);

        // Update match state in database
        await db.updateMatchState(match.match_id, gameState);

        // Create in-memory match
        const activeMatch: ActiveMatch = {
            id: match.match_id,
            player1Id: player1.id,
            player2Id: player2.id,
            gameState,
            currentPlayer: gameState.current_player,
            isFinished: false,
            gameType
        };

        // Add to active matches
        activeMatches.set(match.match_id, activeMatch);

        // Get player sockets
        const socket1 = playerSockets.get(player1.id);
        const socket2 = playerSockets.get(player2.id);

        // Notify players
        if (socket1) {
            socket1.emit('match_found', {
                match_id: match.match_id,
                opponent: player2.username,
                state: gameState,
                your_turn: true,
                game_type: gameType
            });
        }

        if (socket2) {
            socket2.emit('match_found', {
                match_id: match.match_id,
                opponent: player1.username,
                state: gameState,
                your_turn: false,
                game_type: gameType
            });
        }

        console.log(`${gameType} match created: ${player1.username} vs ${player2.username} (Match ID: ${match.match_id})`);
    } catch (error) {
        console.error("Error creating match:", error);

        // Put players back in queue if match creation fails
        if (gameType === 'chess') {
            if (player1) chessQueue.push(player1);
            if (player2) chessQueue.push(player2);
        } else {
            if (player1) ticTacToeQueue.push(player1);
            if (player2) ticTacToeQueue.push(player2);
        }
    }
}

// Notify players of match updates
function notifyMatchPlayers(match: ActiveMatch, winner: number | null, isGameOver: boolean = false, isDraw: boolean = false) {
    const socket1 = playerSockets.get(match.player1Id);
    const socket2 = playerSockets.get(match.player2Id);

    // Logique de tour corrigée
    const currentGamePlayer = match.gameState.current_player; // 1 or 2
    const isPlayer1Turn = currentGamePlayer === 1 && !isGameOver;
    const isPlayer2Turn = currentGamePlayer === 2 && !isGameOver;

    console.log(`🔄 NOTIFY DEBUG: Current game player: ${currentGamePlayer}`);
    console.log(`🔄 NOTIFY DEBUG: Player1 turn: ${isPlayer1Turn}, Player2 turn: ${isPlayer2Turn}`);

    if (socket1) {
        socket1.emit('game_update', {
            match_id: match.id,
            state: match.gameState,
            your_turn: isPlayer1Turn, // Player 1 joue quand current_player = 1
            winner: winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null,
            game_over: isGameOver,
            is_draw: isDraw
        });
    }

    if (socket2) {
        socket2.emit('game_update', {
            match_id: match.id,
            state: match.gameState,
            your_turn: isPlayer2Turn, // Player 2 joue quand current_player = 2
            winner: winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null,
            game_over: isGameOver,
            is_draw: isDraw
        });
    }
}

// Handle player disconnection
async function handlePlayerDisconnect(playerId: number, socketId: string) {
    // Remove from all queues
    chessQueue = chessQueue.filter(p => p.id !== playerId);
    ticTacToeQueue = ticTacToeQueue.filter(p => p.id !== playerId);

    // Remove socket associations
    playerSockets.delete(playerId);
    socketPlayers.delete(socketId);

    // Handle active matches
    for (const [matchId, match] of activeMatches.entries()) {
        if (match.player1Id === playerId || match.player2Id === playerId) {
            // Determine opponent
            const opponentId = match.player1Id === playerId ? match.player2Id : match.player1Id;

            // Mark match as finished with opponent as winner
            if (!match.isFinished) {
                await db.finishMatch(matchId, opponentId);
                match.isFinished = true;
                activeMatches.set(matchId, match);
            }

            // Notify opponent
            const opponentSocket = playerSockets.get(opponentId);
            if (opponentSocket) {
                opponentSocket.emit('opponent_disconnected', { match_id: matchId });
            }
        }
    }

    console.log(`Player ${playerId} disconnected and removed from queues/matches`);
}

// Utility function to determine game type from state
function determineGameTypeFromState(state: any): string {
    if (state && Array.isArray(state.board) && state.board.length === 8 &&
        Array.isArray(state.board[0]) && state.board[0].length === 8) {
        return 'chess';
    }
    return 'tic-tac-toe';
}

// Start matchmaking processors at regular intervals
const chessQueueInterval = setInterval(processChessQueue, 3000);
const ticTacToeQueueInterval = setInterval(processTicTacToeQueue, 3000);

// Start server
const PORT = process.env.PORT || 3000;
server.listen({
    port: PORT,
    host: '0.0.0.0'
}, () => {
    console.log(`🚀 Chess & Tic-Tac-Toe Matchmaking Server running on port ${PORT}`);
    console.log(`🌐 Local access: http://localhost:${PORT}`);
    console.log(`🌐 Network access: http://0.0.0.0:${PORT}`);
    console.log(`♟️  Chess client: python chess_client.py http://YOUR_IP:${PORT}`);
    console.log(`⭕ Tic-Tac-Toe client: python game_client.py http://YOUR_IP:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    clearInterval(chessQueueInterval);
    clearInterval(ticTacToeQueueInterval);
    console.log('Shutting down server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});


function getLocalIP(): string {
    const nets = networkInterfaces();
    const results = Object.create(null);

    for (const name of Object.keys(nets)) {
        for (const net of nets[name]!) {
            // Skip over non-IPv4 and internal (i.e. 127.0.0.1) addresses
            if (net.family === 'IPv4' && !net.internal) {
                if (!results[name]) {
                    results[name] = [];
                }
                results[name].push(net.address);
                return net.address; // Return first found IP
            }
        }
    }
    return 'localhost';
}