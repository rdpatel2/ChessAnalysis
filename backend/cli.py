import sys
import os
from time import sleep
import chess
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt

from services.chess_com_client import fetch_recent_games
from services.chess_engine import minimax

console = Console()

PIECES = {
    chess.PAWN: "♟",
    chess.KNIGHT: "♞",
    chess.BISHOP: "♝",
    chess.ROOK: "♜",
    chess.QUEEN: "♛",
    chess.KING: "♚"
}

def render_board(board: chess.Board, user_color, played_move=None, optimal_move=None):
    table = Table(show_header=False, show_edge=True, padding=(0,1))
    
    # Orientation
    ranks = range(7, -1, -1) if user_color == chess.WHITE else range(8)
    files = range(8) if user_color == chess.WHITE else range(7, -1, -1)
    
    for rank in ranks:
        row_elements = []
        for file in files:
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            
            # Colors
            is_light_square = (rank + file) % 2 != 0
            bg_color = "on #f0d9b5" if is_light_square else "on #b58863"
            
            # Highlights
            if played_move and (square == played_move.from_square or square == played_move.to_square):
                bg_color = "on #718ebd" # Blue-ish for played move
            if optimal_move and (square == optimal_move.from_square or square == optimal_move.to_square):
                bg_color = "on #829769" # Green-ish for optimal move
                
            if played_move and optimal_move and played_move == optimal_move:
                 if square == optimal_move.from_square or square == optimal_move.to_square:
                      bg_color = "on #829769" # Green implies perfect move
            
            if piece:
                char = PIECES[piece.piece_type]
                fg_color = "black" if piece.color == chess.BLACK else "white"
                styled_char = Text(char, style=f"{fg_color} {bg_color} bold")
                row_elements.append(styled_char)
            else:
                row_elements.append(Text(" ", style=f"{bg_color}"))
        table.add_row(*row_elements)
        
    return table

def analyze_board(board: chess.Board):
    with console.status("[bold green]Analyzing optimal move...[/bold green]", spinner="dots"):
        is_white_turn = board.turn == chess.WHITE
        # Using depth 2 for speed
        best_move, _ = minimax(board, depth=2, alpha=float('-inf'), beta=float('inf'), is_max=is_white_turn)
    return best_move

def main():
    console.print(Panel.fit("[bold blue]Terminal Chess Analyzer[/bold blue]\n[green]Powered by Custom Minimax Engine[/green]"))
    
    username = Prompt.ask("Enter your chess.com username")
    
    with console.status("[bold yellow]Fetching your recent games...[/bold yellow]"):
        games = fetch_recent_games(username, limit=5)
    
    if not games:
        console.print("[bold red]No games found or error fetching games![/bold red]")
        sys.exit(1)
        
    console.print("\n[bold]Select a game to analyze:[/bold]")
    for idx, g in enumerate(games):
        color = "White" if g['white'].lower() == username.lower() else "Black"
        console.print(f"[{idx+1}] Played as {color} vs {g['black'] if color=='White' else g['white']} (Result: {g['result']}) - {g['url']}")
        
    choice = Prompt.ask("Enter game number", choices=[str(i+1) for i in range(len(games))])
    selected_game = games[int(choice)-1]
    
    user_is_white = selected_game['white'].lower() == username.lower()
    user_color = chess.WHITE if user_is_white else chess.BLACK
    
    board = chess.Board()
    moves = selected_game["moves"]
    
    console.print("\n[bold yellow]Starting Game Analysis...[/bold yellow]")
    console.print("Press [bold]ENTER[/bold] to step through the moves. Type [bold]q[/bold] to quit.\n")
    
    for i, san_move in enumerate(moves):
        is_user_turn = board.turn == user_color
        optimal_move = None
        optimal_san = "Unknown"
        
        # Parse what the actual move made was
        actual_move = board.parse_san(san_move)
        
        if is_user_turn:
             # Calculate optimal before pushing
             optimal_move = analyze_board(board)
             if optimal_move:
                 optimal_san = board.san(optimal_move)
             
        board.push(actual_move)
        
        # Rendering
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(f"[bold]Move {i//2 + 1}{'.' if is_user_turn else '...'}[/bold]")
        
        rendered_board = render_board(board, user_color, played_move=actual_move, optimal_move=optimal_move)
        console.print(rendered_board)
        
        if is_user_turn:
            if optimal_move == actual_move:
                console.print(f"[bold green]Great move![/bold green] You played {san_move}, which was optimal.")
            else:
                console.print(f"You played: [bold blue]{san_move}[/bold blue].")
                console.print(f"Optimal was: [bold green]{optimal_san}[/bold green].")
                
            console.print("[dim]Blue background = Played Move | Green background = Optimal Move[/dim]\n")
        else:
            opponent = "White" if user_color == chess.BLACK else "Black"
            console.print(f"[dim]{opponent} played {san_move}[/dim]\n")
            
        action = Prompt.ask("Press ENTER for next move, 'q' to quit", default="")
        if action.lower() == 'q':
            break
            
    console.print("[bold]Game analysis finished. Goodbye![/bold]")

if __name__ == "__main__":
    main()
