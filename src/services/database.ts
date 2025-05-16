import { Database } from 'sqlite3';
import path from 'path';

interface Player {
    player_id: number;
    username: string;
    ip_address: string;
    port: number;
    created_at: string;
    last_active: string;
}

interface QueueEntry {
    queue_id: number;
    player_id: number;
    joined_at: string;
    status: string;
}

interface Game {
    game_id: number;
    name: string;
    description: string;
    rules: string;
    default_state: string;
}

interface Match {
    match_id: number;
    player1_id: number;
    player2_id: number;
    game_id: number;
    start_time: string;
    end_time: string | null;
    game_state: any;
    is_finished: boolean;
}

interface Turn {
    turn_id: number;
    match_id: number;
    player_id: number;
    move_data: any;
    turn_number: number;
    created_at: string;
    username?: string;
}

interface CountResult {
    count: number;
}

export class DatabaseService {
    private db: Database;

    constructor() {
        const dbPath = path.join(__dirname, '../../database/database.sqlite');
        this.db = new Database(dbPath);
        this.initializeDatabase();
    }

    private initializeDatabase(): void {
        this.db.serialize(() => {
            // Create Players table
            this.db.run(`
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    port INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            `);

            // Create QueueEntries table
            this.db.run(`
                CREATE TABLE IF NOT EXISTS queue_entries (
                    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'waiting',
                    FOREIGN KEY (player_id) REFERENCES players(player_id)
                )
            `);

            // Create Games table
            this.db.run(`
                CREATE TABLE IF NOT EXISTS games (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    rules TEXT,
                    default_state TEXT
                )
            `);

            // Create Matches table
            this.db.run(`
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_id INTEGER NOT NULL,
                    player2_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL DEFAULT 1,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    game_state TEXT,
                    is_finished BOOLEAN DEFAULT 0,
                    FOREIGN KEY (player1_id) REFERENCES players(player_id),
                    FOREIGN KEY (player2_id) REFERENCES players(player_id),
                    FOREIGN KEY (game_id) REFERENCES games(game_id)
                )
            `);

            // Create Turns table
            this.db.run(`
                CREATE TABLE IF NOT EXISTS turns (
                    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    move_data TEXT NOT NULL,
                    turn_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches(match_id),
                    FOREIGN KEY (player_id) REFERENCES players(player_id)
                )
            `);

            // Insert default game
            this.db.run(`
                INSERT OR IGNORE INTO games (game_id, name, description, rules, default_state)
                VALUES (1, 'Tic-Tac-Toe', 'Classic 3x3 tic-tac-toe game', '{}', '{}')
            `);
        });
    }

    // Players
    async getPlayer(playerId: number): Promise<Player | undefined> {
        return new Promise((resolve, reject) => {
            this.db.get<Player>(
                'SELECT * FROM players WHERE player_id = ?',
                [playerId],
                (err: Error | null, row?: Player) => {
                    if (err) return reject(err);
                    resolve(row);
                }
            );
        });
    }

    async getPlayerByUsername(username: string): Promise<Player | undefined> {
        return new Promise((resolve, reject) => {
            this.db.get<Player>(
                'SELECT * FROM players WHERE username = ?',
                [username],
                (err: Error | null, row?: Player) => {
                    if (err) return reject(err);
                    resolve(row);
                }
            );
        });
    }

    async createPlayer(username: string, ip: string, port: number): Promise<Player> {
        const self = this; // Capture the reference to 'this' in a variable

        return new Promise((resolve, reject) => {
            this.db.run(
                'INSERT INTO players (username, ip_address, port) VALUES (?, ?, ?)',
                [username, ip, port],
                function (this: { lastID: number }, err: Error | null) {
                    if (err) return reject(err);

                    const lastId = this.lastID;

                    // Use 'self.db' instead of 'this.db'
                    self.db.get<Player>(
                        'SELECT * FROM players WHERE player_id = ?',
                        [lastId],
                        (err: Error | null, row?: Player) => {
                            if (err) return reject(err);
                            if (!row) return reject(new Error('Player not found after creation'));
                            resolve(row);
                        }
                    );
                }
            );
        });
    }

    async updatePlayerLastActive(playerId: number): Promise<void> {
        return new Promise((resolve, reject) => {
            this.db.run(
                'UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE player_id = ?',
                [playerId],
                (err: Error | null) => {
                    if (err) return reject(err);
                    resolve();
                }
            );
        });
    }

    // Queue
    async addPlayerToQueue(playerId: number, username: string): Promise<{ queue_id: number }> {
        // First ensure player exists
        let player = await this.getPlayer(playerId);

        if (!player) {
            player = await this.createPlayer(username, '', 0);
            playerId = player.player_id;
        }

        return new Promise((resolve, reject) => {
            this.db.run(
                'INSERT INTO queue_entries (player_id) VALUES (?)',
                [playerId],
                function (this: { lastID: number }, err: Error | null) {
                    if (err) return reject(err);
                    resolve({ queue_id: this.lastID });
                }
            );
        });
    }

    async getPlayersInQueue(): Promise<Array<QueueEntry & { username: string }>> {
        return new Promise((resolve, reject) => {
            this.db.all(
                `SELECT q.*, p.username 
                 FROM queue_entries q
                 JOIN players p ON q.player_id = p.player_id
                 WHERE q.status = 'waiting'
                 ORDER BY q.joined_at ASC`,
                [],
                (err: Error | null, rows?: Array<QueueEntry & { username: string }>) => {
                    if (err) return reject(err);
                    resolve(rows || []);
                }
            );
        });
    }

