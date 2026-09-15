import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, setFactorGymTestToken } from "../api/client";
import { isFactorGymAccessAllowed, type FactorGymStatus } from "../lib/factorGymAccess";

type Step = "idea" | "memory" | "predict" | "result";

type MemoryCheck = {
  classification: string;
  what_we_already_know: string;
  next_best_research_action: string;
  worth_continuing: boolean;
  block_rerun: boolean;
  summary_counts: {
    total: number;
    failed: number;
    some_signal: number;
    forward_or_validated: number;
  };
  dominant_failure_codes: Record<string, number>;
  matches_preview: Array<Record<string, unknown>>;
  hit_id: string | null;
};

type IdeaOut = {
  hypothesis_id: string;
  research_question: string;
  economic_rationale: string;
  prompt: string;
  rule_plain?: string;
  memory_check?: MemoryCheck;
};

type ResultOut = {
  status: string;
  status_label?: string;
  why: string;
  next_best_action: string;
  primary_failure: string | null;
  experiment_id: string;
  save_feedback?: string;
  rule_plain?: string;
  metrics_folded?: Record<string, unknown>;
};

type VaultCard = {
  factor_id: string;
  version: number;
  status: string;
  status_plain: string;
  hypothesis_plain: string;
  why_status: string;
  one_next_action: string | null;
  scientific_protocol_version: string;
  lineage: {
    parent_factor_id: string | null;
    derived_from: string | null;
    revalidation_of: string | null;
  };
  failure_codes: string[];
  assetization?: { FACTORIZATION_ASSETIZED: boolean };
};

const CLASS_LABEL: Record<string, string> = {
  EXACT_DUPLICATE: "和以前某次研究几乎完全一样",
  NEAR_DUPLICATE: "和以前研究很像",
  KNOWN_FAILURE_PATH: "类似方向以前经常失败",
  KNOWN_SUCCESS_PATH: "类似方向以前有过线索",
  NOVEL_VARIANT: "这是相对新的方向",
};

/**
 * Factor Gym First Value path — novice plain language, one next action.
 */
