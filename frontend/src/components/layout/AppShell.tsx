import { NavLink, Outlet } from 'react-router-dom'
import { BookOpen, Droplets, LayoutDashboard, LineChart, Map, Scale } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/trends', label: 'Trends', icon: LineChart, end: false },
  { to: '/map', label: 'Map', icon: Map, end: false },
  { to: '/compare', label: 'Compare', icon: Scale, end: false },
  { to: '/impact', label: 'Impact', icon: Droplets, end: false },
  { to: '/methodology', label: 'Methodology', icon: BookOpen, end: false },
]

export function AppShell() {
  return (
    <div className="min-h-screen bg-ink text-mist lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-b border-line bg-panel lg:border-r lg:border-b-0">
        <div className="px-5 py-5">
          <p className="text-xs tracking-[0.18em] text-accent uppercase">NASA Space Apps</p>
          <h1 className="mt-1 text-lg font-semibold text-white">EarthTrend Myanmar</h1>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-3 pb-3 lg:flex-col lg:px-3 lg:pb-6">
          {links.map((link) => {
            const Icon = link.icon
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm whitespace-nowrap ${
                    isActive ? 'bg-panel-2 text-white' : 'text-muted hover:text-white'
                  }`
                }
              >
                <Icon size={16} aria-hidden="true" />
                {link.label}
              </NavLink>
            )
          })}
        </nav>
      </aside>
      <div>
        <header className="border-b border-line px-6 py-4 text-sm text-muted">
          Rainfall, temperature, and humidity trends from NASA POWER
        </header>
        <main className="px-6 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
