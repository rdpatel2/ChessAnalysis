import requests
import chess.pgn
import io
import datetime

def get_prev_date(year, month):
    """

    Args:
        year (_type_): _description_
        month (_type_): _description_

    Returns:
        _type_: _description_
    """
    if month == 1:
        return year - 1, 12
    return year, month - 1

def clean_pgn(pgn):
    """

    Args:
        pgn (_type_): _description_

    Returns:
        _type_: _description_
    """
    idx = pgn.find("1.")
    return pgn[idx:] if idx != -1 else pgn

def extract_game_data(pgn_str):
    """

    Args:
        pgn_str (_type_): _description_

    Returns:
        _type_: _description_
    """
    pgn_io = io.StringIO(pgn_str)
    try:
        game = chess.pgn.read_game(pgn_io)
    except:
        return None

    if not game:
        return None
    
    headers = game.headers
    board = game.board()
    moves = []
    for move in game.mainline_moves():
        san_move = board.san(move)
        moves.append(san_move)
        board.push(move)
        
    return {
        "white": headers.get("White", "Unknown"),
        "black": headers.get("Black", "Unknown"),
        "date": headers.get("Date", "Unknown"),
        "result": headers.get("Result", "*"),
        "url": headers.get("Link", ""), # chess.com puts link sometimes in Link or URL, actually check payload later
        "moves": moves
    }

def fetch_recent_games(username, limit=10):
    """

    Args:
        username (_type_): _description_
        limit (int, optional): _description_. Defaults to 10.

    Returns:
        _type_: _description_
    """
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    games_found = []

    while len(games_found) < limit:
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
        headers = {'User-Agent': 'ChessAnalysisApp (mailto:developer@example.com)'}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                year, month = get_prev_date(year, month)
                if year < now.year - 10:
                    break
                continue
            
            data = response.json()
            if data and "games" in data and len(data["games"]) > 0:
                for game_data in reversed(data["games"]):
                    if len(games_found) >= limit:
                        break
                    
                    pgn_str = game_data.get("pgn", "")
                    # chess.com specific game url
                    game_url = game_data.get("url", "")
                    
                    cleaned_pgn = clean_pgn(pgn_str)
                    game_extracted = extract_game_data(pgn_str) # Pass full PGN for headers
                    
                    if game_extracted:
                        game_extracted["url"] = game_url
                        games_found.append(game_extracted)
        except Exception as e:
            pass
        
        year, month = get_prev_date(year, month)
        if year < now.year - 10:
            break
            
    return games_found
