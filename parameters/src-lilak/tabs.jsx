/**
 * Register (text or a file → /api/register, which answers the set with the
 * same values when there is one), and the `partable` field: a set's rows in
 * its editor.
 */
import './strings.js'
import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import { tr } from 'lilak-ui/i18n.jsx'
import { PORTAL_BASE, authHeaders, projectKey, registerType, useColumnWidths, RackTable, RackRow } from 'racklist'
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

const COLS = [
  { k: 'line', w: 50, min: 36, label: tr('pa_col_line'), num: true },
  { k: 'path', w: 360, min: 120, label: tr('pa_col_path') },
  { k: 'value', w: 160, min: 60, label: tr('pa_col_value') },
  { k: 'unit', w: 70, min: 40, label: tr('pa_col_unit'), drop: 1000 },
  { k: 'range', w: 120, min: 50, label: tr('pa_col_range'), drop: 1100 },
  { k: 'comment', w: 360, min: 80, label: tr('pa_col_comment') },
]

const PAGE = 300
const TONE = { line: 'dim', unit: 'dim', range: 'dim', comment: 'dim' }

/** A set's rows, read from its source by the backend (/api/table), in the
 *  rack table: inside the set's editor, or filling a tab of its own (`full`,
 *  opened by tableButton at the top of the editor). */
export function ParTable({ id, full }) {
  const [got, setGot] = useState(null)
  const [q, setQ] = useState('')
  const { drag, sized } = useColumnWidths(projectKey('table', 'cols'), COLS)
  const cols = sized(COLS, 9999)
  useEffect(() => {
    if (!id) return
    setGot(null)
    fetch(`${PORTAL_BASE}/api/table?id=${encodeURIComponent(id)}`, { headers: authHeaders() })
      .then((r) => (r.ok ? r.json() : { rows: null })).then(setGot).catch(() => setGot({ rows: null }))
  }, [id])
  const rows = useMemo(() => (got?.rows || []).map((r) => ({
    ...r, hay: `${r.path} ${r.value ?? ''} ${r.comment ?? ''}`.toLowerCase() })), [got])
  const k = useDeferredValue(q.trim().toLowerCase())
  const shown = useMemo(() => (k ? rows.filter((r) => r.hay.includes(k)) : rows), [rows, k])
  // Group headers between rows wherever the path's prefix changes (not while
  // filtering: then it is a flat list of matches). `shut` holds folded prefixes.
  // Remembered per set in this browser, so the editor's table and the tab agree.
  const foldKey = projectKey('table', `fold.${id}`)
  const [shut, setShutState] = useState(() => new Set())
  useEffect(() => {
    try { setShutState(new Set(JSON.parse(localStorage.getItem(foldKey) || '[]'))) } catch { setShutState(new Set()) }
  }, [foldKey])
  const setShut = (next) => setShutState((cur) => {
    const v = typeof next === 'function' ? next(cur) : next
    try { v.size ? localStorage.setItem(foldKey, JSON.stringify([...v])) : localStorage.removeItem(foldKey) } catch { /* private window */ }
    return v
  })
  const items = useMemo(() => {
    if (k) return shown
    const out = []
    const n = {}
    let prev = []
    for (const r of rows) {
      const segs = r.path.split('/').slice(0, -1)
      let i = 0
      while (i < segs.length && segs[i] === prev[i]) i++
      for (let j = i; j < segs.length; j++) out.push({ head: `${segs.slice(0, j + 1).join('/')}/`, depth: j })
      for (let j = 1; j <= segs.length; j++) { const h = `${segs.slice(0, j).join('/')}/`; n[h] = (n[h] || 0) + 1 }
      out.push(r)
      prev = segs
    }
    for (const it of out) if (it.head) it.n = n[it.head]
    return out
  }, [rows, shown, k])
  const heads = useMemo(() => [...new Set(items.filter((it) => it.head).map((it) => it.head))], [items])
  const visible = useMemo(() => {
    if (!shut.size) return items
    const s = [...shut]
    return items.filter((it) => { const key = it.head || it.path; return !s.some((h) => key !== h && key.startsWith(h)) })
  }, [items, shut])
  const fold = (h) => setShut((cur) => { const nx = new Set(cur); nx.has(h) ? nx.delete(h) : nx.add(h); return nx })
  // ponytail: grows by PAGE as the end scrolls into view instead of true
  // virtualisation; fine to ~tens of thousands of rows.
  const [upto, setUpto] = useState(PAGE)
  useEffect(() => setUpto(PAGE), [k, id])
  const end = useRef(null)
  useEffect(() => {
    const el = end.current
    if (!el || upto >= visible.length) return undefined
    const io = new IntersectionObserver((e) => { if (e[0].isIntersecting) setUpto((n) => n + PAGE) }, { rootMargin: '600px' })
    io.observe(el)
    return () => io.disconnect()
  }, [upto, visible.length])
  if (!id) return null
  if (!got) return <span className="rl-hint">…</span>
  if (!got.rows) return <span className="rl-hint">{tr('pa_tbl_none')}</span>
  return (
    <div className={full ? 'pa-tbl pa-sheet pa-tbl-full' : 'pa-tbl pa-sheet'}>
      <div className="pa-row">
        <input className="pa-in pa-grow" value={q} onChange={(e) => setQ(e.target.value)} placeholder={tr('pa_tbl_find')} />
        {!k && heads.length > 0 && <>
          <button type="button" className="rl-btn pa-flat" onClick={() => setShut(new Set(heads))}>{tr('pa_fold_all')}</button>
          <button type="button" className="rl-btn pa-flat" onClick={() => setShut(new Set())}>{tr('pa_open_all')}</button>
        </>}
        <span className="rl-hint">{tr('pa_tbl_count', shown.length, rows.length)}</span>
      </div>
      <div className={full ? 'pa-tbl-fill' : 'pa-tbl-box'}>
        <RackTable cols={cols} onDrag={drag('')}>
          {visible.slice(0, upto).map((r, i) => (r.head ? (
            <RackRow key={`h${i}`} cols={cols} className="pa-grp" onClick={() => fold(r.head)}
              cell={{ line: '', path: <span style={{ paddingLeft: r.depth * 14 }}>{shut.has(r.head) ? '▸' : '▾'} {r.head} <i className="rl-dim">{r.n}</i></span> }} />
          ) : (
            <RackRow key={r.line + r.path} cols={cols} mark={k} tone={TONE}
              cell={{ line: r.line, path: r.path, value: r.value ?? '', unit: r.unit || '', range: r.range || '', comment: r.comment || '' }} />
          )))}
          {upto < visible.length && <div ref={end} className="pa-more">…</div>}
        </RackTable>
      </div>
    </div>
  )
}

registerType('partable', {
  text: () => '',
  Show: ({ value }) => <ParTable id={value} />,
})

/** The formats the backend reads as a table (parlib.FORMATS). */
const TABLED = ['lilak-par', 'get-xcfg']

/** The editor's top-bar button: the set's table as a tab of its own. */
export function tableButton(f, setF, ctx) {
  if (!f.id || !TABLED.includes(f.format) || !ctx?.openTab) return null
  return (
    <button type="button" className="rl-btn" onClick={() => ctx.openTab({
      id: `table:${f.id}`, kind: 'view', view: 'table', who: f.id,
      label: `${tr('pa_f_table')} · ${f.title || String(f.value_hash || '').slice(0, 8)}` })}>
      {tr('pa_tbl_tab')}
    </button>
  )
}

/** The tab that button opens. */
export const tableView = (tab) => <ParTable key={tab.who} id={tab.who} full />
