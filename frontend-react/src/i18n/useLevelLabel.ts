import { useLocale } from "../store/locale";
import { levelLabel as labelForLevel } from "../i18n/dictionaries";

export function useLevelLabel(level: number): string {
  const locale = useLocale((s) => s.locale);
  return labelForLevel(locale, level);
}
