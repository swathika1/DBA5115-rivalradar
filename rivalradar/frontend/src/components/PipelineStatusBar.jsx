import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'

export default function PipelineStatusBar({ lastRun, onRunComplete }) {
  const { authAxios } = useAuth()
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const intervalRef = useRef(null)

  const clearPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  useEffect(() => {
    if (!jobId) return
    intervalRef.current = setInterval(async () => {
      try {
        const res = await authAxios({ method: 'GET', url: `/pipeline/status/${jobId}` })
        setStatus(res.data.status)
        if (res.data.status === 'complete' || res.data.status === 'failed') {
          clearPolling()
          if (res.data.status === 'complete' && onRunComplete) onRunComplete()
        }
      } catch {
        clearPolling()
      }
    }, 3000)
    return clearPolling
  }, [jobId])

  const handleRunNow = async () => {
    try {
      const res = await authAxios({ method: 'POST', url: '/pipeline/run' })
      setJobId(res.data.job_id)
      setStatus('pending')
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="flex items-center justify-between px-6 py-4 rounded-xl border border-gray-700" style={{ background: '#0f1f3d' }}>
      <div className="text-sm text-gray-300">
        {lastRun && <span>Last run: {new Date(lastRun).toLocaleString()}</span>}
        {jobId && status && <span className="ml-4 text-xs px-2 py-1 rounded" style={{ background: '#1e90ff33', color: '#1e90ff' }}>Pipeline: {status}</span>}
      </div>
      <button
        onClick={handleRunNow}
        disabled={status === 'pending' || status === 'running'}
        className="px-4 py-2 rounded-lg text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: '#1e90ff' }}
      >
        Run Now
      </button>
    </div>
  )
}
