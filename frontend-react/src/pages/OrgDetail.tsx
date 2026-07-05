import { useEffect, useState, useRef } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addOrgMember,
  createOrgInvite,
  getOrg,
  getOrgActivity,
  getOrgBilling,
  getOrgBillingHistory,
  getOrgBillingProfile,
  setOrgBillingProfile,
  downloadOrgBillingHistoryCsv,
  downloadOrgBillingInvoicePdf,
  getOrgCatalog,
  listFactors,
  listOrgInvites,
  listOrgMembers,
  orgBillingCheckout,
  orgBillingRedeem,
  getOrgSsoDomains,
  setOrgSsoDomains,
  listOrgExecutionOrders,
  fetchOrgExecutionCompliance,
  fetchOrgTeamAttentionRollup,
  dispatchOrgResearchAttentionAlerts,
  getOrgAlertWebhook,
  setOrgAlertWebhook,
  getOrgResearchAlertWebhook,
  setOrgResearchAlertWebhook,
  dispatchOrgSlaAlerts,
  fetchOrgAlertDeliveries,
  downloadOrgAlertDeliveriesCsv,
  refreshOrgExecutionOrders,
  retryOrgFailedAlertDeliveries,
  removeOrgMember,
  revokeOrgInvite,
  shareFactorToOrg,
  updateOrgMemberRole,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function OrgDetail() {
  const { id = "" } = useParams();
  const o = useLocale((s) => s.dict.orgLibrary);
  const notify = useUi((s) => s.notify);
  const me = useAuth((s) => s.user);
  const qc = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const receiptHandled = useRef(false);
  const [username, setUsername] = useState("");
  const [factorId, setFactorId] = useState("");
  const [symbol, setSymbol] = useState("RB");
  const [inviteUrl, setInviteUrl] = useState("");
  const [teamCode, setTeamCode] = useState("");
  const [ssoDomains, setSsoDomains] = useState("");
  const [billingExporting, setBillingExporting] = useState(false);
  const [billingCompany, setBillingCompany] = useState("");
  const [billingTaxId, setBillingTaxId] = useState("");
  const [billingAddress, setBillingAddress] = useState("");
  const [alertWebhook, setAlertWebhook] = useState("");
  const [alertWebhookSecret, setAlertWebhookSecret] = useState("");
  const [researchAlertWebhook, setResearchAlertWebhook] = useState("");
  const [researchAlertWebhookSecret, setResearchAlertWebhookSecret] = useState("");
  const [deliveryScope, setDeliveryScope] = useState<"all" | "sla" | "research">("all");

  const org = useQuery({ queryKey: ["org", id], queryFn: () => getOrg(id), enabled: Boolean(id) });
  const members = useQuery({
    queryKey: ["org-members", id],
    queryFn: () => listOrgMembers(id),
    enabled: Boolean(id),
  });
  const catalog = useQuery({
    queryKey: ["org-catalog", id, symbol],
    queryFn: () => getOrgCatalog(id, { symbol, timeframe: "1d" }),
    enabled: Boolean(id),
  });
  const myFactors = useQuery({ queryKey: ["factors"], queryFn: listFactors });
  const invites = useQuery({
    queryKey: ["org-invites", id],
    queryFn: () => listOrgInvites(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const activity = useQuery({
    queryKey: ["org-activity", id],
    queryFn: () => getOrgActivity(id),
    enabled: Boolean(id),
  });
  const billing = useQuery({
    queryKey: ["org-billing", id],
    queryFn: () => getOrgBilling(id),
    enabled: Boolean(id) && org.data?.my_role === "owner",
  });
  const billingHistory = useQuery({
    queryKey: ["org-billing-history", id],
    queryFn: () => getOrgBillingHistory(id),
    enabled: Boolean(id) && org.data?.my_role === "owner",
  });
  const billingProfileQuery = useQuery({
    queryKey: ["org-billing-profile", id],
    queryFn: () => getOrgBillingProfile(id),
    enabled: Boolean(id) && org.data?.my_role === "owner",
  });
  const ssoDomainQuery = useQuery({
    queryKey: ["org-sso-domains", id],
    queryFn: () => getOrgSsoDomains(id),
    enabled: Boolean(id) && org.data?.my_role === "owner",
  });
  const execOrders = useQuery({
    queryKey: ["org-exec-orders", id],
    queryFn: () => listOrgExecutionOrders(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const execCompliance = useQuery({
    queryKey: ["org-exec-compliance", id],
    queryFn: () => fetchOrgExecutionCompliance(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const teamAttention = useQuery({
    queryKey: ["org-team-attention", id],
    queryFn: () => fetchOrgTeamAttentionRollup(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const alertWebhookQuery = useQuery({
    queryKey: ["org-alert-webhook", id],
    queryFn: () => getOrgAlertWebhook(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const researchAlertWebhookQuery = useQuery({
    queryKey: ["org-research-alert-webhook", id],
    queryFn: () => getOrgResearchAlertWebhook(id),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });
  const alertDeliveries = useQuery({
    queryKey: ["org-alert-deliveries", id, deliveryScope],
    queryFn: () => fetchOrgAlertDeliveries(id, 20, deliveryScope),
    enabled: Boolean(id) && (org.data?.my_role === "owner" || org.data?.my_role === "admin"),
  });

  const isOwner = org.data?.my_role === "owner";
  const canAdmin = isOwner || org.data?.my_role === "admin";
  const canShare = canAdmin || org.data?.my_role === "member";

  const addMember = useMutation({
    mutationFn: () => addOrgMember(id, { username: username.trim(), role: "member" }),
    onSuccess: () => {
      setUsername("");
      void qc.invalidateQueries({ queryKey: ["org-members", id] });
      notify(o.memberAdded, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.memberFail), "error"),
  });

  const share = useMutation({
    mutationFn: () => shareFactorToOrg(id, factorId),
    onSuccess: () => {
      setFactorId("");
      void qc.invalidateQueries({ queryKey: ["org-catalog", id] });
      void qc.invalidateQueries({ queryKey: ["org", id] });
      notify(o.shared, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.shareFail), "error"),
  });

  const invite = useMutation({
    mutationFn: () => createOrgInvite(id, { role: "member", expires_in_days: 14, max_uses: 20 }),
    onSuccess: (res) => {
      const origin = window.location.origin;
      setInviteUrl(`${origin}${res.invite_path}`);
      void qc.invalidateQueries({ queryKey: ["org-invites", id] });
      notify(o.inviteCreated, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.inviteFail), "error"),
  });

  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateOrgMemberRole(id, userId, role),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["org-members", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.roleUpdated, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.roleUpdateFail), "error"),
  });

  const removeMember = useMutation({
    mutationFn: (userId: string) => removeOrgMember(id, userId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["org-members", id] });
      void qc.invalidateQueries({ queryKey: ["org", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.memberRemoved, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.removeFail), "error"),
  });

  const revokeInviteMut = useMutation({
    mutationFn: (inviteId: string) => revokeOrgInvite(id, inviteId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["org-invites", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.inviteRevoked, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.revokeFail), "error"),
  });

  const teamRedeem = useMutation({
    mutationFn: () => orgBillingRedeem(id, teamCode.trim()),
    onSuccess: (r) => {
      setTeamCode("");
      void qc.invalidateQueries({ queryKey: ["org-billing", id] });
      void qc.invalidateQueries({ queryKey: ["org-billing-history", id] });
      notify(r.message, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.billingRedeemFail), "error"),
  });

  const teamCheckout = useMutation({
    mutationFn: (planCode: string) => orgBillingCheckout(id, planCode),
    onSuccess: (r) => {
      if (r.configured && r.pay_url) {
        window.location.href = r.pay_url;
        return;
      }
      notify(r.message, "info");
    },
    onError: (e) => notify(apiErrorMessage(e, o.billingCheckoutFail), "error"),
  });

  const saveBillingProfile = useMutation({
    mutationFn: () =>
      setOrgBillingProfile(id, {
        company_name: billingCompany.trim(),
        tax_id: billingTaxId.trim(),
        address: billingAddress.trim(),
      }),
    onSuccess: (r) => {
      setBillingCompany(r.company_name);
      setBillingTaxId(r.tax_id);
      setBillingAddress(r.address);
      void qc.invalidateQueries({ queryKey: ["org-billing-profile", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.billingProfileSaved, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.billingProfileFail), "error"),
  });

  const saveSsoDomains = useMutation({
    mutationFn: () =>
      setOrgSsoDomains(
        id,
        ssoDomains
          .split(/[,;\s]+/)
          .map((d) => d.trim().toLowerCase())
          .filter(Boolean),
      ),
    onSuccess: (r) => {
      setSsoDomains(r.domains.join(", "));
      void qc.invalidateQueries({ queryKey: ["org-sso-domains", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.ssoDomainsSaved, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.ssoDomainsFail), "error"),
  });

  const syncExec = useMutation({
    mutationFn: () => refreshOrgExecutionOrders(id),
    onSuccess: (r) => {
      void qc.invalidateQueries({ queryKey: ["org-exec-orders", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.execDeskSynced(r.updated), "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.execDeskSyncFail), "error"),
  });

  const saveAlertWebhook = useMutation({
    mutationFn: () =>
      setOrgAlertWebhook(id, alertWebhook.trim(), alertWebhookSecret.trim() || undefined),
    onSuccess: (r) => {
      setAlertWebhook(r.webhook_url);
      setAlertWebhookSecret("");
      void qc.invalidateQueries({ queryKey: ["org-alert-webhook", id] });
      void qc.invalidateQueries({ queryKey: ["org-research-alert-webhook", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.alertWebhookSaved, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.alertWebhookFail), "error"),
  });

  const saveResearchAlertWebhook = useMutation({
    mutationFn: () =>
      setOrgResearchAlertWebhook(
        id,
        researchAlertWebhook.trim(),
        researchAlertWebhookSecret.trim() || undefined,
      ),
    onSuccess: (r) => {
      setResearchAlertWebhook(r.webhook_url);
      setResearchAlertWebhookSecret("");
      void qc.invalidateQueries({ queryKey: ["org-research-alert-webhook", id] });
      void qc.invalidateQueries({ queryKey: ["org-activity", id] });
      notify(o.researchAlertWebhookSaved, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.researchAlertWebhookFail), "error"),
  });

  const dispatchResearchAttention = useMutation({
    mutationFn: () => dispatchOrgResearchAttentionAlerts(id, true),
    onSuccess: (r) => {
      void qc.invalidateQueries({ queryKey: ["org-alert-deliveries", id] });
      if (r.sent > 0) {
        notify(o.teamAttentionWebhookDispatchDone(r.sent), "success");
      } else if (r.skipped && r.reason) {
        notify(o.alertWebhookDispatchSkipped(r.reason), "info");
      }
    },
    onError: (e) => notify(apiErrorMessage(e, o.alertWebhookDispatchFail), "error"),
  });

  const dispatchOrgAlerts = useMutation({
    mutationFn: () => dispatchOrgSlaAlerts(id, true),
    onSuccess: (r) => {
      void qc.invalidateQueries({ queryKey: ["org-alert-deliveries", id] });
      if (r.sent > 0) notify(o.alertWebhookDispatchDone(r.sent), "success");
      else notify(o.alertWebhookDispatchSkipped(r.reason ?? "none"), "info");
    },
    onError: (e) => notify(apiErrorMessage(e, o.alertWebhookDispatchFail), "error"),
  });

  const retryOrgAlertDeliveries = useMutation({
    mutationFn: () => retryOrgFailedAlertDeliveries(id),
    onSuccess: (r) => {
      void qc.invalidateQueries({ queryKey: ["org-alert-deliveries", id] });
      notify(o.alertDeliveryRetryDone(r.retried), "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.alertDeliveryRetryFail), "error"),
  });

  const exportAlertDeliveries = useMutation({
    mutationFn: () => downloadOrgAlertDeliveriesCsv(id, deliveryScope),
    onSuccess: () => notify(o.alertDeliveryExportDone, "success"),
    onError: (e) => notify(apiErrorMessage(e, o.alertDeliveryExportFail), "error"),
  });

  function canManageMember(userId: string, role: string) {
    if (role === "owner") return false;
    if (!canAdmin) return me?.id === userId;
    if (role === "admin" && !isOwner && userId !== me?.id) return false;
    return true;
  }

  function roleOptionsForMember(role: string) {
    if (isOwner) return ["admin", "member", "viewer"];
    if (role === "admin") return ["admin"];
    return ["member", "viewer"];
  }

  useEffect(() => {
    if (ssoDomainQuery.data) {
      setSsoDomains(ssoDomainQuery.data.domains.join(", "));
    }
  }, [ssoDomainQuery.data]);

  useEffect(() => {
    if (billingProfileQuery.data) {
      setBillingCompany(billingProfileQuery.data.company_name);
      setBillingTaxId(billingProfileQuery.data.tax_id);
      setBillingAddress(billingProfileQuery.data.address);
    }
  }, [billingProfileQuery.data]);

  useEffect(() => {
    const receiptId = searchParams.get("receipt");
    if (!receiptId || !me || receiptHandled.current) return;
    receiptHandled.current = true;
    notify(o.receiptOpening, "info");
    void downloadOrgBillingInvoicePdf(id, receiptId)
      .then(() => notify(o.receiptReady, "success"))
      .catch((e) => notify(apiErrorMessage(e, o.billingInvoiceFail), "error"));
    searchParams.delete("receipt");
    setSearchParams(searchParams, { replace: true });
  }, [searchParams, setSearchParams, notify, o, me, id]);

  useEffect(() => {
    if (alertWebhookQuery.data) {
      setAlertWebhook(alertWebhookQuery.data.webhook_url);
    }
  }, [alertWebhookQuery.data]);

  useEffect(() => {
    if (researchAlertWebhookQuery.data) {
      setResearchAlertWebhook(researchAlertWebhookQuery.data.webhook_url);
    }
  }, [researchAlertWebhookQuery.data]);

  const researchWebhookReady = Boolean(
    researchAlertWebhookQuery.data?.webhook_url || researchAlertWebhookQuery.data?.uses_sla_fallback,
  );

  if (org.isLoading) return <Spinner />;
  if (org.isError || !org.data) {
    return <ErrorBox message={apiErrorMessage(org.error, o.loadFail)} />;
  }

  const cat = catalog.data;

  return (
    <div>
      <Link to="/orgs" className="mb-4 inline-block text-sm text-brand-600 hover:underline dark:text-brand-400">
        {o.back}
      </Link>
      <PageTitle title={org.data.name} subtitle={o.detailSubtitle(org.data.slug, org.data.my_role ?? "—")} />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label={o.members} value={org.data.member_count} />
        <StatCard label={o.sharedFactors} value={org.data.shared_factor_count} />
        <StatCard label={o.overlap} value={cat?.high_overlap_count ?? 0} />
      </div>

      {isOwner && billing.data && (
        <div className="mb-6 card">
          <h2 className="mb-2 font-semibold">{o.billingTitle}</h2>
          <p className="mb-3 text-sm text-slate-500">
            {billing.data.is_paid
              ? o.billingActive(
                  billing.data.tier_name,
                  billing.data.member_count,
                  billing.data.seats,
                  billing.data.expires_at
                    ? new Date(billing.data.expires_at).toLocaleDateString()
                    : "—",
                )
              : o.billingInactive}
          </p>
          <div className="mb-4 flex flex-wrap gap-2">
            {billing.data.team_plans.map((plan) => (
              <button
                key={plan.code}
                type="button"
                className="btn text-sm"
                disabled={teamCheckout.isPending || billing.data.tier >= plan.tier}
                onClick={() => teamCheckout.mutate(plan.code)}
              >
                {plan.name} · ¥{plan.price_cny}
                {plan.seats ? ` · ${plan.seats}${o.billingSeats}` : ""}
              </button>
            ))}
          </div>
          <p className="mb-2 text-sm text-slate-500">{o.billingRedeemHint}</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              className="input flex-1 font-mono"
              placeholder="QLT-XXXXXXXX"
              value={teamCode}
              onChange={(e) => setTeamCode(e.target.value)}
            />
            <button
              type="button"
              className="btn"
              disabled={!teamCode.trim() || teamRedeem.isPending}
              onClick={() => teamRedeem.mutate()}
            >
              {teamRedeem.isPending ? o.billingRedeeming : o.billingRedeemBtn}
            </button>
          </div>
          <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
            <p className="mb-2 text-sm font-medium">{o.billingProfileTitle}</p>
            <p className="mb-2 text-xs text-slate-500">{o.billingProfileHint}</p>
            <div className="flex flex-col gap-2">
              <input
                className="input text-sm"
                placeholder={o.billingProfileCompany}
                value={billingCompany}
                onChange={(e) => setBillingCompany(e.target.value)}
              />
              <input
                className="input text-sm font-mono"
                placeholder={o.billingProfileTaxId}
                value={billingTaxId}
                onChange={(e) => setBillingTaxId(e.target.value)}
              />
              <input
                className="input text-sm"
                placeholder={o.billingProfileAddress}
                value={billingAddress}
                onChange={(e) => setBillingAddress(e.target.value)}
              />
              <button
                type="button"
                className="btn text-sm self-start"
                disabled={saveBillingProfile.isPending || billingProfileQuery.isLoading}
                onClick={() => saveBillingProfile.mutate()}
              >
                {saveBillingProfile.isPending ? o.billingProfileSaving : o.billingProfileSave}
              </button>
            </div>
          </div>
          {billingHistory.data && billingHistory.data.length > 0 && (
            <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-medium">{o.billingHistoryTitle}</p>
                <button
                  type="button"
                  className="btn text-xs"
                  disabled={billingExporting}
                  onClick={() => {
                    setBillingExporting(true);
                    void downloadOrgBillingHistoryCsv(id)
                      .catch((e) => notify(apiErrorMessage(e, o.billingExportFail), "error"))
                      .finally(() => setBillingExporting(false));
                  }}
                >
                  {billingExporting ? o.billingExporting : o.billingExportCsv}
                </button>
              </div>
              <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                {billingHistory.data.slice(0, 8).map((row) => (
                  <li
                    key={row.id}
                    className="flex flex-wrap justify-between gap-2 border-b border-slate-100 py-1 dark:border-slate-800"
                  >
                    <span>
                      {row.plan_name} · {row.tier_name}
                      {row.seats ? ` · ${row.seats}${o.billingSeats}` : ""}
                    </span>
                    <span className="text-slate-400">
                      ¥{row.amount_cny.toLocaleString()} · {row.source} ·{" "}
                      {new Date(row.created_at).toLocaleDateString()}
                    </span>
                    <button
                      type="button"
                      className="btn text-xs"
                      onClick={() =>
                        void downloadOrgBillingInvoicePdf(id, row.id).catch((e) =>
                          notify(apiErrorMessage(e, o.billingInvoiceFail), "error"),
                        )
                      }
                    >
                      {o.billingInvoicePdf}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {isOwner && (
        <div className="mb-6 card">
          <h2 className="mb-2 font-semibold">{o.ssoDomainsTitle}</h2>
          <p className="mb-3 text-sm text-slate-500">{o.ssoDomainsHint}</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              className="input flex-1 font-mono text-sm"
              placeholder={o.ssoDomainsPlaceholder}
              value={ssoDomains}
              onChange={(e) => setSsoDomains(e.target.value)}
            />
            <button
              type="button"
              className="btn"
              disabled={saveSsoDomains.isPending || ssoDomainQuery.isLoading}
              onClick={() => saveSsoDomains.mutate()}
            >
              {saveSsoDomains.isPending ? o.ssoDomainsSaving : o.ssoDomainsSave}
            </button>
          </div>
        </div>
      )}

      {canAdmin && (
        <div className="mb-6 grid gap-4 lg:grid-cols-2">
          <div className="card">
            <h2 className="mb-2 font-semibold">{o.inviteTitle}</h2>
            <p className="mb-3 text-sm text-slate-500">{o.inviteHint}</p>
            <button
              type="button"
              className="btn"
              disabled={invite.isPending}
              onClick={() => invite.mutate()}
            >
              {invite.isPending ? o.inviteCreating : o.inviteBtn}
            </button>
            {inviteUrl && (
              <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-700 dark:bg-slate-900/50">
                <p className="break-all font-mono text-xs text-slate-700 dark:text-slate-200">{inviteUrl}</p>
                <button
                  type="button"
                  className="btn mt-2 text-xs"
                  onClick={() => {
                    void navigator.clipboard?.writeText(inviteUrl);
                    notify(o.inviteCopied, "success");
                  }}
                >
                  {o.copyInvite}
                </button>
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="mb-2 font-semibold">{o.addMember}</h2>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                className="input flex-1"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={o.usernamePlaceholder}
              />
              <button
                type="button"
                className="btn"
                disabled={!username.trim() || addMember.isPending}
                onClick={() => addMember.mutate()}
              >
                {o.addMemberBtn}
              </button>
            </div>
          </div>
        </div>
      )}

      {canShare && (
        <div className="mb-6 card">
          <h2 className="mb-2 font-semibold">{o.shareFactor}</h2>
          <select
            className="input mb-2 w-full"
            value={factorId}
            onChange={(e) => setFactorId(e.target.value)}
          >
            <option value="">{o.pickFactor}</option>
            {myFactors.data?.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name} ({f.kind})
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn"
            disabled={!factorId || share.isPending}
            onClick={() => share.mutate()}
          >
            {o.shareBtn}
          </button>
        </div>
      )}

      <div className="mb-6 card">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <h2 className="font-semibold">{o.catalogTitle}</h2>
          <select className="input text-sm" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {["RB", "AU", "IF"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        {catalog.isLoading ? (
          <Spinner />
        ) : !cat || cat.factors.length === 0 ? (
          <p className="text-sm text-slate-500">{o.catalogEmpty}</p>
        ) : (
          <>
            {cat.market_regime && (
              <p className="mb-3 text-xs text-slate-500">
                {o.regimeCatalogHint(cat.market_regime.label, cat.market_regime.hint)}
              </p>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-700">
                    <th className="py-2 pr-2">{o.colName}</th>
                    <th className="py-2 pr-2">{o.colOwner}</th>
                    <th className="py-2 pr-2">{o.colSharpe}</th>
                    <th className="py-2 pr-2">{o.colOos}</th>
                    <th className="py-2">{o.colRegimeFit}</th>
                  </tr>
                </thead>
                <tbody>
                  {cat.factors.map((f) => (
                    <tr key={f.factor_id} className="border-b border-slate-100 dark:border-slate-800">
                      <td className="py-2 pr-2 font-medium">{f.name}</td>
                      <td className="py-2 pr-2 text-slate-500">{f.owner_username ?? "—"}</td>
                      <td className="py-2 pr-2">{fmt(f.sharpe)}</td>
                      <td className="py-2 pr-2">{fmt(f.oos_sharpe)}</td>
                      <td className="py-2 text-xs">
                        {f.regime_fit_verdict
                          ? `${f.strategy_label ?? ""} · ${f.regime_fit_verdict} (${f.regime_fit_score})`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {cat.redundancy_pairs.length > 0 && (
              <div className="mt-4 text-xs text-slate-600 dark:text-slate-300">
                <p className="font-medium">{o.overlapPairs}</p>
                <ul className="mt-1 list-inside list-disc">
                  {cat.redundancy_pairs.slice(0, 5).map((p) => (
                    <li key={`${p.factor_a}-${p.factor_b}`}>
                      {o.pairLine(p.name_a, p.name_b, p.owner_a, p.owner_b, p.r_squared)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>

      {canAdmin && (
        <div className="mb-6 card border border-violet-100 bg-gradient-to-r from-violet-50/50 to-white dark:border-violet-900 dark:from-violet-950/20 dark:to-slate-900">
          <h2 className="mb-1 font-semibold">{o.teamAttentionTitle}</h2>
          <p className="mb-3 text-xs text-slate-500">{o.teamAttentionSubtitle}</p>
          {teamAttention.isLoading ? (
            <Spinner />
          ) : teamAttention.data ? (
            <>
              <p
                className={`mb-3 text-sm ${
                  teamAttention.data.total_alerts > 0
                    ? "text-violet-800 dark:text-violet-200"
                    : "text-slate-500"
                }`}
              >
                {teamAttention.data.summary}
              </p>
              {teamAttention.data.items.length > 0 ? (
                <ul className="space-y-2">
                  {teamAttention.data.items.slice(0, 8).map((item) => (
                    <li
                      key={`${item.user_id}-${item.alert_key}`}
                      className={`rounded-lg border px-3 py-2.5 text-sm ${
                        item.severity === "alert"
                          ? "border-rose-200 bg-rose-50/70 dark:border-rose-900 dark:bg-rose-950/30"
                          : item.severity === "watch"
                            ? "border-amber-200 bg-amber-50/70 dark:border-amber-900 dark:bg-amber-950/30"
                            : "border-sky-200 bg-sky-50/70 dark:border-sky-900 dark:bg-sky-950/30"
                      }`}
                    >
                      <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
                        {o.teamAttentionMember(item.username, item.kind_label)}
                      </p>
                      <p className="mt-0.5 font-medium text-slate-800 dark:text-slate-100">{item.title}</p>
                      <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{item.message}</p>
                      {item.cta_path && (
                        <Link
                          to={item.cta_path}
                          className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline"
                        >
                          {o.teamAttentionViewProject}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">{o.teamAttentionEmpty}</p>
              )}
              <div className="mt-4 border-t border-violet-100 pt-3 dark:border-violet-900">
                <p className="mb-1 text-sm font-medium">{o.researchAlertWebhookTitle}</p>
                <p className="mb-2 text-xs text-slate-500">{o.researchAlertWebhookHint}</p>
                {researchAlertWebhookQuery.data?.uses_sla_fallback && (
                  <p className="mb-2 text-xs text-violet-700 dark:text-violet-300">
                    {o.researchAlertWebhookFallback(researchAlertWebhookQuery.data.sla_fallback_url)}
                  </p>
                )}
                <div className="flex flex-col gap-2 sm:flex-row">
                  <input
                    className="input flex-1 font-mono text-xs"
                    placeholder={o.researchAlertWebhookPlaceholder}
                    value={researchAlertWebhook}
                    onChange={(e) => setResearchAlertWebhook(e.target.value)}
                  />
                  <input
                    className="input flex-1 font-mono text-xs"
                    placeholder={
                      researchAlertWebhookQuery.data?.secret_configured
                        ? o.alertWebhookSecretConfigured
                        : o.alertWebhookSecretPlaceholder
                    }
                    value={researchAlertWebhookSecret}
                    onChange={(e) => setResearchAlertWebhookSecret(e.target.value)}
                  />
                  <button
                    type="button"
                    className="btn shrink-0 text-xs"
                    disabled={saveResearchAlertWebhook.isPending || researchAlertWebhookQuery.isLoading}
                    onClick={() => saveResearchAlertWebhook.mutate()}
                  >
                    {saveResearchAlertWebhook.isPending
                      ? o.alertWebhookSaving
                      : o.researchAlertWebhookSave}
                  </button>
                </div>
                <p className="mb-2 mt-3 text-xs text-slate-500">{o.teamAttentionWebhookHint}</p>
                <button
                  type="button"
                  className="btn text-xs"
                  disabled={
                    dispatchResearchAttention.isPending || !researchWebhookReady
                  }
                  onClick={() => dispatchResearchAttention.mutate()}
                >
                  {dispatchResearchAttention.isPending
                    ? o.teamAttentionWebhookDispatching
                    : o.teamAttentionWebhookDispatch}
                </button>
              </div>
            </>
          ) : null}
        </div>
      )}

      {canAdmin && (
        <div className="mb-6 card">
          <h2 className="mb-2 font-semibold">{o.execComplianceTitle}</h2>
          {execCompliance.isLoading ? (
            <Spinner />
          ) : execCompliance.data ? (
            <>
              <p
                className={`mb-2 text-sm ${
                  execCompliance.data.alert_count > 0
                    ? "text-amber-700 dark:text-amber-300"
                    : "text-slate-500"
                }`}
              >
                {execCompliance.data.alert_count > 0
                  ? o.execComplianceAlerts(execCompliance.data.alert_count)
                  : o.execComplianceNone}
              </p>
              {execCompliance.data.sla_alerts.length > 0 && (
                <ul className="mb-2 space-y-1 text-xs">
                  {execCompliance.data.sla_alerts.slice(0, 6).map((alert, i) => (
                    <li
                      key={`${alert.code}-${alert.order_id ?? i}`}
                      className={
                        alert.severity === "critical"
                          ? "text-red-600 dark:text-red-400"
                          : "text-amber-700 dark:text-amber-300"
                      }
                    >
                      [{alert.severity}] {alert.message}
                    </li>
                  ))}
                </ul>
              )}
              {execCompliance.data.stale_orders.length > 0 && (
                <p className="text-xs text-slate-500">
                  {o.execComplianceStale}: {execCompliance.data.stale_orders.length}
                </p>
              )}
              <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
                <p className="mb-2 text-sm font-medium">{o.alertWebhookTitle}</p>
                <p className="mb-2 text-xs text-slate-500">{o.alertWebhookHint}</p>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <input
                    className="input flex-1 font-mono text-xs"
                    placeholder={o.alertWebhookPlaceholder}
                    value={alertWebhook}
                    onChange={(e) => setAlertWebhook(e.target.value)}
                  />
                  <input
                    className="input flex-1 font-mono text-xs"
                    placeholder={
                      alertWebhookQuery.data?.secret_configured
                        ? o.alertWebhookSecretConfigured
                        : o.alertWebhookSecretPlaceholder
                    }
                    value={alertWebhookSecret}
                    onChange={(e) => setAlertWebhookSecret(e.target.value)}
                  />
                  <button
                    type="button"
                    className="btn text-xs"
                    disabled={saveAlertWebhook.isPending || alertWebhookQuery.isLoading}
                    onClick={() => saveAlertWebhook.mutate()}
                  >
                    {saveAlertWebhook.isPending ? o.alertWebhookSaving : o.alertWebhookSave}
                  </button>
                  <button
                    type="button"
                    className="btn text-xs"
                    disabled={dispatchOrgAlerts.isPending || !alertWebhook.trim()}
                    onClick={() => dispatchOrgAlerts.mutate()}
                  >
                    {dispatchOrgAlerts.isPending ? o.alertWebhookDispatching : o.alertWebhookDispatch}
                  </button>
                </div>
              </div>
              <div className="mt-4 border-t border-slate-200 pt-3 dark:border-slate-700">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">{o.alertDeliveryTitle}</p>
                  <div className="flex flex-wrap gap-1">
                    {(["all", "sla", "research"] as const).map((s) => (
                      <button
                        key={s}
                        type="button"
                        className={`rounded px-2 py-0.5 text-xs ${
                          deliveryScope === s
                            ? "bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200"
                            : "text-slate-500 hover:text-slate-700"
                        }`}
                        onClick={() => setDeliveryScope(s)}
                      >
                        {s === "all"
                          ? o.alertDeliveryFilterAll
                          : s === "sla"
                            ? o.alertDeliveryFilterSla
                            : o.alertDeliveryFilterResearch}
                      </button>
                    ))}
                  </div>
                  <button
                    type="button"
                    className="btn text-xs"
                    disabled={retryOrgAlertDeliveries.isPending}
                    onClick={() => retryOrgAlertDeliveries.mutate()}
                  >
                    {retryOrgAlertDeliveries.isPending
                      ? o.alertDeliveryRetrying
                      : o.alertDeliveryRetry}
                  </button>
                  <button
                    type="button"
                    className="btn text-xs"
                    disabled={exportAlertDeliveries.isPending}
                    onClick={() => exportAlertDeliveries.mutate()}
                  >
                    {exportAlertDeliveries.isPending
                      ? o.alertDeliveryExporting
                      : o.alertDeliveryExport}
                  </button>
                </div>
                {alertDeliveries.isLoading ? (
                  <Spinner />
                ) : alertDeliveries.data && alertDeliveries.data.length === 0 ? (
                  <p className="text-xs text-slate-500">{o.alertDeliveryEmpty}</p>
                ) : alertDeliveries.data ? (
                  <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                    {alertDeliveries.data.slice(0, 10).map((row) => (
                      <li
                        key={row.id}
                        className={
                          row.status === "failed"
                            ? "text-rose-600 dark:text-rose-400"
                            : row.status === "sent"
                              ? "text-emerald-700 dark:text-emerald-300"
                              : ""
                        }
                      >
                        {new Date(row.created_at).toLocaleString()} · {o.alertDeliveryScope(row.scope)} ·{" "}
                        {row.status} · {row.trigger} · {row.alert_count} alerts
                        {row.signed ? ` · ${o.alertDeliverySigned}` : ""}
                        {row.error_message ? ` · ${row.error_message}` : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </>
          ) : null}
        </div>
      )}

      {canAdmin && (
        <div className="mb-6 card">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">{o.execDeskTitle}</h2>
            <button
              type="button"
              className="btn text-sm"
              disabled={syncExec.isPending}
              onClick={() => syncExec.mutate()}
            >
              {syncExec.isPending ? o.execDeskSyncing : o.execDeskSync}
            </button>
          </div>
          {execOrders.isLoading ? (
            <Spinner />
          ) : (execOrders.data ?? []).length === 0 ? (
            <p className="text-sm text-slate-500">{o.execDeskEmpty}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-700">
                    <th className="py-2 pr-2">{o.execDeskColUser}</th>
                    <th className="py-2 pr-2">{o.execDeskColSymbol}</th>
                    <th className="py-2 pr-2">{o.execDeskColChannel}</th>
                    <th className="py-2">{o.execDeskColStatus}</th>
                  </tr>
                </thead>
                <tbody>
                  {execOrders.data?.slice(0, 10).map((row) => (
                    <tr key={row.id} className="border-b border-slate-100 dark:border-slate-800">
                      <td className="py-2 pr-2 font-medium">{row.username}</td>
                      <td className="py-2 pr-2 font-mono text-xs">
                        {row.symbol} {row.side} ¥{row.notional_cny.toLocaleString()}
                      </td>
                      <td className="py-2 pr-2">{row.channel}</td>
                      <td className="py-2 text-xs">
                        {row.status}
                        {row.gateway_status ? ` (${row.gateway_status})` : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="mb-6 card">
        <h2 className="mb-3 font-semibold">{o.memberList}</h2>
        <ul className="space-y-2 text-sm">
          {(members.data ?? []).map((m) => (
            <li
              key={m.user_id}
              className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 py-2 dark:border-slate-800"
            >
              <span className="font-medium">{m.username}</span>
              <div className="flex items-center gap-2">
                {canManageMember(m.user_id, m.role) ? (
                  <>
                    <select
                      className="input text-xs"
                      value={m.role}
                      disabled={m.role === "owner" || updateRole.isPending}
                      onChange={(e) =>
                        updateRole.mutate({ userId: m.user_id, role: e.target.value })
                      }
                    >
                      {(m.role === "owner" ? ["owner"] : roleOptionsForMember(m.role)).map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="btn text-xs"
                      disabled={removeMember.isPending}
                      onClick={() => removeMember.mutate(m.user_id)}
                    >
                      {me?.id === m.user_id ? o.leaveOrg : o.removeMember}
                    </button>
                  </>
                ) : (
                  <span className="text-xs text-slate-500">{m.role}</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {canAdmin && (invites.data?.length ?? 0) > 0 && (
        <div className="mb-6 card">
          <h2 className="mb-3 font-semibold">{o.activeInvites}</h2>
          <ul className="space-y-2 text-sm">
            {invites.data?.map((inv) => (
              <li
                key={inv.id}
                className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 py-2 dark:border-slate-800"
              >
                <div>
                  <p className="font-mono text-xs">{inv.token.slice(0, 12)}…</p>
                  <p className="text-xs text-slate-500">
                    {o.inviteUsage(inv.used_count, inv.max_uses)} · {inv.active ? o.inviteActive : o.inviteExpired}
                  </p>
                </div>
                {inv.active && (
                  <button
                    type="button"
                    className="btn text-xs"
                    disabled={revokeInviteMut.isPending}
                    onClick={() => revokeInviteMut.mutate(inv.id)}
                  >
                    {o.revokeInvite}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h2 className="mb-3 font-semibold">{o.activityTitle}</h2>
        {activity.isLoading ? (
          <Spinner />
        ) : (activity.data ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">{o.activityEmpty}</p>
        ) : (
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            {activity.data?.map((ev) => (
              <li key={ev.id} className="border-b border-slate-100 py-1 dark:border-slate-800">
                <span className="font-mono">{ev.action}</span>
                <span className="ml-2 text-slate-400">
                  {new Date(ev.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-2xl font-semibold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function fmt(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}
