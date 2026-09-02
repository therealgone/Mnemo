import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || busy) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setBusy(true)

    try {
      const reply = await window.pywebview.api.send_message(text)
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
    <div className="terminal">
      <div className="terminal-log">
        {messages.map((m, i) => (
          <div key={i} className={`line ${m.role}`}>
            <span className="prompt">
              {m.role === 'user' ? '>' : m.role === 'error' ? '!' : '#'}
            </span>
            <span className="text">{m.text}</span>
          </div>
        ))}
        {busy && (
          <div className="line assistant">
            <span className="prompt">#</span>
            <span className="text">...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="terminal-input">
        <span className="prompt">&gt;</span>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message and press Enter..."
          disabled={busy}
          rows={1}
        />
      </div>
    </div>
  )
}

export default App
