import { useEffect, useRef, useState } from 'react'

const GLYPH = { user: '❯', assistant: '#', error: '!' }
const GLYPH_COLOR = { user: 'text-user', assistant: 'text-agent', error: 'text-error' }

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 150)}px`
  }, [input])

  const sendMessage = async () => {
    const value = input.trim()
    if (!value || busy) return

    setMessages((prev) => [...prev, { role: 'user', text: value }])
    setInput('')
    setBusy(true)

    try {
      const reply = await window.pywebview.api.send_message(value)
      setMessages((prev) => [...prev, { role: 'assistant', text: reply }])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'error', text: String(err) }])
    } finally {
      setBusy(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-full w-full flex-col">
      <div className="flex-1 overflow-y-auto px-6 pt-9 pb-2">
        <div className="mx-auto flex max-w-[760px] flex-col gap-[22px]">
          {messages.length === 0 && !busy && (
            <div className="flex flex-col items-start gap-4 pt-6">
              <div className="font-display text-xl font-semibold text-ink">What should I remember?</div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className="grid grid-cols-[20px_1fr] gap-3.5">
              <span className={`font-mono text-[13.5px] leading-[1.7] ${GLYPH_COLOR[m.role]}`}>
                {GLYPH[m.role]}
              </span>
              {m.role === 'error' ? (
                <div className="font-mono text-[14.5px] leading-[1.7] break-words whitespace-pre-wrap text-[#f0b3a6]">
                  {m.text}
                </div>
              ) : (
                <div
                  className={`text-[15px] leading-[1.7] break-words whitespace-pre-wrap ${
                    m.role === 'user' ? 'text-[#cbd8ec]' : 'text-ink'
                  }`}
                  style={{ textWrap: 'pretty' }}
                >
                  {m.text}
                </div>
              )}
            </div>
          ))}

          {busy && (
            <div className="grid grid-cols-[20px_1fr] gap-3.5">
              <span className="font-mono text-[13.5px] leading-[1.7] text-agent">#</span>
              <div className="flex h-[26px] items-center gap-[5px]">
                <span
                  className="h-[5px] w-[5px] rounded-full bg-[#6e7276]"
                  style={{ animation: 'mn-blink 1.1s infinite' }}
                />
                <span
                  className="h-[5px] w-[5px] rounded-full bg-[#6e7276]"
                  style={{ animation: 'mn-blink 1.1s .18s infinite' }}
                />
                <span
                  className="h-[5px] w-[5px] rounded-full bg-[#6e7276]"
                  style={{ animation: 'mn-blink 1.1s .36s infinite' }}
                />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="px-6 pt-3.5 pb-6">
        <div className="mx-auto flex max-w-[760px] flex-col gap-2">
          <div className="flex items-end gap-2.5 rounded-2xl border border-[#232527] bg-[#0f1011] py-2.5 pr-2.5 pl-3.5">
            <span className="pb-[3px] font-mono text-sm text-ink-3">❯</span>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything — memory is searched automatically"
              disabled={busy}
              rows={1}
              className="flex-1 resize-none bg-transparent py-0.5 font-mono text-sm leading-[1.7] text-ink outline-none"
              style={{ maxHeight: 150 }}
            />
            <button
              type="button"
              onClick={() => sendMessage()}
              disabled={busy || !input.trim()}
              className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[10px] border border-border-strong bg-[#191b1d] font-mono text-[13px] text-[#b9bdc1] transition-colors duration-150 hover:bg-surface-2 hover:text-ink disabled:opacity-50"
            >
              ↵
            </button>
          </div>
          <div className="flex justify-between font-mono text-[10.5px] tracking-[.05em] text-ink-3">
            <span>enter to send · shift+enter for newline</span>
            <span>runs entirely on this machine</span>
          </div>
        </div>
      </div>
    </div>
  )
}
