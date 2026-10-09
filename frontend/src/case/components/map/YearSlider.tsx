import { Pause, Play } from 'lucide-react'

export function YearSlider({
  year,
  start,
  end,
  playing,
  onYear,
  onToggle,
}: {
  year: number
  start: number
  end: number
  playing: boolean
  onYear: (year: number) => void
  onToggle: () => void
}) {
  return (
    <div className="mt-3 flex items-center gap-3">
      <button
        type="button"
        className="rounded-full bg-gold p-2 text-navy"
        onClick={onToggle}
        aria-label={playing ? 'Pause years' : 'Play years'}
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>
      <input
        className="w-full accent-[#FBBF24]"
        type="range"
        min={start}
        max={end}
        value={year}
        onChange={(event) => onYear(Number(event.target.value))}
        aria-label="Year"
      />
      <span className="tabular w-12 text-sm text-ink">{year}</span>
    </div>
  )
}
