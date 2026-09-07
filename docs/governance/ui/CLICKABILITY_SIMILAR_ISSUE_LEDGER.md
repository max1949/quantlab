# Clickability Similar-Issue Ledger (Challenge / Paper 500 fix round)

```text
READ_ONLY=NO
LEGACY_PAPER_PATH_REINTRODUCED=NO
```

## Root causes sealed this round

| ID | Pattern | Root cause | Fix |
|---|---|---|---|
| C1 | Challenge blue「30 天研究挑战」dead click | Control was a **challenge selector tab** (semantic D). With one challenge already selected, `onClick` set same `code` → no visual change; looked like primary CTA | Single challenge → status badge (not button). Multi → tabs with aria-pressed; selected marked「当前」 |
| C2 | Paper「启动 BTC 模拟」→ raw Axios 500 | Hardcoded BTC EMA FE bootstrap → paper-sandbox after canonical PaperRun closure; failures surfaced as `Request failed with status code 500` | Retired BTC bootstrap client helpers; Paper page only formal factor_sign; Chinese retired note |
| C3 | Raw HTTP errors to users | `apiErrorMessage` returned axios `err.message` | Map 4xx/5xx to Chinese actionable copy; never raw status-code string |
| C4 | first_paper_order only counted legacy paper_orders | After paper_orders 410, new users could never complete | Count PaperRun / fills; seal factor_sign runs into PaperRun; keep legacy credit read-only |
| C5 | paper_graduated CTA → /paper with weak label | Gate is quality `assess_factor_paper`, not PaperRun | CTA → `/projects` quality gap + Evidence OS secondary |

## Similar scan

| Area | Finding | Action |
|---|---|---|
| Nav 模拟交易 / 证据系统 / 挑战 | Links have valid `to` | OK |
| AI 创建策略 | Wired mutations | OK (demoted in nav) |
| 外部 自营客/决策场/TMOS | `target=_blank` href | OK |
| L4 PaperExecutionPanel | Was order CTA | Already retired → Evidence/Paper links |
| Mastery「去下 Paper 单」copy | Stage CTA updated earlier to Evidence | OK |
| research_quality「一键提交 Paper 订单」 | Legacy wording | Fixed this round |
| Certificate button disabled when incomplete | Looked like primary CTA while locked | Muted non-primary style + title + aria-disabled |
| Duplicate challenge CTAs in coaches | Link to `/challenges` | OK |

## Held (P2/P3)

- Dense JSON blocks on Evidence OS mobile
- English brand “QuantLab AI” in header
- Historical paper_orders GET still available for audit (intentional)

## Counts

```text
SIMILAR_CLICK_ISSUES_FOUND=8
SIMILAR_CLICK_ISSUES_FIXED=7
SIMILAR_CLICK_ISSUES_HELD=2
```
