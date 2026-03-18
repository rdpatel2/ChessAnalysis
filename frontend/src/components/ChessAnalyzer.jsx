import { useState, useEffect, useMemo, useCallback } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { ChevronLeft, ChevronRight, ArrowLeft, Loader2, Info } from 'lucide-react';

export default function ChessAnalyzer({ game, username, onBack }) {
  const [currentMoveIndex, setCurrentMoveIndex] = useState(0);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [customArrows, setCustomArrows] = useState([]);
  const [customSquareStyles, setCustomSquareStyles] = useState({});

  const userIsWhite = game.white.toLowerCase() === username.toLowerCase();
  const userColor = userIsWhite ? 'white' : 'black';

  // Build an array of board positions from the PGN moves
  const moveHistory = useMemo(() => {
    const chess = new Chess();
    const history = [{ 
      fen: chess.fen(), 
      san: 'Start',
      from: null,
      to: null,
      isUserTurn: chess.turn() === (userIsWhite ? 'w' : 'b')
    }];

    for (const moveSan of game.moves) {
      try {
        const move = chess.move(moveSan);
        history.push({
          fen: chess.fen(),
          san: moveSan,
          from: move.from,
          to: move.to,
          isUserTurn: chess.turn() === (userIsWhite ? 'w' : 'b')
        });
      } catch (e) {
        console.error("Invalid move in PGN", moveSan);
        break;
      }
    }
    return history;
  }, [game.moves, userIsWhite]);

  const currentState = moveHistory[currentMoveIndex];
  const nextState = currentMoveIndex < moveHistory.length - 1 ? moveHistory[currentMoveIndex + 1] : null;
  const isCurrentlyUserTurn = currentState.isUserTurn;

  const analyzePosition = useCallback(async () => {
    // Only analyze if it's the user's turn
    if (!isCurrentlyUserTurn) {
      setAnalysis(null);
      return;
    }

    setIsAnalyzing(true);
    setAnalysis(null);
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fen: currentState.fen,
          user_color: userColor
        })
      });
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  }, [currentState.fen, isCurrentlyUserTurn, userColor]);

  // Re-run analysis when stepping to a new position if it's user's turn
  useEffect(() => {
    analyzePosition();
  }, [analyzePosition]);

  // Update visual hints (arrows and square highlights)
  useEffect(() => {
    let arrows = [];
    let styles = {};

    // Highlight the move that was actually played (Blue)
    if (currentMoveIndex > 0) {
      const lastMove = moveHistory[currentMoveIndex];
      if (lastMove.from && lastMove.to) {
        styles[lastMove.from] = { backgroundColor: 'rgba(59, 130, 246, 0.5)' };
        styles[lastMove.to] = { backgroundColor: 'rgba(59, 130, 246, 0.5)' };
      }
    }

    // Highlight optimal move if analyzed (Green)
    if (analysis && analysis.optimal_san) {
      const tempChess = new Chess(currentState.fen);
      try {
        const move = tempChess.move(analysis.optimal_san);
        if (move) {
          arrows.push([move.from, move.to, 'rgba(34, 197, 94, 0.8)']);
          styles[move.from] = { ...styles[move.from], backgroundColor: 'rgba(34, 197, 94, 0.5)' };
          styles[move.to] = { ...styles[move.to], backgroundColor: 'rgba(34, 197, 94, 0.5)' };
        }
      } catch (e) {
        // Ignore fallback
      }
    }

    setCustomArrows(arrows);
    setCustomSquareStyles(styles);
  }, [currentMoveIndex, moveHistory, analysis, currentState.fen]);

  const handleNext = () => {
    if (currentMoveIndex < moveHistory.length - 1) setCurrentMoveIndex(c => c + 1);
  };

  const handlePrev = () => {
    if (currentMoveIndex > 0) setCurrentMoveIndex(c => c - 1);
  };

  return (
    <div className="glass-panel" style={{ flex: 1 }}>
      <button onClick={onBack} className="btn" style={{ background: 'transparent', border: '1px solid var(--glass-border)', marginBottom: '16px' }}>
        <ArrowLeft size={16} /> Back to Games
      </button>

      <div className="analyzer-layout">
        <div className="board-container">
          <Chessboard 
            position={currentState.fen} 
            boardOrientation={userColor}
            customArrows={customArrows}
            customSquareStyles={customSquareStyles}
            animationDuration={300}
            arePiecesDraggable={false}
          />

          <div className="nav-buttons">
            <button className="btn" onClick={handlePrev} disabled={currentMoveIndex === 0}>
              <ChevronLeft size={20} /> Prev
            </button>
            <button className="btn" onClick={handleNext} disabled={currentMoveIndex === moveHistory.length - 1}>
              Next <ChevronRight size={20} />
            </button>
          </div>
        </div>

        <div className="controls">
          <div className="controls-header">
            <h2 style={{ marginBottom: 4 }}>Game Analysis</h2>
            <p className="game-meta">Playing as {userColor}</p>
          </div>

          <div className="evaluation-panel">
            {isAnalyzing ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Loader2 className="animate-spin" size={20} color="var(--accent)" />
                <span>Running Minimax engine...</span>
              </div>
            ) : isCurrentlyUserTurn ? (
              <>
                <div className="eval-score">
                  {analysis?.eval !== undefined ? (analysis.eval > 0 ? `+${analysis.eval}` : analysis.eval) : '-'}
                </div>
                <div className="eval-details">
                  {analysis?.optimal_san ? (
                    <>
                      <p>Optimal Move: <strong style={{ color: '#4ade80' }}>{analysis.optimal_san}</strong></p>
                      {nextState && (
                        <p>Played Move: <strong style={{ color: nextState.san === analysis.optimal_san ? '#4ade80' : '#60a5fa' }}>{nextState.san}</strong></p>
                      )}
                    </>
                  ) : (
                    <p>Eval: {analysis?.eval ?? '-'}</p>
                  )}
                </div>
              </>
            ) : (
              <div style={{ display: 'flex', gap: '8px', color: 'var(--text-muted)' }}>
                <Info size={20} />
                <span>Opponent's turn. Stepping...</span>
              </div>
            )}
          </div>

          <div className="move-history">
            <h3>Moves</h3>
            {moveHistory.map((move, i) => {
              if (i === 0) return null; // Skip 'Start'
              return (
                <div key={i} className={`move-row`} onClick={() => setCurrentMoveIndex(i)}>
                  <span className="move-num">{(i + 1) % 2 === 0 ? i/2 : Math.floor(i/2) + 1}.</span>
                  <span className={`move-san ${currentMoveIndex === i ? 'active' : ''}`}>
                    {move.san}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
