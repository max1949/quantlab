import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { acceptOrgInvite, previewOrgInvite } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function OrgInvite() {
  const { token = "" } = useParams();
  const o = useLocale((s) => s.dict.orgLibrary);
  const notify = useUi((s) => s.notify);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const preview = useQuery({
    queryKey: ["org-invite", token],
    queryFn: () => previewOrgInvite(token),
    enabled: Boolean(token),
    retry: false,
  });

  const accept = useMutation({
    mutationFn: () => acceptOrgInvite(token),
    onSuccess: (org) => {
      void qc.invalidateQueries({ queryKey: ["orgs"] });
      notify(o.inviteAccepted, "success");
      navigate(`/orgs/${org.id}`);
    },
    onError: (e) => notify(apiErrorMessage(e, o.inviteAcceptFail), "error"),
  });

  if (preview.isLoading) return <Spinner />;
  if (preview.isError || !preview.data) {
    return <ErrorBox message={apiErrorMessage(preview.error, o.inviteInvalid)} />;
  }

  const inv = preview.data;

  return (
    <div className="mx-auto max-w-xl">
      <PageTitle title={o.invitePageTitle} subtitle={o.invitePageSubtitle(inv.org_name)} />
      <div className="card">
        <div className="mb-4 rounded-lg border border-brand-100 bg-brand-50/50 px-4 py-3 text-sm text-slate-700 dark:border-brand-900 dark:bg-brand-950/30 dark:text-slate-200">
          <p className="font-semibold text-slate-800 dark:text-slate-100">{inv.org_name}</p>
          <p className="mt-1">{o.inviteRole(inv.role)}</p>
          <p className="mt-1">{o.inviteExpires(new Date(inv.expires_at).toLocaleString())}</p>
        </div>

        {inv.already_member ? (
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
    </div>
  );
}
