import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export default function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-b from-white to-brand-50 px-4 py-10 dark:from-slate-950 dark:to-slate-900">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 text-base font-bold text-white">
            Q
          </span>
          <span className="text-xl font-semibold">QuantLab AI</span>
        </Link>
        <div className="card">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          <div className="mt-5">{children}</div>
        </div>
      </div>
    </div>
  );
}
