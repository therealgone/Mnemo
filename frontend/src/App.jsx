import { useCallback, useEffect, useState } from 'react'
import Rail from './Rail'
import Chat from './Chat'
import Saved_Memory from './Saved-Memory'
import Settings from './Settings'

const LABELS = {
  chat: ['chat', 'talk to your model'],
  memory: ['memory', 'saved notes & recall'],
  settings: ['settings', 'local ollama only'],
}

const HEADER_DOT = {
  ready: 'bg-agent',
  disconnected: 'bg-error',
  not_configured: 'bg-warn',
}

function App() {
  const [view, setView] = useState('chat')
  const [configured, setConfigured] = useState(true)
  const [settings, setSettings] = useState({ ollama_host: '', llm_model: '' })
  const [connStatus, setConnStatus] = useState('not_configured')
  const [memoryCount, setMemoryCount] = useState(0)

  const refreshConnection = useCallback(async () => {
    const ok = await window.pywebview.api.is_configured()
    setConfigured(ok)
    if (!ok) {
      setConnStatus('not_configured')
      return
    }
    const s = await window.pywebview.api.get_settings()
    setSettings(s)
    const res = await window.pywebview.api.test_ollama_connection(s.ollama_host)
    setConnStatus(res.ok ? 'ready' : 'disconnected')
  }, [])

  useEffect(() => {
    refreshConnection()
    window.pywebview.api.get_memory().then((data) => setMemoryCount(data.length))
  }, [refreshConnection])

  useEffect(() => {
    if (!configured) setView('settings')
  }, [configured])

  const [label, sub] = LABELS[view]
  const dotClass = HEADER_DOT[connStatus] ?? HEADER_DOT.not_configured

  return (
    <div className="flex h-screen w-screen bg-bg font-sans text-sm text-ink">
      <Rail
        current={view}
        onChange={setView}
        memoryCount={memoryCount}
        connection={{ model: settings.llm_model, status: connStatus }}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        {!configured && (
          <div className="flex items-center gap-3 border-b border-[rgba(210,160,70,.28)] bg-[rgba(210,160,70,.10)] px-6 py-3">
            <span className="font-mono text-xs text-warn">[ setup ]</span>
            <span className="text-[13px] text-[#ebd6ae]">
              First-time setup — point Mneme at your local Ollama, pick a model, then Save.
            </span>
          </div>
        )}

        <header className="flex h-[58px] shrink-0 items-center justify-between border-b border-surface-3 bg-bg px-6">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-[11px] tracking-[.16em] text-[#6e7276] uppercase">{label}</span>
            <span className="text-[13px] text-ink-2">{sub}</span>
          </div>
          <div className="flex items-center gap-2.5 rounded-full border border-[#202325] px-3 py-1.5">
            <span className={`h-[7px] w-[7px] rounded-full ${dotClass}`} />
            <span className="font-mono text-[11.5px] text-[#9a9ea2]">{settings.llm_model || '—'}</span>
          </div>
        </header>

        <div className="min-h-0 flex-1 overflow-hidden">
          {view === 'chat' && <Chat />}
          {view === 'memory' && <Saved_Memory onCountChange={setMemoryCount} />}
          {view === 'settings' && (
            <Settings
              onSaved={() => {
                setConfigured(true)
                refreshConnection()
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
