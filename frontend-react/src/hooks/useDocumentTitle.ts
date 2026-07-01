import { useEffect } from "react";

/** 设置浏览器标签页标题, 组件卸载时恢复。 */
export function useDocumentTitle(title: string | undefined) {
  useEffect(() => {
    if (!title) return;
    const prev = document.title;
    document.title = title;
    return () => {
      document.title = prev;
    };
  }, [title]);
}
