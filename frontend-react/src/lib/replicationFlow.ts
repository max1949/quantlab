import {
  FOLLOWING_PROJECT_REPLICATION_KEY,
  REPLICATION_FLOW_REPORT_KEY,
  REPLICATION_PUBLISH_FEED_KEY,
  REPLICATION_REPORT_WELCOME_KEY,
} from "./onboardingFocus";

export function resolveReplicationReportId(graphReportId?: string | null): string | null {
  if (graphReportId) return graphReportId;
  if (typeof window === "undefined") return null;
  return (
    sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) ||
    sessionStorage.getItem(REPLICATION_FLOW_REPORT_KEY) ||
    sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY)
  );
}

export function isReplicationReportFlow(reportId: string): boolean {
  if (typeof window === "undefined") return false;
  return (
    sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY) === reportId ||
    sessionStorage.getItem(REPLICATION_FLOW_REPORT_KEY) === reportId ||
    sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) === reportId
  );
}

export function isProjectReplicationFlow(projectId: string, reportId?: string | null): boolean {
  if (typeof window === "undefined") return false;
  if (sessionStorage.getItem(FOLLOWING_PROJECT_REPLICATION_KEY) === projectId) return true;
  const rid = reportId ?? resolveReplicationReportId(null);
  return Boolean(rid && isReplicationReportFlow(rid));
}

export function clearReplicationReportFlow(reportId: string) {
  if (sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY) === reportId) {
    sessionStorage.removeItem(REPLICATION_PUBLISH_FEED_KEY);
  }
  if (sessionStorage.getItem(REPLICATION_FLOW_REPORT_KEY) === reportId) {
    sessionStorage.removeItem(REPLICATION_FLOW_REPORT_KEY);
  }
  if (sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) === reportId) {
    sessionStorage.removeItem(REPLICATION_REPORT_WELCOME_KEY);
  }
}
