/** Canonical Factor Gym access — mirrors backend FACTOR_GYM_ACCESS_RESOLVER. */

export type FactorGymStatus = {
  FACTOR_GYM_ACCESS_ALLOWED?: boolean;
  allowed?: boolean;
  /** Legacy QUANTLAB_FACTOR_GYM flag only — never use alone for access. */
  enabled?: boolean;
  global_enabled?: boolean;
  open_beta?: boolean;
  test_entry?: boolean;
  label?: string;
  mode?: string;
  denied_detail?: string | null;
};

/**
 * Single frontend Gate. Never use ``enabled`` alone.
 */
export function isFactorGymAccessAllowed(status: FactorGymStatus | null | undefined): boolean {
  if (!status) return false;
  if (typeof status.FACTOR_GYM_ACCESS_ALLOWED === "boolean") {
    return status.FACTOR_GYM_ACCESS_ALLOWED;
  }
  if (typeof status.allowed === "boolean") {
    return status.allowed;
  }
  return false;
}
