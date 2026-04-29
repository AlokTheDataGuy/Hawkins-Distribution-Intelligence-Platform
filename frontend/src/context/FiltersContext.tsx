import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface FiltersCtx {
  // GIS Distribution
  gisRegion:          string;   setGisRegion:          (v: string)   => void
  gisMetric:          string;   setGisMetric:          (v: string)   => void
  gisShowDealers:     boolean;  setGisShowDealers:     (v: boolean)  => void
  gisShowFactories:   boolean;  setGisShowFactories:   (v: boolean)  => void
  gisShowCentres:     boolean;  setGisShowCentres:     (v: boolean)  => void
  // Dealer Performance
  dpTiers:            string[]; setDpTiers:            (v: string[]) => void
  dpRegions:          string[]; setDpRegions:          (v: string[]) => void
  // Forecasting
  fcSelectedId:       string;   setFcSelectedId:       (v: string)   => void
  fcHorizon:          number;   setFcHorizon:          (v: number)   => void
  fcBoost:            number;   setFcBoost:            (v: number)   => void
  // Anomaly Detection
  anSevFilter:        string;   setAnSevFilter:        (v: string)   => void
  anMethodFilter:     string;   setAnMethodFilter:     (v: string)   => void
}

const Ctx = createContext<FiltersCtx | null>(null)

export function FiltersProvider({ children }: { children: ReactNode }) {
  const [gisRegion,        setGisRegion]        = useState('All')
  const [gisMetric,        setGisMetric]        = useState('revenue_cr')
  const [gisShowDealers,   setGisShowDealers]   = useState(true)
  const [gisShowFactories, setGisShowFactories] = useState(true)
  const [gisShowCentres,   setGisShowCentres]   = useState(false)
  const [dpTiers,          setDpTiers]          = useState(['A', 'B', 'C'])
  const [dpRegions,        setDpRegions]        = useState(['North', 'South', 'East', 'West', 'Central', 'Northeast'])
  const [fcSelectedId,     setFcSelectedId]     = useState('')
  const [fcHorizon,        setFcHorizon]        = useState(6)
  const [fcBoost,          setFcBoost]          = useState(0)
  const [anSevFilter,      setAnSevFilter]      = useState('All')
  const [anMethodFilter,   setAnMethodFilter]   = useState('All')

  return (
    <Ctx.Provider value={{
      gisRegion, setGisRegion,
      gisMetric, setGisMetric,
      gisShowDealers, setGisShowDealers,
      gisShowFactories, setGisShowFactories,
      gisShowCentres, setGisShowCentres,
      dpTiers, setDpTiers,
      dpRegions, setDpRegions,
      fcSelectedId, setFcSelectedId,
      fcHorizon, setFcHorizon,
      fcBoost, setFcBoost,
      anSevFilter, setAnSevFilter,
      anMethodFilter, setAnMethodFilter,
    }}>
      {children}
    </Ctx.Provider>
  )
}

export function useFilters() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useFilters must be used inside FiltersProvider')
  return ctx
}

// Re-export useEffect so callers can do one-shot init without importing React
export { useEffect }
