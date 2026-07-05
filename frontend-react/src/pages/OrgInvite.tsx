import { useEffect } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  acceptOrgInvite,
  previewOrgInvite,
  previewOrgInvitePublic,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import {
  ORG_INVITE_ACCEPTED_ORG_KEY,
  ORG_INVITE_PENDING_KEY,
} from "../lib/onboardingFocus";
import OrgInviteIncubationPreview from "../components/OrgInviteIncubationPreview";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function OrgInvite() {
  const { token = "" } = useParams();
  const o = useLocale((s) => s.dict.orgLibrary);
  const i = useLocale((s) => s.dict.orgInviteIncubation);
  const user = useAuth((s) => s.user);
  const notify = useUi((s) => s.notify);
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();

  useEffect(() => {
    if (token) {
      sessionStorage.setItem(ORG_INVITE_PENDING_KEY, token);
    }
  }, [token]);

  const preview = useQuery({
    queryKey: ["org-invite", token, Boolean(user)],
    queryFn: () => (user ? previewOrgInvite(token) : previewOrgInvitePublic(token)),
    enabled: Boolean(token),
    retry: false,
  });

  const accept = useMutation({
    mutationFn: () => acceptOrgInvite(token),
    onSuccess: (org) => {
      void qc.invalidateQueries({ queryKey: ["orgs"] });
      sessionStorage.removeItem(ORG_INVITE_PENDING_KEY);
      notify(o.inviteAccepted, "success");
      if (!user?.onboarding_done) {
        sessionStorage.setItem(ORG_INVITE_ACCEPTED_ORG_KEY, org.id);
        navigate("/onboarding", { replace: true });
        return;
      }
      navigate(`/orgs/${org.id}`, { replace: true });
    },
    onError: (e) => notify(apiErrorMessage(e, o.inviteAcceptFail), "error"),
  });

  const loginPath = `/login`;
  const registerPath = `/register`;
  const returnTo = location.pathname;

  if (preview.isLoading) return <Spinner />;
  if (preview.isError || !preview.data) {
    return <ErrorBox message={apiErrorMessage(preview.error, o.inviteInvalid)} />;
  }

  const inv = preview.data;
  const alreadyMember = user && "already_member" in inv ? inv.already_member : false;

  return (
    <div className="mx-auto max-w-xl">
      <PageTitle title={o.invitePageTitle} subtitle={o.invitePageSubtitle(inv.org_name)} />
      <div className="card">
        <div className="mb-4 rounded-lg border border-brand-100 bg-brand-50/50 px-4 py-3 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
          <p className="font-semibold text-slate-800 dark:text-slate-100">{inv.org_name}</p>
          <p className="mt-1">{o.inviteRole(inv.role)}</p>
          <p className="mt-1">{o.inviteExpires(new Date(inv.expires_at).toLocaleString())}</p>
        </div>

        {!user ? (
          <div className="space-y-3">
            <p className="text-sm text-slate-600 dark:text-slate-300">{i.loginHint}</p>
            <div className="flex flex-wrap gap-2">
              <Link
                to={registerPath}
                state={{ from: returnTo }}
                className="btn-primary"
              >
                {i.registerCta}
              </Link>
              <Link to={loginPath} state={{ from: returnTo }} className="btn">
                {i.loginCta}
              </Link>
            </div>
          </div>
        ) : alreadyMember ? (
          <div>
            <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">{o.alreadyMember}</p>
            <Link to={`/orgs/${inv.org_id}`} className="btn inline-block">
              {o.openOrg}
            </Link>
          </div>
        ) : (
          <button
            type="button"
            className="btn"
            disabled={accept.isPending}
            onClick={() => accept.mutate()}
          >
            {accept.isPending ? o.acceptingInvite : o.acceptInvite}
          </button>
        )}
      </div>

      <OrgInviteIncubationPreview />
    </div>
  );
}
