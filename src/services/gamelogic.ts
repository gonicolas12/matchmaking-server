import { PythonShell } from 'python-shell';
import path from 'path';
import fs from 'fs';

export class GameLogicService {
    private pythonPath: string;
    
    constructor() {
        // Path to Python script
        this.pythonPath = path.join(__dirname, '../../python/game_logic.py');
        
        // Ensure Python script directory exists
        const dirPath = path.dirname(this.pythonPath);
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
        }
        
        // Verify Python script exists
        if (!fs.existsSync(this.pythonPath)) {
            console.warn(`Python script not found at ${this.pythonPath}. Game logic might not work.`);
        }
    }
    
    private async runPythonScript(data: any): Promise<any> {
        return new Promise((resolve, reject) => {
            // Create a new PythonShell instance
            const pyshell = new PythonShell(this.pythonPath);
            
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
     * @param gameType Type of game to initialize
     * @returns Initial game state
     */
    async initializeGame(gameType: string): Promise<any> {
        const result = await this.runPythonScript({
            action: 'initialize',
            game_type: gameType
        });
        
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
        const result = await this.runPythonScript({
            action: 'validate',
            state,
            move,
            player_id: playerId,
            game_type: this.determineGameType(state)
        });
        
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
        const result = await this.runPythonScript({
            action: 'apply',
            state,
            move,
            player_id: playerId,
            game_type: this.determineGameType(state)
        });
        
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
        const result = await this.runPythonScript({
            action: 'check_winner',
            state,
            game_type: this.determineGameType(state)
        });
        
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
        const result = await this.runPythonScript({
            action: 'is_game_over',
            state,
            game_type: this.determineGameType(state)
        });
        
        if (result && result.error) {
            throw new Error(result.error);
        }
        
        return result?.game_over || false;
    }
    
    /**
     * Determine the game type based on the state
     * @param state Game state
     * @returns Game type string
     */
    private determineGameType(state: any): string {
        // This is a simple heuristic - in a real implementation,
        // you'd want to store the game type with the match
        if (state && Array.isArray(state.board) && state.board.length === 9) {
            return 'tic-tac-toe';
        } else if (state && Array.isArray(state.board) && state.board.length === 8 && 
                  Array.isArray(state.board[0]) && state.board[0].length === 8) {
            return 'chess';
        }
        
        // Default to tic-tac-toe
        return 'tic-tac-toe';
    }
}