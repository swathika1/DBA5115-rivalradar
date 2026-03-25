export default function RadarPulse() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <style>{`
        @keyframes radar-pulse {
          0% { transform: scale(1); opacity: 0.8; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        .radar-ring { animation: radar-pulse 2s ease-out infinite; }
        .radar-ring:nth-child(2) { animation-delay: 0.6s; }
        .radar-ring:nth-child(3) { animation-delay: 1.2s; }
      `}</style>
      <div className="relative w-24 h-24 flex items-center justify-center">
        {[1,2,3].map(i => (
          <div key={i} className="radar-ring absolute rounded-full border-2" style={{ width: '100%', height: '100%', borderColor: '#1e90ff' }} />
        ))}
        <div className="w-6 h-6 rounded-full z-10" style={{ background: '#1e90ff' }} />
      </div>
      <p className="mt-8 text-gray-400 text-sm">Scanning competitors — pipeline running...</p>
    </div>
  )
}
