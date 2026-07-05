import {
  REPLICATION_FLOW_REPORT_KEY,
  REPLICATION_PUBLISH_FEED_KEY,
  REPLICATION_REPORT_WELCOME_KEY,
} from "./onboardingFocus";

export function isReplicationReportFlow(reportId: string): boolean {
  if (typeof window === "undefined") return false;
  return (
    sessionStorage.getItem(REPLICATION_PUBLISH_FEED_KEY) === reportId ||
    sessionStorage.getItem(REPLICATION_FLOW_REPORT_KEY) === reportId ||
    sessionStorage.getItem(REPLICATION_REPORT_WELCOME_KEY) === reportId
  );
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
