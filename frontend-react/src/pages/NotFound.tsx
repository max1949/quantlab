import { Link } from "react-router-dom";
import { useLocale } from "../store/locale";

export default function NotFound() {
  const { dict } = useLocale();
  const t = dict.notFoundPage;
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-3 py-20 text-center">
      <p className="text-5xl font-bold text-slate-300">404</p>
      <p className="text-slate-500">{t.message}</p>
      <Link to="/app" className="btn-primary mt-2">
        {t.back}
      </Link>
    </div>
  );
}
