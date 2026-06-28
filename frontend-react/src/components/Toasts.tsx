import { useUi } from "../store/ui";

const styles: Record<string, string> = {
  success: "bg-emerald-600",
  error: "bg-rose-600",
  info: "bg-slate-800",
};

export default function Toasts() {
  const toasts = useUi((s) => s.toasts);
  const dismiss = useUi((s) => s.dismiss);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <button
          key={t.id}
          onClick={() => dismiss(t.id)}
          className={`max-w-xs rounded-lg px-4 py-2 text-left text-sm text-white shadow-lg ${
            styles[t.kind] ?? styles.info
          }`}
        >
          {t.message}
        </button>
      ))}
    </div>
  );
}
