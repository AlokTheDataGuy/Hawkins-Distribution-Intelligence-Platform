import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { FiltersProvider } from './context/FiltersContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Executive from './pages/Executive'
import GISDistribution from './pages/GISDistribution'
import DealerPerformance from './pages/DealerPerformance'
import Forecasting from './pages/Forecasting'
import AnomalyDetection from './pages/AnomalyDetection'
import ServiceAnalytics from './pages/ServiceAnalytics'
import CompetitiveIntel from './pages/CompetitiveIntel'

export default function App() {
  return (
    <FiltersProvider>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index                       element={<Home />} />
          <Route path="executive"            element={<Executive />} />
          <Route path="gis-distribution"     element={<GISDistribution />} />
          <Route path="dealer-performance"   element={<DealerPerformance />} />
          <Route path="forecasting"          element={<Forecasting />} />
          <Route path="anomaly-detection"    element={<AnomalyDetection />} />
          <Route path="service-analytics"    element={<ServiceAnalytics />} />
          <Route path="competitive-intel"    element={<CompetitiveIntel />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </FiltersProvider>
  )
}
