import './strings.js'
import { createRoot } from 'react-dom/client'
import { RackService, filesTab } from 'racklist'
import 'racklist/rack.css'
import { tr } from 'lilak-ui/i18n.jsx'
import def from './def.jsx'
import { RegisterTab, tableView } from './tabs.jsx'

createRoot(document.getElementById('root')).render(
  <RackService def={def} slots={{ tabs: [
    { id: 'register', label: tr('pa_tab_register'), render: (api) => <RegisterTab api={api} /> },
    filesTab('files', { label: tr('pa_tab_files') }),
  ], views: { table: tableView } }} />)
