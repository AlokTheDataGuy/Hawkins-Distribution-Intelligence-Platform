import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import { useFilters } from '../context/FiltersContext'

// ─── Shared helpers ────────────────────────────────────────────────────────────

function SLabel({ text }: { text: string }) {
  return (
    <div className="text-[9px] font-extrabold uppercase tracking-widest text-gray-400 pt-3 pb-1">
      {text}
    </div>
  )
}

function SDivider() {
  return <div className="border-t border-gray-200 my-2" />
}

function SNote({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] text-gray-400 leading-snug mt-1">{children}</p>
}

function ColorDot({ color, label, sub }: { color: string; label: string; sub?: string }) {
  return (
    <div className="flex items-start gap-2 py-0.5">
      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-0.5 border border-white shadow-sm"
        style={{ background: color }} />
      <div>
        <span className="text-[11px] font-semibold text-gray-700">{label}</span>
        {sub && <p className="text-[9.5px] text-gray-400 leading-snug">{sub}</p>}
      </div>
    </div>
  )
}

// ─── HOME panel (original sidebar content) ─────────────────────────────────────

function Tag({ text, bg = '#EFF6FF', fg = '#1D4ED8' }: { text: string; bg?: string; fg?: string }) {
  return (
    <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded-full whitespace-nowrap"
      style={{ background: bg, color: fg }}>
      {text}
    </span>
  )
}

function StatBox({ value, label }: { value: string; label: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-3 py-2">
      <div className="text-[17px] font-extrabold text-gray-800 leading-none">{value}</div>
      <div className="text-[9.5px] text-gray-500 mt-0.5">{label}</div>
    </div>
  )
}

function HomePanel() {
  return (
    <>
      <SLabel text="About this project" />
      <p className="text-[11px] text-gray-600 leading-relaxed">
        A production-style internal analytics platform built to demonstrate end-to-end
        IT system development for Hawkins Cookers Ltd — SQL data modelling, Python ETL,
        ML-augmented forecasting, and interactive BI.
      </p>

      <SDivider />

      <SLabel text="Dataset" />
      <div className="grid grid-cols-2 gap-1.5 mt-1">
        <StatBox value="1,900" label="Dealers" />
        <StatBox value="1.05M" label="Transactions" />
        <StatBox value="123"   label="SKUs" />
        <StatBox value="36"    label="States / UTs" />
      </div>
      <SNote>Synthetic · calibrated to Hawkins Annual Report FY24-25 &amp; ICRA 2024</SNote>

      <SDivider />

      <SLabel text="Tech stack" />
      <div className="flex flex-wrap gap-1 mt-1">
        <Tag text="Python" />
        <Tag text="SQL · SQLite"          bg="#FEF2F2" fg="#B91C1C" />
        <Tag text="Pandas · NumPy" />
        <Tag text="FastAPI"               bg="#F0FDF4" fg="#15803D" />
        <Tag text="React + TypeScript"    bg="#EFF6FF" fg="#1D4ED8" />
        <Tag text="Tailwind CSS"          bg="#F0FDFA" fg="#0F766E" />
        <Tag text="Recharts"              bg="#F5F3FF" fg="#6D28D9" />
        <Tag text="scikit-learn"          bg="#F5F3FF" fg="#6D28D9" />
        <Tag text="SARIMA"                bg="#FFFBEB" fg="#B45309" />
        <Tag text="Isolation Forest"      bg="#FEF2F2" fg="#B91C1C" />
      </div>

      <SDivider />

      <SLabel text="Modules" />
      <div className="text-[11px] text-gray-600 leading-relaxed space-y-0.5">
        <div><span className="font-semibold">Executive</span> — Top-line KPIs &amp; trends</div>
        <div><span className="font-semibold">GIS</span> — Dealer map &amp; white-space analysis</div>
        <div><span className="font-semibold">Dealers</span> — Performance scoring &amp; at-risk</div>
        <div><span className="font-semibold">Forecasting</span> — SARIMA demand forecasts</div>
        <div><span className="font-semibold">Anomaly</span> — Z-score + Isolation Forest alerts</div>
        <div><span className="font-semibold">Service</span> — Warranty claims &amp; quality risk</div>
        <div><span className="font-semibold">Competitive</span> — Pricing vs Prestige / Pigeon</div>
      </div>

      <SDivider />
      <p className="text-[10px] text-gray-400">Built by <strong>Alok Deep</strong> · April 2026</p>
    </>
  )
}

// ─── EXECUTIVE panel ────────────────────────────────────────────────────────────

