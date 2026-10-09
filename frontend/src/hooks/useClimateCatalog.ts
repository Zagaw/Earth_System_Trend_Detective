import { useQuery } from '@tanstack/react-query'
import { getAnalysisConfig, getMetadata } from '../lib/api'

export function useMetadata() {
  return useQuery({
    queryKey: ['metadata'],
    queryFn: getMetadata,
  })
}

export function useAnalysisConfig() {
  return useQuery({
    queryKey: ['analysis-config'],
    queryFn: getAnalysisConfig,
  })
}
