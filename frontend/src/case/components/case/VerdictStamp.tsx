import { motion, useReducedMotion } from 'framer-motion'
import { verdictLabel } from '../../lib/format'

export function VerdictStamp({ status, marked = false }: { status: string; marked?: boolean }) {
  const reduce = useReducedMotion()
  const significant = status.startsWith('significant')
  return (
    <motion.div
      data-tour={marked ? 'stamp' : undefined}
      initial={reduce ? false : { rotate: -16, scale: 0.86, opacity: 0 }}
      animate={{ rotate: -6, scale: 1, opacity: 1 }}
      transition={reduce ? { duration: 0 } : { type: 'spring', stiffness: 420, damping: 16, duration: 0.35 }}
      className={`inline-block border-[3px] px-3 py-1 font-display text-sm font-bold tracking-[0.14em] ${
        significant ? 'border-gold text-gold' : 'border-[#64748B] text-[#94A3B8]'
      }`}
    >
      {verdictLabel(status)}
    </motion.div>
  )
}
