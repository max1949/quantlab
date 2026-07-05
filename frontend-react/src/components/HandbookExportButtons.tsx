import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { downloadBeginnerHandbookPdf } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { openBeginnerHandbookPrint } from "../lib/handbook";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";

type Props = {
  className?: string;
  compact?: boolean;
};

export default function HandbookExportButtons({ className = "", compact = false }: Props) {
  const h = useLocale((s) => s.dict.beginnerHandbook);
  const notify = useUi((s) => s.notify);

  const download = useMutation({
    mutationFn: () => downloadBeginnerHandbookPdf(),
    onError: (e) => notify(apiErrorMessage(e, h.downloadFail), "error"),
  });

  if (compact) {
    return (
      <div className={`flex flex-wrap gap-2 ${className}`}>
        <Link to="/handbook" className="btn text-xs">
          {h.printPdf}
        </Link>
        <button
          type="button"
          className="btn text-xs"
          disabled={download.isPending}
          onClick={() => download.mutate()}
        >
          {download.isPending ? h.downloading : h.downloadPdf}
        </button>
      </div>
    );
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      <Link to="/handbook" className="btn text-xs">
        {h.title} →
      </Link>
      <button type="button" className="btn text-xs" onClick={() => openBeginnerHandbookPrint()}>
        {h.printPdf}
      </button>
      <button
        type="button"
        className="btn-primary text-xs"
        disabled={download.isPending}
        onClick={() => download.mutate()}
      >
        {download.isPending ? h.downloading : h.downloadPdf}
      </button>
    </div>
  );
}
