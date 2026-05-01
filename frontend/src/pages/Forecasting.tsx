import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useFilters } from '../context/FiltersContext'
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import KPICard from '../components/KPICard'
import Spinner from '../components/Spinner'

interface SKU { product_id: string; product_name: string }
interface ForecastData {
  product_id: string; product_name: string
  mape: number | null; recent_avg_lakh: number | null; trend_pct: number | null
  historical: { month: string; revenue_lakh: number }[]
  forecast:   { month: string; forecast: number; ci_low: number; ci_high: number }[]
}

export default function Forecasting() {
  const { fcSelectedId: selectedId, setFcSelectedId: setSelectedId, fcHorizon: horizon, fcBoost: boost } = useFilters()

  const { data: skus } = useQuery<SKU[]>({
    queryKey: ['forecast-skus'],
    queryFn: () => api.get('/forecasting/skus').then(r => r.data),
  })

  // Fallback: initialise selection if sidebar hasn't done it yet (e.g. collapsed)
  useEffect(() => {
    if (skus?.length && !selectedId) setSelectedId(skus[0].product_id)
  }, [skus, selectedId, setSelectedId])

  const { data: fc, isLoading } = useQuery<ForecastData>({
    queryKey: ['forecast', selectedId, horizon, boost],
    queryFn: () => api.get(`/forecasting/${selectedId}`, { params: { horizon, boost_pct: boost } }).then(r => r.data),
    enabled: !!selectedId,
  })

  // Merge historical + forecast for the chart
  const chartData = (() => {
    if (!fc) return []
    const hist = fc.historical.map(h => ({ month: h.month, actual: h.revenue_lakh }))
    const fcst = fc.forecast.map(f => ({
      month: f.month, forecast: f.forecast, ci_low: f.ci_low, ci_high: f.ci_high,
    }))
    // mark the join point: duplicate last historical point as first forecast anchor
    const last = hist[hist.length - 1]
    if (last) {
      fcst.unshift({ month: last.month, forecast: last.actual, ci_low: last.actual, ci_high: last.actual })
    }
    return [...hist, ...fcst]
  })()

  const forecastStart = fc?.historical[fc.historical.length - 1]?.month

  if (!skus || skus.length === 0) {
    return (
      <div>
        <PageHeader title="Demand Forecasting" />
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
          No trained models found. Run <code className="font-mono bg-yellow-100 px-1 rounded">python src/ml/train_forecasts.py</code> first.
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Demand Forecasting" subtitle="SARIMA per-SKU revenue forecasts with seasonality and what-if scenarios" />

      {/* KPIs */}
      {isLoading || !fc ? <Spinner /> : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
            <KPICard label="SKU"                 value={fc.product_name.slice(0, 26)} />
            <KPICard label="Backtest sMAPE"       value={fc.mape != null ? `${fc.mape}%` : '—'}
              sub={fc.mape != null ? (fc.mape < 20 ? 'Good accuracy' : 'Moderate accuracy') : undefined} />
            <KPICard label="Recent Avg (6m)"      value={fc.recent_avg_lakh != null ? `₹${fc.recent_avg_lakh}L` : '—'} />
            <KPICard label="Next-Quarter Trend"
              value={fc.trend_pct != null ? `${fc.trend_pct > 0 ? '+' : ''}${fc.trend_pct}%` : '—'}
              sub={fc.trend_pct != null ? (fc.trend_pct > 0 ? 'Upward trend' : 'Downward trend') : undefined} />
          </div>

          {/* Main forecast chart */}
          <ChartCard title={`Revenue Forecast — ${fc.product_name} (₹ Lakh/month)`} className="mb-5">
            <ResponsiveContainer width="100%" height={340}>
              <ComposedChart data={chartData} margin={{ top: 8, right: 20, bottom: 8, left: 10 }}>
                <defs>
                  <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#F59E0B" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 9 }} tickLine={false}
                  tickFormatter={v => v.slice(2)} interval={1} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                  tickFormatter={v => `₹${v}`} />
                <Tooltip formatter={(v: number, name: string) => [`₹${v}L`, name]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {forecastStart && (
                  <ReferenceLine x={forecastStart} stroke="#6B7280" strokeDasharray="4 4"
                    label={{ value: 'Forecast start', fill: '#6B7280', fontSize: 10, position: 'insideTopRight' }} />
                )}
                {/* CI band */}
                <Area type="monotone" dataKey="ci_high" fill="url(#ciGrad)"
                  stroke="none" name="CI High" legendType="none" />
                <Area type="monotone" dataKey="ci_low" fill="#fff"
                  stroke="none" name="CI Low" legendType="none" />
                {/* Historical */}
                <Line type="monotone" dataKey="actual" stroke="#C8102E" strokeWidth={2}
                  dot={false} name="Actual (₹L)" connectNulls={false} />
                {/* Forecast */}
                <Line type="monotone" dataKey="forecast" stroke="#F59E0B" strokeWidth={2}
                  strokeDasharray="6 3" dot={{ r: 3, fill: '#F59E0B' }} name="Forecast (₹L)" connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Forecast table */}
          <ChartCard title="Forecast Summary Table">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Month','Forecast (₹L)','Lower CI (₹L)','Upper CI (₹L)'].map(h => (
                    <th key={h} className="py-1.5 px-3 text-left text-gray-500 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {fc.forecast.map(row => (
                  <tr key={row.month} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-1.5 px-3 font-medium text-gray-800">{row.month}</td>
                    <td className="py-1.5 px-3 font-bold text-hawkins-red">₹{row.forecast}L</td>
                    <td className="py-1.5 px-3 text-gray-500">₹{row.ci_low}L</td>
                    <td className="py-1.5 px-3 text-gray-500">₹{row.ci_high}L</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ChartCard>
        </>
      )}
    </div>
  )
}
