import { useState } from 'react';
import { Search, Loader2, Play } from 'lucide-react';

export default function Dashboard({ onSelectGame }) {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [games, setGames] = useState([]);
  const [error, setError] = useState(null);

  const fetchGames = async (e) => {
    e.preventDefault();
    if (!username) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/games/${username}?limit=10`);
      if (!response.ok) throw new Error('Failed to fetch games');
      const data = await response.json();
      setGames(data.games || []);
      if (data.games.length === 0) {
        setError("No recent games found.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
      <h1 className="header-title">ChessAnalyzer</h1>
      <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Analyze your chess.com games with our custom Minimax engine.
      </p>

      <form onSubmit={fetchGames} style={{ display: 'flex', gap: '12px' }}>
        <input
          type="text"
          className="input"
          placeholder="Enter chess.com username (e.g., hikaru)"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <button type="submit" className="btn" disabled={loading || !username}>
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
          Find
        </button>
      </form>

      {error && <p style={{ color: '#ef4444', marginTop: '1rem', textAlign: 'center' }}>{error}</p>}

      {games.length > 0 && (
        <div className="game-list">
          <h2 style={{ fontSize: '1.2rem', marginTop: '1rem' }}>Recent Games</h2>
          {games.map((game, i) => {
            const isWhite = game.white.toLowerCase() === username.toLowerCase();
            const color = isWhite ? 'White' : 'Black';
            const opponent = isWhite ? game.black : game.white;
            
            let resultClass = 'draw';
            if (game.result === 'win') resultClass = 'win';
            else if (['checkmated', 'resigned', 'timeout', 'abandoned'].includes(game.result)) resultClass = 'loss';

            return (
              <div key={i} className="game-card" onClick={() => onSelectGame(game, username)}>
                <div className="game-info">
                  <h3>Played as {color} vs {opponent}</h3>
                  <p className="game-meta">{game.date} • {game.moves.length} moves</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <span className={`badge ${resultClass}`}>{game.result}</span>
                  <Play size={20} color="var(--accent)" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
