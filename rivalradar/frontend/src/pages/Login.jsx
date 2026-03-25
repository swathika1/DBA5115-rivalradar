import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const nav = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLogin = async () => {
    try {
      await login({ email, password })
      nav('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="w-full max-w-sm space-y-4">
        <h2 className="text-2xl font-bold text-white text-center">Sign in to RivalRadar</h2>
        <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button onClick={handleLogin} className="w-full py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Sign In</button>
        <p className="text-center text-gray-400 text-sm">No account? <span className="cursor-pointer" style={{ color: '#1e90ff' }} onClick={() => nav('/signup')}>Sign up</span></p>
      </div>
    </div>
  )
}
