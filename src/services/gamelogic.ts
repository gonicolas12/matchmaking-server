import { PythonShell } from 'python-shell';
import path from 'path';
import fs from 'fs';

export class GameLogicService {
    private pythonPath: string;
    private chessPythonPath: string;

    constructor() {
        // Paths to Python scripts
        this.pythonPath = path.join(__dirname, '../../python/game_logic.py');
        this.chessPythonPath = path.join(__dirname, '../../python/chess_logic.py');

        // Ensure Python script directories exist
        const dirPath = path.dirname(this.pythonPath);
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
        }

        // Create chess logic file if it doesn't exist
        this.ensureChessLogicExists();

        // Verify Python scripts exist
        if (!fs.existsSync(this.pythonPath)) {
            console.warn(`Tic-tac-toe script not found at ${this.pythonPath}`);
        }
        if (!fs.existsSync(this.chessPythonPath)) {
            console.warn(`Chess script not found at ${this.chessPythonPath}`);
        }
    }

    private ensureChessLogicExists(): void {
        if (!fs.existsSync(this.chessPythonPath)) {
            // You would copy the chess_logic.py content here
            console.log(`Creating chess logic file at ${this.chessPythonPath}`);
            // For now, we'll assume the file exists
        }
    }

    private async runPythonScript(data: any, gameType: string = 'tic-tac-toe'): Promise<any> {
        return new Promise((resolve, reject) => {
            // Choose the appropriate Python script based on game type
            const scriptPath = gameType === 'chess' ? this.chessPythonPath : this.pythonPath;
            
            if (!fs.existsSync(scriptPath)) {
                return reject(new Error(`Python script not found: ${scriptPath}`));
            }

            // Create a new PythonShell instance
            const pyshell = new PythonShell(scriptPath);

            // Send data to the Python script
            pyshell.send(JSON.stringify(data));

            let result = '';

            // Collect output from the Python script
            pyshell.on('message', (message) => {
                result += message;
            });

            // Handle errors
            pyshell.on('error', (err) => {
                reject(err);
            });

            // End the process and resolve the promise
            pyshell.end((err) => {
                if (err) {
                    return reject(err);
                }

                try {
                    const parsedResult = JSON.parse(result);
                    resolve(parsedResult);
                } catch (e) {
                    reject(new Error(`Failed to parse Python result: ${result}`));
                }
            });
        });
    }

    /**
     * Initialize a new game state for the specified game type
     * @param gameType Type of game to initialize ('tic-tac-toe' or 'chess')
     * @returns Initial game state
     */
    async initializeGame(gameType: string): Promise<any> {
        const result = await this.runPythonScript({
            action: 'initialize',
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result;
    }

    /**
     * Validate if a move is legal
     * @param state Current game state
     * @param move Move to validate
     * @param playerId ID of player making the move
     * @returns Whether the move is valid
     */
    async validateMove(state: any, move: any, playerId: number): Promise<boolean> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'validate',
            state,
            move,
            player_id: playerId,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.valid || false;
    }

    /**
     * Apply a move to the game state
     * @param state Current game state
     * @param move Move to apply
     * @param playerId ID of player making the move
     * @returns New game state after the move
     */
    async applyMove(state: any, move: any, playerId: number): Promise<any> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'apply',
            state,
            move,
            player_id: playerId,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result;
    }

    /**
     * Check if there's a winner
     * @param state Current game state
     * @returns ID of winner if there is one, null otherwise
     */
    async checkWinner(state: any): Promise<number | null> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'check_winner',
            state,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.winner || null;
    }

    /**
     * Check if the game is over (win or draw)
     * @param state Current game state
     * @returns Whether the game is over
     */
    async isGameOver(state: any): Promise<boolean> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'is_game_over',
            state,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.game_over || false;
    }

    /**
     * Check if the game is a draw
     * @param state Current game state
     * @returns Whether the game is a draw
     */
    async isDraw(state: any): Promise<boolean> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'is_draw',
            state,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.is_draw || false;
    }

    /**
     * Determine the game type based on the state
     * @param state Game state
     * @returns Game type string
     */
    private determineGameType(state: any): string {
        // Check for chess game (8x8 board with piece objects)
        if (state && Array.isArray(state.board) && state.board.length === 8 &&
            Array.isArray(state.board[0]) && state.board[0].length === 8) {
            // Further check if it contains chess-like pieces
            if (state.castling_rights || state.en_passant_target !== undefined || 
                state.king_positions || state.captured_pieces) {
                return 'chess';
            }
        }
        
        // Check for tic-tac-toe (1D array of 9 elements)
        if (state && Array.isArray(state.board) && state.board.length === 9) {
            return 'tic-tac-toe';
        }

        // Default to tic-tac-toe for backwards compatibility
        return 'tic-tac-toe';
    }

    /**
     * Get available moves for a player (mainly for chess)
     * @param state Current game state
     * @param playerId Player ID
     * @returns List of legal moves
     */
    async getAvailableMoves(state: any, playerId: number): Promise<any[]> {
        const gameType = this.determineGameType(state);
        
        if (gameType !== 'chess') {
            // For tic-tac-toe, just return empty squares
            const moves = [];
            for (let i = 0; i < state.board.length; i++) {
                if (state.board[i] === null) {
                    moves.push({ position: i });
                }
            }
            return moves;
        }

        const result = await this.runPythonScript({
            action: 'get_available_moves',
            state,
            player_id: playerId,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.moves || [];
    }

    /**
     * Evaluate the board position (for AI purposes)
     * @param state Current game state
     * @param playerId Player ID to evaluate for
     * @returns Evaluation score
     */
    async evaluatePosition(state: any, playerId: number): Promise<number> {
        const gameType = this.determineGameType(state);
        
        const result = await this.runPythonScript({
            action: 'evaluate',
            state,
            player_id: playerId,
            game_type: gameType
        }, gameType);

        if (result && result.error) {
            throw new Error(result.error);
        }

        return result?.evaluation || 0;
    }
}