import React, { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const RISK_COLORS = { low: '#22c55e', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' }
const MOAT_DIMS = ['network_effects','switching_costs','economies_of_scale','proprietary_technology','brand_strength','data_moat','integration_lock_in','regulatory_barriers']

export default function RiskTable({ data = [] }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Portfolio Risk Assessment</h2>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-400 border-b border-gray-700">
            <th className="text-left px-6 py-3">Company</th>
            <th className="text-left px-6 py-3">Risk Level</th>
            <th className="text-left px-6 py-3">Vulnerability Score</th>
            <th className="text-left px-6 py-3">Confidence</th>
            <th className="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <React.Fragment key={row.company}>
              <tr className="border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer" onClick={() => setExpanded(expanded === i ? null : i)}>
                <td className="px-6 py-4 text-white font-medium">{row.company}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 rounded text-xs font-semibold" style={{ background: RISK_COLORS[row.risk_level] + '33', color: RISK_COLORS[row.risk_level] }}>
                    {row.risk_level?.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-300">{(row.vulnerability_score * 100).toFixed(0)}%</td>
                <td className="px-6 py-4 text-gray-300">{(row.confidence * 100).toFixed(0)}%</td>
                <td className="px-6 py-4 text-gray-500">{expanded === i ? '▲' : '▼'}</td>
              </tr>
              {expanded === i && (
                <tr key={`${row.company}-exp`} className="border-b border-gray-800">
                  <td colSpan={5} className="px-6 py-4">
                    <p className="text-gray-300 text-sm mb-4">{row.reasoning_summary}</p>
                    <ResponsiveContainer width="100%" height={160}>
                      <BarChart data={MOAT_DIMS.map(dim => {
                        const comp = row.component_breakdown?.find(c => c.dimension === dim)
                        return { name: dim.replace(/_/g,' '), score: comp?.score || 0 }
                      })}>
                        <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <YAxis domain={[0,1]} tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <Tooltip contentStyle={{ background: '#0f1f3d', border: '1px solid #374151' }} />
                        <Bar dataKey="score" fill="#1e90ff" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
          {data.length === 0 && (
            <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No data available</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
