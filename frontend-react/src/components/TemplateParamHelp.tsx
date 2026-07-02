import type { ParamSpec } from "../api/types";

type Props = {
  param: ParamSpec;
  value: number;
};

export default function TemplateParamHelp({ param, value }: Props) {
  const help = param.help;
  if (!help) return null;

  const mid = (param.min + param.max) / 2;
  let rangeHint = help.suggested;
  if (value <= mid * 0.55 && help.low_hint) rangeHint = help.low_hint;
  else if (value >= mid * 1.45 && help.high_hint) rangeHint = help.high_hint;

  return (
    <div className="mt-1.5 rounded-lg border border-slate-200 bg-white/80 px-3 py-2 text-xs text-slate-600 dark:border-slate-600 dark:bg-slate-900/50 dark:text-slate-300">
      <p>
        <span className="mr-1 font-medium text-brand-600 dark:text-brand-400">?</span>
        {help.tip}
      </p>
      {rangeHint && <p className="mt-1 text-slate-500 dark:text-slate-400">{rangeHint}</p>}
    </div>
  );
}

export function pickParamRangeHint(param: ParamSpec, value: number): string {
  const help = param.help;
  if (!help) return "";
  const mid = (param.min + param.max) / 2;
  if (value <= mid * 0.55 && help.low_hint) return help.low_hint;
  if (value >= mid * 1.45 && help.high_hint) return help.high_hint;
  return help.suggested;
}
