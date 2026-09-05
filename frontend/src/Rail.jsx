import { useEffect, useState } from 'react'

const ITEMS = [
  { id: 'chat', glyph: '❯', label: 'Chat', accent: 'text-user', sub: 'Talk to your local model' },
  { id: 'memory', glyph: '◈', label: 'Memory', accent: 'text-agent', sub: null },
  { id: 'settings', glyph: '⌗', label: 'Settings', accent: 'text-warn', sub: 'Host, model, diagnostics' },
]

const SHORTCUT_KEYS = { '1': 'chat', '2': 'memory', '3': 'settings' }

const STATUS_DOT = {
  ready: 'bg-agent',
  disconnected: 'bg-error',
  not_configured: 'bg-warn',
}

const STATUS_LABEL = {
  ready: (model) => `${model || 'model'} · ready`,
  disconnected: () => 'disconnected',
  not_configured: () => 'not configured',
}

export default function Rail({ current, onChange, memoryCount, connection }) {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onKey = (e) => {
      if (!(e.metaKey || e.ctrlKey)) return
      const target = SHORTCUT_KEYS[e.key]
      if (!target) return
      e.preventDefault()
      onChange(target)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onChange])

  const go = (id) => {
    onChange(id)
    setOpen(false)
  }

  const status = connection?.status ?? 'ready'
  const dotClass = STATUS_DOT[status] ?? STATUS_DOT.ready
  const statusText = (STATUS_LABEL[status] ?? STATUS_LABEL.ready)(connection?.model)

  return (
    <aside
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false)
      }}
      className="relative z-30 flex w-[72px] shrink-0 flex-col items-center gap-2.5 border-r border-border bg-surface py-4 pb-[18px]"
    >
      <div className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[11px] border border-border-strong bg-gradient-to-b from-[#191b1d] to-[#101113] font-display text-[17px] font-bold text-ink">
        M
      </div>
      <div className="my-1.5 h-px w-[22px] shrink-0 bg-border" />

      {ITEMS.map((item) => {
        const active = current === item.id
        return (
          <button
            key={item.id}
            type="button"
            title={item.label}
            aria-current={active ? 'page' : undefined}
            onClick={() => go(item.id)}
            className={`flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl font-mono text-base transition-colors duration-150 focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#3a3e41] ${
              active
                ? 'bg-surface-3 text-ink shadow-[inset_0_0_0_1px_#26292b]'
                : 'text-ink-3 hover:bg-surface-2 hover:text-ink'
            }`}
          >
            {item.glyph}
          </button>
        )
      })}

      <div className="flex-1" />
      <div className={`h-2 w-2 shrink-0 rounded-full ${dotClass}`} />

      {open && (
        <div
          className="absolute inset-y-0 left-0 flex w-[252px] flex-col gap-1.5 border-r border-[#232527] bg-[#0f1011] p-3.5 pt-4 pb-[18px] shadow-[28px_0_60px_rgba(0,0,0,.55)]"
          style={{ animation: 'mn-slide .16s ease both' }}
        >
          <div className="mb-3.5 flex items-center gap-3 px-1">
            <div className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[11px] border border-border-strong bg-gradient-to-b from-[#191b1d] to-[#101113] font-display text-[17px] font-bold text-ink">
              M
            </div>
            <div className="flex flex-col gap-0.5">
              <div className="font-display text-base font-semibold tracking-tight text-ink">Mneme</div>
              <div className="font-mono text-[10.5px] tracking-[.09em] text-[#6e7276] uppercase">
                local · ollama
              </div>
            </div>
          </div>

          {ITEMS.map((item) => {
            const active = current === item.id
            const sub = item.id === 'memory' ? `${memoryCount} saved` : item.sub
            return (
              <button
                key={item.id}
                type="button"
                aria-current={active ? 'page' : undefined}
                onClick={() => go(item.id)}
                className={`flex items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-colors duration-150 ${
                  active ? 'bg-surface-3 shadow-[inset_0_0_0_1px_#26292b]' : 'hover:bg-surface-2'
                }`}
              >
                <span className={`w-4 shrink-0 text-center font-mono text-[15px] ${item.accent}`}>
                  {item.glyph}
                </span>
                <span className="flex flex-col gap-0.5">
                  <span className="text-sm font-medium text-ink">{item.label}</span>
                  <span className="text-[11.5px] leading-snug text-ink-2">{sub}</span>
                </span>
              </button>
            )
          })}

          <div className="flex-1" />
          <div className="flex items-center gap-2.5 rounded-[11px] border border-[#202325] bg-[#0c0d0e] px-3 py-2.5">
            <span className={`h-2 w-2 shrink-0 rounded-full ${dotClass}`} />
            <span className="font-mono text-[11.5px] text-[#9a9ea2]">{statusText}</span>
          </div>
        </div>
      )}
    </aside>
  )
}
