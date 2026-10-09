import { Fingerprint, FolderOpen, GitCompare, Map, Search } from 'lucide-react'
import type { SectionId } from '../../types'
import { useCase } from '../../context/CaseContext'

const items: Array<{ id: SectionId; label: string; icon: typeof Search; tour?: string }> = [
  { id: 'overview', label: 'Case Overview', icon: Search },
  { id: 'map', label: 'Investigation Map', icon: Map },
  { id: 'fingerprint', label: 'Fingerprint', icon: Fingerprint },
  { id: 'compare', label: 'Compare Twins', icon: GitCompare, tour: 'compare' },
  { id: 'evidence', label: 'Evidence', icon: FolderOpen },
]

export function SectionNav() {
  const { section, setSection } = useCase()
  return (
    <>
      <nav className="hidden gap-2 border-b border-line px-4 py-3 md:flex">
        {items.map((item) => {
          const Icon = item.icon
          const active = section === item.id
          return (
            <button
              key={item.id}
              type="button"
              data-tour={item.tour}
              onClick={() => setSection(item.id)}
              className={`flex items-center gap-2 rounded-2xl px-4 py-3 text-sm ${
                active ? 'bg-gold text-navy' : 'border border-line text-ink'
              }`}
            >
              <Icon size={18} aria-hidden="true" />
              {item.label}
            </button>
          )
        })}
      </nav>
      <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-line bg-navy md:hidden">
        {items.map((item) => {
          const Icon = item.icon
          const active = section === item.id
          return (
            <button
              key={item.id}
              type="button"
              data-tour={item.tour}
              onClick={() => setSection(item.id)}
              className={`flex flex-col items-center gap-1 px-1 py-2 text-[10px] ${active ? 'text-gold' : 'text-muted'}`}
            >
              <Icon size={16} aria-hidden="true" />
              {item.label.split(' ')[0]}
            </button>
          )
        })}
      </nav>
    </>
  )
}
