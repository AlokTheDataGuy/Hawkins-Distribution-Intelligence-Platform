import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts'
import api from '../api/client'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import PageHeader from '../components/PageHeader'
import Spinner from '../components/Spinner'

const RED    = '#C8102E'
const REGION_COLORS: Record<string, string> = {
  North: '#3B82F6', South: '#10B981', East: '#F59E0B',
  West: '#EF4444', Central: '#8B5CF6', Northeast: '#06B6D4',
}
const CAT_COLORS: Record<string, string> = {
  'Pressure Cooker': '#C8102E', Cookware: '#3B82F6',
  Electricals: '#10B981', Accessory: '#F59E0B',
}

export default function Executive() {
  const { data: kpis }    = useQuery({ queryKey: ['kpis'],    queryFn: () => api.get('/kpis').then(r => r.data) })
  const { data: monthly } = useQuery({ queryKey: ['monthly'], queryFn: () => api.get('/executive/monthly-revenue').then(r => r.data) })
  const { data: regions } = useQuery({ queryKey: ['regions'], queryFn: () => api.get('/executive/region-breakdown').then(r => r.data) })
  const { data: products }= useQuery({ queryKey: ['top-products'], queryFn: () => api.get('/executive/top-products').then(r => r.data) })
  const { data: states }  = useQuery({ queryKey: ['state-summary'], queryFn: () => api.get('/executive/state-summary').then(r => r.data) })

  if (!kpis) return <Spinner />

  return (
    <div>
      <PageHeader title="Executive Overview" subtitle="Top-line KPIs and business trends — FY2024 to FY2026" />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPICard label="Total Revenue (3Y)"  value={`₹${kpis.revenue_cr} Cr`} />
        <KPICard label="Units Sold"          value={`${(kpis.units_sold / 1e6).toFixed(2)}M`} />
        <KPICard label="Active Dealers"      value={kpis.active_dealers.toLocaleString()} />
        <KPICard label="SKUs Sold"           value={String(kpis.skus_sold)} />
      </div>

      {/* Row 1: Revenue trend + Region breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard title="Monthly Revenue Trend (₹ Cr)" className="lg:col-span-2">
          {monthly ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={monthly} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={RED} stopOpacity={0.25} />
                    <stop offset="95%" stopColor={RED} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} tickLine={false}
                       tickFormatter={v => v.slice(2)} interval={2} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                       tickFormatter={v => `₹${v}`} />
                <Tooltip formatter={(v: number) => [`₹${v} Cr`, 'Revenue']} />
                <Area type="monotone" dataKey="revenue_cr" stroke={RED} strokeWidth={2}
                      fill="url(#revGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Revenue by Region (₹ Cr)">
          {regions ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={regions} layout="vertical" margin={{ top: 4, right: 20, bottom: 0, left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="region" tick={{ fontSize: 10 }} tickLine={false} width={60} />
                <Tooltip formatter={(v: number) => [`₹${v} Cr`, 'Revenue']} />
                <Bar dataKey="revenue_cr" radius={[0, 4, 4, 0]}>
                  {(regions as any[]).map((entry: any) => (
                    <Cell key={entry.region} fill={REGION_COLORS[entry.region] ?? RED} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>
      </div>

      {/* Row 2: Top SKUs + State table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <ChartCard title="Top 10 SKUs by Revenue (₹ Cr)" className="lg:col-span-2">
          {products ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={products} layout="vertical" margin={{ top: 4, right: 20, bottom: 0, left: 160 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="product_name" tick={{ fontSize: 10 }} tickLine={false} width={160} />
                <Tooltip formatter={(v: number) => [`₹${v} Cr`, 'Revenue']} />
                <Bar dataKey="revenue_cr" radius={[0, 4, 4, 0]}>
                  {(products as any[]).map((entry: any) => (
                    <Cell key={entry.product_id} fill={CAT_COLORS[entry.category] ?? '#6B7280'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Top 10 States by Revenue">
          {states ? (
            <div className="overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="py-1 text-left text-gray-500 font-semibold">State</th>
                    <th className="py-1 text-right text-gray-500 font-semibold">Rev (Cr)</th>
                    <th className="py-1 text-right text-gray-500 font-semibold">Dealers</th>
                  </tr>
                </thead>
                <tbody>
                  {(states as any[]).map((s: any) => (
                    <tr key={s.state_name} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-1 text-gray-800">{s.state_name}</td>
                      <td className="py-1 text-right font-semibold text-gray-900">₹{s.revenue_cr}</td>
                      <td className="py-1 text-right text-gray-500">{s.active_dealers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Spinner />}
        </ChartCard>
      </div>
    </div>
  )
}
