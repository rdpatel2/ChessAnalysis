import chess
import random
import concurrent.futures
from functools import lru_cache

# Piece Square Tables (PST) adapted from Sunfish
# https://github.com/thomasahle/sunfish/blob/master/sunfish.py

WEIGHTS = {
    chess.PAWN: 100,
    chess.KNIGHT: 280,
    chess.BISHOP: 320,
    chess.ROOK: 479,
    chess.QUEEN: 929,
    chess.KING: 60000,
}

PST_W = {
    chess.PAWN: [
        100, 100, 100, 100, 105, 100, 100, 100,
         78,  83,  86,  73, 102,  82,  85,  90,
          7,  29,  21,  44,  40,  31,  44,   7,
        -17,  16,  -2,  15,  14,   0,  15, -13,
        -26,   3,  10,   9,   6,   1,   0, -23,
        -22,   9,   5, -11, -10,  -2,   3, -19,
        -31,   8,  -7, -37, -36, -14,   3, -31,
          0,   0,   0,   0,   0,   0,   0,   0,
    ],
    chess.KNIGHT: [
        -66, -53, -75, -75, -10, -55, -58, -70,
         -3,  -6, 100, -36,   4,  62,  -4, -14,
         10,  67,   1,  74,  73,  27,  62,  -2,
         24,  24,  45,  37,  33,  41,  25,  17,
         -1,   5,  31,  21,  22,  35,   2,   0,
        -18,  10,  13,  22,  18,  15,  11, -14,
        -23, -15,   2,   0,   2,   0, -23, -20,
        -74, -23, -26, -24, -19, -35, -22, -69,
    ],
    chess.BISHOP: [
        -59, -78, -82, -76, -23,-107, -37, -50,
        -11,  20,  35, -42, -39,  31,   2, -22,
         -9,  39, -32,  41,  52, -10,  28, -14,
         25,  17,  20,  34,  26,  25,  15,  10,
         13,  10,  17,  23,  17,  16,   0,   7,
         14,  25,  24,  15,   8,  25,  20,  15,
         19,  20,  11,   6,   7,   6,  20,  16,
         -7,   2, -15, -12, -14, -15, -10, -10,
    ],
    chess.ROOK: [
         35,  29,  33,   4,  37,  33,  56,  50,
         55,  29,  56,  67,  55,  62,  34,  60,
         19,  35,  28,  33,  45,  27,  25,  15,
          0,   5,  16,  13,  18,  -4,  -9,  -6,
        -28, -35, -16, -21, -13, -29, -46, -30,
        -42, -28, -42, -25, -25, -35, -26, -46,
        -53, -38, -31, -26, -29, -43, -44, -53,
        -30, -24, -18,   5,  -2, -18, -31, -32,
    ],
    chess.QUEEN: [
          6,   1,  -8,-104,  69,  24,  88,  26,
         14,  32,  60, -10,  20,  76,  57,  24,
         -2,  43,  32,  60,  72,  63,  43,   2,
          1, -16,  22,  17,  25,  20, -13,  -6,
        -14, -15,  -2,  -5,  -1, -10, -20, -22,
        -30,  -6, -13, -11, -16, -11, -16, -27,
        -36, -18,   0, -19, -15, -15, -21, -38,
        -39, -30, -31, -13, -31, -36, -34, -42,
    ],
    chess.KING: [
          4,  54,  47, -99, -99,  60,  83, -62,
        -32,  10,  55,  56,  56,  55,  10,   3,
        -62,  12, -57,  44, -67,  28,  37, -31,
        -55,  50,  11,  -4, -19,  13,   0, -49,
        -55, -43, -52, -28, -51, -47,  -8, -50,
        -47, -42, -43, -79, -64, -32, -29, -32,
         -4,   3, -14, -50, -57, -18,  13,   4,
         17,  30,  -3, -14,   6,  -1,  40,  18,
    ],
    'k_e': [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10,   0,   0, -10, -20, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -30,   0,   0,   0,   0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50,
    ]
}

PST_B = {}
for pt, table in PST_W.items():
    # Reverse rows for black
    PST_B[pt] = []
    for r in reversed(range(8)):
        PST_B[pt].extend(table[r*8:(r+1)*8])

def evaluate_board(board: chess.Board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_game_over(): # If it's over and NOT checkmate, it's a draw
        return 0

    score = 0
    # True if endgame
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    endgame = queens == 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        
        val = WEIGHTS[piece.piece_type]
        
        if piece.piece_type == chess.KING:
            pst = PST_W['k_e'] if endgame and piece.color == chess.WHITE else PST_W[chess.KING] if piece.color == chess.WHITE else PST_B['k_e'] if endgame and piece.color == chess.BLACK else PST_B[chess.KING]
        else:
            pst = PST_W[piece.piece_type] if piece.color == chess.WHITE else PST_B[piece.piece_type]
            
        mirror_sq = 63 - square if piece.color == chess.WHITE else square # python-chess A1=0, A8=56, H8=63
        square_val = pst[mirror_sq]

        if piece.color == chess.WHITE:
            score += val + square_val
        else:
            score -= val + square_val
            
    return score

def minimax(board: chess.Board, depth: int, alpha: float, beta: float, is_max: bool):
    if depth == 0 or board.is_game_over():
        return None, evaluate_board(board)

    moves = list(board.legal_moves)
    random.shuffle(moves)

    best_move = None
    if is_max:
        max_val = float('-inf')
        for move in moves:
            board.push(move)
            _, val = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if val > max_val:
                max_val = val
                best_move = move
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return best_move, max_val
    else:
        min_val = float('inf')
        for move in moves:
            board.push(move)
            _, val = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if val < min_val:
                min_val = val
                best_move = move
            beta = min(beta, val)
            if alpha >= beta:
                break
        return best_move, min_val

def analyze_state(fen: str) -> str:
    board = chess.Board(fen)
    is_white_turn = board.turn == chess.WHITE
    best_move, _ = minimax(board, 2, float('-inf'), float('inf'), is_white_turn)
    # Return SAN notation
    if best_move:
        return board.san(best_move)
    return ""

def analyze_game_parallel(game_moves: list[str]) -> list[str]:
    board = chess.Board()
    fens = []
    
    # We analyze every position EXCEPT the very last move (which ends the game typically)
    for move in game_moves[:-1]:
        board.push_san(move)
        fens.append(board.fen())

    # Map minimax over evaluations in parallel, drastically improving performance compared to NodeJS single thread!
    with concurrent.futures.ProcessPoolExecutor() as executor:
        best_moves = list(executor.map(analyze_state, fens))
        
    return best_moves