const REGION_COLORS: Record<string, string> = {
  North: '#3B82F6', South: '#10B981', East: '#F59E0B',
  West: '#EF4444', Central: '#8B5CF6', Northeast: '#06B6D4',
}
const CAT_COLORS: Record<string, string> = {
  'Pressure Cooker': '#C8102E', Cookware: '#3B82F6',
  Electricals: '#10B981', Accessory: '#F59E0B',
}

function ExecutivePanel() {
  return (
    <>
      <SLabel text="Data Coverage" />
      <div className="text-[11px] text-gray-600 space-y-0.5">
        <div>FY2024 – FY2026 · 36 months</div>
        <div>1,053,833 transactions · 123 SKUs</div>
        <div>1,900 active dealers · 36 states</div>
      </div>

      <SDivider />

      <SLabel text="Region Legend" />
      {Object.entries(REGION_COLORS).map(([r, c]) => (
        <ColorDot key={r} color={c} label={r} />
      ))}

      <SDivider />

      <SLabel text="Product Categories" />
      {Object.entries(CAT_COLORS).map(([cat, c]) => (
        <ColorDot key={cat} color={c} label={cat} />
      ))}

      <SDivider />

      <SLabel text="What to look for" />
      <div className="text-[10.5px] text-gray-500 space-y-1.5 leading-snug">
        <p>• North &amp; West drive ~55% of total revenue</p>
        <p>• Pressure Cookers remain the flagship category (~60% revenue)</p>
        <p>• Seasonality peaks in Oct–Dec (festive demand)</p>
      </div>
    </>
  )
}

// ─── GIS DISTRIBUTION panel ─────────────────────────────────────────────────────

function GISPanel() {
  const {
    gisRegion, setGisRegion,
    gisMetric, setGisMetric,
    gisShowDealers, setGisShowDealers,
    gisShowFactories, setGisShowFactories,
    gisShowCentres, setGisShowCentres,
  } = useFilters()

  const { data: dealers = [] } = useQuery<any[]>({
    queryKey: ['gis-dealers', gisRegion],
    queryFn: () => api.get('/gis/dealers', { params: { region: gisRegion } }).then(r => r.data),
  })

  const sel = 'border border-gray-200 rounded-lg px-2 py-1 text-xs bg-white w-full'

  return (
    <>
      <SLabel text="Region" />
      <select value={gisRegion} onChange={e => setGisRegion(e.target.value)} className={sel}>
        {['All', 'North', 'South', 'East', 'West', 'Central', 'Northeast'].map(r => (
          <option key={r}>{r}</option>
        ))}
      </select>
      <SNote>{dealers.length.toLocaleString()} dealer{dealers.length !== 1 ? 's' : ''} in view</SNote>

      <SDivider />

      <SLabel text="Choropleth Metric" />
      <select value={gisMetric} onChange={e => setGisMetric(e.target.value)} className={sel}>
        <option value="revenue_cr">Revenue (₹ Cr)</option>
        <option value="total_units">Units Sold</option>
        <option value="active_dealers">Dealer Count</option>
      </select>
      <SNote>Darker shade = higher value</SNote>

      <SDivider />

      <SLabel text="Map Layers" />
      <div className="space-y-1.5 mt-1">
        {[
          { label: 'Dealers',         sub: 'Bubble size = monthly capacity', checked: gisShowDealers,   set: setGisShowDealers },
          { label: 'Factories',       sub: '★ 3 manufacturing plants',       checked: gisShowFactories, set: setGisShowFactories },
          { label: 'Service Centres', sub: '● 140 authorised centres',       checked: gisShowCentres,   set: setGisShowCentres },
        ].map(({ label, sub, checked, set }) => (
          <label key={label} className="flex items-start gap-2 cursor-pointer select-none">
            <input type="checkbox" checked={checked} onChange={e => set(e.target.checked)}
              className="accent-hawkins-red mt-0.5 flex-shrink-0" />
            <div>
              <span className="text-[11px] font-semibold text-gray-700">{label}</span>
              <p className="text-[9.5px] text-gray-400">{sub}</p>
            </div>
          </label>
        ))}
      </div>

      <SDivider />

      <SLabel text="Dealer Tier Legend" />
      <ColorDot color="#10B981" label="Tier A" sub="High volume, flagship" />
      <ColorDot color="#F59E0B" label="Tier B" sub="Mid-range volume" />
      <ColorDot color="#6B7280" label="Tier C" sub="Entry / low volume" />
    </>
  )
}

// ─── DEALER PERFORMANCE panel ───────────────────────────────────────────────────

