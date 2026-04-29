import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useFilters } from '../context/FiltersContext'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import api from '../api/client'
import PageHeader from '../components/PageHeader'
import ChartCard from '../components/ChartCard'
import Spinner from '../components/Spinner'

const TIER_COLORS: Record<string, string> = { A: '#10B981', B: '#F59E0B', C: '#6B7280' }
const REGION_COLORS: Record<string, string> = {
  North: '#3B82F6', South: '#10B981', East: '#F59E0B',
  West: '#EF4444', Central: '#8B5CF6', Northeast: '#06B6D4',
}

function normalize(val: number, min: number, max: number, lo = 4, hi = 18) {
  if (max === min) return (lo + hi) / 2
  return lo + ((val - min) / (max - min)) * (hi - lo)
}

// ─────────────────────────────────────────────────────────────────────────────
// Inner component — lives inside MapContainer so it can call useMap()
// All layers are managed imperatively via useEffect so filter changes are
// guaranteed to take effect (react-leaflet's declarative API silently ignores
// prop changes to style/pathOptions after first mount).
// ─────────────────────────────────────────────────────────────────────────────
interface LayersProps {
  geojson:      any
  states:       any[]
  dealers:      any[]
  factories:    any[]
  centres:      any[]
  metric:       string
  showDealers:  boolean
  showFactories:boolean
  showCentres:  boolean
}

function MapLayers({
  geojson, states, dealers, factories, centres,
  metric, showDealers, showFactories, showCentres,
}: LayersProps) {
  const map         = useMap()
  const choropleth  = useRef<L.GeoJSON    | null>(null)
  const dealerGroup = useRef<L.LayerGroup | null>(null)
  const factGroup   = useRef<L.LayerGroup | null>(null)
  const centreGroup = useRef<L.LayerGroup | null>(null)

  // ── Choropleth — rebuild whenever metric or states data changes ───────────
  useEffect(() => {
    if (choropleth.current) { map.removeLayer(choropleth.current); choropleth.current = null }
    if (!geojson || !states.length) return

    const stateMap: Record<string, any> = {}
    states.forEach(s => { stateMap[s.state_name] = s })
    const maxVal = Math.max(...states.map(s => s[metric] ?? 0), 1)

    choropleth.current = L.geoJSON(geojson, {
      style: (feature) => {
        const name = feature?.properties?.ST_NM ?? ''
        const val  = stateMap[name]?.[metric] ?? 0
        const pct  = val / maxVal
        return {
          fillColor:   `rgb(${Math.round(200 + pct * 55)},${Math.round(60 - pct * 60)},${Math.round(30 - pct * 20)})`,
          fillOpacity: 0.65,
          color:       '#fff',
          weight:      1,
        }
      },
      onEachFeature: (feature, layer) => {
        const name = feature?.properties?.ST_NM ?? ''
        const s    = stateMap[name]
        if (!s) return
        const val =
          metric === 'revenue_cr'    ? `₹${s.revenue_cr ?? 0} Cr` :
          metric === 'total_units'   ? `${(s.total_units ?? 0).toLocaleString()} units` :
                                       `${s.active_dealers ?? 0} dealers`
        layer.bindTooltip(`<strong>${name}</strong><br/>${val}`)
      },
    }).addTo(map)

    return () => { if (choropleth.current) { map.removeLayer(choropleth.current); choropleth.current = null } }
  }, [geojson, states, metric, map])

  // ── Dealer bubbles — rebuild when dealers list or visibility changes ───────
  useEffect(() => {
    if (dealerGroup.current) { map.removeLayer(dealerGroup.current); dealerGroup.current = null }
    if (!showDealers || !dealers.length) return

    const caps   = dealers.map(d => d.monthly_capacity_units)
    const minCap = Math.min(...caps)
    const maxCap = Math.max(...caps)

    const group = L.layerGroup()
    dealers.forEach(d => {
      if (!d.latitude || !d.longitude) return
      L.circleMarker([d.latitude, d.longitude], {
        radius:      normalize(d.monthly_capacity_units, minCap, maxCap),
        fillColor:   TIER_COLORS[d.tier] ?? '#6B7280',
        fillOpacity: 0.75,
        color:       '#fff',
        weight:      0.5,
      }).bindTooltip(`<strong>${d.dealer_name}</strong> (${d.tier})<br/>${d.city_name}, ${d.state_name}`)
        .addTo(group)
    })
    dealerGroup.current = group.addTo(map)

    return () => { if (dealerGroup.current) { map.removeLayer(dealerGroup.current); dealerGroup.current = null } }
  }, [dealers, showDealers, map])

  // ── Factory markers ────────────────────────────────────────────────────────
  useEffect(() => {
    if (factGroup.current) { map.removeLayer(factGroup.current); factGroup.current = null }
    if (!showFactories || !factories.length) return

    const icon = L.divIcon({ html: '<div style="font-size:18px;line-height:1">⭐</div>', className: '', iconAnchor: [9, 9] })
    const group = L.layerGroup()
    factories.forEach(f => {
      if (!f.latitude || !f.longitude) return
      L.marker([f.latitude, f.longitude], { icon })
        .bindTooltip(`<strong>${f.factory_name}</strong><br/>${f.primary_product_line} · ${f.monthly_capacity_units?.toLocaleString()} units/mo`)
        .addTo(group)
    })
    factGroup.current = group.addTo(map)

    return () => { if (factGroup.current) { map.removeLayer(factGroup.current); factGroup.current = null } }
  }, [factories, showFactories, map])

  // ── Service centre markers ─────────────────────────────────────────────────
  useEffect(() => {
    if (centreGroup.current) { map.removeLayer(centreGroup.current); centreGroup.current = null }
    if (!showCentres || !centres.length) return

    const group = L.layerGroup()
    centres.forEach(c => {
      if (!c.latitude || !c.longitude) return
      L.circleMarker([c.latitude, c.longitude], {
        radius: 5, fillColor: '#3B82F6', fillOpacity: 0.75, color: '#fff', weight: 0.5,
      }).bindTooltip(`<strong>${c.state_name}</strong><br/>Capacity: ${c.monthly_capacity_requests}/mo`)
        .addTo(group)
    })
    centreGroup.current = group.addTo(map)

    return () => { if (centreGroup.current) { map.removeLayer(centreGroup.current); centreGroup.current = null } }
  }, [centres, showCentres, map])

  return null
}

