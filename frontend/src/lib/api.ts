import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
});

export interface Server {
  id: number;
  name: string;
  hostname: string;
  environment: string;
  exporter_port: number;
  enabled: boolean;
}

export interface MetricResult {
  metric: string;
  results: Array<{
    metric: Record<string, string>;
    value: [number, string];
  }>;
}

export const getServers = async (): Promise<Server[]> => {
  const { data } = await api.get("/api/v1/servers/");
  return data;
};

export const getMetric = async (
  name: string,
): Promise<MetricResult> => {
  const { data } = await api.get(`/api/v1/metrics/${name}`);
  return data;
};
