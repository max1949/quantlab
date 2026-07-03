import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addOrgMember,
  createOrgInvite,
  getOrg,
  getOrgActivity,
  getOrgCatalog,
  listFactors,
  listOrgInvites,
  listOrgMembers,
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
  const [username, setUsername] = useState("");
  const [factorId, setFactorId] = useState("");
  const [symbol, setSymbol] = useState("RB");
  const [inviteUrl, setInviteUrl] = useState("");

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
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-700">
                    <th className="py-2 pr-2">{o.colName}</th>
                    <th className="py-2 pr-2">{o.colOwner}</th>
                    <th className="py-2 pr-2">{o.colSharpe}</th>
                    <th className="py-2">{o.colOos}</th>
                  </tr>
                </thead>
                <tbody>
                  {cat.factors.map((f) => (
                    <tr key={f.factor_id} className="border-b border-slate-100 dark:border-slate-800">
                      <td className="py-2 pr-2 font-medium">{f.name}</td>
                      <td className="py-2 pr-2 text-slate-500">{f.owner_username ?? "—"}</td>
                      <td className="py-2 pr-2">{fmt(f.sharpe)}</td>
                      <td className="py-2">{fmt(f.oos_sharpe)}</td>
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
