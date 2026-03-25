import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const FREQUENCIES = ['daily', 'weekly', 'monthly']
const CONCERNS = ['Pricing Threats', 'Feature Gaps', 'Market Positioning']

export default function SettingsForm({ initialData = {} }) {
  const { authAxios } = useAuth()
  const [freq, setFreq] = useState(initialData.update_frequency || 'weekly')
  const [concern, setConcern] = useState(initialData.primary_concern || 'Pricing Threats')
  const [competitors, setCompetitors] = useState((initialData.competitors || []).join(', '))
  const [saved, setSaved] = useState(false)

  const save = async () => {
    await authAxios({
      method: 'PATCH',
      url: '/user/settings',
      data: {
        update_frequency: freq,
        primary_concern: concern,
        competitors: competitors.split(',').map(s => s.trim()).filter(Boolean),
      },
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <label className="text-sm text-gray-400 block mb-2">Monitoring Frequency</label>
        <div className="flex gap-2">
          {FREQUENCIES.map(f => (
            <button key={f} onClick={() => setFreq(f)}
              className="px-4 py-2 rounded-lg text-sm capitalize"
              style={{ background: freq === f ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {f}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-sm text-gray-400 block mb-2">Primary Concern</label>
        <div className="flex gap-2 flex-wrap">
          {CONCERNS.map(c => (
            <button key={c} onClick={() => setConcern(c)}
              className="px-4 py-2 rounded-lg text-sm"
              style={{ background: concern === c ? '#1e90ff' : '#1a2744', color: 'white' }}>
              {c}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="text-sm text-gray-400 block mb-2">Custom Competitors</label>
        <textarea
          className="w-full p-3 rounded-lg bg-gray-800 text-white border border-gray-700 text-sm"
          rows={3}
          placeholder="Comma-separated company names"
          value={competitors}
          onChange={e => setCompetitors(e.target.value)}
        />
      </div>
      <button onClick={save} className="px-6 py-2 rounded-lg text-white font-semibold" style={{ background: '#1e90ff' }}>
        {saved ? 'Saved!' : 'Save Settings'}
      </button>
    </div>
  )
}
