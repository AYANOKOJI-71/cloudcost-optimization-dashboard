import { useEffect, useMemo, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  CloudCog,
  Database,
  Gauge,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react'

import { TrendChart } from './components/TrendChart'
import { currency, percent, titleCase } from './lib/format'
import type { Dashboard, Recommendation } from './lib/types'

const providerColors: Record<string, string> = { aws: '#ffb666', azure: '#69b7ff' }

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [activeFilter, setActiveFilter] = useState<'open' | 'in_review' | 'all'>('open')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      setError('')
      const [dashboardResponse, recommendationResponse] = await Promise.all([
        fetch('/api/v1/dashboard'),
        fetch('/api/v1/recommendations'),
      ])
      if (!dashboardResponse.ok || !recommendationResponse.ok) throw new Error('Unable to reach the cost-intelligence API.')
      const [nextDashboard, nextRecommendations] = await Promise.all([
        dashboardResponse.json() as Promise<Dashboard>,
        recommendationResponse.json() as Promise<{ items: Recommendation[] }>,
      ])
      setDashboard(nextDashboard)
      setRecommendations(nextRecommendations.items)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load dashboard data.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { void loadData() }, [])

  const visibleRecommendations = useMemo(
    () => recommendations.filter((item) => activeFilter === 'all' || item.status === activeFilter),
    [activeFilter, recommendations],
  )

  const updateStatus = async (recommendation: Recommendation, status: Recommendation['status']) => {
    const response = await fetch(`/api/v1/recommendations/${recommendation.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    if (!response.ok) return
    setRecommendations((current) => current.map((item) => item.id === recommendation.id ? { ...item, status } : item))
    void loadData()
  }

  if (loading) return <main className="loading-screen"><LoaderCircle className="spin" size={24} /> Loading cost intelligence…</main>

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Gauge size={19} /></span><span>CloudCost<span className="brand-accent">IQ</span></span></div>
        <nav aria-label="Primary navigation">
          <a className="nav-item active" href="#overview"><Gauge size={17} /> Overview</a>
          <a className="nav-item" href="#recommendations"><Sparkles size={17} /> Opportunities <span>{dashboard?.summary.open_recommendations ?? 0}</span></a>
          <a className="nav-item" href="#spend"><CircleDollarSign size={17} /> Cost allocation</a>
          <a className="nav-item" href="#integrations"><CloudCog size={17} /> Integrations</a>
        </nav>
        <div className="sidebar-bottom"><div className="security-note"><ShieldCheck size={16} /><span>Read-only provider contracts<br /><strong>Credentials stay server-side</strong></span></div><div className="profile"><div className="profile-avatar">SR</div><div><strong>Sarowar H. Rony</strong><small>FinOps workspace</small></div></div></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div><p className="eyebrow">FINOPS CONTROL ROOM</p><h1>Make cloud spend <em>intentional.</em></h1></div>
          <div className="topbar-actions"><div className="demo-pill"><Database size={14} /> {dashboard?.summary.data_mode === 'demo' ? 'Local demo workspace' : 'Live provider data'}</div><button className="refresh-button" onClick={() => { setRefreshing(true); void loadData() }} aria-label="Refresh dashboard"><RefreshCw className={refreshing ? 'spin' : ''} size={17} /> Refresh</button></div>
        </header>

        {error && <div className="error-banner">{error}<button onClick={() => { setRefreshing(true); void loadData() }}>Try again</button></div>}

        <section id="overview" className="hero-grid">
          <article className="hero-card card"><div className="hero-card-header"><span className="eyebrow">MONTH-TO-DATE SPEND</span><span className="status-live"><i /> FRESH DATA</span></div><div className="metric-hero">{currency(dashboard?.summary.month_to_date_cost ?? 0)}</div><div className="metric-subtext"><span className={(dashboard?.summary.month_over_month_change ?? 0) > 0 ? 'up' : 'down'}>{(dashboard?.summary.month_over_month_change ?? 0) > 0 ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}{percent(dashboard?.summary.month_over_month_change ?? 0)}</span> versus prior month</div><TrendChart points={dashboard?.trend ?? []} /></article>
          <article className="forecast-card card"><div className="mini-icon orange"><TrendingUp size={19} /></div><p className="eyebrow">PROJECTED MONTH-END</p><div className="metric-secondary">{currency(dashboard?.summary.forecast_cost ?? 0)}</div><p>Based on observed daily run rate</p><div className="forecast-bar"><span /></div><small>Forecast keeps a 30-day baseline.</small></article>
          <article className="savings-card card"><div className="savings-orb"><Sparkles size={22} /></div><p className="eyebrow">ACTIONABLE SAVINGS</p><div className="metric-secondary">{currency(dashboard?.summary.potential_monthly_savings ?? 0)}<small>/mo</small></div><p>Across {dashboard?.summary.open_recommendations ?? 0} identified review opportunities.</p><a href="#recommendations">Explore savings map <ChevronRight size={15} /></a></article>
        </section>

        <section id="spend" className="split-grid">
          <article className="card allocation-card"><div className="section-heading"><div><p className="eyebrow">COST ALLOCATION</p><h2>Where spend is concentrated</h2></div><button className="subtle-button">This month</button></div><div className="allocation-rows">{(dashboard?.by_service ?? []).slice(0, 5).map((service, index, list) => <div className="allocation-row" key={service.name}><div className="allocation-name"><span className="service-rank">0{index + 1}</span><strong>{service.name}</strong></div><div className="allocation-bar"><span style={{ width: `${(service.cost / list[0].cost) * 100}%` }} /></div><span>{currency(service.cost)}</span></div>)}</div></article>
          <article className="card providers-card"><div className="section-heading"><div><p className="eyebrow">MULTI-CLOUD MIX</p><h2>Provider exposure</h2></div><CloudCog size={20} /></div><div className="provider-donut"><div className="donut-center"><strong>2</strong><span>providers</span></div></div><div className="provider-list">{(dashboard?.by_provider ?? []).map((provider) => <div key={provider.name}><span><i style={{ background: providerColors[provider.name] ?? '#8c96ac' }} />{provider.name === 'aws' ? 'Amazon Web Services' : 'Microsoft Azure'}</span><strong>{currency(provider.cost)}</strong></div>)}</div></article>
        </section>

        <section id="recommendations" className="recommendation-section"><div className="section-heading"><div><p className="eyebrow">OPTIMIZATION QUEUE</p><h2>Prioritized cost opportunities</h2></div><div className="filter-group" role="group" aria-label="Recommendation status filter">{(['open', 'in_review', 'all'] as const).map((filter) => <button key={filter} onClick={() => setActiveFilter(filter)} className={activeFilter === filter ? 'selected' : ''}>{filter === 'all' ? 'All' : titleCase(filter)}</button>)}</div></div><div className="recommendation-list">{visibleRecommendations.map((recommendation) => <article className="recommendation" key={recommendation.id}><div className="recommendation-symbol"><Sparkles size={17} /></div><div className="recommendation-copy"><div className="recommendation-title"><span className={`provider-badge ${recommendation.provider}`}>{recommendation.provider}</span><h3>{recommendation.title}</h3><span className={`confidence ${recommendation.confidence}`}>{recommendation.confidence} confidence</span></div><p>{recommendation.rationale}</p><small>{recommendation.resource_name} · {titleCase(recommendation.category)}</small></div><div className="recommendation-value"><strong>{currency(recommendation.monthly_savings)}<small>/mo</small></strong><span>Potential savings</span><div className="action-row">{recommendation.status === 'open' && <button onClick={() => void updateStatus(recommendation, 'in_review')}>Review</button>}{recommendation.status === 'in_review' && <button onClick={() => void updateStatus(recommendation, 'accepted')}><CheckCircle2 size={14} /> Accept</button>}<button className="more-button" aria-label={`More actions for ${recommendation.title}`}>•••</button></div></div></article>)}{visibleRecommendations.length === 0 && <div className="empty-state">No recommendations in this view.</div>}</div></section>

        <footer id="integrations" className="dashboard-footer"><div><ShieldCheck size={17} /><span><strong>Integration-safe by design.</strong> Live AWS and Azure synchronization remains disabled until explicit read-only credentials are configured.</span></div><a href="/metrics" target="_blank" rel="noreferrer">Open Prometheus metrics <ChevronRight size={15} /></a></footer>
      </section>
    </main>
  )
}
