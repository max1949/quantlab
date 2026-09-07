/** Soft-retired legacy paper_orders panel — no new order CTA. */
import { Link } from "react-router-dom";

export default function PaperExecutionPanel(_props: {
  factorId?: string | null;
  symbol?: string;
  projectId?: string;
} = {}) {
  return (
    <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-sm dark:border-amber-900 dark:bg-amber-950/30">
      <p className="font-medium text-amber-900 dark:text-amber-100">旧版模拟下单已关闭</p>
      <p className="mt-1 text-amber-800 dark:text-amber-200">
        paper_orders / QMT / vn.py 不再接受新订单。请使用证据系统中的正式模拟（PaperRun）。历史订单仅供审计查询。
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to="/evidence" className="btn-primary text-sm">
          证据系统 →
        </Link>
        <Link to="/paper" className="btn text-sm">
          正式模拟交易 →
        </Link>
      </div>
    </div>
  );
}
