import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createOrg, listOrgs } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function OrgLibrary() {
  const o = useLocale((s) => s.dict.orgLibrary);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();
  const [name, setName] = useState("");

  const orgs = useQuery({ queryKey: ["orgs"], queryFn: listOrgs });

  const create = useMutation({
    mutationFn: () => createOrg(name.trim()),
    onSuccess: () => {
      setName("");
      void qc.invalidateQueries({ queryKey: ["orgs"] });
      notify(o.created, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, o.createFail), "error"),
  });

  return (
    <div>
      <PageTitle title={o.title} subtitle={o.subtitle} />

      <div className="mb-6 card">
        <h2 className="mb-2 font-semibold text-slate-800 dark:text-slate-100">{o.createTitle}</h2>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            className="input flex-1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={o.createPlaceholder}
          />
          <button
            type="button"
            className="btn"
            disabled={!name.trim() || create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? o.creating : o.createBtn}
          </button>
        </div>
      </div>

      {orgs.isLoading ? (
        <Spinner />
      ) : orgs.isError ? (
        <ErrorBox message={apiErrorMessage(orgs.error, o.loadFail)} />
      ) : orgs.data?.length === 0 ? (
        <p className="text-sm text-slate-500">{o.empty}</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {orgs.data?.map((org) => (
            <Link
              key={org.id}
              to={`/orgs/${org.id}`}
              className="card block transition hover:border-brand-300 dark:hover:border-brand-700"
            >
              <p className="font-semibold text-slate-800 dark:text-slate-100">{org.name}</p>
              <p className="mt-1 text-xs text-slate-500">
                {o.meta(org.member_count, org.shared_factor_count, org.my_role ?? "—")}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
