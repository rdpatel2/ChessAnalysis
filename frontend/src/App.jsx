import { useState } from 'react'
import Dashboard from './components/Dashboard'
import ChessAnalyzer from './components/ChessAnalyzer'
import './index.css'

function App() {
  const [selectedGame, setSelectedGame] = useState(null)
  const [username, setUsername] = useState('')

  return (
    <div className="container">
      {!selectedGame ? (
        <Dashboard 
          onSelectGame={(game, user) => {
            setSelectedGame(game)
            setUsername(user)
          }} 
        />
      ) : (
        <ChessAnalyzer 
          game={selectedGame} 
          username={username}
          onBack={() => setSelectedGame(null)} 
        />
      )}
    </div>
  )
}

export default App
