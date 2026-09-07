/** Research / Evidence OS API client — thin wrap of /research-os. */
import { api } from "./client";

export async function getDoctrine() {
  const { data } = await api.get("/research-os/doctrine");
  return data;
}

export async function listOsStrategies() {
  const { data } = await api.get("/research-os/strategies");
  return data as { items: Array<Record<string, unknown>>; n: number };
}

export async function getOsStrategy(strategyId: string) {
  const { data } = await api.get(`/research-os/strategies/${encodeURIComponent(strategyId)}`);
  return data;
}

export async function runOsEvidence(params: {
  strategy_id?: string;
  instrument?: string;
  bars?: number;
}) {
  const { data } = await api.post("/research-os/evidence/run", null, { params });
  return data;
}

export async function listOsExperiments(limit = 50) {
  const { data } = await api.get("/research-os/experiments", { params: { limit } });
  return data;
}

export async function getOsExperiment(id: string) {
  const { data } = await api.get(`/research-os/experiments/${encodeURIComponent(id)}`);
  return data;
}

export async function reproduceOsExperiment(id: string) {
  const { data } = await api.post(`/research-os/experiments/${encodeURIComponent(id)}/reproduce`);
  return data;
}

export async function runOsFactorSignPaper(params: {
  strategy_id?: string;
  instrument?: string;
  bars?: number;
}) {
  const { data } = await api.post("/research-os/paper/factor-sign", null, { params });
  return data;
}

export async function getOsShadow(params?: {
  strategy_id?: string;
  instrument?: string;
  bars?: number;
}) {
  const { data } = await api.get("/research-os/shadow", { params });
  return data;
}

export async function getOsGovernor() {
  const { data } = await api.get("/research-os/portfolio/governor");
  return data;
}

export async function getOsDna(strategyId: string) {
  const { data } = await api.get(`/research-os/dna/${encodeURIComponent(strategyId)}`);
  return data;
}

export async function getOsLiveReadiness() {
  const { data } = await api.get("/research-os/live-readiness");
  return data;
}

export async function diffOsStrategies(a: string, b: string) {
  const { data } = await api.get(
    `/research-os/strategies/diff/${encodeURIComponent(a)}/${encodeURIComponent(b)}`,
  );
  return data;
}