export default function FactorGym() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sessionId] = useState(() => `HS-${Math.random().toString(36).slice(2, 10).toUpperCase()}`);
  const [pageLabel, setPageLabel] = useState("Factor Gym（测试版）");
  const [testEntry, setTestEntry] = useState(true);
  const [step, setStep] = useState<Step>("idea");
  const [idea, setIdea] = useState("");
  const [draft, setDraft] = useState<IdeaOut | null>(null);
  const [memory, setMemory] = useState<MemoryCheck | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showRule, setShowRule] = useState(false);
  const [direction, setDirection] = useState<"positive" | "negative" | "unclear">("unclear");
  const [result, setResult] = useState<ResultOut | null>(null);
  const [vault, setVault] = useState<VaultCard | null>(null);
  const [showMetrics, setShowMetrics] = useState(false);
  const [showVaultPro, setShowVaultPro] = useState(false);
  const [acked, setAcked] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function emitEvent(event: string, payload: Record<string, unknown> = {}) {
    try {
      await api.post("/factor-gym/events", { event, payload: { session_id: sessionId, ...payload } });
    } catch {
      /* telemetry must not block path */
    }
  }

  useEffect(() => {
    const tok = searchParams.get("test_token");
    if (tok) {
      setFactorGymTestToken(tok);
      const next = new URLSearchParams(searchParams);
      next.delete("test_token");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get<FactorGymStatus>("/factor-gym/status");
        const open = isFactorGymAccessAllowed(data);
        if (!open) {
          setError(data.denied_detail || "请先登录后使用 Factor Gym（测试版）。");
          setTestEntry(false);
          return;
        }
        setTestEntry(Boolean(data.test_entry ?? data.open_beta ?? true));
        setPageLabel(data.label || "Factor Gym（测试版）");
        if (data.test_entry || data.open_beta) {
          await emitEvent("factor_gym_test_entry_opened", { mode: data.mode });
        } else {
          await emitEvent("factor_gym_opened");
        }
      } catch {
        setError("没法确认入口状态，请稍后再试");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- once per mount after token capture
  }, []);

  async function submitIdea() {
    setError(null);
    setBusy(true);
    try {
      // Canonical gate is API require_gym_access / FACTOR_GYM_ACCESS_ALLOWED.
      // Never re-check status.enabled here (global OFF ≠ access denied).
      const { data } = await api.post<IdeaOut>("/factor-gym/ideas", { idea });
      await api.post("/factor-gym/hypotheses/seal", {
        hypothesis_id: data.hypothesis_id,
        research_question: data.research_question,
        economic_rationale: data.economic_rationale,
        expected_direction: "unknown",
      });
      setDraft(data);
      setMemory(data.memory_check ?? null);
      setStep("memory");
      await emitEvent("idea_submitted", { idea_len: idea.length });
      await emitEvent("hypothesis_committed", { hypothesis_id: data.hypothesis_id });
      await emitEvent("memory_check_seen", {
        classification: data.memory_check?.classification,
      });
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string }; status?: number } })?.response
        ?.data?.detail;
      const http = (e as { response?: { status?: number } })?.response?.status;
      if (http === 403 || http === 503) {
        setError(typeof detail === "string" && detail.trim() ? detail : "请先登录后使用 Factor Gym（测试版）。");
      } else {
        setError(String(detail || "没法开始，请稍后再试"));
      }
    } finally {
      setBusy(false);
    }
  }

  async function continueAfterMemory() {
    if (!memory?.hit_id) {
      setStep("predict");
      await emitEvent("prediction_committed", { stage: "entered" });
      return;
    }
    setBusy(true);
    try {
      await api.post("/factor-gym/memory-decision", {
        hit_id: memory.hit_id,
        decision: "continue",
        hypothesis_id: draft?.hypothesis_id,
      });
      setStep("predict");
      await emitEvent("prediction_committed", { stage: "entered" });
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "没法继续";
      setError(String(msg));
    } finally {
      setBusy(false);
    }
  }

  async function runExperiment() {
    if (!draft) return;
    setError(null);
    setBusy(true);
    try {
      await emitEvent("prediction_committed", { predicted_direction: direction });
      await emitEvent("experiment_started");
      const { data } = await api.post<ResultOut>("/factor-gym/experiments/run", {
        hypothesis_id: draft.hypothesis_id,
        predicted_direction: direction,
        predicted_strength: "moderate",
        memory_hit_id: memory?.hit_id ?? undefined,
        force_despite_duplicate: false,
      });
      setResult(data);
      setAcked(false);
      setVault(null);
      setStep("result");
      await emitEvent("experiment_completed", {
        experiment_id: data.experiment_id,
        status: data.status,
      });
      await emitEvent("next_action_seen", { experiment_id: data.experiment_id });
      const fid = data.metrics_folded?.factor_id;
      if (typeof fid === "string" && fid) {
        try {
          const v = await api.get<VaultCard>(`/factor-gym/vault/${fid}`);
          setVault(v.data);
        } catch {
          /* vault optional for path */
        }
      }
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
      if (detail && typeof detail === "object" && detail !== null && "message" in detail) {
        setError(String((detail as { message?: string }).message));
      } else {
        setError(String(detail || "实验没有跑完，请稍后再试"));
      }
    } finally {
      setBusy(false);
    }
  }

  async function acknowledgeResult() {
    if (!result) return;
    await emitEvent("result_acknowledged", { experiment_id: result.experiment_id });
    setAcked(true);
  }

  async function revalidateAsset() {
    if (!vault) return;
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<{
        new_factor_id: string;
        new_version: number;
        why: string;
        next_best_action: string;
      }>(`/factor-gym/vault/${vault.factor_id}/revalidate`);
      const v = await api.get<VaultCard>(`/factor-gym/vault/${data.new_factor_id}`);
      setVault(v.data);
      setResult((prev) =>
        prev
          ? {
              ...prev,
              why: data.why,
              next_best_action: data.next_best_action,
              save_feedback: `已重新验证：保存为 ${data.new_factor_id} v${data.new_version}（旧证据保留）`,
            }
          : prev,
      );
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "重新验证失败";
      setError(String(msg));
    } finally {
      setBusy(false);
    }
  }

  async function startSecond() {
    await emitEvent("second_experiment_started", {
      from_experiment: result?.experiment_id,
    });
    setIdea("");
    setDraft(null);
    setMemory(null);
    setResult(null);
    setAcked(false);
    setShowMetrics(false);
    setShowHistory(false);
    setShowRule(false);
    setStep("idea");
  }

  const counts = memory?.summary_counts;
  const topFail = memory ? Object.keys(memory.dominant_failure_codes || {})[0] : null;

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <h1 className="font-serif text-3xl tracking-tight text-slate-900 dark:text-slate-100">
        {pageLabel}
      </h1>
      {testEntry && (
        <p className="mt-2 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          测试版 · 不是正式发布 · 用于收集真实研究反馈
        </p>
      )}
      <p className="mt-2 text-sm text-slate-500">用一句话提出想法，一步一步做完第一次规范研究。</p>

      {error && (
        <div className="mt-4 rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </div>
      )}

      {step === "idea" && (
        <section className="mt-10 space-y-4">
          <label className="block text-lg text-slate-800 dark:text-slate-200">
            你觉得市场里有什么规律？
          </label>
          <textarea
            className="min-h-[120px] w-full rounded border border-slate-300 bg-white p-3 text-base dark:border-slate-600 dark:bg-slate-900"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="例如：连续跌了几天的股票，是不是容易反弹？"
          />
          <button
            type="button"
            disabled={busy || idea.trim().length < 4}
            onClick={() => void submitIdea()}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
          >
            {busy ? "处理中…" : "下一步"}
          </button>
        </section>
      )}

      {step === "memory" && memory && draft && (
        <section className="mt-10 space-y-4">
          <h2 className="text-xl text-slate-900 dark:text-slate-100">我们以前研究过类似问题吗？</h2>
          <p className="text-base text-slate-800 dark:text-slate-200">{memory.what_we_already_know}</p>
          {counts && counts.total > 0 ? (
            <p className="text-sm text-slate-600 dark:text-slate-300">
              找到 {counts.total} 个相关研究
              {topFail ? `。最值得先避开的坑：和「${topFail === "SIZE_EXPOSURE" ? "小市值干扰" : topFail}」有关` : ""}
              。
            </p>
          ) : (
            <p className="text-sm text-slate-600">还没有很接近的历史记录，可以放心做第一次。</p>
          )}
          <div className="rounded border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950/40">
            <p className="text-xs text-amber-800 dark:text-amber-200">建议你现在怎么做</p>
            <p className="mt-1 text-base text-amber-950 dark:text-amber-100">
              {memory.next_best_research_action}
            </p>
          </div>
          <p className="text-sm text-slate-500">
            {CLASS_LABEL[memory.classification] || memory.classification}
          </p>
          <button
            type="button"
            className="text-sm text-slate-500 underline"
            onClick={() => setShowHistory((v) => !v)}
          >
            {showHistory ? "收起历史细节" : "查看历史研究（可选）"}
          </button>
          {showHistory && (
            <pre className="max-h-40 overflow-auto rounded bg-slate-100 p-3 text-xs dark:bg-slate-900">
              {JSON.stringify(memory.matches_preview ?? [], null, 2)}
            </pre>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={() => void continueAfterMemory()}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
          >
            继续这个研究
          </button>
        </section>
      )}

      {step === "predict" && draft && (
        <section className="mt-10 space-y-4">
          <p className="text-sm text-slate-600">当前想法</p>
          <p className="text-base text-slate-900 dark:text-slate-100">{draft.research_question}</p>
          <p className="text-sm text-slate-500">
            {draft.rule_plain || "系统已把你的想法转换成可测试规则。"}
          </p>
          <button
            type="button"
            className="text-sm text-slate-500 underline"
            onClick={() => setShowRule((v) => !v)}
          >
            {showRule ? "收起规则" : "查看规则（可选）"}
          </button>
          {showRule && (
            <p className="text-xs text-slate-500">
              完整技术规则保存在研究记录中；默认不必阅读。
            </p>
          )}
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
            先猜一猜结果，再看实验（这样更容易真正学会）
          </p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["positive", "会支持我的方向"],
                ["negative", "可能相反"],
                ["unclear", "不确定"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setDirection(k)}
                className={`rounded border px-3 py-1.5 text-sm ${
                  direction === k
                    ? "border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900"
                    : "border-slate-300 text-slate-700 dark:border-slate-600 dark:text-slate-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void runExperiment()}
            className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-40 dark:bg-slate-100 dark:text-slate-900"
          >
            {busy ? "实验中…" : "运行实验"}
          </button>
        </section>
      )}

      {step === "result" && result && (
        <section className="mt-10 space-y-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">结果</p>
            <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {result.status_label || result.status}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">为什么</p>
            <p className="mt-1 text-base text-slate-800 dark:text-slate-200">{result.why}</p>
          </div>
          <div className="rounded border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950/40">
            <p className="text-xs text-amber-800 dark:text-amber-200">下一步（只做这一件）</p>
            <p className="mt-1 text-base text-amber-950 dark:text-amber-100">{result.next_best_action}</p>
          </div>
          {result.save_feedback && (
            <p className="text-sm text-slate-600 dark:text-slate-300">{result.save_feedback}</p>
          )}
          {vault && (
            <div className="space-y-4 border-t border-slate-200 pt-6 dark:border-slate-700">
              <p className="text-xs uppercase tracking-wide text-slate-500">研究资产（Vault）</p>
              <div>
                <p className="text-xs text-slate-500">这个研究是什么</p>
                <p className="mt-1 text-base text-slate-800 dark:text-slate-200">
                  {vault.hypothesis_plain || draft?.research_question}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">当前状态</p>
                <p className="mt-1 text-lg font-medium text-slate-900 dark:text-slate-100">
                  {vault.status_plain}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500">为什么是这个状态</p>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{vault.why_status}</p>
              </div>
              {vault.one_next_action && (
                <div>
                  <p className="text-xs text-slate-500">下一步</p>
                  <p className="mt-1 text-sm text-slate-800 dark:text-slate-200">{vault.one_next_action}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-slate-500">历史</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {vault.factor_id} · v{vault.version}
                  {vault.lineage.derived_from ? ` · 来自 ${vault.lineage.derived_from}` : ""}
                  {vault.lineage.revalidation_of
                    ? ` · 重验自 ${vault.lineage.revalidation_of}`
                    : ""}
                </p>
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={() => void revalidateAsset()}
                className="rounded border border-slate-300 px-4 py-2 text-sm dark:border-slate-600"
              >
                {busy ? "验证中…" : "重新验证"}
              </button>
              <button
                type="button"
                className="ml-3 text-sm text-slate-500 underline"
                onClick={() => setShowVaultPro((v) => !v)}
              >
                {showVaultPro ? "收起专业数据" : "查看专业数据"}
              </button>
              {showVaultPro && (
                <pre className="overflow-auto rounded bg-slate-100 p-3 text-xs dark:bg-slate-900">
                  {JSON.stringify(
                    {
                      factor_id: vault.factor_id,
                      version: vault.version,
                      status: vault.status,
                      failure_codes: vault.failure_codes,
                      scientific_protocol_version: vault.scientific_protocol_version,
                      assetization: vault.assetization,
                      lineage: vault.lineage,
                    },
                    null,
                    2,
                  )}
                </pre>
              )}
            </div>
          )}
          {!acked ? (
            <button
              type="button"
              onClick={() => void acknowledgeResult()}
              className="rounded border border-slate-300 px-4 py-2 text-sm dark:border-slate-600"
            >
              我看懂了这次结果
            </button>
          ) : (
            <p className="text-sm text-emerald-700 dark:text-emerald-300">已记录：你理解了本次结果。</p>
          )}
          <button
            type="button"
            className="block text-sm text-slate-500 underline"
            onClick={() => setShowMetrics((v) => !v)}
          >
            {showMetrics ? "收起专业数据" : "查看实验专业数据"}
          </button>
          {showMetrics && (
            <pre className="overflow-auto rounded bg-slate-100 p-3 text-xs dark:bg-slate-900">
              {JSON.stringify(result.metrics_folded ?? {}, null, 2)}
            </pre>
          )}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void startSecond()}
              className="rounded bg-slate-900 px-4 py-2 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
            >
              按建议开始下一次研究
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
