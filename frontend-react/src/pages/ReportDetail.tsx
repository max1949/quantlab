import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getReport, shareReport, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { ErrorBox, GradeBadge, PageTitle, Spinner } from "../components/ui";

export default function ReportDetail() {
  const { id = "" } = useParams();
  const notify = useUi((s) => s.notify);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const report = useQuery({ queryKey: ["report", id], queryFn: () => getReport(id) });

  const share = useMutation({
    mutationFn: () => shareReport(id),
    onSuccess: (res) => {
      void trackEvent("share_created", { report: id });
      const url = `${window.location.origin}/app/share/${res.token}`;
      setShareUrl(url);
      notify("分享卡片已生成!", "success");
    },
    onError: (e) => notify(apiErrorMessage(e, "生成分享失败"), "error"),
  });

  if (report.isLoading) return <Spinner />;
  if (report.isError)
    return <ErrorBox message={apiErrorMessage(report.error, "报告不存在")} />;

  const r = report.data!;

  const sections: { title: string; body: string }[] = [
    { title: "研究假设", body: r.hypothesis },
    { title: "研究方法", body: r.methodology },
    { title: "结果", body: r.result },
    { title: "风险分析", body: r.risk_analysis },
    { title: "改进建议", body: r.improvement_suggestion },
  ];

  async function copyLink() {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    notify("链接已复制, 去分享吧!", "success");
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title={r.title} subtitle={r.summary} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <GradeBadge grade={r.grade} />
        <span className="badge">标的 {r.symbol}</span>
        <span className="badge">因子 v{r.factor_version}</span>
        {r.project_id && (
          <Link to={`/projects/${r.project_id}`} className="badge text-brand-600">
            ← 所属项目
          </Link>
        )}
      </div>

      <div className="space-y-4">
        {sections
          .filter((s) => s.body)
          .map((s) => (
            <div key={s.title} className="card">
              <h3 className="font-semibold text-slate-800">{s.title}</h3>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
                {s.body}
              </p>
            </div>
          ))}
      </div>

      {/* 分享 */}
      <div className="mt-6 card bg-brand-50/40">
        <h3 className="font-semibold text-slate-800">📣 分享你的研究</h3>
        <p className="mt-1 text-sm text-slate-500">
          生成一张公开分享卡片, 朋友点开就能看到你的研究成果 (免登录)。
        </p>
        {shareUrl ? (
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <input className="input flex-1" value={shareUrl} readOnly />
            <button className="btn-primary" onClick={copyLink}>
              复制链接
            </button>
            <a
              className="btn-ghost"
              href={shareUrl}
              target="_blank"
              rel="noreferrer"
            >
              预览
            </a>
          </div>
        ) : (
          <button
            className="btn-primary mt-3"
            disabled={share.isPending}
            onClick={() => share.mutate()}
          >
            {share.isPending ? "生成中…" : "生成分享卡片"}
          </button>
        )}
      </div>
    </div>
  );
}
