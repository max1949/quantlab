import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearcher } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../store/auth";
import { ErrorBox, Spinner } from "../components/ui";
import ProfileView from "../components/ProfileView";

export default function Researcher() {
  const { userId = "" } = useParams();
  const me = useAuth((s) => s.user);
  const q = useQuery({
    queryKey: ["researcher", userId],
    queryFn: () => getResearcher(userId),
  });

  if (q.isLoading) return <Spinner />;
  if (q.isError)
    return <ErrorBox message={apiErrorMessage(q.error, "研究员不存在")} />;

  const isSelf = me?.id === userId;
  return (
    <ProfileView
      profile={q.data!}
      canFollow={Boolean(me) && !isSelf}
      queryKey={["researcher", userId]}
    />
  );
}
