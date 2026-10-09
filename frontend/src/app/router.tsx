import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '../components/layout/AppShell'
import { ComparePage } from '../pages/ComparePage'
import { DashboardPage } from '../pages/DashboardPage'
import { ImpactPage } from '../pages/ImpactPage'
import { MapExplorerPage } from '../pages/MapExplorerPage'
import { MethodologyPage } from '../pages/MethodologyPage'
import { TrendsPage } from '../pages/TrendsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'trends', element: <TrendsPage /> },
      { path: 'map', element: <MapExplorerPage /> },
      { path: 'compare', element: <ComparePage /> },
      { path: 'impact', element: <ImpactPage /> },
      { path: 'methodology', element: <MethodologyPage /> },
    ],
  },
])