const DP_ALL_TIERS   = ['A', 'B', 'C']
const DP_ALL_REGIONS = ['North', 'South', 'East', 'West', 'Central', 'Northeast']
const TIER_COLORS: Record<string, string> = { A: '#10B981', B: '#F59E0B', C: '#6B7280' }

function DealerPanel() {
  const { dpTiers, setDpTiers, dpRegions, setDpRegions } = useFilters()

  function toggleTier(t: string) {
    const next = dpTiers.includes(t) ? dpTiers.filter(x => x !== t) : [...dpTiers, t]
    setDpTiers(next.length === 0 ? DP_ALL_TIERS : next)
  }

  function toggleRegion(r: string) {
    const next = dpRegions.includes(r) ? dpRegions.filter(x => x !== r) : [...dpRegions, r]
    setDpRegions(next.length === 0 ? DP_ALL_REGIONS : next)
  }

  const isDefault = dpTiers.length === 3 && dpRegions.length === 6

  return (
    <>
      <SLabel text="Tier" />
      <div className="flex gap-3 mt-1">
        {DP_ALL_TIERS.map(t => (
          <label key={t} className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={dpTiers.includes(t)} onChange={() => toggleTier(t)}
              className="accent-hawkins-red" />
            <span className="text-xs font-bold" style={{ color: TIER_COLORS[t] }}>
              {t}
            </span>
          </label>
        ))}
      </div>

      <SLabel text="Region" />
      <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-1">
        {DP_ALL_REGIONS.map(r => (
          <label key={r} className="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" checked={dpRegions.includes(r)} onChange={() => toggleRegion(r)}
              className="accent-hawkins-red" />
            <span className="text-[11px] text-gray-700">{r}</span>
          </label>
        ))}
      </div>

      {!isDefault && (
        <button
          onClick={() => { setDpTiers(DP_ALL_TIERS); setDpRegions(DP_ALL_REGIONS) }}
          className="mt-3 text-xs text-hawkins-red hover:underline"
        >
          Reset filters
        </button>
      )}

      <SDivider />

      <SNote>Filters apply to the Scorecard tab only.</SNote>
      <SNote>Decliners &amp; Risers and Cohort Analysis always show all dealers.</SNote>

      <SDivider />

      <SLabel text="Score Breakdown" />
      <div className="text-[10.5px] text-gray-500 space-y-1 leading-snug">
        <p>Score = weighted composite of revenue, growth, basket size, and activity recency.</p>
        <p><span className="font-semibold text-gray-700">80–100</span> — Elite performers</p>
        <p><span className="font-semibold text-gray-700">50–79</span> — Solid / growing</p>
        <p><span className="font-semibold text-gray-700">&lt; 50</span> — At-risk or dormant</p>
      </div>
    </>
  )
}

// ─── FORECASTING panel ───────────────────────────────────────────────────────────

function ForecastPanel() {
  const { fcSelectedId, setFcSelectedId, fcHorizon, setFcHorizon, fcBoost, setFcBoost } = useFilters()

  const { data: skus = [] } = useQuery<{ product_id: string; product_name: string }[]>({
    queryKey: ['forecast-skus'],
    queryFn: () => api.get('/forecasting/skus').then(r => r.data),
  })

  useEffect(() => {
    if (skus.length && !fcSelectedId) setFcSelectedId(skus[0].product_id)
  }, [skus, fcSelectedId, setFcSelectedId])

  const sel = 'border border-gray-200 rounded-lg px-2 py-1 text-xs bg-white w-full'

  return (
    <>
      <SLabel text="SKU" />
      <select value={fcSelectedId} onChange={e => setFcSelectedId(e.target.value)} className={sel}>
        {skus.map(s => (
          <option key={s.product_id} value={s.product_id}>{s.product_name}</option>
        ))}
      </select>

      <SLabel text={`Forecast Horizon · ${fcHorizon} months`} />
      <input
        type="range" min={3} max={12} value={fcHorizon}
        onChange={e => setFcHorizon(+e.target.value)}
        className="w-full accent-hawkins-red"
      />
      <div className="flex justify-between text-[9px] text-gray-400 mt-0.5">
        <span>3m</span><span>12m</span>
      </div>

      <SLabel text={`What-if Boost · ${fcBoost > 0 ? '+' : ''}${fcBoost}%`} />
      <input
        type="range" min={-30} max={50} step={5} value={fcBoost}
        onChange={e => setFcBoost(+e.target.value)}
        className="w-full accent-hawkins-red"
      />
      <div className="flex justify-between text-[9px] text-gray-400 mt-0.5">
        <span>-30%</span><span>+50%</span>
      </div>
      {fcBoost !== 0 && (
        <button onClick={() => setFcBoost(0)} className="text-[10px] text-hawkins-red hover:underline mt-1">
          Reset boost
        </button>
      )}

      <SDivider />

      <SLabel text="Model Accuracy (sMAPE)" />
      <div className="text-[10.5px] text-gray-500 space-y-0.5 leading-snug">
        <p><span className="font-semibold text-green-600">&lt; 15%</span> — Excellent fit</p>
        <p><span className="font-semibold text-amber-500">15–25%</span> — Good fit</p>
        <p><span className="font-semibold text-red-400">&gt; 25%</span> — Use with caution</p>
      </div>

      <SDivider />

      <SLabel text="About the model" />
      <SNote>
        SARIMA fitted per SKU on 36 months of monthly revenue. Seasonality order auto-selected by
        AIC. Confidence intervals reflect in-sample variance.
      </SNote>
    </>
  )
}

