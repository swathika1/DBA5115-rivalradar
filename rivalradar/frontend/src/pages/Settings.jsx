import Header from '../components/Header'
import SettingsForm from '../components/SettingsForm'

export default function Settings() {
  return (
    <div className="min-h-screen" style={{ background: '#0a1628' }}>
      <Header />
      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-bold text-white mb-8">Settings</h1>
        <SettingsForm />
      </main>
    </div>
  )
}
