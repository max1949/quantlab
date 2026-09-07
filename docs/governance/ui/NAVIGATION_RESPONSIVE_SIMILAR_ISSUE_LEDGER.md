# Navigation Responsive Similar-Issue Ledger

```text
ACTIVITY=QUANTLAB_NAVIGATION_RESPONSIVE_FIX
HEADER_LAYOUT_LANGUAGE_INDEPENDENT=YES
DATABASE_CHANGE=NONE
LIVE_CHANGE=NONE
REAL_MONEY_CHANGE=NONE
QLN_11_STARTED=NO
```

## Root cause

`HEADER_RESPONSIVE_LAYOUT_DEFECT`

Desktop `<nav>` rendered **all** primary + external links with `shrink-0 whitespace-nowrap` inside `flex-1 justify-center`. English labels (`Desk`, `Evidence OS`, `Paper Trading`, …) exceeded remaining width between Brand and Theme/User rails → **visual overlap** (Desk into QuantLab AI; theme labels colliding). Desk did **not** use absolute/negative-margin overlay; it was flex overflow collision.

Chinese appeared “crowded but OK” only because shorter glyphs temporarily fit — language-dependent capacity, not a stable model.

## Priority IA (canonical)

| Priority | Items | Responsive behavior |
|---|---|---|
| P0 Brand | QuantLab AI | Zone A `shrink-0`, truncate label only, icon always visible |
| P1 Core | Desk, Evidence OS, Paper, Projects, Challenge | Always in primary strip (doctrine: PROVE_BEFORE_CAPITAL — Evidence not demoted) |
| P2 Secondary | Feed, Ranks, Team library, Plans | **More** menu |
| P3 External | About, Decision, TMOS | **More** menu |
| Controls | Theme, Locale, User | Zone D `shrink-0`; theme compact icons |

## Similar scan

| ID | Surface | Finding | Class |
|---|---|---|---|
| N1 | `Layout` desktop nav | All links shrink-0 + justify-center overflow into brand | **FIX** |
| N2 | `ThemeSwitcher` | Full Light/Dark/Auto text in header under EN | **FIX** (icon compact + title/aria) |
| N3 | `LanguageSwitcher` | OK width; align height with theme | **FIX** (h-8 align) |
| N4 | User + plan badge | Username + level badge push right rail | **FIX** (truncate; badge xl-only) |
| N5 | Mobile second row | `overflow-x-auto` entire nav + externals | **FIX** (wrap primary + More; no unexpected page scroll) |
| N6 | `BeginnerHandbookPage` header | Print/page title only, not app shell | **NOT_APPLICABLE** |
| N7 | Absolute user dropdown | Dropdown only; not nav overlap | **NOT_APPLICABLE** |
| N8 | Admin-only shell | No separate admin header in SPA | **NOT_APPLICABLE** |
| N9 | Evidence/Paper page secondary tabs | Tab row expanded document width | **FIX** (`min-w-0` + nested `w-max` scroll container) |
| N10 | Zoom 125% | Would worsen N1 without capacity model | **FIX** (covered by More + compact) |

## Counts

```text
SIMILAR_NAV_ISSUES_FOUND=10
SIMILAR_NAV_ISSUES_FIXED=7
SIMILAR_NAV_ISSUES_HELD=0
SIMILAR_NAV_ISSUES_NOT_APPLICABLE=3
```
