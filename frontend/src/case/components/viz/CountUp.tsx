import { useReducedMotion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { formatSigned, isFiniteNumber } from '../../lib/format'

export function CountUp({ value, digits }: { value: number | null; digits: number }) {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce || !isFiniteNumber(value) ? value : 0)

  useEffect(() => {
    if (!isFiniteNumber(value)) {
      setShown(null)
      return
    }
    if (reduce) {
      setShown(value)
      return
    }
    const started = performance.now()
    let frame = 0
    const tick = (now: number) => {
      const progress = Math.min(1, (now - started) / 360)
      setShown(value * progress)
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value, reduce])

  if (!isFiniteNumber(shown) || !isFiniteNumber(value)) return <>unavailable</>
  return <>{formatSigned(shown, digits)}</>
}
