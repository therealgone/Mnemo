import { useRef, useState } from 'react'

export default function UploadMemory({ onUploaded }) {
  const [mode, setMode] = useState('paste')
  const [text, setText] = useState('')
  const [fileName, setFileName] = useState('')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState(null)
  const fileInputRef = useRef(null)

  const reset = () => {
    setText('')
    setFileName('')
    setStatus(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const content = await file.text()
    setBusy(true)
    setStatus(null)
    const res = await window.pywebview.api.upload_memory(content, file.name)
    setStatus(
      res.ok
        ? { ok: true, message: `added ${res.chunks_added} chunk(s) from ${file.name}` }
        : { ok: false, message: res.error }
    )
    setBusy(false)
    if (res.ok) onUploaded?.()
  }

  const handlePaste = async () => {
    if (!text.trim()) return
    setBusy(true)
    setStatus(null)
    const res = await window.pywebview.api.upload_memory(text.trim())
    setStatus(
      res.ok ? { ok: true, message: `added ${res.chunks_added} chunk(s)` } : { ok: false, message: res.error }
    )
    setBusy(false)
    if (res.ok) {
      setText('')
      onUploaded?.()
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-surface p-[18px]">
      <div className="mb-3.5 flex items-center justify-between">
        <span className="font-mono text-[11px] tracking-[.14em] text-[#6e7276] uppercase">add to memory</span>
        <div className="flex gap-1 rounded-full border border-[#202325] p-[3px]">
          <button
            type="button"
            onClick={() => setMode('paste')}
            className={`rounded-full px-3 py-1.5 text-xs transition-colors duration-150 ${
              mode === 'paste' ? 'bg-surface-3 text-ink' : 'text-ink-2 hover:text-ink'
            }`}
          >
            Paste text
          </button>
          <button
            type="button"
            onClick={() => setMode('upload')}
            className={`rounded-full px-3 py-1.5 text-xs transition-colors duration-150 ${
              mode === 'upload' ? 'bg-surface-3 text-ink' : 'text-ink-2 hover:text-ink'
            }`}
          >
            Upload .txt
          </button>
        </div>
      </div>

      {mode === 'paste' ? (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste notes, a transcript, anything worth remembering…"
          disabled={busy}
          rows={3}
          className="min-h-[96px] w-full resize-none rounded-xl border border-dashed border-border-strong bg-[#0b0c0d] p-4 font-mono text-[13px] leading-[1.7] text-ink outline-none"
        />
      ) : (
        <label className="flex min-h-[96px] cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border-strong bg-[#0b0c0d] p-4 text-center">
          <span className="font-mono text-[13px] text-ink-3">{fileName || 'Choose a .txt file to add'}</span>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt"
            onChange={(e) => {
              setFileName(e.target.files[0]?.name ?? '')
              handleFile(e)
            }}
            disabled={busy}
            className="hidden"
          />
        </label>
      )}

      <div className="mt-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {status && (
            <>
              <span className={`h-1.5 w-1.5 rounded-full ${status.ok ? 'bg-agent' : 'bg-error'}`} />
              <span className={`font-mono text-[11.5px] ${status.ok ? 'text-[#93a99a]' : 'text-[#f0b3a6]'}`}>
                {status.message}
              </span>
            </>
          )}
          {!status && busy && <span className="font-mono text-[11.5px] text-ink-3">adding…</span>}
        </div>
        <div className="flex items-center gap-2.5">
          <button type="button" onClick={reset} className="text-[13px] text-ink-2 hover:text-ink">
            Clear
          </button>
          <button
            type="button"
            onClick={handlePaste}
            disabled={busy || mode !== 'paste' || !text.trim()}
            className="rounded-[11px] bg-ink px-4 py-2 text-[13px] font-semibold text-bg transition-colors duration-150 hover:bg-white disabled:opacity-40"
          >
            Add to Memory
          </button>
        </div>
      </div>
    </div>
  )
}
