import { motion, useReducedMotion } from 'framer-motion'
import { VARIABLE_NAME } from '../../lib/format'
import type { PlaceRecord, VariableId } from '../../types'

export function OppositeBanner({
  variable,
  left,
  right,
}: {
  variable: VariableId
  left: PlaceRecord
  right: PlaceRecord
}) {
  const reduce = useReducedMotion()
  const rising = left.trend_status === 'significant_increasing' ? left : right
  const falling = left.trend_status === 'significant_decreasing' ? left : right
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border-2 border-gold bg-gold/10 p-4 text-sm shadow-[0_0_24px_rgba(251,191,36,0.2)]"
    >
      Opposite trends found. {VARIABLE_NAME[variable]} is rising in {rising.geography_name} and falling in{' '}
      {falling.geography_name} over the same years.
    </motion.div>
  )
}
