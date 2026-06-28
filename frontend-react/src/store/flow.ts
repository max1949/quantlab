import { create } from "zustand";

// 研究引导态: 驱动工作台/项目页的"你的下一步"分步引导。
// 仅存内存即可 (刷新后由后端 next-step/graph 重新推导)。
export type FlowStep = "factor" | "backtest" | "validation" | "report" | "share";

interface FlowState {
  currentProjectId: string | null;
  currentFactorId: string | null;
  done: Record<FlowStep, boolean>;
  setProject: (projectId: string, factorId?: string | null) => void;
  markDone: (step: FlowStep) => void;
  reset: () => void;
}

const emptyDone = (): Record<FlowStep, boolean> => ({
  factor: false,
  backtest: false,
  validation: false,
  report: false,
  share: false,
});

export const useFlow = create<FlowState>((set) => ({
  currentProjectId: null,
  currentFactorId: null,
  done: emptyDone(),
  setProject(projectId, factorId = null) {
    set({
      currentProjectId: projectId,
      currentFactorId: factorId,
      done: { ...emptyDone(), factor: Boolean(factorId) },
    });
  },
  markDone(step) {
    set((s) => ({ done: { ...s.done, [step]: true } }));
  },
  reset() {
    set({ currentProjectId: null, currentFactorId: null, done: emptyDone() });
  },
}));
