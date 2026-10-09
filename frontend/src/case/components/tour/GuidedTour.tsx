import { useEffect, useState } from 'react'
import { useCase } from '../../context/CaseContext'

const steps = [
  {
    target: 'cases',
    title: 'Pick a case',
    body: 'Each climate variable is a case. Switching the case recolors the maps, charts, and verdicts.',
  },
  {
    target: 'map',
    title: 'Clue 2: Where?',
    body: 'Solid color means a significant trend. A hatch means no clear change. Grey means not enough data.',
  },
  {
    target: 'legend',
    title: 'Clue 3: How much?',
    body: 'The legend is the change per 10 years. The scale is centered on zero and uses that variable’s colors.',
  },
  {
    target: 'stamp',
    title: 'Clue 4: Significant?',
    body: 'Open a region for the verdict stamp, the yearly series, and the corrected p-value.',
  },
  {
    target: 'compare',
    title: 'Compare twins',
    body: 'Choose two states. The opposite-trend banner appears only when the statuses really disagree.',
  },
]

export function GuidedTour() {
  const { tourStep, setTourStep, setSection, setSelectedRegionId, file, variable, section, selectedRegionId } = useCase()
  const [rect, setRect] = useState<DOMRect | null>(null)
  const step = tourStep ?? 0

  useEffect(() => {
    if (tourStep == null || !file) return
    if (tourStep === 1 || tourStep === 2 || tourStep === 3) setSection('map')
    if (tourStep === 3) {
      const ranked = [...file.variables[variable].regions].sort(
        (left, right) => Math.abs(right.slope_per_decade ?? 0) - Math.abs(left.slope_per_decade ?? 0),
      )
      if (ranked[0]) setSelectedRegionId(ranked[0].geography_id)
    }
    if (tourStep === 4) setSection('compare')
  }, [tourStep, file, variable, setSection, setSelectedRegionId])

  useEffect(() => {
    if (tourStep == null) return
    const measure = () => {
      const element = [...document.querySelectorAll(`[data-tour="${steps[step].target}"]`)].find(
        (node) => node.getBoundingClientRect().width > 0,
      )
      setRect(element?.getBoundingClientRect() ?? null)
    }
    const frame = requestAnimationFrame(measure)
    window.addEventListener('resize', measure)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', measure)
    }
  }, [tourStep, step, section, selectedRegionId])

  if (tourStep == null) return null
  const current = steps[step]
  const cardTop = rect ? Math.min(window.innerHeight - 180, rect.bottom + 12) : 80
  const cardLeft = rect ? Math.min(window.innerWidth - 320, Math.max(16, rect.left)) : 16

  return (
    <div className="fixed inset-0 z-50">
      {rect ? (
        <div
          className="pointer-events-none absolute rounded-xl border-2 border-gold"
          style={{
            top: rect.top - 6,
            left: rect.left - 6,
            width: rect.width + 12,
            height: rect.height + 12,
            boxShadow: '0 0 0 9999px rgba(7, 11, 31, 0.72)',
          }}
        />
      ) : null}
      <div className="absolute w-[300px] rounded-2xl border border-line bg-surface p-4" style={{ top: cardTop, left: cardLeft }}>
        <p className="text-xs text-gold">Step {step + 1} of {steps.length}</p>
        <h3 className="mt-1 font-display text-lg font-bold">{current.title}</h3>
        <p className="mt-2 text-sm text-muted">{current.body}</p>
        <div className="mt-4 flex gap-2">
          <button type="button" className="rounded-full border border-line px-3 py-1 text-sm" disabled={step === 0} onClick={() => setTourStep(step - 1)}>
            Back
          </button>
          {step < steps.length - 1 ? (
            <button type="button" className="rounded-full bg-gold px-3 py-1 text-sm font-semibold text-navy" onClick={() => setTourStep(step + 1)}>
              Next
            </button>
          ) : (
            <button type="button" className="rounded-full bg-gold px-3 py-1 text-sm font-semibold text-navy" onClick={() => setTourStep(null)}>
              Finish
            </button>
          )}
          <button type="button" className="ml-auto text-sm text-muted" onClick={() => setTourStep(null)}>
            Skip
          </button>
        </div>
      </div>
    </div>
  )
}
