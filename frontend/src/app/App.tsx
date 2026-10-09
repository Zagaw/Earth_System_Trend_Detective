import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CaseApp } from '../case/CaseApp'

const queryClient = new QueryClient()

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CaseApp />
    </QueryClientProvider>
  )
}
