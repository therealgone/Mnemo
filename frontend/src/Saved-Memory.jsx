import { useCallback, useEffect, useState } from 'react'
import UploadMemory from './UploadMemory'

function SkeletonCard() {
  return <div className="h-[104px] animate-pulse rounded-2xl border border-border bg-surface" />
}

export default function Saved_Memory({ onCountChange }) {
  const [memory, setMemory] = useState(null)
  const [expanded, setExpanded] = useState({})
  const [query, setQuery] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editDraft, setEditDraft] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState('')

  const loadMemory = useCallback(async () => {
    const data = await window.pywebview.api.get_memory()
    setMemory(data)
    onCountChange?.(data.length)
  }, [onCountChange])

  useEffect(() => {
    loadMemory()
  }, [loadMemory])

  const toggleTrail = (id) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))

  const handleDelete = async (id) => {
    setDeletingId(id)
    try {
      await window.pywebview.api.delete_memory(id)
      setMemory((prev) => {
        const next = prev.filter((m) => m.id !== id)
        onCountChange?.(next.length)
        return next
      })
    } finally {
      setDeletingId(null)
    }
  }

  const startEdit = (id) => {
    setEditingId(id)
    setEditDraft('')
    setEditError('')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditDraft('')
    setEditError('')
  }

  const handleEditSave = async (id) => {
    if (!editDraft.trim()) return
    setSavingEdit(true)
    setEditError('')
    try {
      const res = await window.pywebview.api.edit_memory(id, editDraft.trim())
      if (res.ok) {
        setEditingId(null)
        setEditDraft('')
        await loadMemory()
      } else {
        setEditError(res.error || 'Failed to save edit.')
      }
    } finally {
      setSavingEdit(false)
    }
  }

  const filtered = memory?.filter((m) => m.text.toLowerCase().includes(query.trim().toLowerCase())) ?? null

  return (
    <div className="h-full overflow-y-auto px-6 pt-[30px] pb-10">
      <div className="mx-auto flex max-w-[880px] flex-col gap-[26px]">
        <UploadMemory onUploaded={loadMemory} />

        {memory && memory.length > 0 && (
          <div className="flex items-center gap-2.5 rounded-[11px] border border-[#232527] bg-surface px-3.5 py-2.5">
            <span className="font-mono text-[13px] text-ink-3">⌕</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search memory…"
              className="flex-1 bg-transparent font-mono text-[13px] text-ink outline-none placeholder:text-ink-3"
            />
          </div>
        )}

        {memory === null && (
          <div className="flex flex-col gap-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {memory?.length === 0 && (
          <div className="flex flex-col items-center gap-2.5 rounded-2xl border border-dashed border-[#26292b] px-6 py-[52px] text-center">
            <div className="font-mono text-xl text-[#3e4245]">◈</div>
            <div className="font-display text-[17px] font-semibold text-ink">No memories stored yet</div>
            <div className="max-w-[340px] text-[13px] leading-[1.6] text-ink-2">
              Paste a note or drop a .txt above. Mneme chunks it, tags it, and recalls it in chat when it's
              relevant.
            </div>
          </div>
        )}

        {memory && memory.length > 0 && filtered.length === 0 && (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-[#26292b] px-6 py-10 text-center">
            <div className="text-[13px] text-ink-2">No memories match "{query}"</div>
          </div>
        )}

        {memory && filtered.length > 0 && (
          <div className="flex flex-col gap-3">
            {filtered.map((mem) => {
              const trail = Array.isArray(mem.edit_trail) ? mem.edit_trail : []
              const isExpanded = !!expanded[mem.id]
              const visibleTrail = isExpanded ? trail : trail.slice(0, 3)
              const isEditing = editingId === mem.id
              return (
                <div key={mem.id} className="rounded-2xl border border-border bg-surface p-[18px]">
                  <div className="mb-2.5 flex items-center justify-end gap-2 font-mono text-[11px]">
                    <button
                      type="button"
                      onClick={() => (isEditing ? cancelEdit() : startEdit(mem.id))}
                      disabled={deletingId === mem.id}
                      className="rounded-full border border-warn/40 bg-warn/10 px-2.5 py-1 text-warn transition-colors duration-150 hover:bg-warn/20 disabled:opacity-50"
                    >
                      {isEditing ? 'cancel' : 'edit'}
                    </button>
                    <button
                      type="button"
                      onClick={() => deletingId === null && handleDelete(mem.id)}
                      disabled={deletingId !== null}
                      className="rounded-full border border-error/40 bg-error/10 px-2.5 py-1 text-error transition-colors duration-150 hover:bg-error/20 disabled:opacity-50"
                    >
                      {deletingId === mem.id ? 'deleting…' : 'delete'}
                    </button>
                  </div>
                  <div className="text-[14.5px] leading-[1.72] text-ink" style={{ textWrap: 'pretty' }}>
                    {mem.text}
                  </div>

                  {isEditing && (
                    <div className="mt-3 flex flex-col gap-2 rounded-[11px] border border-warn/30 bg-warn/5 p-3">
                      <textarea
                        value={editDraft}
                        onChange={(e) => setEditDraft(e.target.value)}
                        placeholder="What changed? e.g. I watched it already, it was 10/10"
                        rows={2}
                        autoFocus
                        className="resize-none bg-transparent font-mono text-[13px] leading-[1.6] text-ink outline-none placeholder:text-ink-3"
                      />
                      {editError && <div className="text-[11.5px] text-error">{editError}</div>}
                      <div className="flex items-center gap-2 self-end">
                        <button
                          type="button"
                          onClick={cancelEdit}
                          disabled={savingEdit}
                          className="rounded-[9px] border border-[#232527] px-3 py-1.5 text-[12px] text-ink-2 hover:bg-surface-2 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEditSave(mem.id)}
                          disabled={savingEdit || !editDraft.trim()}
                          className="rounded-[9px] border border-warn/40 bg-warn/15 px-3 py-1.5 text-[12px] font-semibold text-warn hover:bg-warn/25 disabled:opacity-50"
                        >
                          {savingEdit ? 'saving…' : 'Save edit'}
                        </button>
                      </div>
                    </div>
                  )}
                  <div className="mt-3 flex gap-4 font-mono text-[10.5px] tracking-[.05em] text-ink-3">
                    <span>created {mem.date}</span>
                    {mem.last_edited && <span>last edited {mem.last_edited}</span>}
                  </div>
                  {trail.length > 0 && (
                    <div className="mt-3 flex flex-col gap-1.5 border-t border-[#1a1c1e] pt-3">
                      <div className="font-mono text-[10.5px] tracking-[.12em] text-ink-3 uppercase">
                        edit trail · {trail.length}
                      </div>
                      {visibleTrail.map((entry, i) => (
                        <div key={i} className="flex items-baseline gap-2">
                          <span className="font-mono text-[11px] text-[#3e4245]">·</span>
                          <span className="text-[12.5px] leading-[1.55] text-ink-2">{entry}</span>
                        </div>
                      ))}
                      {trail.length > 3 && (
                        <button
                          type="button"
                          onClick={() => toggleTrail(mem.id)}
                          className="mt-0.5 self-start font-mono text-[11px] text-ink-3 hover:text-ink"
                        >
                          {isExpanded ? 'show less' : 'show all'}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
