import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useFilters } from '../context/FiltersContext'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

function SeverityBadge({ sev }: { sev: string }) {
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold text-white
      ${sev === 'Critical' ? 'bg-red-500' : 'bg-amber-400'}`}>
      {sev}
    </span>
  )
}

function MethodBadge({ method }: { method: string }) {
  const cls = method === 'Rule-based'        ? 'bg-blue-100 text-blue-700'
            : method === 'Z-Score'            ? 'bg-purple-100 text-purple-700'
            : 'bg-orange-100 text-orange-700'
  return (
    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${cls}`}>{method}</span>
  )
}

export default function AnomalyDetection() {
  const { anSevFilter: sevFilter, anMethodFilter: methodFilter } = useFilters()

  const { data: dormancy,   isLoading: loadDorm  } = useQuery({ queryKey: ['anomaly-dormancy'],   queryFn: () => api.get('/anomalies/dormancy').then(r => r.data) })
  const { data: priceErrors, isLoading: loadPrice } = useQuery({ queryKey: ['anomaly-price'],      queryFn: () => api.get('/anomalies/price-errors').then(r => r.data) })
  const { data: zscore,     isLoading: loadZ     } = useQuery({ queryKey: ['anomaly-zscore'],     queryFn: () => api.get('/anomalies/zscore').then(r => r.data) })
  const { data: isoForest,  isLoading: loadIso   } = useQuery({ queryKey: ['anomaly-iso'],        queryFn: () => api.get('/anomalies/isolation-forest').then(r => r.data) })

  const allAlerts = useMemo(() => {
    const alerts: any[] = []
    if (dormancy) (dormancy as any[]).forEach(d => alerts.push({
      entity:       d.dealer_name,
      tier:         d.tier,
      region:       d.region,
      anomaly_type: 'Dormant Dealer',
      observed:     `${d.days_inactive}d since last sale`,
      expected:     '< 30 days',
      severity:     d.severity,
      method:       'Rule-based',
    }))
    if (zscore) (zscore as any[]).forEach(d => alerts.push({
      entity:       d.dealer_id ?? '—',
      tier:         '—',
      region:       d.region ?? '—',
      anomaly_type: d.anomaly_type ?? 'Revenue Spike/Drop',
      observed:     d.revenue != null ? `₹${Math.round(d.revenue).toLocaleString()}` : '—',
      expected:     d.mean_rev != null ? `~₹${Math.round(d.mean_rev).toLocaleString()}` : '—',
      severity:     d.severity ?? 'Warning',
      method:       'Z-Score',
    }))
    if (isoForest) (isoForest as any[]).forEach(d => alerts.push({
      entity:       d.dealer_id ?? '—',
      tier:         '—',
      region:       '—',
      anomaly_type: 'Multivariate Outlier',
      observed:     `Score ${d.anomaly_score?.toFixed(3) ?? '—'}`,
      expected:     '> 0 (normal range)',
      severity:     d.severity ?? 'Warning',
      method:       'Isolation Forest',
    }))
    return alerts
  }, [dormancy, zscore, isoForest])

  const filtered = useMemo(() => allAlerts.filter(a => {
    if (sevFilter    !== 'All' && a.severity !== sevFilter)    return false
    if (methodFilter !== 'All' && a.method   !== methodFilter) return false
    return true
  }), [allAlerts, sevFilter, methodFilter])

  const isLoading = loadDorm || loadZ || loadIso

  const criticalCount  = allAlerts.filter(a => a.severity === 'Critical').length
  const warningCount   = allAlerts.filter(a => a.severity === 'Warning').length
  const zscoreCount    = allAlerts.filter(a => a.method === 'Z-Score').length
  const isoCount       = allAlerts.filter(a => a.method === 'Isolation Forest').length
  const ruleCount      = allAlerts.filter(a => a.method === 'Rule-based').length

  const modelsReady    = zscoreCount > 0 || isoCount > 0

  return (
    <div>
      <PageHeader
        title="Anomaly Detection"
        subtitle="Rule-based dormancy · Z-score statistical alerts · Isolation Forest ML detection"
      />

      {/* Model status banner if ML models not yet trained */}
      {!modelsReady && !isLoading && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-xl p-3 text-sm text-amber-800 flex items-start gap-2">
          <span className="text-lg leading-none">⚠️</span>
          <div>
            <p className="font-semibold">Z-Score & Isolation Forest models not found.</p>
            <p className="text-xs mt-0.5">
              Run <code className="font-mono bg-amber-100 px-1 rounded">python src/ml/anomaly_detection.py</code> to generate ML alerts.
              Currently showing rule-based dormancy alerts only.
            </p>
          </div>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-5">
        <KPICard label="Total Alerts"      value={String(allAlerts.length)} />
        <KPICard label="Critical"          value={String(criticalCount)} sub="Needs immediate action" />
        <KPICard label="Warnings"          value={String(warningCount)}  sub="Monitor closely" />
        <KPICard label="By Method"
          value={`${ruleCount} · ${zscoreCount} · ${isoCount}`}
          sub="Rule-based · Z-Score · Isolation Forest" />
      </div>

      {/* ── Alert Inbox ── */}
      <ChartCard title="Alert Inbox" className="mb-5">
        <div className="mb-2">
          <span className="text-xs text-gray-400">
            {filtered.length} of {allAlerts.length} alerts
            {(sevFilter !== 'All' || methodFilter !== 'All') && (
              <span className="ml-1 text-gray-300">
                (filtered by {[sevFilter !== 'All' && sevFilter, methodFilter !== 'All' && methodFilter].filter(Boolean).join(' · ')})
              </span>
            )}
          </span>
        </div>

        {isLoading ? <Spinner /> : (
          <div className="overflow-auto max-h-[480px]">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white z-10 shadow-sm">
                <tr className="border-b border-gray-100">
                  {['Dealer / Entity','Tier','Region','Anomaly Type','Observed','Expected','Severity','Method'].map(h => (
                    <th key={h} className="py-2 px-2 text-left text-gray-500 font-semibold whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((a, i) => (
                  <tr key={i}
                    className={`border-b border-gray-50 ${a.severity === 'Critical' ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'}`}>
                    <td className="py-1.5 px-2 font-medium text-gray-800 max-w-[160px] truncate">{a.entity}</td>
                    <td className="py-1.5 px-2 text-gray-500">{a.tier}</td>
                    <td className="py-1.5 px-2 text-gray-500">{a.region}</td>
                    <td className="py-1.5 px-2 text-gray-700">{a.anomaly_type}</td>
                    <td className="py-1.5 px-2 text-gray-600">{a.observed}</td>
                    <td className="py-1.5 px-2 text-gray-400 italic">{a.expected}</td>
                    <td className="py-1.5 px-2"><SeverityBadge sev={a.severity} /></td>
                    <td className="py-1.5 px-2"><MethodBadge method={a.method} /></td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-10 text-center text-sm text-gray-400">
                      No alerts match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>

      {/* ── Price Entry Anomalies ── */}
      <ChartCard title="Price Entry Anomalies  (actual vs list price > ±20%)">
        {loadPrice ? <Spinner /> : (priceErrors as any[]).length === 0 ? (
          <div className="flex items-center gap-3 py-8 px-4 bg-green-50 rounded-lg">
            <span className="text-2xl">✅</span>
            <div>
              <p className="text-sm font-semibold text-green-700">No price anomalies detected</p>
              <p className="text-xs text-green-600 mt-0.5">
                All {(1053833).toLocaleString()} transactions are within ±20% of the catalogue list price.
                Data quality is good.
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-auto max-h-[400px]">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white z-10">
                <tr className="border-b border-gray-100">
                  {['Dealer','Tier','SKU','List Price','Actual Price','Deviation %','Date'].map(h => (
                    <th key={h} className="py-2 px-2 text-left text-gray-500 font-semibold whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(priceErrors as any[]).map((e: any, i: number) => (
                  <tr key={i} className={`border-b border-gray-50 ${Math.abs(e.pct_diff) > 40 ? 'bg-red-50' : 'hover:bg-gray-50'}`}>
                    <td className="py-1.5 px-2 font-medium text-gray-800 max-w-[140px] truncate">{e.dealer_name}</td>
                    <td className="py-1.5 px-2"><span className="px-1 py-0.5 rounded text-[9px] font-bold bg-gray-100 text-gray-600">{e.tier}</span></td>
                    <td className="py-1.5 px-2 text-gray-700 max-w-[140px] truncate">{e.product_name}</td>
                    <td className="py-1.5 px-2 text-gray-600">₹{e.list_price?.toLocaleString()}</td>
                    <td className="py-1.5 px-2 text-gray-600">₹{e.actual_price?.toLocaleString()}</td>
                    <td className={`py-1.5 px-2 font-bold ${e.pct_diff > 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {e.pct_diff > 0 ? '+' : ''}{e.pct_diff}%
                    </td>
                    <td className="py-1.5 px-2 text-gray-400">{e.transaction_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>
    </div>
  )
}
