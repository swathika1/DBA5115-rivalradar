import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskTable from '../components/RiskTable'
import ForecastTable from '../components/ForecastTable'
import ActionTable from '../components/ActionTable'
import PipelineStatusBar from '../components/PipelineStatusBar'
import RadarPulse from '../components/RadarPulse'
import ChatPanel from '../components/ChatPanel'

export default function Dashboard() {
  const { authAxios } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchDashboard = async () => {
    try {
      const res = await authAxios({ method: 'GET', url: '/dashboard' })
      setData(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDashboard() }, [])

  const isPending = !data || data.status === 'pipeline_pending'

  return (
    <div className="min-h-screen" style={{ background: '#0a1628' }}>
      <Header />
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <PipelineStatusBar lastRun={data?.created_at} onRunComplete={fetchDashboard} />

        {loading && <RadarPulse />}

        {!loading && isPending && <RadarPulse />}

        {!loading && !isPending && (
          <>
            <RiskTable data={data?.agent2_output || []} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ForecastTable data={data?.agent3_output || []} />
              <ActionTable data={data?.agent4_output || []} />
            </div>
          </>
        )}
      </main>
      <ChatPanel />
    </div>
  )
}