// ─── ANOMALY DETECTION panel ─────────────────────────────────────────────────────

function AnomalyPanel() {
  const { anSevFilter, setAnSevFilter, anMethodFilter, setAnMethodFilter } = useFilters()

  const sel = 'border border-gray-200 rounded-lg px-2 py-1 text-xs bg-white w-full'

  return (
    <>
      <SLabel text="Severity" />
      <select value={anSevFilter} onChange={e => setAnSevFilter(e.target.value)} className={sel}>
        {['All', 'Critical', 'Warning'].map(v => <option key={v}>{v}</option>)}
      </select>

      <SLabel text="Detection Method" />
      <select value={anMethodFilter} onChange={e => setAnMethodFilter(e.target.value)} className={sel}>
        {['All', 'Rule-based', 'Z-Score', 'Isolation Forest'].map(v => <option key={v}>{v}</option>)}
      </select>

      <SDivider />

      <SLabel text="Detection Methods" />

      <div className="mt-1 space-y-2.5">
        <div className="bg-blue-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-blue-700 mb-0.5">Rule-based</p>
          <p className="text-[10px] text-blue-600 leading-snug">
            Dealers with no sales in &gt;30 days are flagged as dormant. Simple, interpretable, zero false negatives.
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-purple-700 mb-0.5">Z-Score</p>
          <p className="text-[10px] text-purple-600 leading-snug">
            Revenue deviating &gt;2σ from the dealer's 12-month rolling mean. Catches sudden spikes or drops in activity.
          </p>
        </div>
        <div className="bg-orange-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-orange-700 mb-0.5">Isolation Forest</p>
          <p className="text-[10px] text-orange-600 leading-snug">
            Unsupervised ML: isolates outliers across revenue, returns &amp; service claims simultaneously. Score &lt;0 = anomalous.
          </p>
        </div>
      </div>
    </>
  )
}

// ─── SERVICE ANALYTICS panel ─────────────────────────────────────────────────────

function ServicePanel() {
  return (
    <>
      <SLabel text="Data Coverage" />
      <div className="text-[11px] text-gray-600 space-y-0.5">
        <div>~45,000 warranty claims</div>
        <div>140 authorised service centres</div>
        <div>FY2024 – FY2026 · pan-India</div>
      </div>

      <SDivider />

      <SLabel text="Severity Levels" />
      <div className="space-y-2 mt-1">
        <div className="bg-red-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-red-600 mb-0.5">Critical</p>
          <p className="text-[10px] text-red-500 leading-snug">Safety-related defect requiring immediate repair or product recall.</p>
        </div>
        <div className="bg-amber-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-amber-600 mb-0.5">Routine</p>
          <p className="text-[10px] text-amber-500 leading-snug">Functional failure covered under warranty — replacement or repair.</p>
        </div>
        <div className="bg-green-50 rounded-lg px-2.5 py-2">
          <p className="text-[10.5px] font-bold text-green-600 mb-0.5">Cosmetic</p>
          <p className="text-[10px] text-green-500 leading-snug">Appearance defect — discretionary repair, no safety impact.</p>
        </div>
      </div>

      <SDivider />

      <SLabel text="SLA Benchmarks" />
      <div className="text-[10.5px] text-gray-500 space-y-0.5 leading-snug">
        <p>Critical → target resolution <span className="font-semibold">≤ 7 days</span></p>
        <p>Routine  → target resolution <span className="font-semibold">≤ 14 days</span></p>
        <p>Cosmetic → target resolution <span className="font-semibold">≤ 21 days</span></p>
      </div>

      <SDivider />

      <SLabel text="Quality Risk SKUs" />
      <SNote>
        Claim Rate = warranty claims per 1,000 units sold. SKUs above 2× category average are
        flagged as quality-risk.
      </SNote>
    </>
  )
}

