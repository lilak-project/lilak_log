/**
 * The service's own tabs: Register (text or a file → /api/register, which
 * answers the set with the same values when there is one) and Table (a set's
 * rows from /api/table, filtered by path).
 */
import './strings.js'
import { useEffect, useMemo, useRef, useState } from 'react'
import { tr } from 'lilak-ui/i18n.jsx'
import { PORTAL_BASE, authHeaders } from 'racklist'
import { FORMATS } from './def.jsx'
import './tabs.css'

export function RegisterTab({ api }) {
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [format, setFormat] = useState('lilak-par')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(null)
  const pick = useRef(null)

  async function go() {
    setBusy(true); setDone(null)
    try {
      const q = new URLSearchParams({ title, format, ...(file ? { name: file.name } : {}) })
      const r = await fetch(`${PORTAL_BASE}/api/register?${q}`, {
        method: 'POST', body: file || text, headers: { 'Content-Type': 'text/plain', ...authHeaders() } })
      const got = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(got.detail || r.status)
      setDone(got)
      if (!got.existing) { setText(''); setFile(null); setTitle('') }
      await api.reload()
    } catch (e) {
      api.setNote?.(tr('pa_reg_failed', e.message))
    }
    setBusy(false)
  }

  const label = done && (done.record.title || done.record.value_hash?.slice(0, 8))
  return (
    <div className="pa-reg">
      <div className="pa-row">
        <input className="pa-in" value={title} onChange={(e) => setTitle(e.target.value)} placeholder={tr('pa_f_title')} />
        <select className="pa-in" value={format} onChange={(e) => setFormat(e.target.value)}>
          {FORMATS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <button type="button" className="rl-btn" onClick={() => pick.current?.click()}>{tr('pa_reg_file')}</button>
        <input ref={pick} type="file" hidden onChange={(e) => { setFile(e.target.files?.[0] || null); e.target.value = '' }} />
        {file && <span className="rl-hint">{file.name} <button type="button" className="rl-x" onClick={() => setFile(null)}>×</button></span>}
      </div>
      {!file && <textarea className="pa-text" value={text} onChange={(e) => setText(e.target.value)}
        placeholder={tr('pa_reg_text')} spellCheck={false} />}
      <div className="pa-row">
        <button type="button" className="rl-btn rl-go" disabled={busy || (!file && !text.trim())} onClick={go}>
          {busy ? tr('pa_reg_busy') : tr('pa_reg_go')}
        </button>
        {done && <span className={done.existing ? 'pa-same' : 'rl-hint'}>
          {tr(done.existing ? 'pa_reg_same' : 'pa_reg_new', label)}{' '}
          <button type="button" className="rl-linkish" onClick={() => api.openItem?.(done.record.id, done.record)}>{tr('pa_reg_open')}</button>
        </span>}
      </div>
    </div>
  )
}

export function TableTab({ api }) {
  const sets = api.doc?.sets || []
  const [id, setId] = useState(sets[0]?.id || '')
  const [got, setGot] = useState(null)
  const [q, setQ] = useState('')
  useEffect(() => {
    if (!id) return
    setGot(null)
    fetch(`${PORTAL_BASE}/api/table?id=${encodeURIComponent(id)}`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : null)).then(setGot).catch(() => setGot(null))
  }, [id])
  const rows = useMemo(() => (got?.rows || []).filter((r) => r.kind === 'value' || r.kind === 'key'), [got])
  const shown = q.trim() ? rows.filter((r) => r.path.toLowerCase().includes(q.trim().toLowerCase())) : rows
  return (
    <div className="pa-tbl">
      <div className="pa-row">
        <select className="pa-in" value={id} onChange={(e) => setId(e.target.value)}>
          <option value="">{tr('pa_tbl_pick')}</option>
          {sets.map((s) => <option key={s.id} value={s.id}>{s.title || s.value_hash?.slice(0, 8)}</option>)}
        </select>
        <input className="pa-in pa-grow" value={q} onChange={(e) => setQ(e.target.value)} placeholder={tr('pa_tbl_find')} />
        {got?.rows && <span className="rl-hint">{tr('pa_tbl_count', shown.length, rows.length)}</span>}
      </div>
      {got && !got.rows && <p className="rl-hint">{tr('pa_tbl_none')}</p>}
      {got?.rows && (
        <table className="pa-grid">
          <thead><tr><th>{tr('pa_col_line')}</th><th>{tr('pa_col_path')}</th><th>{tr('pa_col_value')}</th><th>{tr('pa_col_comment')}</th></tr></thead>
          <tbody>{shown.map((r) => (
            <tr key={r.line}><td className="rl-hint">{r.line}</td><td className="pa-mono">{r.path}</td>
              <td className="pa-mono">{r.value}</td><td className="rl-hint">{r.comment}</td></tr>
          ))}</tbody>
        </table>
      )}
    </div>
  )
}
