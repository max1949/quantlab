import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyProfile } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { ErrorBox, PageTitle, Spinner } from "../components/ui";
import ProfileView from "../components/ProfileView";

export default function MyProfile() {
  const q = useQuery({ queryKey: ["my-profile"], queryFn: getMyProfile });

  if (q.isLoading) return <Spinner />;
  if (q.isError) return <ErrorBox message={apiErrorMessage(q.error)} />;

  return (
    <div>
      <PageTitle title="我的研究主页" />
      <ProfileView profile={q.data!} canFollow={false} queryKey={["my-profile"]} />
      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/me/referral" className="btn-ghost">
          邀请好友
        </Link>
        <Link to="/me/following" className="btn-ghost">
          关注动态
        </Link>
        <Link to="/projects" className="btn-ghost">
          我的项目
        </Link>
      </div>
    </div>
  );
}
