import { useQuery } from '@tanstack/react-query'
import { ApiRequestError, getJson } from '../../lib/api'

export function NotReadyPanel({
  title,
  description,
  endpoint,
}: {
  title: string
  description: string
  endpoint: string
}) {
  const query = useQuery({
    queryKey: ['not-ready', endpoint],
    queryFn: () => getJson(endpoint),
    retry: false,
  })

  const message =
    query.error instanceof ApiRequestError
      ? query.error.message
      : query.error instanceof Error
        ? query.error.message
        : null

  return (
    <section className="max-w-3xl">
      <h2 className="text-3xl font-semibold text-white">{title}</h2>
      <p className="mt-3 text-muted">{description}</p>
      <div className="mt-6 rounded-2xl border border-line bg-panel p-5">
        <p className="text-xs tracking-wide text-accent uppercase">API status</p>
        {query.isLoading ? <p className="mt-2">Checking the analysis service…</p> : null}
        {message ? <p className="mt-2">{message}</p> : null}
        {query.isSuccess ? (
          <p className="mt-2">
            The service returned data for an analysis that this version does not calculate yet.
          </p>
        ) : null}
      </div>
    </section>
  )
}
