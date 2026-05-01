import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useFilters } from '../context/FiltersContext'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ScatterChart, Scatter, Cell,
} from 'recharts'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

const TIER_COLORS: Record<string, string> = { A: '#10B981', B: '#F59E0B', C: '#6B7280' }
const TABS = ['Scorecard', 'Decliners & Risers', 'Cohort Analysis']

export default function DealerPerformance() {
  const [tab, setTab] = useState(0)
  const { dpTiers: tiers, dpRegions: regions } = useFilters()

  const tiersParam   = tiers.join(',')
  const regionsParam = regions.join(',')

  const { data: scored, isLoading: loadingScored } = useQuery({
    queryKey: ['dealers-scored', tiersParam, regionsParam],
    queryFn: () => api.get('/dealers/scored', { params: { tiers: tiersParam, regions: regionsParam } }).then(r => r.data),
  })
  const { data: movers,  isLoading: loadingMovers }  = useQuery({ queryKey: ['dealers-movers'],  queryFn: () => api.get('/dealers/movers').then(r => r.data) })
  const { data: cohorts, isLoading: loadingCohorts } = useQuery({ queryKey: ['dealers-cohorts'], queryFn: () => api.get('/dealers/cohorts').then(r => r.data) })

  const decliners = useMemo(() => movers ? (movers as any[]).filter(d => d.growth_ratio < 0.70).sort((a, b) => a.growth_ratio - b.growth_ratio).slice(0, 30) : [], [movers])
  const risers    = useMemo(() => movers ? (movers as any[]).filter(d => d.growth_ratio > 1.40).sort((a, b) => b.growth_ratio - a.growth_ratio).slice(0, 30) : [], [movers])

  const scoreBuckets = useMemo(() => {
    if (!scored) return []
    const buckets = [0,10,20,30,40,50,60,70,80,90,100]
    return buckets.slice(0,-1).map((lo, i) => ({
      range: `${lo}–${buckets[i+1]}`,
      A: (scored as any[]).filter(d => d.tier === 'A' && d.score >= lo && d.score < buckets[i+1]).length,
      B: (scored as any[]).filter(d => d.tier === 'B' && d.score >= lo && d.score < buckets[i+1]).length,
      C: (scored as any[]).filter(d => d.tier === 'C' && d.score >= lo && d.score < buckets[i+1]).length,
    }))
  }, [scored])

  const bucketData = useMemo(() => {
    if (!movers) return []
    const labels = ['<-50%', '-30→-50%', '-10→-30%', '-10→+10%', '+10→+30%', '+30→+50%', '>+50%']
    const thresholds = [-Infinity, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, Infinity]
    return labels.map((label, i) => ({
      label,
      count: (movers as any[]).filter(d => {
        const g = d.growth_ratio - 1
        return g >= thresholds[i] && g < thresholds[i+1]
      }).length,
    }))
  }, [movers])

  const cohortChart = useMemo(() => {
    if (!cohorts) return []
    const years = [...new Set((cohorts as any[]).map(c => c.onboard_year))].sort()
    return years.map(year => {
      const row: any = { year: String(year) }
      for (const t of ['A','B','C']) {
        const found = (cohorts as any[]).find(c => c.onboard_year === year && c.tier === t)
        row[`rev_${t}`]   = found?.avg_revenue_lakh ?? 0
        row[`count_${t}`] = found?.dealer_count     ?? 0
      }
      return row
    })
  }, [cohorts])

  return (
    <div>
      <PageHeader title="Dealer Performance" subtitle="Performance scoring, growth movers, and cohort analysis" />

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5">
        {TABS.map((label, i) => (
          <button
            key={label}
            onClick={() => setTab(i)}
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
              tab === i ? 'text-hawkins-red border-hawkins-red' : 'text-gray-400 border-transparent hover:text-gray-600'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── Tab 0: Scorecard ── */}
      {tab === 0 && (
        <>
          {loadingScored ? <Spinner /> : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                {['A','B','C'].map(t => {
                  const group = (scored as any[]).filter(d => d.tier === t)
                  const avg   = group.length ? (group.reduce((s, d) => s + d.score, 0) / group.length).toFixed(1) : '—'
                  return (
                    <KPICard key={t}
                      label={`Tier ${t} — ${group.length} dealers`}
                      value={`Avg Score: ${avg}`}
                      sub={`Avg Rev: ₹${group.length ? (group.reduce((s,d)=>s+d.revenue_lakh,0)/group.length).toFixed(1):0} L`}
                    />
                  )
                })}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <ChartCard title="Score Distribution by Tier">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={scoreBuckets} margin={{ top:4, right:12, bottom:0, left:0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="range" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      {['A','B','C'].map(t => (
                        <Bar key={t} dataKey={t} name={`Tier ${t}`} fill={TIER_COLORS[t]} stackId="a" />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>
                <ChartCard title="Revenue vs Score (bubble = avg basket)">
                  <ResponsiveContainer width="100%" height={260}>
                    <ScatterChart margin={{ top:4, right:12, bottom:16, left:0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="score" name="Score" type="number" domain={[0,100]} tick={{ fontSize:10 }} label={{ value:'Score', position:'insideBottom', offset:-6, fontSize:10 }} />
                      <YAxis dataKey="revenue_lakh" name="Revenue (₹L)" tick={{ fontSize:10 }} />
                      <Tooltip content={({ payload }) => {
                        if (!payload?.length) return null
                        const d = payload[0]?.payload
                        return (
                          <div className="bg-white border border-gray-200 rounded p-2 text-xs shadow">
                            <p className="font-semibold">{d.dealer_name}</p>
                            <p>Score: {d.score} | Rev: ₹{d.revenue_lakh}L</p>
                          </div>
                        )
                      }} />
                      <Scatter data={scored as any[]} opacity={0.7}>
                        {(scored as any[]).map((d: any) => (
                          <Cell key={d.dealer_id} fill={TIER_COLORS[d.tier] ?? '#999'} />
                        ))}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>
              <ChartCard title="Top 20 Dealers by Score">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-100">
                      {['Dealer','Tier','Region','Score','Revenue (₹L)','Avg Basket (₹)'].map(h => (
                        <th key={h} className="py-1.5 px-2 text-left text-gray-500 font-semibold">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(scored as any[]).sort((a,b) => b.score - a.score).slice(0,20).map((d: any) => (
                      <tr key={d.dealer_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-1.5 px-2 font-medium text-gray-800">{d.dealer_name}</td>
                        <td className="py-1.5 px-2">
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: TIER_COLORS[d.tier] }}>
                            {d.tier}
                          </span>
                        </td>
                        <td className="py-1.5 px-2 text-gray-500">{d.region}</td>
                        <td className="py-1.5 px-2 font-bold text-hawkins-red">{d.score}</td>
                        <td className="py-1.5 px-2 text-gray-700">₹{d.revenue_lakh}</td>
                        <td className="py-1.5 px-2 text-gray-700">₹{d.avg_basket?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ChartCard>
            </>
          )}
        </>
      )}

      {/* ── Tab 1: Decliners & Risers ── */}
      {tab === 1 && (
        <>
          {loadingMovers ? <Spinner /> : (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <KPICard label="Decliners (>30% drop)" value={String(decliners.length)} />
                <KPICard label="Risers (>40% growth)"  value={String(risers.length)} />
              </div>
              <ChartCard title="Revenue Growth Distribution (last 90d vs prior 90d)" className="mb-4">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={bucketData} margin={{ top:4, right:12, bottom:0, left:0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="count" name="Dealers">
                      {bucketData.map((b, i) => (
                        <Cell key={b.label} fill={i < 2 ? '#EF4444' : i < 3 ? '#F59E0B' : i === 3 ? '#6B7280' : i < 5 ? '#10B981' : '#059669'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <ChartCard title="Top Decliners (revenue fell >30%)">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-gray-100">
                      {['Dealer','Tier','Prior 90d (₹L)','Last 90d (₹L)','Change'].map(h => (
                        <th key={h} className="py-1.5 px-2 text-left text-gray-500 font-semibold">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {decliners.map((d: any) => (
                        <tr key={d.dealer_id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-1.5 px-2 font-medium text-gray-800">{d.dealer_name}</td>
                          <td className="py-1.5 px-2"><span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: TIER_COLORS[d.tier] }}>{d.tier}</span></td>
                          <td className="py-1.5 px-2 text-gray-600">₹{d.rev_prior90}</td>
                          <td className="py-1.5 px-2 text-gray-600">₹{d.rev_last90}</td>
                          <td className="py-1.5 px-2 font-bold text-red-500">{((d.growth_ratio - 1)*100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </ChartCard>
                <ChartCard title="Top Risers (revenue up >40%)">
                  <table className="w-full text-xs">
                    <thead><tr className="border-b border-gray-100">
                      {['Dealer','Tier','Prior 90d (₹L)','Last 90d (₹L)','Change'].map(h => (
                        <th key={h} className="py-1.5 px-2 text-left text-gray-500 font-semibold">{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {risers.map((d: any) => (
                        <tr key={d.dealer_id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-1.5 px-2 font-medium text-gray-800">{d.dealer_name}</td>
                          <td className="py-1.5 px-2"><span className="px-1.5 py-0.5 rounded text-[9px] font-bold text-white" style={{ background: TIER_COLORS[d.tier] }}>{d.tier}</span></td>
                          <td className="py-1.5 px-2 text-gray-600">₹{d.rev_prior90}</td>
                          <td className="py-1.5 px-2 text-gray-600">₹{d.rev_last90}</td>
                          <td className="py-1.5 px-2 font-bold text-green-600">+{((d.growth_ratio - 1)*100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </ChartCard>
              </div>
            </>
          )}
        </>
      )}

      {/* ── Tab 2: Cohort Analysis ── */}
      {tab === 2 && (
        <>
          {loadingCohorts ? <Spinner /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Avg Revenue per Dealer by Onboard Year (₹ Lakh)">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={cohortChart} margin={{ top:4, right:12, bottom:0, left:0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    {['A','B','C'].map(t => (
                      <Bar key={t} dataKey={`rev_${t}`} name={`Tier ${t}`} fill={TIER_COLORS[t]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
                <p className="text-xs text-gray-400 mt-2">Newer cohorts often show lower revenue due to ramp-up time.</p>
              </ChartCard>
              <ChartCard title="Dealer Count by Onboard Year">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={cohortChart} margin={{ top:4, right:12, bottom:0, left:0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    {['A','B','C'].map(t => (
                      <Bar key={t} dataKey={`count_${t}`} name={`Tier ${t}`} fill={TIER_COLORS[t]} stackId="a" />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          )}
        </>
      )}
    </div>
  )
}
