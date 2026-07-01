import { useCallback, useEffect, useState } from "react";
import { fetchCaptcha } from "../api/endpoints";
import { useLocale } from "../store/locale";

export default function CaptchaField({
  answer,
  onAnswer,
  token: _token,
  onToken,
}: {
  answer: string;
  onAnswer: (v: string) => void;
  token: string;
  onToken: (v: string) => void;
}) {
  const t = useLocale((s) => s.dict.auth);
  const [svg, setSvg] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await fetchCaptcha();
      if (data.token && data.svg) {
        onToken(data.token);
        setSvg(data.svg);
        onAnswer("");
      }
    } catch {
      setSvg("");
    }
  }, [onAnswer, onToken]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!svg) return null;

  return (
    <div>
      <label className="label">{t.captchaLabel}</label>
      <div className="flex items-center gap-2">
        <div
          className="shrink-0 overflow-hidden rounded-lg ring-1 ring-slate-200 dark:ring-slate-600"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
        <input
          className="input flex-1 font-mono uppercase"
          value={answer}
          onChange={(e) => onAnswer(e.target.value)}
          placeholder={t.captchaPlaceholder}
          autoComplete="off"
          required
        />
        <button type="button" className="btn-ghost shrink-0" onClick={() => void load()}>
          {t.captchaRefresh}
        </button>
      </div>
    </div>
  );
}
