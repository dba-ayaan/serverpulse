import { useCallback, useEffect, useState } from "react";
import {
  Activity, Cpu, Database, HardDrive, LayoutDashboard,
  Server, ShieldCheck, Wifi, RefreshCw, Clock,
} from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";

import { getServers } from "./lib/api";
import type { Server as ServerInfo } from "./lib/api";
import { getHistory, getSummary } from "./lib/monitoring";
import type { MetricsSummary } from "./lib/monitoring";
import "./App.css";

type MetricName = "cpu" | "memory" | "disk";
type HistoryPoint = {
  time: string;
  timestamp: number;
  value: number;
};

const emptySummary: MetricsSummary = {
  cpu: [], memory: [], disk: [], up: [],
};

const metricOptions: {
  id: MetricName;
  label: string;
  icon: typeof Cpu;
}[] = [
  { id: "cpu", label: "CPU", icon: Cpu },
  { id: "memory", label: "Memory", icon: Database },
  { id: "disk", label: "Disk", icon: HardDrive },
];

const ranges = [
  { label: "1H", hours: 1 },
  { label: "6H", hours: 6 },
  { label: "24H", hours: 24 },
  { label: "7D", hours: 168 },
];

function currentValue(
  values: MetricsSummary,
  metric: MetricName,
): number {
  const results = values[metric];
  if (!results.length) return 0;

  return results.reduce(
    (sum, item) => sum + Number(item.value[1]),
    0,
  ) / results.length;
}

