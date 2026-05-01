import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts'
import { useMemo } from 'react'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

const SEV_COLORS: Record<string, string> = {
  Critical: '#EF4444', Routine: '#F59E0B', Cosmetic: '#10B981',
}
const RCOLORS = ['#C8102E','#3B82F6','#10B981','#F59E0B','#8B5CF6','#06B6D4','#EF4444','#F97316']

export default function ServiceAnalytics() {
  const { data: kpis }      = useQuery({ queryKey: ['svc-kpis'],     queryFn: () => api.get('/service/kpis').then(r => r.data) })
  const { data: trend }     = useQuery({ queryKey: ['svc-trend'],    queryFn: () => api.get('/service/monthly-trend').then(r => r.data) })
  const { data: issues }    = useQuery({ queryKey: ['svc-issues'],   queryFn: () => api.get('/service/issue-breakdown').then(r => r.data) })
  const { data: heatmap }   = useQuery({ queryKey: ['svc-heatmap'],  queryFn: () => api.get('/service/sku-heatmap').then(r => r.data) })
  const { data: resolution} = useQuery({ queryKey: ['svc-res'],      queryFn: () => api.get('/service/resolution-times').then(r => r.data) })
  const { data: quality }   = useQuery({ queryKey: ['svc-quality'],  queryFn: () => api.get('/service/quality-risk').then(r => r.data) })
  const { data: stateLoad } = useQuery({ queryKey: ['svc-state'],    queryFn: () => api.get('/service/state-load').then(r => r.data) })

  // Pivot monthly trend: [{month, Critical, Routine, Cosmetic}]
  const trendPivot = useMemo(() => {
    if (!trend) return []
    const map: Record<string, any> = {}
    for (const r of trend as any[]) {
      if (!map[r.month]) map[r.month] = { month: r.month }
      map[r.month][r.severity] = r.count
    }
    return Object.values(map).sort((a, b) => a.month.localeCompare(b.month))
  }, [trend])

  // Category resolution: avg by category
  const catResolution = useMemo(() => {
    if (!resolution) return []
    const map: Record<string, { total: number; count: number }> = {}
    for (const r of resolution as any[]) {
      if (!map[r.category]) map[r.category] = { total: 0, count: 0 }
      map[r.category].total += r.avg_days
      map[r.category].count += 1
    }
    return Object.entries(map).map(([cat, v]) => ({ category: cat, avg_days: +(v.total / v.count).toFixed(1) }))
  }, [resolution])

  // Heatmap: skus × issue_types
  const { skus: hSkus, issueTypes, matrix: hMatrix } = useMemo(() => {
    if (!heatmap) return { skus: [], issueTypes: [], matrix: {} }
    const skus      = [...new Set((heatmap as any[]).map((r: any) => r.product_name))]
    const issueTypes = [...new Set((heatmap as any[]).map((r: any) => r.issue_type))]
    const matrix: Record<string, Record<string, number>> = {}
    for (const row of heatmap as any[]) {
      if (!matrix[row.product_name]) matrix[row.product_name] = {}
      matrix[row.product_name][row.issue_type] = row.count
    }
    return { skus, issueTypes, matrix }
  }, [heatmap])

  const maxCell = useMemo(() => {
    let m = 0
    Object.values(hMatrix).forEach(row => Object.values(row).forEach(v => { if (v > m) m = v }))
    return m || 1
  }, [hMatrix])

  // Category avg claim rate for threshold line
  const catAvgRate = useMemo(() => {
    if (!quality) return 0
    const rates = (quality as any[]).map((q: any) => q.claim_rate_per_1k ?? 0)
    return rates.length ? rates.reduce((a, b) => a + b, 0) / rates.length : 0
  }, [quality])

  if (!kpis) return <Spinner />

  return (
    <div>
      <PageHeader title="Service Analytics" subtitle="Warranty claims, resolution times, and quality risk SKUs — 45K claims across 140 service centres" />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <KPICard label="Total Service Requests" value={kpis.total_requests?.toLocaleString() ?? '—'} />
        <KPICard label="Critical Cases"          value={kpis.critical?.toLocaleString() ?? '—'}
          sub={kpis.total_requests ? `${((kpis.critical / kpis.total_requests) * 100).toFixed(1)}% of total` : undefined} />
        <KPICard label="Avg Resolution Time"     value={`${kpis.avg_resolution_days ?? '—'} days`} />
        <KPICard label="Out-of-Warranty Cost"    value={`₹${kpis.warranty_cost_cr ?? '—'} Cr`} />
      </div>

      {/* Row 1: Trend + Issue breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard title="Monthly Service Requests by Severity" className="lg:col-span-2">
          {trendPivot.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={trendPivot} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 9 }} tickFormatter={v => v.slice(2)} interval={1} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {['Critical','Routine','Cosmetic'].map(sev => (
                  <Area key={sev} type="monotone" dataKey={sev}
                    stroke={SEV_COLORS[sev]} fill={SEV_COLORS[sev]}
                    fillOpacity={0.15} stackId="a" dot={false} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Issue Type Distribution">
          {issues ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={issues as any[]} dataKey="count" nameKey="issue_type"
                  cx="50%" cy="50%" outerRadius={80} innerRadius={40}
                  label={({ issue_type, percent }) => `${(percent*100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {(issues as any[]).map((_: any, i: number) => (
                    <Cell key={i} fill={RCOLORS[i % RCOLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number, name: string) => [v.toLocaleString(), name]} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>
      </div>

      {/* Row 2: SKU Heatmap */}
      <ChartCard title="SKU × Issue Type Heatmap (claim count)" className="mb-4">
        {heatmap ? (
          <div className="overflow-auto">
            <table className="text-[9px] border-collapse">
              <thead>
                <tr>
                  <th className="pr-3 py-1 text-left text-gray-500 sticky left-0 bg-white font-semibold min-w-[160px]">SKU</th>
                  {issueTypes.map(it => (
                    <th key={it} className="px-1 py-1 text-gray-400 font-normal whitespace-nowrap min-w-[70px] text-center">{it}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {hSkus.map(sku => (
                  <tr key={sku}>
                    <td className="pr-3 py-0.5 text-gray-700 sticky left-0 bg-white font-medium whitespace-nowrap">{sku}</td>
                    {issueTypes.map(it => {
                      const val = hMatrix[sku]?.[it] ?? 0
                      const pct = val / maxCell
                      return (
                        <td key={it} className="px-1 py-0.5 text-center"
                          title={`${sku} · ${it}: ${val}`}
                          style={{
                            background: val === 0 ? '#F9FAFB' : `rgba(200,16,46,${0.1 + pct * 0.85})`,
                            color: pct > 0.55 ? '#fff' : '#374151',
                          }}
                        >
                          {val || ''}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <Spinner />}
      </ChartCard>

      {/* Row 3: Resolution times + Quality risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <ChartCard title="Avg Resolution Days by Category">
          {catResolution.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={catResolution} margin={{ top:4, right:12, bottom:0, left:0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="category" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v: number) => [`${v} days`, 'Avg Days']} />
                <Bar dataKey="avg_days" fill="#C8102E" radius={[4,4,0,0]}>
                  {catResolution.map((_, i) => (
                    <Cell key={i} fill={RCOLORS[i % RCOLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Top Quality-Risk SKUs (claims per 1K units sold)">
          {quality ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={(quality as any[]).slice(0,10)}
                layout="vertical"
                margin={{ top:4, right:40, bottom:0, left:130 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="product_name" tick={{ fontSize: 9 }} width={130} />
                <Tooltip formatter={(v: number) => [`${v} per 1K units`, 'Claim Rate']} />
                <ReferenceLine x={catAvgRate * 2} stroke="#EF4444" strokeDasharray="4 4"
                  label={{ value: '2× avg', fill: '#EF4444', fontSize: 9, position: 'right' }} />
                <Bar dataKey="claim_rate_per_1k" fill="#C8102E" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>
      </div>

      {/* Row 4: State load */}
      <ChartCard title="Service Request Volume by State (top 20)">
        {stateLoad ? (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stateLoad as any[]} margin={{ top:4, right:12, bottom:40, left:0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="state_name" tick={{ fontSize: 9 }} angle={-35} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="total_requests"  name="Total Requests" fill="#C8102E" stackId="a" />
              <Bar dataKey="critical_count"  name="Critical"       fill="#7F0018" stackId="b" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : <Spinner />}
      </ChartCard>
    </div>
  )
}
