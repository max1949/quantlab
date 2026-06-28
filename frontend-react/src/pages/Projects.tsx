import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { EmptyState, ErrorBox, PageTitle, Spinner } from "../components/ui";

export default function Projects() {
  const projects = useQuery({ queryKey: ["projects"], queryFn: listProjects });

  return (
    <div>
      <div className="flex items-center justify-between">
        <PageTitle title="我的研究项目" />
        <Link to="/templates" className="btn-primary">
          + 新建 (从模板)
        </Link>
      </div>

      {projects.isLoading ? (
        <Spinner />
      ) : projects.isError ? (
        <ErrorBox message={apiErrorMessage(projects.error)} />
      ) : projects.data && projects.data.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {projects.data.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="card hover:shadow-md">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">{p.title}</h3>
                <span className="badge">{p.status}</span>
              </div>
              {p.symbol && (
                <span className="mt-1 inline-block text-sm text-slate-400">
                  标的 {p.symbol}
                </span>
              )}
              {p.question && (
                <p className="mt-2 text-sm text-slate-500">{p.question}</p>
              )}
              <div className="mt-3 flex flex-wrap gap-1">
                {p.tags?.map((tag) => (
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
          title="还没有研究项目"
          hint="从模板开始, 30 秒建好你的第一个研究"
          action={
            <Link to="/templates" className="btn-primary mt-2">
              去模板库
            </Link>
          }
        />
      )}
    </div>
  );
}
