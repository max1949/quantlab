const ADMIN_KEY = "ql_admin_key";

export function getAdminKey(): string | null {
  return sessionStorage.getItem(ADMIN_KEY);
}

export function setAdminKey(key: string | null): void {
  if (key) sessionStorage.setItem(ADMIN_KEY, key);
  else sessionStorage.removeItem(ADMIN_KEY);
}
