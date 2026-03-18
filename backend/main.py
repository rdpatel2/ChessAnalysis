from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess

from services.chess_com_client import fetch_recent_games
from services.chess_engine import analyze_state, evaluate_board

app = FastAPI(title="ChessAnalysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    fen: str
    user_color: str # "white" or "black"

@app.get("/api/games/{username}")
def get_recent_games(username: str, limit: int = 10):
    try:
        games = fetch_recent_games(username, limit=limit)
        if not games:
            return {"games": []}
        return {"games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def analyze_position(req: AnalyzeRequest):
    try:
        board = chess.Board(req.fen)
        is_user_turn = (board.turn == chess.WHITE and req.user_color == "white") or \
                       (board.turn == chess.BLACK and req.user_color == "black")
                       
        if not is_user_turn:
            return {"optimal_san": None, "eval": evaluate_board(board)}
            
        optimal_san = analyze_state(req.fen)
        
        # Calculate evaluation after optimal move is made
        if optimal_san:
            temp_board = board.copy()
            temp_board.push_san(optimal_san)
            evaluation = evaluate_board(temp_board)
        else:
            evaluation = evaluate_board(board)
            
        return {"optimal_san": optimal_san, "eval": evaluation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
