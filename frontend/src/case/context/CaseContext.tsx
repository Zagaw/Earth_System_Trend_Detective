import { useQuery } from '@tanstack/react-query'
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { getJson } from '../../lib/api'
import { VARIABLE_ORDER } from '../lib/format'
import type { BoundaryCollection, CaseFile, MapMode, SectionId, VariableId } from '../types'

interface CaseState {
  file?: CaseFile
  boundaries?: BoundaryCollection
  isLoading: boolean
  isError: boolean
  refetch: () => void
  variable: VariableId
  setVariable: (variable: VariableId) => void
  section: SectionId
  setSection: (section: SectionId) => void
  mapMode: MapMode
  setMapMode: (mode: MapMode) => void
  year: number
  setYear: (year: number) => void
  playing: boolean
  setPlaying: (playing: boolean) => void
  selectedRegionId: string | null
  setSelectedRegionId: (id: string | null) => void
  hoverRegionId: string | null
  setHoverRegionId: (id: string | null) => void
  highlightIds: string[]
  setHighlightIds: (ids: string[]) => void
  compareA: string | null
  compareB: string | null
  setCompareA: (id: string | null) => void
  setCompareB: (id: string | null) => void
  assignCompare: (id: string) => void
  tourStep: number | null
  setTourStep: (step: number | null) => void
  twinNote: string
  setTwinNote: (note: string) => void
}

const CaseContext = createContext<CaseState | null>(null)

function readHash() {
  const [section, variable, iso] = window.location.hash.replace('#', '').split('/')
  const sections: SectionId[] = ['overview', 'map', 'fingerprint', 'compare', 'evidence']
  const variables = new Set<string>(VARIABLE_ORDER)
  return {
    section: sections.includes(section as SectionId) ? (section as SectionId) : 'overview',
    variable: variables.has(variable) ? (variable as VariableId) : 'temperature',
    iso: iso || null,
  }
}

export function CaseProvider({ children }: { children: ReactNode }) {
  const initial = readHash()
  const fileQuery = useQuery({
    queryKey: ['case-file'],
    queryFn: () => getJson('/case-files?start_year=2001&end_year=2025') as Promise<CaseFile>,
    staleTime: Number.POSITIVE_INFINITY,
  })
  const boundaryQuery = useQuery({
    queryKey: ['adm1-boundary'],
    queryFn: async () => {
      const response = await fetch('/myanmar-adm1.json?v=3')
      if (!response.ok) throw new Error('The Myanmar boundary file could not be loaded.')
      return (await response.json()) as BoundaryCollection
    },
    staleTime: Number.POSITIVE_INFINITY,
  })
  const [variable, setVariable] = useState<VariableId>(initial.variable)
  const [section, setSection] = useState<SectionId>(initial.section)
  const [mapMode, setMapMode] = useState<MapMode>('trend')
  const [year, setYear] = useState(2016)
  const [playing, setPlaying] = useState(false)
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null)
  const [hoverRegionId, setHoverRegionId] = useState<string | null>(null)
  const [highlightIds, setHighlightIds] = useState<string[]>([])
  const [compareA, setCompareA] = useState<string | null>(null)
  const [compareB, setCompareB] = useState<string | null>(null)
  const [tourStep, setTourStep] = useState<number | null>(null)
  const [twinNote, setTwinNote] = useState('')
  const [pendingIso, setPendingIso] = useState<string | null>(initial.iso)

  useEffect(() => {
    const file = fileQuery.data
    if (!file || !pendingIso) return
    const match = file.regions.find((region) => region.iso === pendingIso || region.id === pendingIso)
    if (match) setSelectedRegionId(match.id)
    setPendingIso(null)
  }, [fileQuery.data, pendingIso])

  useEffect(() => {
    if (mapMode !== 'year') setPlaying(false)
  }, [mapMode])

  useEffect(() => {
    const file = fileQuery.data
    if (!playing || !file) return
    const timer = window.setInterval(() => {
      setYear((current) => (current >= file.end_year ? file.start_year : current + 1))
    }, 400)
    return () => window.clearInterval(timer)
  }, [playing, fileQuery.data])

  useEffect(() => {
    const file = fileQuery.data
    const iso = file?.regions.find((region) => region.id === selectedRegionId)?.iso
    const next = `#${section}/${variable}${iso ? `/${iso}` : ''}`
    if (window.location.hash !== next) window.history.replaceState(null, '', next)
  }, [section, variable, selectedRegionId, fileQuery.data])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (target?.closest('input, textarea, select')) return
      if (event.key === '1') setVariable('temperature')
      if (event.key === '2') setVariable('precipitation')
      if (event.key === '3') setVariable('relative_humidity')
      if (event.key === 'Escape') {
        setSelectedRegionId(null)
        setTourStep(null)
      }
      if (event.key === ' ' && section === 'map') {
        event.preventDefault()
        setMapMode('year')
        setPlaying((current) => !current)
      }
      if ((event.key === 'ArrowRight' || event.key === 'ArrowLeft') && section === 'map') {
        event.preventDefault()
        const file = fileQuery.data
        if (!file) return
        setMapMode('year')
        setYear((current) => {
          const next = event.key === 'ArrowRight' ? current + 1 : current - 1
          if (next > file.end_year) return file.start_year
          if (next < file.start_year) return file.end_year
          return next
        })
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [section, fileQuery.data])

  const value = useMemo<CaseState>(
    () => ({
      file: fileQuery.data,
      boundaries: boundaryQuery.data,
      isLoading: fileQuery.isLoading || boundaryQuery.isLoading,
      isError: fileQuery.isError || boundaryQuery.isError,
      refetch: () => {
        void fileQuery.refetch()
        void boundaryQuery.refetch()
      },
      variable,
      setVariable: (next) => {
        setVariable(next)
        setHighlightIds([])
        setTwinNote('')
      },
      section,
      setSection,
      mapMode,
      setMapMode,
      year,
      setYear,
      playing,
      setPlaying,
      selectedRegionId,
      setSelectedRegionId,
      hoverRegionId,
      setHoverRegionId,
      highlightIds,
      setHighlightIds,
      compareA,
      compareB,
      setCompareA,
      setCompareB,
      assignCompare: (id) => {
        if (!compareA || compareB) {
          setCompareA(id)
          setCompareB(null)
          return
        }
        if (id !== compareA) setCompareB(id)
      },
      tourStep,
      setTourStep,
      twinNote,
      setTwinNote,
    }),
    [
      fileQuery,
      boundaryQuery,
      variable,
      section,
      mapMode,
      year,
      playing,
      selectedRegionId,
      hoverRegionId,
      highlightIds,
      compareA,
      compareB,
      tourStep,
      twinNote,
    ],
  )

  return <CaseContext.Provider value={value}>{children}</CaseContext.Provider>
}

export function useCase() {
  const value = useContext(CaseContext)
  if (!value) throw new Error('useCase must be used inside CaseProvider')
  return value
}
