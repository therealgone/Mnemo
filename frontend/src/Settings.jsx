import { useEffect, useState } from 'react'

export default function Settings({ onSaved }) {
  const [host, setHost] = useState('http://localhost:11434')
  const [models, setModels] = useState([])
  const [model, setModel] = useState('')
  const [helper, setHelper] = useState('')
  const [diagnostics, setDiagnostics] = useState(null)
  const [pending, setPending] = useState(null)

  useEffect(() => {
    async function load() {
      const settings = await window.pywebview.api.get_settings()
      setHost(settings.ollama_host)
      setModel(settings.llm_model)
      await fetchModels(settings.ollama_host)
    }
    load()
  }, [])

  const fetchModels = async (hostValue) => {
    setPending('models')
    setDiagnostics(null)
    const res = await window.pywebview.api.get_ollama_models(hostValue)
    if (res.ok) {
      setModels(res.models)
      setHelper(res.models.length ? `${res.models.length} model(s) found` : 'no local models found')
    } else {
      setDiagnostics({ ok: false, message: res.error })
    }
    setPending(null)
  }

  const refreshModels = () => fetchModels(host)

  const testConnection = async () => {
    setPending('connection')
    setDiagnostics(null)
    const res = await window.pywebview.api.test_ollama_connection(host)
    setDiagnostics({ ok: res.ok, message: res.message })
    setPending(null)
  }

  const testToolCalling = async () => {
    setPending('tools')
    setDiagnostics(null)
    const res = await window.pywebview.api.test_tool_calling(host, model)
    setDiagnostics({ ok: res.ok, message: res.message })
    setPending(null)
  }

  const save = async () => {
    setPending('save')
    const res = await window.pywebview.api.save_settings({ ollama_host: host, llm_model: model })
    setDiagnostics({ ok: res.ok, message: res.ok ? 'settings saved' : res.error })
    setPending(null)
    if (res.ok) onSaved?.()
  }

  const dotColor = diagnostics == null ? 'bg-warn' : diagnostics.ok ? 'bg-agent' : 'bg-error'

  return (
    <div className="h-full overflow-y-auto px-6 pt-[34px] pb-11">
      <div className="mx-auto flex max-w-[620px] flex-col gap-[26px]">
        <div className="flex flex-col gap-1.5">
          <h1 className="m-0 font-display text-[26px] font-semibold tracking-tight text-ink">Settings</h1>
          <p className="m-0 text-[13.5px] leading-[1.6] text-ink-2">
            Mneme talks only to the Ollama instance you point it at. Nothing leaves this machine.
          </p>
        </div>

        <div className="flex flex-col gap-[18px]">
          <div className="flex flex-col gap-2">
            <label className="font-mono text-[10.5px] tracking-[.12em] text-[#6e7276] uppercase">
              ollama host
            </label>
            <input
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="http://localhost:11434"
              className="rounded-[11px] border border-[#232527] bg-surface px-3.5 py-3 font-mono text-[13.5px] text-ink outline-none focus:border-[#3a3e41]"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="font-mono text-[10.5px] tracking-[.12em] text-[#6e7276] uppercase">model</label>
            <div className="flex gap-2.5">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="flex-1 rounded-[11px] border border-[#232527] bg-surface px-3.5 py-3 font-mono text-[13.5px] text-ink outline-none focus:border-[#3a3e41]"
              >
                {model && !models.includes(model) && <option value={model}>{model}</option>}
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={refreshModels}
                disabled={pending !== null}
                className="rounded-[11px] border border-[#232527] px-4 py-3 text-[13px] whitespace-nowrap text-[#b9bdc1] transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
              >
                {pending === 'models' ? 'testing…' : 'Refresh'}
              </button>
            </div>
            {helper && <span className="font-mono text-[11px] text-ink-3">{helper}</span>}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={save}
            disabled={pending !== null}
            className="rounded-[11px] bg-ink px-[17px] py-2.5 text-[13px] font-semibold text-bg transition-colors duration-150 hover:bg-white"
          >
            {pending === 'save' ? 'testing…' : 'Save'}
          </button>
          <button
            type="button"
            onClick={testConnection}
            disabled={pending !== null}
            className="rounded-[11px] border border-[#232527] px-[15px] py-2.5 text-[13px] text-[#b9bdc1] transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
          >
            {pending === 'connection' ? 'testing…' : 'Test connection'}
          </button>
          <button
            type="button"
            onClick={testToolCalling}
            disabled={pending !== null || !model}
            className="rounded-[11px] border border-[#232527] px-[15px] py-2.5 text-[13px] text-[#b9bdc1] transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
          >
            {pending === 'tools' ? 'testing…' : 'Test tool-calling'}
          </button>
        </div>

        {diagnostics && (
          <div className="flex flex-col gap-2.5 rounded-2xl border border-border bg-[#0c0d0e] p-4">
            <div className="flex items-center gap-2.5">
              <span className={`h-[7px] w-[7px] rounded-full ${dotColor}`} />
              <span className="font-mono text-[11px] tracking-[.1em] text-[#93a99a] uppercase">diagnostics</span>
            </div>
            <pre className="m-0 font-mono text-xs leading-[1.75] whitespace-pre-wrap text-[#9a9ea2]">
              {diagnostics.message}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
