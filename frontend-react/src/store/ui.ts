import { create } from "zustand";

export interface Toast {
  id: number;
  message: string;
  kind: "success" | "error" | "info";
}

interface UiState {
  toasts: Toast[];
  notify: (message: string, kind?: Toast["kind"]) => void;
  dismiss: (id: number) => void;
}

let seq = 1;

export const useUi = create<UiState>((set) => ({
  toasts: [],
  notify(message, kind = "info") {
    const id = seq++;
    set((s) => ({ toasts: [...s.toasts, { id, message, kind }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3500);
  },
  dismiss(id) {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },
}));
