import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-3 py-20 text-center">
      <p className="text-5xl font-bold text-slate-300">404</p>
      <p className="text-slate-500">页面不存在</p>
      <Link to="/app" className="btn-primary mt-2">
        回到工作台
      </Link>
    </div>
  );
}
