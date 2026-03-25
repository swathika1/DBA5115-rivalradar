import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const nav = useNavigate()
  const { token, logout } = useAuth()

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800" style={{ background: '#0a1628' }}>
      <span className="text-xl font-bold cursor-pointer" onClick={() => nav('/')} >
        <span style={{ color: '#1e90ff' }}>Rival</span>Radar
      </span>
      {token && (
        <nav className="flex items-center gap-6">
          <span className="text-gray-300 cursor-pointer hover:text-white text-sm" onClick={() => nav('/dashboard')}>Dashboard</span>
          <span className="text-gray-300 cursor-pointer hover:text-white text-sm" onClick={() => nav('/settings')}>Settings</span>
          <button onClick={() => { logout(); nav('/') }} className="text-sm px-3 py-1 rounded border border-gray-600 text-gray-300 hover:text-white">Logout</button>
        </nav>
      )}
    </header>
  )
}
