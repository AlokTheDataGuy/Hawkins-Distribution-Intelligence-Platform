import { NavLink } from 'react-router-dom'

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

export default function TopNav() {
  return (
    <nav className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm overflow-x-auto">
      <div className="flex items-stretch h-11 min-w-max">
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
    </nav>
  )
}
