import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startTemplate, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { FIRST_PROJECT_WELCOME_KEY } from "./onboardingFocus";
import { useFlow } from "../store/flow";
import { useUi } from "../store/ui";

type Options = {
  startedMessage: string;
  failMessage: string;
  from?: string;
};

export function useStartTemplateFlow({ startedMessage, failMessage, from }: Options) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const notify = useUi((s) => s.notify);
  const setProject = useFlow((s) => s.setProject);

  return useMutation({
    mutationFn: (code: string) => startTemplate(code, true),
    onSuccess: (res) => {
      void trackEvent("template_start", { template: res.template_code, one_click: true, from: from ?? "direct" });
      setProject(res.project_id, res.factor_id);
      sessionStorage.setItem(FIRST_PROJECT_WELCOME_KEY, res.project_id);
      void qc.invalidateQueries({ queryKey: ["projects"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      notify(startedMessage, "success");
      navigate(`/projects/${res.project_id}`);
    },
    onError: (err) => notify(apiErrorMessage(err, failMessage), "error"),
  });
}
