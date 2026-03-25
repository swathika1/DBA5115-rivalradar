import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function ChatPanel() {
  const { authAxios } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim()) return
    const userMsg = { role: 'user', content: input }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await authAxios({ method: 'POST', url: '/chat', data: { message: input } })
      setMessages(m => [...m, { role: 'assistant', content: res.data.reply }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Error getting response.' }])
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="fixed bottom-6 right-6 w-12 h-12 rounded-full flex items-center justify-center text-white text-xl shadow-lg" style={{ background: '#1e90ff' }}>
        💬
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-80 rounded-xl border border-gray-700 flex flex-col shadow-2xl" style={{ background: '#0f1f3d', height: '420px' }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <span className="text-sm font-semibold text-white">RivalRadar AI</span>
        <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">✕</button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`text-sm ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <span className="inline-block px-3 py-2 rounded-lg max-w-[85%]" style={{ background: m.role === 'user' ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {m.content}
            </span>
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 px-4 py-3 border-t border-gray-700">
        <input
          className="flex-1 bg-gray-800 text-white text-sm px-3 py-2 rounded-lg border border-gray-700 outline-none"
          placeholder="Ask about competitors..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button onClick={send} className="px-3 py-2 rounded-lg text-white text-sm" style={{ background: '#1e90ff' }}>↑</button>
      </div>
    </div>
  )
}
