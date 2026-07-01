import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Projects() {
  const p = useLocale((s) => s.dict.projects);
  const projects = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <PageTitle title={p.title} />
        <Link to="/templates" className="btn-primary shrink-0 whitespace-nowrap">
          {p.newFromTemplate}
        </Link>
      </div>

      {projects.isLoading ? (
        <Spinner />
      ) : projects.isError ? (
        <ErrorBox message={apiErrorMessage(projects.error)} />
      ) : projects.data && projects.data.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {projects.data.map((proj) => (
            <Link key={proj.id} to={`/projects/${proj.id}`} className="card hover:shadow-md">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-800 dark:text-slate-100">
                  {proj.title}
                </h3>
                <span className="badge">{proj.status}</span>
              </div>
              {proj.symbol && (
                <span className="mt-1 inline-block text-sm text-slate-400">
                  {p.symbol} {proj.symbol}
                </span>
              )}
              {proj.question && (
                <p className="mt-2 text-sm text-slate-500">{proj.question}</p>
              )}
              <div className="mt-3 flex flex-wrap gap-1">
                {proj.tags?.map((tag) => (
                  <span key={tag} className="badge">
                    #{tag}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          title={p.emptyTitle}
          hint={p.emptyHint}
          action={
            <Link to="/templates" className="btn-primary mt-2">
              {p.goTemplates}
            </Link>
          }
        />
      )}
    </div>
  );
}
