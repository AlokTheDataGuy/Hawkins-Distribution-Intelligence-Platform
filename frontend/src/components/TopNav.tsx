import { NavLink } from 'react-router-dom'
import { Menu } from 'lucide-react'

const PAGES = [
  { label: 'HOME',               to: '/' },
  { label: 'EXECUTIVE',          to: '/executive' },
  { label: 'GIS DISTRIBUTION',   to: '/gis-distribution' },
  { label: 'DEALER PERFORMANCE', to: '/dealer-performance' },
  { label: 'FORECASTING',        to: '/forecasting' },
  { label: 'ANOMALY DETECTION',  to: '/anomaly-detection' },
  { label: 'SERVICE ANALYTICS',  to: '/service-analytics' },
  { label: 'COMPETITIVE INTEL',  to: '/competitive-intel' },
]

export default function TopNav({ onMenuToggle }: { onMenuToggle: () => void }) {
  return (
    <nav className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-stretch h-11">
        <button
          onClick={onMenuToggle}
          className="lg:hidden flex items-center px-3 text-gray-500 hover:text-gray-700 border-r border-gray-200 flex-shrink-0"
          aria-label="Toggle navigation"
        >
          <Menu size={18} />
        </button>
        <div className="flex items-stretch overflow-x-auto min-w-0 flex-1">
          {PAGES.map(({ label, to }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `inline-flex items-center px-4 text-[10.5px] font-bold tracking-wider whitespace-nowrap
                 border-b-2 transition-colors duration-100 select-none
                 ${isActive
                   ? 'text-hawkins-red border-hawkins-red'
                   : 'text-gray-400 border-transparent hover:text-gray-600'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
