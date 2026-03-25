const DOMAIN_META = {
  fintech_neobanks: { icon: '🏦', label: 'Fintech & Neobanks', desc: 'Digital banking, cross-border payments' },
  ecommerce_platforms: { icon: '🛒', label: 'E-Commerce Platforms', desc: 'Shopify, BigCommerce, WooCommerce' },
  edtech: { icon: '🎓', label: 'EdTech', desc: 'Online learning and professional education' },
  pharma_biotech: { icon: '🧬', label: 'Pharma & Biotech', desc: 'FDA approvals, clinical trials, patents' },
  saas_b2b: { icon: '⚡', label: 'B2B SaaS', desc: 'CRM, productivity, and project tools' },
}

export default function DomainCard({ domain, selected, onSelect }) {
  const meta = DOMAIN_META[domain] || { icon: '📊', label: domain, desc: '' }
  return (
    <div
      onClick={() => onSelect(domain)}
      className="p-4 rounded-xl border cursor-pointer transition-all"
      style={{
        background: selected ? 'rgba(30,144,255,0.15)' : '#0f1f3d',
        borderColor: selected ? '#1e90ff' : '#374151',
        boxShadow: selected ? '0 0 12px rgba(30,144,255,0.3)' : 'none',
      }}
    >
      <div className="text-3xl mb-2">{meta.icon}</div>
      <div className="text-sm font-semibold text-white">{meta.label}</div>
      <div className="text-xs text-gray-400 mt-1">{meta.desc}</div>
    </div>
  )
}
