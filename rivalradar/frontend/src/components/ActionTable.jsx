const PRIORITY_COLORS = { P0: '#ef4444', P1: '#f97316', P2: '#f59e0b', P3: '#22c55e' }

export default function ActionTable({ data = [] }) {
  const sorted = [...data].sort((a, b) => a.priority.localeCompare(b.priority))
  return (
    <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: '#0f1f3d' }}>
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-white">Board Action Recommendations</h2>
      </div>
      <div className="divide-y divide-gray-800">
        {sorted.map((row, i) => (
          <div key={i} className="px-6 py-4">
            <div className="flex items-start gap-3">
              <span className="px-2 py-0.5 rounded text-xs font-bold shrink-0" style={{ background: PRIORITY_COLORS[row.priority] + '33', color: PRIORITY_COLORS[row.priority] }}>
                {row.priority}
              </span>
              <div>
                <p className="text-white font-medium text-sm">{row.action_title}</p>
                <p className="text-gray-400 text-xs mt-1">{row.company} · {row.owner} · {row.due_window}</p>
                <p className="text-gray-300 text-sm mt-2">{row.action_detail}</p>
              </div>
            </div>
          </div>
        ))}
        {sorted.length === 0 && <div className="px-6 py-6 text-center text-gray-500 text-sm">No recommendations</div>}
      </div>
    </div>
  )
}
