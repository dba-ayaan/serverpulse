import { api } from "./api";

export interface HistoryResponse {
  metric: string;
  server_id: number | null;
  hours: number;
  step: number;
  results: Array<{
    metric: Record<string, string>;
    values: [number, string][];
  }>;
}

export interface SummaryResult {
  metric: Record<string, string>;
  value: [number, string];
}

export interface MetricsSummary {
  cpu: SummaryResult[];
  memory: SummaryResult[];
  disk: SummaryResult[];
  up: SummaryResult[];
}

export async function getHistory(
  metric: string,
  serverId: number,
  hours: number,
): Promise<HistoryResponse> {
  const step = hours <= 1 ? 15 : hours <= 6 ? 60 : hours <= 24 ? 300 : 900;

  const { data } = await api.get(
    `/api/v1/metrics/history/${metric}`,
    { params: { server_id: serverId, hours, step } },
  );

  return data;
}

export async function getSummary(
  serverId: number,
): Promise<MetricsSummary> {
  const { data } = await api.get(
    "/api/v1/metrics/summary",
    { params: { server_id: serverId } },
  );

  return data;
}
