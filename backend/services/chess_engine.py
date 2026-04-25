import chess
import concurrent.futures
import atexit
import os
import time
from dataclasses import dataclass

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

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2
DEFAULT_TIME_BUDGET_MS = 750
_GLOBAL_EXECUTOR: concurrent.futures.ProcessPoolExecutor | None = None


@dataclass(slots=True)
class TTEntry:
    depth: int
    value: int
    flag: int
    best_move: chess.Move | None

def evaluate_board(board: chess.Board):
    """
    Evaluates the current weights of the board

    Args:
        board (chess.Board): _description_

    Returns:
        _type_: _description_
    """
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_game_over(): # If it's over and NOT checkmate, it's a draw
        return 0

    score = 0
    # True if endgame
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    endgame = queens == 0

    for square in chess.SQUARES:
        # Pull the piece on the current square
        piece = board.piece_at(square)
        if piece is None:
            continue
        # Current weight depending on the piece
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

class SearchTimeout(Exception):
    pass


def _board_key(board: chess.Board):
    transposition_key = getattr(board, "transposition_key", None)
    if callable(transposition_key):
        return transposition_key()

    private_key = getattr(board, "_transposition_key", None)
    if callable(private_key):
        return private_key()
    if private_key is not None:
        return private_key

    # Fallback for compatibility when no zobrist key API is available.
    return (
        board.board_fen(),
        board.turn,
        board.castling_rights,
        board.ep_square,
    )


def _move_history_key(move: chess.Move):
    return move.from_square, move.to_square, move.promotion


def _score_move(
    board: chess.Board,
    move: chess.Move,
    tt_move: chess.Move | None,
    killers: dict[int, tuple[chess.Move, ...]],
    history: dict[tuple[int, int, int | None], int],
    depth: int,
):
    if tt_move and move == tt_move:
        return 1_000_000_000

    score = history.get(_move_history_key(move), 0)

    if board.is_capture(move):
        captured_piece_type = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
        attacker_piece_type = board.piece_type_at(move.from_square)
        if captured_piece_type is not None and attacker_piece_type is not None:
            score += 100_000 + (10 * WEIGHTS[captured_piece_type] - WEIGHTS[attacker_piece_type])

    if move.promotion:
        score += 50_000 + WEIGHTS[move.promotion]

    killer_moves = killers.get(depth, ())
    if move in killer_moves:
        score += 25_000

    if board.gives_check(move):
        score += 12_000

    return score


def _order_moves(
    board: chess.Board,
    moves: list[chess.Move],
    tt_move: chess.Move | None,
    killers: dict[int, tuple[chess.Move, ...]],
    history: dict[tuple[int, int, int | None], int],
    depth: int,
):
    return sorted(
        moves,
        key=lambda move: _score_move(board, move, tt_move, killers, history, depth),
        reverse=True,
    )


def _record_killer(depth: int, move: chess.Move, killers: dict[int, tuple[chess.Move, ...]]):
    current = killers.get(depth, ())
    if move in current:
        return
    if len(current) == 0:
        killers[depth] = (move,)
    elif len(current) == 1:
        killers[depth] = (move, current[0])
    else:
        killers[depth] = (move, current[0])


def _record_history(move: chess.Move, depth: int, history: dict[tuple[int, int, int | None], int]):
    key = _move_history_key(move)
    history[key] = history.get(key, 0) + depth * depth


def _search(
    board: chess.Board,
    depth: int,
    alpha: float,
    beta: float,
    is_max: bool,
    deadline: float,
    tt: dict[tuple[object, bool], TTEntry],
    killers: dict[int, tuple[chess.Move, ...]],
    history: dict[tuple[int, int, int | None], int],
):
    if time.perf_counter() >= deadline:
        raise SearchTimeout()

    if depth == 0 or board.is_game_over():
        return None, evaluate_board(board)

    key = (_board_key(board), is_max)
    original_alpha = alpha
    original_beta = beta
    entry = tt.get(key)
    tt_move = None
    if entry and entry.best_move:
        tt_move = entry.best_move
    if entry and entry.depth >= depth:
        if entry.flag == TT_EXACT:
            return entry.best_move, entry.value
        if entry.flag == TT_LOWER:
            alpha = max(alpha, entry.value)
        elif entry.flag == TT_UPPER:
            beta = min(beta, entry.value)
        if alpha >= beta:
            return entry.best_move, entry.value

    moves = _order_moves(board, list(board.legal_moves), tt_move, killers, history, depth)
    if not moves:
        return None, evaluate_board(board)

    best_move = None
    if is_max:
        best_value = float("-inf")
        for move in moves:
            board.push(move)
            try:
                _, value = _search(board, depth - 1, alpha, beta, False, deadline, tt, killers, history)
            finally:
                board.pop()

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value
            if alpha >= beta:
                _record_killer(depth, move, killers)
                _record_history(move, depth, history)
                break
    else:
        best_value = float("inf")
        for move in moves:
            board.push(move)
            try:
                _, value = _search(board, depth - 1, alpha, beta, True, deadline, tt, killers, history)
            finally:
                board.pop()

            if value < best_value:
                best_value = value
                best_move = move

            if value < beta:
                beta = value
            if alpha >= beta:
                _record_killer(depth, move, killers)
                _record_history(move, depth, history)
                break

    if best_value <= original_alpha:
        flag = TT_UPPER
    elif best_value >= original_beta:
        flag = TT_LOWER
    else:
        flag = TT_EXACT
    tt[key] = TTEntry(depth=depth, value=int(best_value), flag=flag, best_move=best_move)

    return best_move, best_value


