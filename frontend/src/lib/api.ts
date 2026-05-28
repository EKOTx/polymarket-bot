/**
 * Axios API client — injects JWT from localStorage automatically.
 */

import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Inject bearer token on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  plan: string;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name: string | null;
  plan: string;
  is_active: boolean;
}

export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post<TokenResponse>("/auth/register", { email, password, full_name }).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }).then((r) => r.data),

  me: () => api.get<UserResponse>("/auth/me").then((r) => r.data),

  updateMe: (full_name: string) =>
    api.patch<UserResponse>("/auth/me", { full_name }).then((r) => r.data),
};

// ── Opportunities ─────────────────────────────────────────────────────────────

export interface Opportunity {
  id: number;
  opportunity_type: string;
  title: string;
  event_title: string;
  market_id: string | null;
  edge_pct: number;
  confidence: number;
  expected_value: number;
  suggested_size_usd: number;
  yes_bid: number | null;
  yes_ask: number | null;
  vig_pct: number | null;
  liquidity: number;
  market_count: number;
  warnings: string[];
  details: Record<string, unknown>;
  timestamp: string;
}

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScannerStatus {
  last_scan_id: number | null;
  last_scan_at: string | null;
  duration_seconds: number | null;
  markets_fetched: number;
  markets_priced: number;
  opportunities_found: number;
  is_running: boolean;
  error: string | null;
}

export const opportunitiesApi = {
  list: (params?: {
    opp_type?: string;
    min_edge?: number;
    min_confidence?: number;
    page?: number;
    page_size?: number;
  }) =>
    api.get<OpportunityListResponse>("/opportunities", { params }).then((r) => r.data),

  latest: (limit?: number) =>
    api.get<Opportunity[]>("/opportunities/latest", { params: { limit } }).then((r) => r.data),

  scannerStatus: () =>
    api.get<ScannerStatus>("/opportunities/scanner/status").then((r) => r.data),
};

// ── Trades ────────────────────────────────────────────────────────────────────

export interface PaperTrade {
  id: number;
  market_id: string;
  question: string;
  outcome: string;
  strategy: string;
  entry_price: number;
  exit_price: number | null;
  size_shares: number;
  cost_usd: number;
  realized_pnl: number | null;
  unrealized_pnl: number | null;
  status: string;
  resolution: string | null;
  opened_at: string;
  closed_at: string | null;
}

export interface Portfolio {
  balance: number;
  starting_balance: number;
  total_invested: number;
  realized_pnl: number;
  unrealized_pnl: number;
  open_positions: number;
  total_trades: number;
  timestamp?: string;
}

export interface PortfolioHistory {
  timestamp: string;
  balance: number;
  realized_pnl: number;
  unrealized_pnl: number;
}

export const tradesApi = {
  list: (params?: { status?: string; limit?: number }) =>
    api.get<PaperTrade[]>("/trades", { params }).then((r) => r.data),

  portfolio: () => api.get<Portfolio>("/trades/portfolio").then((r) => r.data),

  portfolioHistory: (limit?: number) =>
    api.get<PortfolioHistory[]>("/trades/portfolio/history", { params: { limit } }).then((r) => r.data),
};

// ── Alerts ────────────────────────────────────────────────────────────────────

export interface AlertConfig {
  discord_configured: boolean;
  slack_configured: boolean;
  min_edge_pct: number;
  cooldown_minutes: number;
  digest_hour: number;
}

export interface AlertTestResult {
  discord: boolean | null;
  slack: boolean | null;
}

export const alertsApi = {
  config: () => api.get<AlertConfig>("/alerts/config").then((r) => r.data),
  test: () => api.post<AlertTestResult>("/alerts/test").then((r) => r.data),
};
