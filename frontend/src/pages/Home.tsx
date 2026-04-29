import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

interface KPIs {
  transactions: number
  units_sold: number
  revenue_cr: number
  active_dealers: number
  skus_sold: number
}

const MODULES = [
  { name: 'Executive Overview',   q: 'How is the business doing this month?' },
  { name: 'GIS Distribution',     q: 'Where are we strong — where are the white-space gaps?' },
  { name: 'Dealer Performance',   q: 'Who is over/under-performing relative to potential?' },
  { name: 'Demand Forecasting',   q: 'What should we produce next quarter?' },
  { name: 'Anomaly Detection',    q: 'What dealer or SKU needs investigation right now?' },
  { name: 'Service Analytics',    q: 'Which products drive the most warranty claims?' },
  { name: 'Competitive Intel',    q: 'How do we price vs Prestige, Butterfly, and Pigeon?' },
]

export default function Home() {
  const { data, isLoading } = useQuery<KPIs>({
    queryKey: ['kpis'],
    queryFn: () => api.get('/kpis').then(r => r.data),
  })

  return (
    <div className="max-w-5xl">
      {/* Title */}
      <div className="flex items-center gap-4 mb-6">
        <img src="/logo.png" alt="Hawkins" className="h-14 w-14 object-contain" />
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">
            Hawkins Distribution Intelligence Platform
          </h1>
          <p className="text-sm text-gray-500 mt-0.5 max-w-2xl">
            A unified analytics platform giving Hawkins management a single pane of glass over{' '}
            <strong>dealer performance, regional demand, inventory, service quality, and competitive
            positioning</strong> — replacing scattered Excel reports with an automated, ML-augmented system.
          </p>
        </div>
      </div>

      <div className="border-t border-gray-200 mb-6" />

      {/* KPIs */}
      <h2 className="text-base font-bold text-gray-800 mb-3">Top-line Snapshot — FY2024 to FY2026</h2>
      {isLoading || !data ? (
        <Spinner />
      ) : (
        <div className="grid grid-cols-5 gap-4 mb-8">
          <KPICard label="Total Revenue"  value={`₹${data.revenue_cr} Cr`}        help="Gross sales across 3 years" />
          <KPICard label="Units Sold"     value={`${(data.units_sold / 1e6).toFixed(2)}M`} />
          <KPICard label="Transactions"   value={`${(data.transactions / 1e6).toFixed(2)}M`} />
          <KPICard label="Active Dealers" value={data.active_dealers.toLocaleString()} />
          <KPICard label="SKUs Sold"      value={String(data.skus_sold)} />
        </div>
      )}

      <div className="border-t border-gray-200 mb-6" />

      {/* Two-col: modules + architecture */}
      <div className="grid grid-cols-3 gap-8">
        <div className="col-span-2">
          <h2 className="text-base font-bold text-gray-800 mb-2">What this platform does</h2>
          <p className="text-sm text-gray-600 mb-3">
            Hawkins operates a complex <strong>9,379-dealer pan-India network</strong> across three
            manufacturing plants (Thane, Hoshiarpur, Sathariya). This platform consolidates sales,
            inventory, service, and competitive data into seven actionable modules:
          </p>
          <div className="overflow-hidden rounded-xl border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Module</th>
                  <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Question it answers</th>
                </tr>
              </thead>
              <tbody>
                {MODULES.map(({ name, q }, i) => (
                  <tr key={name} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-2 font-semibold text-gray-800">{name}</td>
                    <td className="px-4 py-2 text-gray-600">{q}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h2 className="text-base font-bold text-gray-800 mb-2">Architecture</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <div>
              <p className="font-semibold text-gray-800">Data layer</p>
              <p>SQLite (192 MB · production-mappable to PostgreSQL or SQL Server)</p>
            </div>
            <div>
              <p className="font-semibold text-gray-800">ETL pipeline</p>
              <p>Python · Pandas · scheduled via cron in production</p>
            </div>
            <div>
              <p className="font-semibold text-gray-800">ML layer</p>
              <p>SARIMA forecasts per SKU · Isolation Forest anomaly detection RFM + K-Means dealer segmentation</p>
            </div>
            <div>
              <p className="font-semibold text-gray-800">BI layer</p>
              <p>React + TypeScript · FastAPI · Tailwind CSS · Recharts</p>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 mt-8 pt-3">
        <p className="text-xs text-gray-400">
          Built by Alok Deep 
        </p>
      </div>
    </div>
  )
}
