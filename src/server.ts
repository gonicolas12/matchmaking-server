import express from 'express';
import http from 'http';
import { Server, Socket } from 'socket.io';
import path from 'path';
import cors from 'cors';
import { DatabaseService } from './services/database';
import { GameLogicService } from './services/gamelogic';

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
        <title>Matchmaking Server</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          h1 { color: #333; }
          p { line-height: 1.6; }
        </style>
      </head>
      <body>
        <h1>Matchmaking Server</h1>
        <p>Le serveur de matchmaking est en cours d'exécution. Utilisez le client Python pour vous connecter.</p>
        <p>Statut du serveur : <span style="color: green; font-weight: bold;">En ligne</span></p>
        <p>Port : ${PORT}</p>
        <p>Date de démarrage : ${new Date().toLocaleString()}</p>
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
}

// In-memory storage for active matches
interface ActiveMatch {
    id: number;
    player1Id: number;
    player2Id: number;
    gameState: any;
    currentPlayer: number;
    isFinished: boolean;
    playerMapping?: Record<number, number>;
}

// In-memory state
let queue: Player[] = [];
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

    // Handle queue joining
    socket.on('join_queue', async (data: { player_id: number, username: string }) => {
        try {
            const { player_id, username } = data;

            // Validate player
            if (!player_id) {
                return socket.emit('error', { message: "Invalid player ID" });
            }

            // Check if player is already in queue
            const existingPlayer = queue.find(p => p.id === player_id);
            if (existingPlayer) {
                return socket.emit('error', { message: "Already in queue" });
            }

            // Add player to database queue
            await db.addPlayerToQueue(player_id, username);

            // Add player to in-memory queue
            const player: Player = {
                id: player_id,
                username,
                socketId: socket.id,
                joinedAt: new Date()
            };

            queue.push(player);

            socket.emit('queue_joined', { position: queue.length });

            console.log(`Player ${username} (ID: ${player_id}) joined queue. Queue size: ${queue.length}`);

            // Process queue immediately in case we can make a match
            processQueue();
        } catch (error) {
            console.error("Error joining queue:", error);
            socket.emit('error', { message: "Failed to join queue" });
        }
    });

    // Handle game moves
    socket.on('make_move', async (data) => {
        try {
            const { match_id, player_id, move } = data;

            // Get match from memory or database
            let match = activeMatches.get(match_id);
            if (!match) {
                const dbMatch = await db.getMatch(match_id);
                if (!dbMatch || dbMatch.is_finished) {
                    return socket.emit('error', { message: "Match not found or already finished" });
                }

                // Create in-memory match object
                match = {
                    id: dbMatch.match_id,
                    player1Id: dbMatch.player1_id,
                    player2Id: dbMatch.player2_id,
                    gameState: dbMatch.game_state,
                    currentPlayer: dbMatch.game_state.current_player,
                    isFinished: dbMatch.is_finished
                };

                activeMatches.set(match_id, match);
            }

            // Modification cruciale: déterminer le joueur actuel en fonction de l'ordre des joueurs, pas de l'ID
            const isPlayer1 = player_id === match.player1Id;
            const isPlayer2 = player_id === match.player2Id;

            // Si c'est au tour du joueur 1 (current_player = 1) et que le joueur est player1,
            // OU si c'est au tour du joueur 2 (current_player = 2) et que le joueur est player2,
            // alors c'est bien au tour du joueur
            const isPlayerTurn = (match.gameState.current_player === 1 && isPlayer1) ||
                (match.gameState.current_player === 2 && isPlayer2);

            // Validate if it's the player's turn
            if (!isPlayerTurn) {
                return socket.emit('error', { message: "Not your turn" });
            }

            // Pour appliquer le coup, nous devons mapper l'ID du joueur à 1 ou 2
            const gamePlayerId = isPlayer1 ? 1 : 2;

            // Validate move with game logic
            const isValidMove = await gameLogic.validateMove(match.gameState, move, gamePlayerId);
            if (!isValidMove) {
                return socket.emit('error', { message: "Invalid move" });
            }

            // Apply move to game state using the mapped ID
            const newState = await gameLogic.applyMove(match.gameState, move, gamePlayerId);

            // Record turn in database with the original player_id
            await db.recordTurn(match_id, player_id, move);

            // Update match state in database
            await db.updateMatchState(match_id, newState);

            // Check for game over
            const winner = await gameLogic.checkWinner(newState);
            const isGameOver = await gameLogic.isGameOver(newState);

            // Update in-memory match
            match.gameState = newState;
            match.currentPlayer = newState.current_player;

            if (isGameOver) {
                match.isFinished = true;
                // Mapper le vainqueur de la logique de jeu (1 ou 2) à l'ID réel du joueur
                // Si winner est null (match nul), on garde null
                const realWinnerId = winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null;
                await db.finishMatch(match_id, realWinnerId);
            }

            // Update in-memory match
            activeMatches.set(match_id, match);

            // Notify both players with updated logic for draw detection
            notifyMatchPlayers(match, winner, isGameOver);

            console.log(`Move made in match ${match_id} by player ${player_id}. Game over: ${isGameOver}, Winner: ${winner || 'draw'}`);
        } catch (error) {
            console.error("Error handling move:", error);
            socket.emit('error', { message: "Failed to process move" });
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

// Process the matchmaking queue
async function processQueue() {
    if (queue.length < 2) return;

    // Sort queue by join time
    queue.sort((a, b) => a.joinedAt.getTime() - b.joinedAt.getTime());

    // Match first two players
    const player1 = queue.shift();
    const player2 = queue.shift();

    if (!player1 || !player2) return;

    try {
        // Create match in database
        const match = await db.createMatch(player1.id, player2.id);

        // Initialize game state
        const gameState = await gameLogic.initializeGame('tic-tac-toe');

        // Update match state in database
        await db.updateMatchState(match.match_id, gameState);

        // Create in-memory match
        const activeMatch: ActiveMatch = {
            id: match.match_id,
            player1Id: player1.id,
            player2Id: player2.id,
            gameState,
            currentPlayer: gameState.current_player,
            isFinished: false
        };

        // Add to active matches
        activeMatches.set(match.match_id, activeMatch);

        // Get player sockets
        const socket1 = playerSockets.get(player1.id);
        const socket2 = playerSockets.get(player2.id);

        // Notify players - le premier joueur (player1) commence toujours
        if (socket1) {
            socket1.emit('match_found', {
                match_id: match.match_id,
                opponent: player2.username,
                state: gameState,
                your_turn: true  // Premier joueur (player1) commence toujours
            });
        }

        if (socket2) {
            socket2.emit('match_found', {
                match_id: match.match_id,
                opponent: player1.username,
                state: gameState,
                your_turn: false  // Deuxième joueur (player2) attend
            });
        }

        console.log(`Match created: ${player1.username} vs ${player2.username} (Match ID: ${match.match_id})`);
    } catch (error) {
        console.error("Error creating match:", error);

        // Put players back in queue if match creation fails
        if (player1) queue.push(player1);
        if (player2) queue.push(player2);
    }
}

// Notify players of match updates
function notifyMatchPlayers(match: ActiveMatch, winner: number | null, isGameOver: boolean = false) {
    const socket1 = playerSockets.get(match.player1Id);
    const socket2 = playerSockets.get(match.player2Id);

    // Le joueur dont l'ID correspond au current_player doit jouer
    const isPlayer1Turn = match.gameState.current_player === 1 && !isGameOver;

    if (socket1) {
        socket1.emit('game_update', {
            match_id: match.id,
            state: match.gameState,
            your_turn: isPlayer1Turn,
            // Mapper le vainqueur du jeu (1 ou 2) à l'ID réel du joueur pour la notification
            winner: winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null,
            game_over: isGameOver,
            is_draw: isGameOver && winner === null
        });
    }

    if (socket2) {
        socket2.emit('game_update', {
            match_id: match.id,
            state: match.gameState,
            your_turn: !isPlayer1Turn && !isGameOver,
            // Mapper le vainqueur du jeu (1 ou 2) à l'ID réel du joueur pour la notification
            winner: winner === 1 ? match.player1Id : winner === 2 ? match.player2Id : null,
            game_over: isGameOver,
            is_draw: isGameOver && winner === null
        });
    }
}

// Handle player disconnection
async function handlePlayerDisconnect(playerId: number, socketId: string) {
    // Remove from queue if in queue
    queue = queue.filter(p => p.id !== playerId);

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

    console.log(`Player ${playerId} disconnected and removed from queue/matches`);
}

// Start matchmaking processor at regular intervals
const queueCheckInterval = setInterval(processQueue, 5000);

// Start server
const PORT = process.env.PORT || 3000;
server.listen({
    port: PORT,
    host: '0.0.0.0'
}, () => {
    console.log(`Server running on port ${PORT}, accessible at http://0.0.0.0:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    clearInterval(queueCheckInterval);
    console.log('Shutting down server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});