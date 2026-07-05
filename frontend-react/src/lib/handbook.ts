/** Open printable handbook (browser Save as PDF). */
export function openBeginnerHandbookPrint(): void {
  window.open("/handbook?print=1", "_blank", "noopener,noreferrer");
}