    // Matches
    async createMatch(player1Id: number, player2Id: number, gameId: number = 1): Promise<Match> {
        const self = this;
        return new Promise((resolve, reject) => {
            this.db.run(
                'INSERT INTO matches (player1_id, player2_id, game_id) VALUES (?, ?, ?)',
                [player1Id, player2Id, gameId],
                function (this: { lastID: number }, err: Error | null) {
                    if (err) return reject(err);

                    const lastId = this.lastID;

                    // Update queue entries status
                    self.db.run(
                        "UPDATE queue_entries SET status = 'matched' WHERE player_id IN (?, ?)",
                        [player1Id, player2Id]
                    );

                    // Get the created match
                    self.db.get<Match>(
                        'SELECT * FROM matches WHERE match_id = ?',
                        [lastId],
                        (err: Error | null, row?: Match) => {
                            if (err) return reject(err);
                            if (!row) return reject(new Error('Match not found after creation'));
                            resolve(row);
                        }
                    );
                }
            );
        });
    }

    async getMatch(matchId: number): Promise<Match | undefined> {
        return new Promise((resolve, reject) => {
            this.db.get<Match>(
                `SELECT * FROM matches WHERE match_id = ?`,
                [matchId],
                (err: Error | null, row?: Match) => {
                    if (err) return reject(err);

                    if (row && row.game_state && typeof row.game_state === 'string') {
                        try {
                            row.game_state = JSON.parse(row.game_state);
                        } catch (e) {
                            console.error("Failed to parse game state:", e);
                        }
                    }

                    resolve(row);
                }
            );
        });
    }

    async updateMatchState(matchId: number, state: any): Promise<void> {
        return new Promise((resolve, reject) => {
            this.db.run(
                'UPDATE matches SET game_state = ? WHERE match_id = ?',
                [JSON.stringify(state), matchId],
                (err: Error | null) => {
                    if (err) return reject(err);
                    resolve();
                }
            );
        });
    }

    async finishMatch(matchId: number, winnerId: number | null): Promise<void> {
        return new Promise((resolve, reject) => {
            this.db.run(
                'UPDATE matches SET is_finished = 1, end_time = CURRENT_TIMESTAMP WHERE match_id = ?',
                [matchId],
                (err: Error | null) => {
                    if (err) return reject(err);
                    resolve();
                }
            );
        });
    }

    async getActiveMatchesForPlayer(playerId: number): Promise<Match[]> {
        return new Promise((resolve, reject) => {
            this.db.all<Match>(
                `SELECT * FROM matches 
                 WHERE (player1_id = ? OR player2_id = ?) 
                 AND is_finished = 0`,
                [playerId, playerId],
                (err: Error | null, rows?: Match[]) => {
                    if (err) return reject(err);

                    if (rows) {
                        for (const row of rows) {
                            if (row.game_state && typeof row.game_state === 'string') {
                                try {
                                    row.game_state = JSON.parse(row.game_state);
                                } catch (e) {
                                    console.error("Failed to parse game state:", e);
                                }
                            }
                        }
                    }

                    resolve(rows || []);
                }
            );
        });
    }

    // Turns
    async recordTurn(matchId: number, playerId: number, move: any): Promise<{ turn_id: number }> {
        return new Promise((resolve, reject) => {
            // Get current turn number for this match
            this.db.get<CountResult>(
                'SELECT COUNT(*) as count FROM turns WHERE match_id = ?',
                [matchId],
                (err: Error | null, row?: CountResult) => {
                    if (err) return reject(err);

                    const turnNumber = (row?.count || 0) + 1;

                    // Insert new turn
                    this.db.run(
                        'INSERT INTO turns (match_id, player_id, move_data, turn_number) VALUES (?, ?, ?, ?)',
                        [matchId, playerId, JSON.stringify(move), turnNumber],
                        function (this: { lastID: number }, err: Error | null) {
                            if (err) return reject(err);
                            resolve({ turn_id: this.lastID });
                        }
                    );
                }
            );
        });
    }

    async getMatchTurns(matchId: number): Promise<Array<Turn & { username: string }>> {
        return new Promise((resolve, reject) => {
            this.db.all<Turn & { username: string }>(
                `SELECT t.*, p.username 
                 FROM turns t
                 JOIN players p ON t.player_id = p.player_id
                 WHERE t.match_id = ?
                 ORDER BY t.turn_number ASC`,
                [matchId],
                (err: Error | null, rows?: Array<Turn & { username: string }>) => {
                    if (err) return reject(err);

                    if (rows) {
                        for (const row of rows) {
                            if (row.move_data && typeof row.move_data === 'string') {
                                try {
                                    row.move_data = JSON.parse(row.move_data);
                                } catch (e) {
                                    console.error("Failed to parse move data:", e);
                                }
                            }
                        }
                    }

                    resolve(rows || []);
                }
            );
        });
    }

    // Games
    async getGames(): Promise<Game[]> {
        return new Promise((resolve, reject) => {
            this.db.all<Game>(
                'SELECT * FROM games',
                [],
                (err: Error | null, rows?: Game[]) => {
                    if (err) return reject(err);
                    resolve(rows || []);
                }
            );
        });
    }
}