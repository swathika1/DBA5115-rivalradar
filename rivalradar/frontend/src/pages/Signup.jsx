import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import DomainCard from '../components/DomainCard'

const DOMAINS = ['fintech_neobanks', 'ecommerce_platforms', 'edtech', 'pharma_biotech', 'saas_b2b']
const FREQUENCIES = ['Daily', 'Weekly', 'Monthly']
const CONCERNS = ['Pricing Threats', 'Feature Gaps', 'Market Positioning']

export default function Signup() {
  const nav = useNavigate()
  const { signup } = useAuth()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '', email: '', password: '',
    company_name: '', domain: '',
    update_frequency: 'Weekly', primary_concern: 'Pricing Threats', competitors: '',
  })
  const [error, setError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async () => {
    try {
      await signup({
        email: form.email,
        password: form.password,
        company_name: form.company_name,
        domain: form.domain,
        update_frequency: form.update_frequency.toLowerCase(),
        primary_concern: form.primary_concern,
        competitors: form.competitors ? form.competitors.split(',').map(s => s.trim()).filter(Boolean) : [],
      })
      nav('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Signup failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: '#0a1628' }}>
      <div className="w-full max-w-lg">
        {/* Progress bar */}
        <div className="flex gap-2 mb-8">
          {[1,2,3].map(i => (
            <div key={i} className="h-1 flex-1 rounded-full" style={{ background: i <= step ? '#1e90ff' : '#374151' }} />
          ))}
        </div>

        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Create your account</h2>
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Full name" value={form.name} onChange={e => set('name', e.target.value)} />
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Email" type="email" value={form.email} onChange={e => set('email', e.target.value)} />
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Password" type="password" value={form.password} onChange={e => set('password', e.target.value)} />
            <button onClick={() => setStep(2)} className="w-full py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Next</button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Select your domain</h2>
            <input className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700" placeholder="Company name" value={form.company_name} onChange={e => set('company_name', e.target.value)} />
            <div className="grid grid-cols-2 gap-3 mt-2">
              {DOMAINS.map(d => <DomainCard key={d} domain={d} selected={form.domain === d} onSelect={v => set('domain', v)} />)}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setStep(1)} className="flex-1 py-3 rounded-lg text-white border border-gray-600">Back</button>
              <button onClick={() => setStep(3)} className="flex-1 py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Next</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white">Preferences</h2>
            <div>
              <p className="text-sm text-gray-400 mb-2">Monitoring frequency</p>
              <div className="flex gap-2">
                {FREQUENCIES.map(f => (
                  <button key={f} onClick={() => set('update_frequency', f)}
                    className="flex-1 py-2 rounded-lg text-sm font-medium"
                    style={{ background: form.update_frequency === f ? '#1e90ff' : '#1a2744', color: 'white' }}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-2">Primary concern</p>
              <div className="flex gap-2 flex-wrap">
                {CONCERNS.map(c => (
                  <button key={c} onClick={() => set('primary_concern', c)}
                    className="px-3 py-2 rounded-lg text-sm font-medium"
                    style={{ background: form.primary_concern === c ? '#1e90ff' : '#1a2744', color: 'white' }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
            <textarea className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 text-sm" rows={3} placeholder="Custom competitors (optional, comma-separated)" value={form.competitors} onChange={e => set('competitors', e.target.value)} />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <div className="flex gap-2">
              <button onClick={() => setStep(2)} className="flex-1 py-3 rounded-lg text-white border border-gray-600">Back</button>
              <button onClick={handleSubmit} className="flex-1 py-3 rounded-lg font-semibold text-white" style={{ background: '#1e90ff' }}>Launch RivalRadar</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
