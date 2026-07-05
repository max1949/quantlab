export type ReplicationBenchmark = {
  report_id: string;
  oos_sharpe: number | null;
  robustness_score: number | null;
  owner_username: string | null;
  symbol: string;
};

export const REPLICATION_BENCHMARK_PENDING_KEY = "quantlab-replication-benchmark-pending";

export function replicationBenchmarkKey(projectId: string) {
  return `quantlab-replication-benchmark-${projectId}`;
}

function parseBenchmark(raw: string | null): ReplicationBenchmark | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ReplicationBenchmark;
  } catch {
    return null;
  }
}

export function savePendingReplicationBenchmark(benchmark: ReplicationBenchmark): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(REPLICATION_BENCHMARK_PENDING_KEY, JSON.stringify(benchmark));
}

export function attachReplicationBenchmarkToProject(projectId: string): void {
  if (typeof window === "undefined") return;
  const pending = sessionStorage.getItem(REPLICATION_BENCHMARK_PENDING_KEY);
  if (!pending) return;
  sessionStorage.setItem(replicationBenchmarkKey(projectId), pending);
  sessionStorage.removeItem(REPLICATION_BENCHMARK_PENDING_KEY);
}

export function loadReplicationBenchmark(projectId: string): ReplicationBenchmark | null {
  if (typeof window === "undefined") return null;
  return parseBenchmark(sessionStorage.getItem(replicationBenchmarkKey(projectId)));
}

export function clearReplicationBenchmark(projectId: string): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(replicationBenchmarkKey(projectId));
}

export function replicationBenchmarkFromReport(report: {
  id: string;
  symbol: string;
  oos_sharpe?: number | null;
  robustness_score?: number | null;
  owner_username?: string | null;
}): ReplicationBenchmark {
  return {
    report_id: report.id,
    oos_sharpe: report.oos_sharpe ?? null,
    robustness_score: report.robustness_score ?? null,
    owner_username: report.owner_username ?? null,
    symbol: report.symbol,
  };
}
