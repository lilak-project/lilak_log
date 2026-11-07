/**
 * parameters — the declaration. A set is one tool's parameters in one format,
 * kept once and reused by every run that used exactly those values (a log in
 * logbook points at it: its `params`; here, `usedBy` lists those logs).
 *
 * The source (text or files), the hashes and the value count are made by the
 * backend's /api/register (tabs.jsx), never typed in the form: that is what
 * keeps "same values → same set" true.
 */
import './strings.js'
import { tr } from 'lilak-ui/i18n.jsx'

export const FORMATS = [
  ['lilak-par', 'lilak-par'], ['nptool', 'nptool'], ['narval-xml', 'narval-xml'], ['get-xcfg', 'get-xcfg'],
  ['manual', tr('pa_fmt_manual')],
]
const short = (h) => String(h || '').slice(0, 8)

export default {
  name: 'parameters', title: tr('pa_title'), unit: tr('pa_unit'), key: 'pa',
  item: {
    key: 'sets', noun: tr('pa_noun'), allLabel: tr('pa_tab_sets'), tabId: 'sets',
    label: (r) => r.title || short(r.value_hash) || tr('pa_noun'),
    order: { k: 'updatedAt', dir: -1 },
    findHint: tr('pa_find_hint'),
    check: (r) => (String(r.title || '').trim() ? '' : tr('pa_need_title')),
    fill: (r) => ({ ...r, title: String(r.title || '').trim(), format: r.format || 'manual',
      origin: r.origin || 'person', status: r.status || 'trial' }),
    fields: [
      { k: 'title', label: tr('pa_f_title'), type: 'text', required: true, width: 420, col: { w: 260, min: 120 }, tone: 'ink' },
      { k: 'format', label: tr('pa_f_format'), type: 'select', options: FORMATS, col: { w: 90, min: 60 }, tone: 'dim' },
      { k: 'stage', label: tr('pa_f_stage'), type: 'class', col: { w: 100, min: 60, drop: 900 }, tone: 'dim' },
      { k: 'status', label: tr('pa_f_status'), type: 'select',
        options: [['trial', tr('pa_s_trial')], ['used', tr('pa_s_used')], ['retired', tr('pa_s_retired')]],
        col: { w: 70, min: 50 }, tone: 'dim' },
      { k: 'count', label: tr('pa_f_count'), type: 'number', edit: false, col: { w: 60, min: 44, drop: 1000 }, tone: 'dim' },
      { k: 'value_hash', label: tr('pa_f_value_hash'), type: 'text', mono: true, edit: false, hint: tr('pa_hash_note'),
        col: { w: 80, min: 60, drop: 1100 }, tone: 'dim', cell: (r) => short(r.value_hash) },
      { k: 'text_hash', label: tr('pa_f_text_hash'), type: 'text', mono: true, edit: false },
      { k: 'files', label: tr('pa_f_files'), type: 'uploads', edit: false, col: { w: 44, min: 36 } },
      { k: 'text', label: tr('pa_f_text'), type: 'longtext', mono: true, rows: 12, edit: false },
      { k: 'cuts', label: tr('pa_f_cuts'), type: 'longtext', mono: true, rows: 4, hint: tr('pa_f_cuts_hint') },
      { k: 'based_on', label: tr('pa_f_based_on'), type: 'ref', to: 'self' },
      { k: 'usedBy', label: tr('pa_f_used_by'), type: 'backlinks',
        from: { svc: 'logbook', item: 'logs', field: 'params', label: 'title' } },
      { k: 'origin', label: tr('pa_f_origin'), type: 'select',
        options: [['auto', tr('pa_o_auto')], ['person', tr('pa_o_person')], ['llm', tr('pa_o_llm')]], tone: 'dim' },
      { k: 'tags', label: tr('pa_f_tags'), type: 'tags', col: { w: 140, min: 60, drop: 1200 }, tone: 'dim' },
      { k: 'author', label: tr('pa_f_author'), type: 'text', edit: false },
      { k: 'body', label: tr('pa_f_body'), type: 'longtext', rows: 6 },
    ],
  },
  classes: [],
  listing: { presets: [['기본', '[{format}] {title}', '⏎']] },
}