def minimax(board: chess.Board, depth: int, alpha: float, beta: float, is_max: bool):
    """
    Implements a custom minimax algorithm to calculate best moves

    Args:
        board (chess.Board): _description_
        depth (int): _description_
        alpha (float): _description_
        beta (float): _description_
        is_max (bool): _description_

    Returns:
        _type_: _description_
    """
    tt: dict[tuple[object, bool], TTEntry] = {}
    killers: dict[int, tuple[chess.Move, ...]] = {}
    history: dict[tuple[int, int, int | None], int] = {}
    deadline = time.perf_counter() + 3600
    return _search(board, depth, alpha, beta, is_max, deadline, tt, killers, history)


def _iterative_deepening(
    board: chess.Board,
    max_depth: int,
    is_max: bool,
    max_time_ms: int,
):
    if board.is_game_over():
        return None, evaluate_board(board), 0

    if max_time_ms <= 0:
        max_time_ms = DEFAULT_TIME_BUDGET_MS

    deadline = time.perf_counter() + (max_time_ms / 1000.0)
    tt: dict[tuple[object, bool], TTEntry] = {}
    killers: dict[int, tuple[chess.Move, ...]] = {}
    history: dict[tuple[int, int, int | None], int] = {}

    best_move = None
    best_eval = evaluate_board(board)
    completed_depth = 0

    for current_depth in range(1, max_depth + 1):
        try:
            move, value = _search(
                board,
                current_depth,
                float("-inf"),
                float("inf"),
                is_max,
                deadline,
                tt,
                killers,
                history,
            )
        except SearchTimeout:
            break

        if move is not None:
            best_move = move
            best_eval = value
            completed_depth = current_depth

    return best_move, best_eval, completed_depth


def analyze_state(fen: str, depth: int = 3, max_time_ms: int = DEFAULT_TIME_BUDGET_MS) -> str:
    """
    Analyzes the current state of the board to get best current move

    Args:
        fen (str): _description_

    Returns:
        str: _description_
    """
    root_board = chess.Board(fen)
    search_board = root_board.copy(stack=False)
    is_white_turn = search_board.turn == chess.WHITE
    best_move, _, _ = _iterative_deepening(
        board=search_board,
        max_depth=max(1, depth),
        is_max=is_white_turn,
        max_time_ms=max_time_ms,
    )
    # Return SAN notation
    if best_move:
        return root_board.san(best_move)
    return ""


def _analyze_state_worker(args: tuple[str, int, int]):
    fen, depth, max_time_ms = args
    return analyze_state(fen=fen, depth=depth, max_time_ms=max_time_ms)


def _get_executor():
    global _GLOBAL_EXECUTOR
    if _GLOBAL_EXECUTOR is None:
        cpu_count = os.cpu_count() or 2
        _GLOBAL_EXECUTOR = concurrent.futures.ProcessPoolExecutor(max_workers=max(1, cpu_count - 1))
    return _GLOBAL_EXECUTOR


def _shutdown_executor():
    global _GLOBAL_EXECUTOR
    if _GLOBAL_EXECUTOR is not None:
        _GLOBAL_EXECUTOR.shutdown(wait=False, cancel_futures=True)
        _GLOBAL_EXECUTOR = None


atexit.register(_shutdown_executor)

def analyze_game_parallel(
    game_moves: list[str],
    depth: int = 3,
    max_time_ms: int = DEFAULT_TIME_BUDGET_MS,
) -> list[str]:
    """
    Runs game analysis concurrently as single threaded was taking much too long upward of 3 minutes

    Args:
        game_moves (list[str]): _description_

    Returns:
        list[str]: _description_
    """
    board = chess.Board()
    fens = []
    
    # We analyze every position EXCEPT the very last move (which ends the game typically)
    for move in game_moves[:-1]:
        board.push_san(move)
        fens.append(board.fen())

    if len(fens) <= 2:
        return [analyze_state(fen, depth=depth, max_time_ms=max_time_ms) for fen in fens]

    tasks = [(fen, depth, max_time_ms) for fen in fens]
    executor = _get_executor()
    return list(executor.map(_analyze_state_worker, tasks))
