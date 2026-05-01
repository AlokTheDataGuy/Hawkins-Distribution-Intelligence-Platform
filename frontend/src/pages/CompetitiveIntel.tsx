import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, ReferenceLine, Cell,
} from 'recharts'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

const COMP_COLORS: Record<string, string> = {
  'TTK Prestige': '#3B82F6',
  'Butterfly':    '#10B981',
  'Pigeon':       '#F59E0B',
  'Stove Kraft':  '#8B5CF6',
}

function PostureBadge({ posture }: { posture: string }) {
  const cfg = posture === 'Value Leader'
    ? 'bg-green-100 text-green-700'
    : posture === 'Parity'
    ? 'bg-yellow-100 text-yellow-700'
    : 'bg-red-100 text-red-700'
  return <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${cfg}`}>{posture}</span>
}

export default function CompetitiveIntel() {
  const [selCompetitors, setSelCompetitors] = useState<string[]>([])

  const { data: kpis }      = useQuery({ queryKey: ['comp-kpis'],     queryFn: () => api.get('/competitive/kpis').then(r => r.data) })
  const { data: trend }     = useQuery({ queryKey: ['comp-trend'],    queryFn: () => api.get('/competitive/gap-trend').then(r => r.data) })
  const { data: posture }   = useQuery({ queryKey: ['comp-posture'],  queryFn: () => api.get('/competitive/posture-summary').then(r => r.data) })
  const { data: heatmap }   = useQuery({ queryKey: ['comp-heatmap'],  queryFn: () => api.get('/competitive/sku-heatmap').then(r => r.data) })
  const { data: vulnerable }= useQuery({ queryKey: ['comp-vuln'],     queryFn: () => api.get('/competitive/vulnerable-skus').then(r => r.data) })

  // Pivot trend data → [{month, 'TTK Prestige': gap, ...}]
  const trendPivot = useMemo(() => {
    if (!trend) return []
    const map: Record<string, any> = {}
    for (const r of trend as any[]) {
      if (!map[r.month]) map[r.month] = { month: r.month }
      map[r.month][r.competitor] = r.avg_gap_pct
    }
    return Object.values(map).sort((a, b) => a.month.localeCompare(b.month))
  }, [trend])

  const competitors = useMemo(() => {
    if (!posture) return []
    return (posture as any[]).map((p: any) => p.competitor)
  }, [posture])

  // Heatmap: skus × competitors
  const { hSkus, hComps, hMatrix } = useMemo(() => {
    if (!heatmap) return { hSkus: [], hComps: [], hMatrix: {} }
    const hSkus  = [...new Set((heatmap as any[]).map((r: any) => r.product_name))]
    const hComps = [...new Set((heatmap as any[]).map((r: any) => r.competitor))]
    const hMatrix: Record<string, Record<string, number>> = {}
    for (const row of heatmap as any[]) {
      if (!hMatrix[row.product_name]) hMatrix[row.product_name] = {}
      hMatrix[row.product_name][row.competitor] = row.avg_gap_pct
    }
    return { hSkus, hComps, hMatrix }
  }, [heatmap])

  const filteredTrend = useMemo(() => {
    if (!selCompetitors.length) return trendPivot
    return trendPivot  // show all — filter is for posture bar
  }, [trendPivot, selCompetitors])

  if (!kpis) return <Spinner />

  const postureCfg = kpis.avg_gap_pct > 0
    ? { label: 'Value Leader', cls: 'text-green-600', desc: 'Hawkins priced below competitors on avg' }
    : { label: 'Premium', cls: 'text-red-500', desc: 'Hawkins priced above competitors on avg' }

  return (
    <div>
      <PageHeader title="Competitive Intel" subtitle="Pricing posture vs TTK Prestige, Butterfly, Pigeon & Stove Kraft — 5.7K price snapshots" />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <KPICard label="Competitors Tracked" value={String(kpis.competitors_tracked ?? 4)} />
        <KPICard label="SKUs Tracked"        value={String(kpis.skus_tracked ?? '—')} />
        <KPICard label="Pricing Posture"
          value={postureCfg.label}
          sub={postureCfg.desc}
        />
        <KPICard label="Avg Price Gap"
          value={`${kpis.avg_gap_pct > 0 ? '+' : ''}${kpis.avg_gap_pct ?? 0}%`}
          sub="Positive = Hawkins cheaper" />
      </div>

      {/* Row 1: Trend + Posture bar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <ChartCard title="Price Gap Trend — Hawkins vs Competitors (% gap)" className="lg:col-span-2">
          {filteredTrend.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={filteredTrend} margin={{ top:8, right:20, bottom:0, left:0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 9 }} tickFormatter={v => v.slice(2)} interval={1} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
                <Tooltip formatter={(v: number, name: string) => [`${v}%`, name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="4 4" label={{ value: 'Parity', fill: '#9CA3AF', fontSize: 9 }} />
                {competitors.map((comp: string) => (
                  <Line key={comp} type="monotone" dataKey={comp}
                    stroke={COMP_COLORS[comp] ?? '#999'}
                    strokeWidth={2} dot={false} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Avg Pricing Posture by Competitor">
          {posture ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={posture as any[]} margin={{ top:4, right:20, bottom:0, left:0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="competitor" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v: number) => [`${v}%`, 'Avg Gap']} />
                  <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
                  <Bar dataKey="avg_gap_pct" radius={[4,4,0,0]}>
                    {(posture as any[]).map((p: any) => (
                      <Cell key={p.competitor}
                        fill={p.posture === 'Value Leader' ? '#10B981' : p.posture === 'Parity' ? '#F59E0B' : '#EF4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-2 space-y-1">
                {(posture as any[]).map((p: any) => (
                  <div key={p.competitor} className="flex items-center justify-between text-xs">
                    <span className="text-gray-700 font-medium">{p.competitor}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">{p.pct_hawkins_cheaper}% SKUs cheaper</span>
                      <PostureBadge posture={p.posture} />
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : <Spinner />}
        </ChartCard>
      </div>

      {/* Row 2: Heatmap */}
      <ChartCard title="SKU × Competitor Price Gap % (positive = Hawkins cheaper)" className="mb-4">
        {heatmap ? (
          <div className="overflow-auto">
            <table className="text-[9px] border-collapse">
              <thead>
                <tr>
                  <th className="pr-3 py-1 text-left text-gray-500 sticky left-0 bg-white font-semibold min-w-[160px]">SKU</th>
                  {hComps.map(comp => (
                    <th key={comp} className="px-2 py-1 text-gray-400 font-normal whitespace-nowrap min-w-[80px] text-center">{comp}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {hSkus.map(sku => (
                  <tr key={sku}>
                    <td className="pr-3 py-0.5 text-gray-700 sticky left-0 bg-white font-medium whitespace-nowrap">{sku}</td>
                    {hComps.map(comp => {
                      const val = hMatrix[sku]?.[comp] ?? null
                      if (val == null) return <td key={comp} className="px-2 py-0.5 text-center text-gray-200">—</td>
                      // positive gap = Hawkins cheaper → green; negative = costlier → red
                      const intensity = Math.min(Math.abs(val) / 25, 1)
                      const bg = val > 0
                        ? `rgba(16,185,129,${0.1 + intensity * 0.7})`
                        : `rgba(239,68,68,${0.1 + intensity * 0.7})`
                      const fg = intensity > 0.5 ? '#fff' : '#374151'
                      return (
                        <td key={comp} className="px-2 py-0.5 text-center font-semibold"
                          title={`${sku} vs ${comp}: ${val}%`}
                          style={{ background: bg, color: fg }}>
                          {val > 0 ? '+' : ''}{val}%
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

      {/* Row 3: Vulnerable SKUs + Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Vulnerable SKUs (gap narrowing >2pp in last 90 days)">
          {vulnerable ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  {['SKU','Competitor','Prior Gap','Recent Gap','Change'].map(h => (
                    <th key={h} className="py-1.5 px-2 text-left text-gray-500 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(vulnerable as any[]).map((v: any, i: number) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 px-2 font-medium text-gray-800 max-w-[120px] truncate">{v.product_name}</td>
                    <td className="py-1.5 px-2 text-gray-600">{v.competitor}</td>
                    <td className="py-1.5 px-2 text-green-600 font-semibold">+{v.older_gap}%</td>
                    <td className="py-1.5 px-2 text-amber-600 font-semibold">{v.recent_gap > 0 ? '+' : ''}{v.recent_gap}%</td>
                    <td className="py-1.5 px-2 font-bold text-red-500">{v.gap_change}pp</td>
                  </tr>
                ))}
                {!(vulnerable as any[]).length && (
                  <tr><td colSpan={5} className="py-4 text-center text-gray-400 text-sm">No vulnerable SKUs detected</td></tr>
                )}
              </tbody>
            </table>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Pricing Recommendations">
          {posture ? (
            <div className="space-y-2">
              {(posture as any[]).map((p: any) => {
                const gap = p.avg_gap_pct ?? 0
                let rec = '', priority = '', cls = ''
                if (gap < -10) {
                  rec = `Hawkins is ${Math.abs(gap).toFixed(1)}% costlier than ${p.competitor} → review entry-tier SKU pricing`
                  priority = 'High'; cls = 'border-red-200 bg-red-50'
                } else if (gap > 10) {
                  rec = `Hawkins is ${gap.toFixed(1)}% cheaper than ${p.competitor} → consider selective price increases`
                  priority = 'Medium'; cls = 'border-yellow-200 bg-yellow-50'
                } else {
                  rec = `Near parity with ${p.competitor} → differentiate on quality and service`
                  priority = 'Low'; cls = 'border-green-200 bg-green-50'
                }
                const badgeCls = priority === 'High' ? 'bg-red-500' : priority === 'Medium' ? 'bg-amber-400' : 'bg-green-500'
                return (
                  <div key={p.competitor} className={`border rounded-lg p-3 ${cls}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-gray-700">{p.competitor}</span>
                      <span className={`text-[9px] font-bold text-white px-2 py-0.5 rounded-full ${badgeCls}`}>{priority}</span>
                    </div>
                    <p className="text-xs text-gray-600 leading-snug">{rec}</p>
                  </div>
                )
              })}
            </div>
          ) : <Spinner />}
        </ChartCard>
      </div>
    </div>
  )
}
