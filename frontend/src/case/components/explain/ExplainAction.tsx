import { useMutation, useQuery } from '@tanstack/react-query'
import { Sparkles, X } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { API_BASE, ApiRequestError, postJson } from '../../../lib/api'
import { useCase } from '../../context/CaseContext'
import type { MapMode, SectionId, VariableId } from '../../types'

interface ActionRequest {
  page: SectionId
  variable: VariableId
  start_year: number
  end_year: number
  region_id: string | null
  compare_region_id: string | null
  map_mode: MapMode | null
  year: number | null
}

interface ActionExplanation {
  title: string
  action: string
  manual: string
  mode: 'ai' | 'manual'
  answer: string | null
  notice: string
  ai_available: boolean
}

interface ChatTurn {
  role: 'user' | 'assistant'
  text: string
}

export function ExplainAction() {
  const state = useCase()
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatTurn[]>([])
  const [request, setRequest] = useState<ActionRequest | null>(null)
  const requestKey = JSON.stringify(request)

  useEffect(() => {
    if (!open || state.playing) return
    setRequest(buildRequest(state))
  }, [
    open,
    state.playing,
    state.section,
    state.variable,
    state.selectedRegionId,
    state.hoverRegionId,
    state.compareA,
    state.compareB,
    state.mapMode,
    state.year,
    state.file?.start_year,
    state.file?.end_year,
  ])

  useEffect(() => {
    setMessages([])
    setQuestion('')
  }, [requestKey])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      event.stopPropagation()
      setOpen(false)
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [open])

  const explanation = useQuery({
    queryKey: ['explain-action', request],
    queryFn: () => postJson('/understand/action', request) as Promise<ActionExplanation>,
    enabled: open && request != null && Boolean(state.file),
    staleTime: Number.POSITIVE_INFINITY,
    refetchOnWindowFocus: false,
    retry: false,
  })
  const followUp = useMutation({
    mutationFn: (text: string) =>
      postJson('/understand/action', {
        ...request,
        question: text,
        history: messages.slice(-6).map((item) => ({ role: item.role, content: item.text })),
      }) as Promise<ActionExplanation>,
    onSuccess: (reply, text) => {
      setMessages((current) => [
        ...current,
        { role: 'user', text },
        { role: 'assistant', text: reply.answer ?? reply.notice },
      ])
      setQuestion('')
    },
  })

  const ask = (event: FormEvent) => {
    event.preventDefault()
    const text = question.trim()
    if (!text || followUp.isPending || request == null) return
    followUp.mutate(text)
  }

  const download = async () => {
    if (request == null) return
    const response = await fetch(`${API_BASE}/understand/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        variable: request.variable,
        start_year: request.start_year,
        end_year: request.end_year,
        region_id: request.region_id,
        compare_region_id: request.compare_region_id,
      }),
    })
    if (!response.ok) return
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `earthtrend-${request.variable}-report.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  const data = explanation.data

  return (
    <>
      <div className="mb-4 flex justify-end">
        <button
          type="button"
          onClick={() => {
            setRequest(buildRequest(state))
            setOpen(true)
          }}
          className="inline-flex items-center gap-2 rounded-full bg-gold px-4 py-2 text-sm font-semibold text-navy"
        >
          <Sparkles size={16} aria-hidden="true" />
          Explain with AI
        </button>
      </div>
      {open ? (
        <div className="fixed inset-0 z-[70] flex items-end justify-center bg-black/60 p-4 sm:items-center" onClick={() => setOpen(false)}>
          <article
            role="dialog"
            aria-modal="true"
            aria-labelledby="explain-title"
            className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-line bg-navy p-5 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 id="explain-title" className="font-display text-2xl font-bold">
                  Explain with AI
                </h2>
                <p className="mt-1 text-sm text-muted">{data?.action ?? 'This explanation follows the page you are on.'}</p>
              </div>
              <button type="button" className="rounded-full border border-line p-2" aria-label="Close explanation" onClick={() => setOpen(false)}>
                <X size={16} />
              </button>
            </div>
            {explanation.isLoading ? <p className="mt-4 text-sm text-muted">Reading the calculated results…</p> : null}
            {explanation.isError ? (
              <p className="mt-4 text-sm text-gold">
                {explanation.error instanceof ApiRequestError ? explanation.error.message : 'The explanation could not be loaded.'}
              </p>
            ) : null}
            {data ? (
              <div className="mt-4 space-y-4 text-sm leading-6">
                {data.answer ? (
                  <section>
                    <h3 className="font-display text-base font-semibold text-gold">AI interpretation</h3>
                    <p className="mt-2">{data.answer}</p>
                  </section>
                ) : null}
                <details className="rounded-xl border border-line bg-surface p-3" open={!data.answer}>
                  <summary className="cursor-pointer font-display font-semibold">Calculated explanation</summary>
                  <p className="mt-2">{data.manual}</p>
                </details>
                {data.notice ? <p className="text-xs text-muted">{data.notice}</p> : null}
                <div className="space-y-2">
                  {messages.map((message, index) => (
                    <p key={`${message.role}-${index}`} className={message.role === 'user' ? 'text-ink' : 'text-muted'}>
                      <span className="text-gold">{message.role === 'user' ? 'You' : 'AI'}: </span>
                      {message.text}
                    </p>
                  ))}
                </div>
                <form className="flex flex-col gap-2 sm:flex-row" onSubmit={ask}>
                  <input
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    maxLength={800}
                    placeholder="Ask about this page"
                    className="w-full rounded-xl border border-line bg-navy px-3 py-2 text-sm"
                  />
                  <button type="submit" className="rounded-full bg-gold px-4 py-2 text-sm font-semibold text-navy" disabled={followUp.isPending}>
                    {followUp.isPending ? 'Asking…' : 'Ask'}
                  </button>
                </form>
                {followUp.isError ? <p className="text-sm text-gold">The question could not be sent. The calculated explanation is unchanged.</p> : null}
                <button type="button" onClick={() => void download()} className="rounded-full border border-line px-4 py-2 text-sm">
                  Download calculated report
                </button>
              </div>
            ) : null}
          </article>
        </div>
      ) : null}
    </>
  )
}

function buildRequest(state: ReturnType<typeof useCase>): ActionRequest {
  const start_year = state.file?.start_year ?? 2001
  const end_year = state.file?.end_year ?? 2025
  const base = {
    variable: state.variable,
    start_year,
    end_year,
  }
  if (state.section === 'compare') {
    const paired = state.compareA && state.compareB && state.compareA !== state.compareB
    return {
      ...base,
      page: 'compare',
      region_id: state.compareA,
      compare_region_id: paired ? state.compareB : null,
      map_mode: null,
      year: null,
    }
  }
  if (state.section === 'fingerprint') {
    return {
      ...base,
      page: 'fingerprint',
      region_id: state.hoverRegionId ?? state.selectedRegionId,
      compare_region_id: null,
      map_mode: null,
      year: null,
    }
  }
  if (state.section === 'map') {
    return {
      ...base,
      page: 'map',
      region_id: state.selectedRegionId,
      compare_region_id: null,
      map_mode: state.mapMode,
      year: state.mapMode === 'year' ? state.year : null,
    }
  }
  return {
    ...base,
    page: state.section,
    region_id: null,
    compare_region_id: null,
    map_mode: null,
    year: null,
  }
}
