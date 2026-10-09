const colors: Record<string, string> = {
  significant_increasing: 'bg-heat/20 text-heat',
  significant_decreasing: 'bg-rain/20 text-rain',
  not_significant: 'bg-white/10 text-mist',
  insufficient_data: 'bg-white/5 text-muted',
}

export function StatusPill({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs ${colors[status] ?? colors.insufficient_data}`}>
      {status.replaceAll('_', ' ')}
    </span>
  )
}

export const statusColor: Record<string, string> = {
  significant_increasing: '#e07a5f',
  significant_decreasing: '#79b4d6',
  not_significant: '#8d9a90',
  insufficient_data: '#24302b',
}
