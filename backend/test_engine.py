import pytest
import chess
from services.chess_com_client import fetch_recent_games
from services.chess_engine import minimax

def test_fetch_and_analyze_entire_game():
    # Use ProximityGames1 as requested by the user
    username = "ProximityGames1"
    
    # Fetch recent games for the user
    games = fetch_recent_games(username, limit=1)
    
    assert len(games) > 0, "No games found for user ProximityGames1"
    
    game = games[0]
    moves = game["moves"]
    assert len(moves) > 0, "Game has no moves"
    
    # Find out if the user played White or Black in this game
    user_is_white = game["white"].lower() == username.lower()
    user_color = chess.WHITE if user_is_white else chess.BLACK
    
    board = chess.Board()
    
    # We will step through the ENTIRE game sequence
    for i, san_move in enumerate(moves):
        is_user_turn = board.turn == user_color
        
        # Verify minimax evaluates successfully without crashing on the user's turn
        if is_user_turn:
            # We use depth=2 for testing to keep it fast, similar to the CLI
            best_move, value = minimax(board, depth=2, alpha=float('-inf'), beta=float('inf'), is_max=True)
            
            # The game isn't over yet in this loop if there are moves being played, so best_move shouldn't be None
            # unless it's checkmate, but in valid games there is always a move before checkmate.
            assert best_move is not None, f"Minimax returned None for best_move at move {i+1} ({san_move})"
            assert isinstance(best_move, chess.Move), "Best move should be a chess.Move type"
        
        # Pushing the actual move made in the game
        actual_move = board.parse_san(san_move)
        board.push(actual_move)
        
    # Test completed successfully if we reached the end of the PGN sequence
    assert board.is_valid()