// ─── COMPETITIVE INTEL panel ─────────────────────────────────────────────────────

const COMP_COLORS: Record<string, string> = {
  'TTK Prestige': '#3B82F6',
  'Butterfly':    '#10B981',
  'Pigeon':       '#F59E0B',
  'Stove Kraft':  '#8B5CF6',
}

function CompetitivePanel() {
  return (
    <>
      <SLabel text="Competitors Tracked" />
      {Object.entries(COMP_COLORS).map(([name, color]) => (
        <ColorDot key={name} color={color} label={name} />
      ))}

      <SDivider />

      <SLabel text="Reading Price Gap %" />
      <div className="text-[10.5px] text-gray-500 space-y-1 leading-snug">
        <p>
          <span className="font-semibold text-green-600">Positive %</span> → Hawkins is cheaper (value-leader position)
        </p>
        <p>
          <span className="font-semibold text-red-500">Negative %</span> → Hawkins is costlier (premium position)
        </p>
      </div>

      <SDivider />

      <SLabel text="Posture Thresholds" />
      <div className="text-[10.5px] text-gray-500 space-y-0.5 leading-snug">
        <p><span className="font-semibold text-green-600">Value Leader</span> — avg gap &gt; +5%</p>
        <p><span className="font-semibold text-amber-500">Parity</span> — avg gap −5% to +5%</p>
        <p><span className="font-semibold text-red-500">Premium</span> — avg gap &lt; −5%</p>
      </div>

      <SDivider />

      <SLabel text="Data Coverage" />
      <div className="text-[11px] text-gray-600 space-y-0.5">
        <div>~5,700 price snapshots</div>
        <div>4 competitors · monthly tracking</div>
        <div>Covers all major Hawkins SKU categories</div>
      </div>

      <SDivider />

      <SLabel text="Vulnerable SKUs" />
      <SNote>
        A SKU is "vulnerable" when Hawkins' price advantage over a competitor has narrowed by
        more than 2 percentage points in the last 90 days — signalling competitive pressure.
      </SNote>
    </>
  )
}

// ─── Main Sidebar ─────────────────────────────────────────────────────────────────

const PAGE_TITLES: Record<string, string> = {
  '/':                   'Home',
  '/executive':          'Executive Overview',
  '/gis-distribution':   'Map Controls',
  '/dealer-performance': 'Dealer Filters',
  '/forecasting':        'Forecast Controls',
  '/anomaly-detection':  'Anomaly Filters',
  '/service-analytics':  'Service Analytics',
  '/competitive-intel':  'Competitive Intel',
}

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { pathname } = useLocation()

  const panel = (() => {
    switch (pathname) {
      case '/':                   return <HomePanel />
      case '/executive':          return <ExecutivePanel />
      case '/gis-distribution':   return <GISPanel />
      case '/dealer-performance': return <DealerPanel />
      case '/forecasting':        return <ForecastPanel />
      case '/anomaly-detection':  return <AnomalyPanel />
      case '/service-analytics':  return <ServicePanel />
      case '/competitive-intel':  return <CompetitivePanel />
      default:                    return <HomePanel />
    }
  })()

  if (collapsed) {
    return (
      <div className="w-8 bg-gray-50 border-r border-gray-200 flex items-start pt-3 justify-center flex-shrink-0">
        <button onClick={() => setCollapsed(false)} className="text-gray-400 hover:text-gray-600">
          <ChevronRight size={16} />
        </button>
      </div>
    )
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-50 border-r border-gray-200 overflow-y-auto flex flex-col">
      <div className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-1">
          <img src="/logo.png" alt="Hawkins" className="h-14 w-14 object-contain" />
          <button onClick={() => setCollapsed(true)} className="text-gray-400 hover:text-gray-600">
            <ChevronLeft size={16} />
          </button>
        </div>
        <div className="text-[11px] text-gray-500 leading-snug pb-3">
          Distribution Intelligence Platform<br />
          Internal Analytics · Hawkins Cookers Ltd
        </div>

        <div className="border-t border-gray-200" />

        {/* Page-specific panel */}
        <div className="text-[9px] font-extrabold uppercase tracking-widest text-hawkins-red pt-2 pb-0">
          {PAGE_TITLES[pathname] ?? 'Navigation'}
        </div>

        {panel}
      </div>
    </aside>
  )
}