// ─────────────────────────────────────────────────────────────────────────────
// Page component
// ─────────────────────────────────────────────────────────────────────────────
export default function GISDistribution() {
  const {
    gisRegion:        region,
    gisMetric:        metric,
    gisShowDealers:   showDealers,
    gisShowFactories: showFactories,
    gisShowCentres:   showCentres,
  } = useFilters()

  const { data: states = [] }     = useQuery({ queryKey: ['gis-states'],              queryFn: () => api.get('/gis/states').then(r => r.data) })
  const { data: dealers = [] }    = useQuery({ queryKey: ['gis-dealers', region],     queryFn: () => api.get('/gis/dealers', { params: { region } }).then(r => r.data) })
  const { data: factories = [] }  = useQuery({ queryKey: ['gis-factories'],           queryFn: () => api.get('/gis/factories').then(r => r.data) })
  const { data: centres = [] }    = useQuery({ queryKey: ['gis-centres'],             queryFn: () => api.get('/gis/service-centres').then(r => r.data) })
  const { data: geojson }         = useQuery({ queryKey: ['geojson'],                 queryFn: () => api.get('/gis/geojson').then(r => r.data) })
  const { data: whitespace = [] } = useQuery({ queryKey: ['whitespace'],              queryFn: () => api.get('/gis/whitespace').then(r => r.data) })

  const mapReady = !!geojson && (states as any[]).length > 0

  return (
    <div>
      <PageHeader title="GIS Distribution" subtitle="Pan-India dealer footprint, factory locations, and white-space opportunities" />

      {/* Map */}
      <div className="rounded-xl overflow-hidden border border-gray-200 mb-4" style={{ height: 500 }}>
        {!mapReady ? (
          <div className="h-full flex items-center justify-center"><Spinner /></div>
        ) : (
          <MapContainer center={[22, 82]} zoom={4.5} style={{ height: '100%', width: '100%' }} zoomControl>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            />
            <MapLayers
              geojson={geojson}
              states={states as any[]}
              dealers={dealers as any[]}
              factories={factories as any[]}
              centres={centres as any[]}
              metric={metric}
              showDealers={showDealers}
              showFactories={showFactories}
              showCentres={showCentres}
            />
          </MapContainer>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-5 mb-5 text-xs text-gray-500">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-600">Dealer tier:</span>
          {Object.entries(TIER_COLORS).map(([tier, color]) => (
            <span key={tier} className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full inline-block border border-white shadow-sm" style={{ background: color }} />
              Tier {tier}
            </span>
          ))}
        </div>
        <span className="flex items-center gap-1">⭐ Factory</span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full inline-block bg-blue-500" /> Service Centre
        </span>
        <span className="flex items-center gap-1 ml-4 text-gray-400">
          Choropleth: light → dark = low → high {metric === 'revenue_cr' ? 'revenue' : metric === 'total_units' ? 'units' : 'dealer count'}
        </span>
      </div>

      {/* White-space analysis */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="White-Space: Market Potential vs Active Dealers">
          {(whitespace as any[]).length ? (
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="active_dealers" name="Dealers"
                  label={{ value: 'Active Dealers', position: 'insideBottom', offset: -10, fontSize: 11 }}
                  tick={{ fontSize: 10 }} />
                <YAxis dataKey="market_potential" name="Potential"
                  label={{ value: 'Market Potential', angle: -90, position: 'insideLeft', fontSize: 11 }}
                  tick={{ fontSize: 10 }} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }) => {
                    if (!payload?.length) return null
                    const d = payload[0]?.payload
                    return (
                      <div className="bg-white border border-gray-200 rounded-lg p-2 text-xs shadow">
                        <p className="font-semibold">{d.state_name}</p>
                        <p>Revenue: ₹{d.revenue_cr} Cr</p>
                        <p>Dealers: {d.active_dealers}</p>
                        <p>Opportunity score: {d.opportunity_score}</p>
                      </div>
                    )
                  }}
                />
                <Scatter data={whitespace as any[]}>
                  {(whitespace as any[]).map((entry: any) => (
                    <Cell key={entry.state_name} fill={REGION_COLORS[entry.region] ?? '#6B7280'} fillOpacity={0.85} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          ) : <Spinner />}
        </ChartCard>

        <ChartCard title="Top Under-Served States (Opportunity Score)">
          {(whitespace as any[]).length ? (
            <div className="overflow-auto max-h-72">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="py-1.5 text-left text-gray-500 font-semibold">State</th>
                    <th className="py-1.5 text-left text-gray-500 font-semibold">Region</th>
                    <th className="py-1.5 text-right text-gray-500 font-semibold">Dealers</th>
                    <th className="py-1.5 text-right text-gray-500 font-semibold">Rev (Cr)</th>
                    <th className="py-1.5 text-right text-gray-500 font-semibold">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(whitespace as any[]).slice(0, 15).map((s: any) => (
                    <tr key={s.state_name} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-1.5 text-gray-800">{s.state_name}</td>
                      <td className="py-1.5">
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold"
                          style={{ background: (REGION_COLORS[s.region] ?? '#6B7280') + '22', color: REGION_COLORS[s.region] ?? '#6B7280' }}>
                          {s.region}
                        </span>
                      </td>
                      <td className="py-1.5 text-right text-gray-600">{s.active_dealers}</td>
                      <td className="py-1.5 text-right text-gray-600">₹{s.revenue_cr}</td>
                      <td className="py-1.5 text-right font-bold text-hawkins-red">{s.opportunity_score}</td>
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
