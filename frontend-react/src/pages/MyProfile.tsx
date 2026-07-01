import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyProfile } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import ProfileView from "../components/ProfileView";

export default function MyProfile() {
  const { dict } = useLocale();
  const t = dict.profile;
  const q = useQuery({ queryKey: ["my-profile"], queryFn: getMyProfile });

  if (q.isLoading) return <Spinner />;
  if (q.isError) return <ErrorBox message={apiErrorMessage(q.error)} />;

  return (
    <div>
      <PageTitle title={t.myTitle} />
      <ProfileView profile={q.data!} canFollow={false} queryKey={["my-profile"]} />
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/me/referral" className="btn-ghost">
          {t.inviteFriends}
        </Link>
        <Link to="/me/following" className="btn-ghost">
          {t.followingFeed}
        </Link>
        <Link to="/projects" className="btn-ghost">
          {t.myProjects}
        </Link>
      </div>
    </div>
  );
}
