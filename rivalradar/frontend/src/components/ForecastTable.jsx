const RISK_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' }

export default function ForecastTable({ data = [] }) {
  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Impact Forecasts</h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left px-4 py-3">Company</th>
            <th className="text-left px-4 py-3">Revenue at Risk</th>
            <th className="text-left px-4 py-3">Time to Impact</th>
            <th className="text-left px-4 py-3">Risk</th>
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.company} className="border-b border-gray-800">
              <td className="px-4 py-3 text-white">{row.company}</td>
              <td className="px-4 py-3 text-gray-300">{(row.revenue_at_risk_pct * 100).toFixed(1)}%</td>
              <td className="px-4 py-3 text-gray-300">{row.time_to_impact}</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 rounded text-xs" style={{ background: RISK_COLORS[row.risk_level] + '33', color: RISK_COLORS[row.risk_level] }}>
                  {row.risk_level}
                </span>
              </td>
            </tr>
          ))}
          {data.length === 0 && <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">No forecasts</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