function App() {
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [serverId, setServerId] = useState<number | null>(null);
  const [summary, setSummary] = useState(emptySummary);
  const [metric, setMetric] = useState<MetricName>("cpu");
  const [hours, setHours] = useState(1);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const serverData = await getServers();
      setServers(serverData);

      const selectedId =
        serverId && serverData.some(s => s.id === serverId)
          ? serverId
          : serverData[0]?.id;

      if (!selectedId) {
        setServerId(null);
        setSummary(emptySummary);
        setHistory([]);
        setError("");
        return;
      }

      setServerId(selectedId);

      const [summaryData, historyData] = await Promise.all([
        getSummary(selectedId),
        getHistory(metric, selectedId, hours),
      ]);

      setSummary(summaryData);

      const points = historyData.results.flatMap(series =>
        series.values.map(([timestamp, value]) => ({
          timestamp,
          time: new Date(timestamp * 1000).toLocaleTimeString(
            [],
            { hour: "2-digit", minute: "2-digit" },
          ),
          value: Number(value),
        })),
      );

      points.sort((a, b) => a.timestamp - b.timestamp);
      setHistory(points);
      setLastUpdated(new Date());
      setError("");
    } catch {
      setError("Unable to load metrics. Check FastAPI and Prometheus.");
    } finally {
      setLoading(false);
    }
  }, [serverId, metric, hours]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const online = summary.up.filter(
    item => Number(item.value[1]) === 1,
  ).length;

  const cpu = currentValue(summary, "cpu");
  const memory = currentValue(summary, "memory");
  const disk = currentValue(summary, "disk");

  const cards = [
    { label: "CPU UTILIZATION", value: cpu, icon: Cpu },
    { label: "MEMORY UTILIZATION", value: memory, icon: Database },
    { label: "DISK UTILIZATION", value: disk, icon: HardDrive },
  ];

  const selectedMetric = metricOptions.find(
    item => item.id === metric,
  )!;

  const formatTime = (timestamp: number) =>
    new Date(timestamp * 1000).toLocaleString();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Activity size={22} /></div>
          <div>
            <strong>ServerPulse</strong>
            <span>INFRASTRUCTURE INTELLIGENCE</span>
          </div>
        </div>

        <div className="nav-label">MONITORING</div>
        <div className="nav-item active">
          <LayoutDashboard size={18} /> Overview
        </div>
        <div className="nav-item">
          <Server size={18} /> Server inventory
        </div>
        <div className="nav-item">
          <Activity size={18} /> Performance
        </div>
        <div className="nav-item">
          <ShieldCheck size={18} /> Alerts
        </div>

        <div className="sidebar-footer">
          <span className="live-dot" /> Monitoring engine active
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">MONITORING / OVERVIEW</div>
            <h1>Infrastructure Overview</h1>
            <p>Real-time visibility into your infrastructure.</p>
          </div>
          <button className="refresh-button" onClick={() => void refresh()}>
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <section className="welcome-panel">
          <div>
            <span className="eyebrow">SYSTEM OVERVIEW</span>
            <h2>Your infrastructure, at a glance.</h2>
            <p>Monitor server health and resource utilization centrally.</p>
          </div>
          <div className="welcome-status">
            <Wifi size={19} />
            {loading ? "CONNECTING" : "LIVE MONITORING"}
          </div>
        </section>

        <section className="section-heading">
          <div>
            <h2>Infrastructure metrics</h2>
            <p>Current Prometheus measurements</p>
          </div>
          <span className="update-label">AUTO-REFRESH · 30 SEC</span>
        </section>

        <section className="metric-grid">
          {cards.map(card => {
            const Icon = card.icon;
            return (
              <article className="metric-card" key={card.label}>
                <div className="metric-card-top">
                  <span>{card.label}</span>
                  <Icon size={19} />
                </div>
                <strong className="metric-value">
                  {card.value.toFixed(1)}%
                </strong>
                <p>Selected server</p>
              </article>
            );
          })}
          <article className="metric-card">
            <div className="metric-card-top">
              <span>SERVER AVAILABILITY</span>
              <Server size={19} />
            </div>
            <strong className="metric-value">
              {online}/{summary.up.length}
            </strong>
            <p>Online monitoring targets</p>
          </article>
        </section>

        <section className="panel inventory-panel">
          <div className="panel-heading">
            <div>
              <h2>Performance explorer</h2>
              <p>Historical metrics queried directly from Prometheus</p>
            </div>
            <span className="live-tag">PROMETHEUS</span>
          </div>

          <div className="filter-row">
            <label>
              <span>SERVER</span>
              <select
                value={serverId ?? ""}
                onChange={event => setServerId(Number(event.target.value))}
              >
                {servers.map(server => (
                  <option key={server.id} value={server.id}>
                    {server.name} · {server.environment}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>METRIC</span>
              <select
                value={metric}
                onChange={event => setMetric(event.target.value as MetricName)}
              >
                {metricOptions.map(item => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="range-control">
              <span>TIME RANGE</span>
              <div className="range-buttons">
                {ranges.map(range => (
                  <button
                    key={range.hours}
                    className={hours === range.hours ? "selected" : ""}
                    onClick={() => setHours(range.hours)}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="chart-summary">
            <div>
              <span className="eyebrow">{selectedMetric.label} HISTORY</span>
              <strong>{history.length ? `${history[history.length - 1].value.toFixed(2)}%` : "--"}</strong>
            </div>
            <span className="update-label">
              <Clock size={13} /> {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Loading"}
            </span>
          </div>

          <div className="chart">
            {history.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="historyFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#253044" strokeDasharray="3 3" />
                  <XAxis dataKey="time" stroke="#8290a5" tick={{ fontSize: 10 }} minTickGap={35} />
                  <YAxis domain={[0, 100]} stroke="#8290a5" tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip
                    labelFormatter={(_, payload) =>
                      payload?.[0]?.payload
                        ? formatTime(payload[0].payload.timestamp)
                        : ""
                    }
                    formatter={(value) => [`${Number(value).toFixed(2)}%`, selectedMetric.label]}
                    contentStyle={{ background: "#111b2c", border: "1px solid #334155" }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#38bdf8"
                    fill="url(#historyFill)"
                    strokeWidth={2}
                    dot={false}
                    name={selectedMetric.label}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-chart">
                {loading ? "Loading historical metrics..." : "No historical data available for this selection."}
              </div>
            )}
          </div>
        </section>

        <section className="panel inventory-panel">
          <div className="panel-heading">
            <div>
              <h2>Server inventory</h2>
              <p>Registered infrastructure</p>
            </div>
            <span className="inventory-count">{servers.length} SERVERS</span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>SERVER</th>
                  <th>HOSTNAME</th>
                  <th>ENVIRONMENT</th>
                  <th>EXPORTER PORT</th>
                  <th>CONFIGURATION</th>
                </tr>
              </thead>
              <tbody>
                {servers.map(server => (
                  <tr key={server.id}>
                    <td><strong>{server.name}</strong></td>
                    <td>{server.hostname}</td>
                    <td><span className="environment">{server.environment}</span></td>
                    <td>{server.exporter_port}</td>
                    <td>
                      <span className={server.enabled ? "enabled" : "disabled"}>
                        {server.enabled ? "Enabled" : "Disabled"}
                      </span>
                    </td>
                  </tr>
                ))}
                {!servers.length && (
                  <tr><td colSpan={5}>No servers registered.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <footer>ServerPulse · Infrastructure Monitoring Platform</footer>
      </main>
    </div>
  );
}

export default App;
