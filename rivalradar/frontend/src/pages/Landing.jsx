import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const nav = useNavigate()
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="text-center mb-16">
        <h1 className="text-5xl font-bold text-white mb-4">
          <span style={{ color: '#1e90ff' }}>Rival</span>Radar
        </h1>
        <p className="text-xl text-gray-300 mb-8">AI-Powered Portfolio Risk Intelligence</p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => nav('/signup')}
            className="px-6 py-3 rounded-lg font-semibold text-white"
            style={{ background: '#1e90ff' }}
          >
            Get Started
          </button>
          <button
            onClick={() => nav('/login')}
            className="px-6 py-3 rounded-lg font-semibold text-white border border-gray-600"
          >
            See How It Works
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
        {[
          { title: 'Early Warning', desc: '12–18 month competitive lead time for portfolio decisions' },
          { title: 'Portfolio Scale', desc: 'Monitor 150–300 portfolio companies simultaneously' },
          { title: 'Cost Efficiency', desc: '$15K vs $50K+ for traditional intelligence platforms' },
        ].map((card) => (
          <div key={card.title} className="p-6 rounded-xl border border-gray-700" style={{ background: '#0f1f3d' }}>
            <h3 className="text-lg font-semibold text-white mb-2" style={{ color: '#1e90ff' }}>{card.title}</h3>
            <p className="text-gray-400 text-sm">{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
