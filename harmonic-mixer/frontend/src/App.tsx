import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { ScanPage } from './pages/ScanPage'
import { MixPage } from './pages/MixPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/mix" element={<MixPage />} />
      </Routes>
    </BrowserRouter>
  )
}
