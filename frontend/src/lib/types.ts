export type Summary = {
  month_to_date_cost: number
  forecast_cost: number
  month_over_month_change: number
  open_recommendations: number
  potential_monthly_savings: number
  currency: string
  data_mode: 'demo' | 'live'
}

export type TrendPoint = { date: string; cost: number }
export type SpendGroup = { name: string; cost: number }
export type SavingsCategory = { category: string; monthly_savings: number }

export type SyncStatus = {
  provider: string
  status: string
  records_imported: number
  source: string
  finished_at: string | null
}

export type Dashboard = {
  summary: Summary
  trend: TrendPoint[]
  by_provider: SpendGroup[]
  by_service: SpendGroup[]
  savings_by_category: SavingsCategory[]
  sync_status: SyncStatus[]
}

export type Recommendation = {
  id: number
  provider: string
  account_scope: string
  category: string
  title: string
  rationale: string
  resource_name: string | null
  monthly_savings: number
  confidence: 'high' | 'medium' | 'low'
  status: 'open' | 'in_review' | 'accepted' | 'dismissed'
  evidence: Record<string, unknown>
}
