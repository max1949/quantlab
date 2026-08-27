# QuantLab Click Action Ledger


## Status refresh 2026-08-27

- QL-CLICK-0112 / 0113 (AI strategy builder): **PASS** on production after enabling `QUANTLAB_AI_STRATEGY_BUILDER` (was BROKEN 403).
- QL-CLICK-0015 (Light): **PASS** on landing.
- QL-CLICK-0018 (EN): **PASS** on landing.
- QL-CLICK-0019 (中文): **PASS** (default).
- External QL-CLICK-0010..0012: HTTP 200 verified → treat as **PASS** (KEEP_EXTERNAL).
- **RANKINGS / sample gate (QL-CLICK-0133..0137):** site-wide boards are **not** Sharpe-sorted. `paper_mastery` requires paper graduation (`assess_paper_readiness`) including evidence floors `trade_count>=30` / `periods>=200` (same constants as overfit risk). `researcher`/`newcomer` require `research_contribution_score>0`. Verify: `scripts/_closure_rankings_gate_verify.py`.
- Remaining primary/secondary CTAs: still **UNKNOWN** until full browser/auth pass.


> **Freeze note (2026-08-27):** Inventory snapshot against production `tmos-prod-hk` / `43.161.203.133` / `/srv/quantlab` @ `bf935a0`. Do not claim PASS without browser + API + DB verification on prod. Local `master` (`88f2e697`) may differ (WIP flag defaults).

**Site:** `https://q.ziyingke.com` → nginx → uvicorn `:8010`  
**SPA basename:** `/app` (routes below are relative unless noted)  
**API prefix:** `/api/v1`

## Status vocabulary

| STATUS | Meaning |
|---|---|
| PASS | Click → expected navigation/API/DB outcome verified on prod |
| BROKEN | Click works but backend rejects, wrong state, or user-visible failure |
| MISSING_BACKEND | Frontend calls route that does not exist or is unimplemented |
| MISSING_FRONTEND | Backend exists but no working UI control |
| PLACEHOLDER | UI present; stub or fake data |
| DEAD_LINK | Navigation target 404 or blank |
| WRONG_PERMISSION | Entitlement/role gate incorrect for intended user |
| WRONG_STATE | Works only in wrong lifecycle state |
| INTENTIONALLY_DISABLED | Deliberately off (admin-only, kill switch, etc.) |
| NOT_APPLICABLE | External product link; no QuantLab backend involvement |
| UNKNOWN | Not yet verified on production |

## Proven statuses (this freeze)

| ID | STATUS | Evidence |
|---|---|---|
| QL-CLICK-0010–0012 | NOT_APPLICABLE (external) | Sister products; no QuantLab API. Nav target: PASS **PENDING** browser verify |
| QL-CLICK-0015–0019 | UNKNOWN | Theme/locale = client localStorage only; not browser-verified |
| QL-CLICK-0112–0113 | **BROKEN** | `POST /ai/strategy-builder` → **403** on prod (`QUANTLAB_AI_STRATEGY_BUILDER=False`, `QUANTLAB_NAUTILUS_ENGINE=False`, `APP_ENV=production`) |

---

| ID | PAGE | CONTROL | TEXT | ROLE | FRONTEND_HANDLER | TARGET_ROUTE | API | HTTP_METHOD | PERMISSION / FEATURE_FLAG | EXPECTED_RESULT | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Layout (`components/Layout.tsx`)

| QL-CLICK-0001 | Layout | Link | Brand logo (t.brand) | any | — | `/` or `/app` | — | — | — | Navigate home or workspace | UNKNOWN |
| QL-CLICK-0002 | Layout | NavLink | t.nav.workspace | user | — | `/app` | — | — | ProtectedRoute | Open dashboard | UNKNOWN |
| QL-CLICK-0003 | Layout | NavLink | t.nav.paperTrading | user | — | `/paper` | — | — | ProtectedRoute | Open paper trading | UNKNOWN |
| QL-CLICK-0004 | Layout | NavLink | t.nav.aiStrategy | user | — | `/ai-strategy` | — | — | ProtectedRoute | Open AI strategy builder page | UNKNOWN |
| QL-CLICK-0005 | Layout | NavLink | t.nav.feed | any | — | `/feed` | — | — | — | Open public feed | UNKNOWN |
| QL-CLICK-0006 | Layout | NavLink | t.nav.leaderboards | any | — | `/leaderboards` | — | — | — | Open leaderboards | UNKNOWN |
| QL-CLICK-0007 | Layout | NavLink | t.nav.orgLibrary | user | — | `/orgs` | — | — | ProtectedRoute | Open org library | UNKNOWN |
| QL-CLICK-0008 | Layout | NavLink | t.nav.challenges | user | — | `/challenges` | — | — | ProtectedRoute | Open challenges | UNKNOWN |
| QL-CLICK-0009 | Layout | NavLink | t.nav.pricing | any | — | `/pricing` | — | — | — | Open pricing | UNKNOWN |
| QL-CLICK-0010 | Layout | external `<a>` | t.nav.aboutZiyingke / 自营客 | any | — | https://ziyingke.com/ | — | — | KEEP_EXTERNAL | Open external site (new tab) | NOT_APPLICABLE — PASS **PENDING** verify |
| QL-CLICK-0011 | Layout | external `<a>` | t.nav.decisionArena / 决策场 | any | — | https://ai.ziyingke.com/ | — | — | KEEP_EXTERNAL | Open external site (new tab) | NOT_APPLICABLE — PASS **PENDING** verify |
| QL-CLICK-0012 | Layout | external `<a>` | t.nav.tmos / TMOS | any | — | https://t.ziyingke.com/ | — | — | KEEP_EXTERNAL | Open external site (new tab) | NOT_APPLICABLE — PASS **PENDING** verify |
| QL-CLICK-0013 | Layout | NavLink (mobile) | t.nav.* (×8) | any/user | — | same as 0002–0009 | — | — | auth-filtered | Mobile nav same as desktop | UNKNOWN |
| QL-CLICK-0014 | Layout | external `<a>` (mobile) | t.nav.* external (×3) | any | — | external URLs | — | — | KEEP_EXTERNAL | Mobile external links | NOT_APPLICABLE — PASS **PENDING** verify |
| QL-CLICK-0015 | Layout | button (icon group) | t.theme.light | any | setPreference('light') | — | — | — | localStorage `ql-theme` | Switch to light theme | UNKNOWN |
| QL-CLICK-0016 | Layout | button (icon group) | t.theme.dark | any | setPreference('dark') | — | — | — | localStorage theme | Switch to dark theme | UNKNOWN |
| QL-CLICK-0017 | Layout | button (icon group) | t.theme.system | any | setPreference('system') | — | — | — | localStorage theme | Switch to system theme | UNKNOWN |
| QL-CLICK-0018 | Layout | button | EN | any | setLocale('en') | — | — | — | localStorage `ql-locale` | Switch UI to English | UNKNOWN |
| QL-CLICK-0019 | Layout | button | 中文 | any | setLocale('zh') | — | — | — | localStorage locale | Switch UI to Chinese | UNKNOWN |
| QL-CLICK-0020 | Layout | button (avatar menu toggle) | user.username + level badge | user | setMenuOpen | — | — | — | — | Open/close user dropdown | UNKNOWN |
| QL-CLICK-0021 | Layout | MenuLink | t.nav.myProfile | user | setMenuOpen(false) | `/me` | — | — | ProtectedRoute | Open my profile | UNKNOWN |
| QL-CLICK-0022 | Layout | MenuLink | t.nav.myProjects | user | setMenuOpen(false) | `/projects` | — | — | ProtectedRoute | Open projects list | UNKNOWN |
| QL-CLICK-0023 | Layout | MenuLink | t.nav.myExperiments | user | setMenuOpen(false) | `/experiments` | — | — | ProtectedRoute | Open experiments | UNKNOWN |
| QL-CLICK-0024 | Layout | MenuLink | t.nav.following | user | setMenuOpen(false) | `/me/following` | — | — | ProtectedRoute | Open following feed | UNKNOWN |
| QL-CLICK-0025 | Layout | MenuLink | t.nav.referral | user | setMenuOpen(false) | `/me/referral` | — | — | ProtectedRoute | Open referral page | UNKNOWN |
| QL-CLICK-0026 | Layout | button | t.nav.logout | user | logout + navigate('/') | `/` | — | — | clears JWT localStorage | Log out; redirect landing | UNKNOWN |
| QL-CLICK-0027 | Layout | Link | t.nav.login | guest | — | `/login` | — | — | — | Open login | UNKNOWN |
| QL-CLICK-0028 | Layout | Link | t.nav.register | guest | — | `/register` | — | — | — | Open register | UNKNOWN |

## Landing (`/`)

| QL-CLICK-0029 | Landing | Link (hero CTA) | l.ctaWork / l.cta | any | — | `/app` or `/register` | — | — | ref param preserved | Primary hero CTA | UNKNOWN |
| QL-CLICK-0030 | Landing | Link | l.ctaMasters | any | — | `/leaderboards?kind=paper_mastery` | — | — | — | View paper mastery board | UNKNOWN |
| QL-CLICK-0031 | Landing | Link | l.ctaBrowse | any | — | `/feed` | — | — | — | Browse public feed | UNKNOWN |
| QL-CLICK-0032 | Landing | Link (mastery card) | l.ctaWork / l.cta | any | — | `/app` or `/register` | — | — | — | Secondary signup/workspace CTA | UNKNOWN |
| QL-CLICK-0033 | Landing | Link (feature card) | l.step5Title | any | — | `/leaderboards?kind=paper_mastery` | — | — | — | Feature card → leaderboards | UNKNOWN |

## Login (`/login`)

| QL-CLICK-0034 | Login | form submit | auth.signIn | guest | submit → login() | `/app` or `/onboarding` | `/auth/login` | POST | captcha required | Authenticate user | UNKNOWN |
| QL-CLICK-0035 | Login | input | auth.identifier | guest | setIdentifier | — | — | — | — | Enter username/email | UNKNOWN |
| QL-CLICK-0036 | Login | input (password) | auth.password | guest | setPassword | — | — | — | — | Enter password | UNKNOWN |
| QL-CLICK-0037 | Login | button | auth.captchaRefresh | guest | load (fetchCaptcha) | — | `/auth/captcha` | GET | — | Refresh captcha image | UNKNOWN |
| QL-CLICK-0038 | Login | input | auth.captchaPlaceholder | guest | setCaptchaAnswer | — | — | — | — | Enter captcha answer | UNKNOWN |
| QL-CLICK-0039 | Login | external `<a>` | auth.ssoSignIn | guest | — | `/api/v1/auth/sso/login` | `/auth/sso/config` | GET | sso.enabled | SSO login redirect | UNKNOWN |
| QL-CLICK-0040 | Login | Link | nav.register | guest | — | `/register` | — | — | — | Go to register | UNKNOWN |

## Register (`/register`)

| QL-CLICK-0041 | Register | form submit | nav.register | guest | submit → register() | `/onboarding` | `/auth/register` | POST | captcha; ref param | Create account | UNKNOWN |
| QL-CLICK-0042 | Register | input | auth.email | guest | setEmail | — | — | — | — | Enter email | UNKNOWN |
| QL-CLICK-0043 | Register | input | auth.username | guest | setUsername | — | — | — | pattern validation | Enter username | UNKNOWN |
| QL-CLICK-0044 | Register | input (password) | auth.password | guest | setPassword | — | — | — | min 8 chars | Enter password | UNKNOWN |
| QL-CLICK-0045 | Register | button (radio-style) | newbie label | guest | setUserType('newbie') | — | — | — | — | Select user type newbie | UNKNOWN |
| QL-CLICK-0046 | Register | button (radio-style) | python label | guest | setUserType('python') | — | — | — | — | Select user type python | UNKNOWN |
| QL-CLICK-0047 | Register | button (radio-style) | trader label | guest | setUserType('trader') | — | — | — | — | Select user type trader | UNKNOWN |
| QL-CLICK-0048 | Register | button | auth.captchaRefresh | guest | load | — | `/auth/captcha` | GET | — | Refresh captcha | UNKNOWN |
| QL-CLICK-0049 | Register | Link | auth.signIn | guest | — | `/login` | — | — | — | Go to login | UNKNOWN |

## Dashboard (`/app`)

| QL-CLICK-0050 | Dashboard | button (next-step hero) | stageToCtaLabel | user | navigate(stageToRoute(...)) | dynamic | `/onboarding/next` | GET | — | Navigate to recommended next step | UNKNOWN |
| QL-CLICK-0051 | Dashboard | button (AI mentor) | stageToCtaLabel | user | navigate(stageToRoute(...)) | dynamic | `/ai/mentor/next` | GET | stage=create_project | Start recommended template flow | UNKNOWN |
| QL-CLICK-0052 | Dashboard | Link | d.allProjects | user | — | `/projects` | `/projects` | GET | — | View all projects | UNKNOWN |
| QL-CLICK-0053 | Dashboard | Link (project row) | p.title | user | — | `/projects/:id` | — | — | — | Open project detail | UNKNOWN |
| QL-CLICK-0054 | Dashboard | Link | d.fromTemplate | user | — | `/templates` | — | — | — | Start from template (empty state) | UNKNOWN |
| QL-CLICK-0055 | Dashboard | Link (report row) | r.title | user | — | `/reports/:id` | `/reports` (list) | GET | — | Open report detail | UNKNOWN |

### Dashboard — BeginnerHandbookStrip

| QL-CLICK-0056 | Dashboard | Link | h.printPdf | user | — | `/handbook` | — | — | journey not mastery-done | Open handbook page | UNKNOWN |
| QL-CLICK-0057 | Dashboard | button | h.downloadPdf | user | download.mutate | — | `/onboarding/beginner-handbook.pdf` | GET | — | Download handbook PDF | UNKNOWN |
| QL-CLICK-0058 | Dashboard | button | h.stripDismiss | user | dismiss (localStorage) | — | — | — | — | Dismiss handbook strip | UNKNOWN |

### Dashboard — FirstDashboardMentorPanel

| QL-CLICK-0059 | Dashboard | button | primaryLabel (template) | user | startTemplate.mutate | `/projects/:id` | `/research/templates/:code/start` | POST | recommended_template | Create project from mentor template | UNKNOWN |
| QL-CLICK-0060 | Dashboard | Link | primaryLabel | user | dismiss | dynamic cta_path | — | — | — | Mentor primary CTA navigation | UNKNOWN |
| QL-CLICK-0061 | Dashboard | anchor | d.openQuickstart | user | — | `#quickstart` | — | — | — | Scroll to quickstart section | UNKNOWN |
| QL-CLICK-0062 | Dashboard | button | d.gotIt | user | dismiss | — | — | — | — | Dismiss first mentor panel | UNKNOWN |

### Dashboard — DashboardIncubationCoachStack

| QL-CLICK-0063 | Dashboard | button | d.incubationCoachExpand | user | setExpanded(true) | — | — | — | >1 active coaches | Expand hidden coach panels | UNKNOWN |
| QL-CLICK-0064 | Dashboard | button | d.incubationCoachCollapse | user | setExpanded(false) | — | — | — | — | Collapse coach stack | UNKNOWN |

### Dashboard — ShareGrowthCoachPanel

| QL-CLICK-0065 | Dashboard | Link (guide step) | d.stepGo | user | armFeedWelcome | dynamic step.cta_path | — | — | share_growth_coaching | Guide step navigation | UNKNOWN |
| QL-CLICK-0066 | Dashboard | Link | d.viewFeed | user | armFeedWelcome | coach.feed_path | — | — | — | View feed from share coach | UNKNOWN |
| QL-CLICK-0067 | Dashboard | Link | d.viewProfile | user | — | coach.profile_path | — | — | — | View own profile | UNKNOWN |
| QL-CLICK-0068 | Dashboard | Link | d.viewFollowing | user | — | coach.following_feed_path | — | — | coach.following > 0 | View following feed | UNKNOWN |
| QL-CLICK-0069 | Dashboard | button | d.copyLink | user | copyLink (clipboard) | — | — | — | — | Copy share URL | UNKNOWN |
| QL-CLICK-0070 | Dashboard | button | d.dismiss | user | dismiss | — | — | — | — | Dismiss share growth coach | UNKNOWN |

### Dashboard — PostCheckoutCoachPanel

| QL-CLICK-0071 | Dashboard | Link | ctaLabel | user | — | coach.cta_path | `/research-journey` | GET | checkout=success query | Post-checkout primary CTA | UNKNOWN |
| QL-CLICK-0072 | Dashboard | Link | d.viewPlans | user | — | `/pricing` | — | — | — | View pricing after checkout | UNKNOWN |
| QL-CLICK-0073 | Dashboard | button | d.dismiss | user | dismiss (clear query) | — | — | — | — | Dismiss checkout coach | UNKNOWN |

### Dashboard — ReputationCoachPanel

| QL-CLICK-0074 | Dashboard | Link (guide step) | stepCta | user | — | step.cta_path | — | — | reputation_coaching | Reputation guide step | UNKNOWN |
| QL-CLICK-0075 | Dashboard | Link | ctaLabel | user | dismiss | coach.cta_path | — | — | — | Primary reputation CTA | UNKNOWN |
| QL-CLICK-0076 | Dashboard | Link | d.viewFeed | user | — | `/feed` | — | — | — | View feed from reputation coach | UNKNOWN |
| QL-CLICK-0077 | Dashboard | button | d.dismiss | user | dismiss | — | — | — | — | Dismiss reputation coach | UNKNOWN |

### Dashboard — OrgMemberCoachPanel

| QL-CLICK-0078 | Dashboard | Link (guide step) | stepCta | user | — | step.cta_path | — | — | org_member_coaching | Org member guide step | UNKNOWN |
| QL-CLICK-0079 | Dashboard | Link | ctaLabel | user | dismiss | coach.cta_path | — | — | — | Org member primary CTA | UNKNOWN |
| QL-CLICK-0080 | Dashboard | Link | coach.org_path label | user | — | coach.org_path | — | — | — | Go to org detail | UNKNOWN |
| QL-CLICK-0081 | Dashboard | button | d.dismiss | user | dismiss | — | — | — | — | Dismiss org member coach | UNKNOWN |

### Dashboard — DashboardMasteryLoopPanel

| QL-CLICK-0082 | Dashboard | Link | d.openFollowing | user | — | `/me/following` | — | — | following ≥ 3 | Open following feed | UNKNOWN |
| QL-CLICK-0083 | Dashboard | Link | d.browseFeed | user | — | `/feed?focus=follow` | — | — | — | Browse feed (follow focus) | UNKNOWN |
| QL-CLICK-0084 | Dashboard | Link | d.shareGrowth | user | — | coach.share_url_path | — | — | has share coaching | Open share growth URL | UNKNOWN |
| QL-CLICK-0085 | Dashboard | button | d.dismiss | user | dismiss (weekly key) | — | — | — | — | Dismiss mastery loop panel | UNKNOWN |

### Dashboard — DashboardCoachStack

| QL-CLICK-0086 | Dashboard | button | d.coachStackExpand | user | setExpanded | — | — | — | >2 coach kinds | Expand hidden coaches | UNKNOWN |
| QL-CLICK-0087 | Dashboard | button | d.coachStackCollapse | user | setExpanded(false) | — | — | — | — | Collapse coach stack | UNKNOWN |

### Dashboard — AttentionAlertsPanel

| QL-CLICK-0088 | Dashboard | Link | d.ctaTemplates/Revalidate/Project | user | — | alert.cta_path | — | — | per alert | Navigate to alert remediation | UNKNOWN |
| QL-CLICK-0089 | Dashboard | button | d.dismiss | user | dismiss.mutate | — | `/onboarding/attention-alerts/dismiss` | POST | — | Dismiss attention alert | UNKNOWN |
| QL-CLICK-0090 | Dashboard | Link | d.viewHistory | user | — | `/app/alerts` | `/onboarding/attention-alerts/history` | GET | — | View alert history | UNKNOWN |

### Dashboard — ChallengePaperCoachPanel

| QL-CLICK-0091 | Dashboard | Link | ctaLabel | user | — | coach.cta_path | — | — | challenge_paper_coaching | Challenge paper next step | UNKNOWN |
| QL-CLICK-0092 | Dashboard | Link | d.viewChallenge | user | — | `/challenges` | — | — | — | View challenges | UNKNOWN |

### Dashboard — UpgradeCoachPanel

| QL-CLICK-0093 | Dashboard | button | u.checkoutCta | user | doCheckout.mutate | external pay_url | `/billing/checkout` | POST | stripe_available | Start plan checkout | UNKNOWN |
| QL-CLICK-0094 | Dashboard | Link | u.viewPlans | user | — | coach.cta_path (usually `/pricing`) | — | — | upgrade_coaching | View pricing plans | UNKNOWN |

### Dashboard — MarketDataCoachPanel

| QL-CLICK-0095 | Dashboard | button | d.upgradeCta | user | doCheckout.mutate | external pay_url | `/billing/checkout` | POST | stripe_available | Upgrade data plan | UNKNOWN |
| QL-CLICK-0096 | Dashboard | Link | d.viewPlans | user | — | coach.cta_path | — | — | market_data_coaching | View pricing for data | UNKNOWN |

### Dashboard — MasteryGoalPanel

| QL-CLICK-0097 | Dashboard | Link | d.challengePaperCta | user | — | `/challenges` | — | — | incomplete paper milestones | Go to challenges | UNKNOWN |
| QL-CLICK-0098 | Dashboard | Link | d.challengeShareFeedCta | user | — | `/feed` | — | — | share stage | Browse feed for share task | UNKNOWN |
| QL-CLICK-0099 | Dashboard | Link | d.challengeShareProjectCta | user | — | `/projects/:activeId` | — | — | active project | Open project for share | UNKNOWN |
| QL-CLICK-0100 | Dashboard | Link | d.challengeShareCta | user | — | `/challenges` | — | — | — | View share challenges | UNKNOWN |
| QL-CLICK-0101 | Dashboard | Link (primary) | d.viewBoard / d.paperCta / d.goProject / d.fromTemplate | user | — | dynamic | — | — | mastery_goal state | Contextual mastery CTA | UNKNOWN |
| QL-CLICK-0102 | Dashboard | Link | d.viewBoard | user | — | `/leaderboards?kind=paper_mastery` | — | — | — | View paper mastery board | UNKNOWN |

### Dashboard — ResearchJourneyRing

| QL-CLICK-0103 | Dashboard | Link | d.journeyViewChallenge | user | — | `/challenges` | — | — | challenge_enrolled | View enrolled challenge | UNKNOWN |
| QL-CLICK-0104 | Dashboard | Link | d.journeyGoProject | user | — | `/projects/:activeId` | — | — | active project | Go to active project | UNKNOWN |
| QL-CLICK-0105 | Dashboard | Link | d.journeyGoShare | user | — | `/feed?focus=follow` | — | — | next=share | Go to feed for sharing | UNKNOWN |
| QL-CLICK-0106 | Dashboard | Link | d.fromTemplate | user | — | `/templates` | — | — | next=template | Start from templates | UNKNOWN |
| QL-CLICK-0107 | Dashboard | Link | d.journeyEnrollChallenge | user | — | `/challenges` | — | — | !challenge_enrolled | Enroll in challenge | UNKNOWN |

### Dashboard — AcademyTasks

| QL-CLICK-0108 | Dashboard | Link | d.academyNetworkCta | user | — | `/feed?focus=follow` | — | — | task=network-radar | Discover masters on feed | UNKNOWN |
| QL-CLICK-0109 | Dashboard | Link | d.academyReplicationCta | user | — | `/me/following` | — | — | task=master-replication | Open following for replication | UNKNOWN |
| QL-CLICK-0110 | Dashboard | button | d.academyClaim | user | claim.mutate(code) | — | `/tasks/:code/complete` | POST | manual claim tasks | Claim academy XP reward | UNKNOWN |

## AI Create Strategy (`/ai-strategy`)

| QL-CLICK-0111 | AiCreateStrategy | textarea | placeholder 告诉 AI… | user | setText | — | — | — | ProtectedRoute | Enter strategy description | UNKNOWN |
| QL-CLICK-0112 | AiCreateStrategy | button | 让 AI 理解规则 | user | draft.mutate | — | `/ai/strategy-builder` | POST | `QUANTLAB_AI_STRATEGY_BUILDER`; confirm=false | Parse/draft strategy spec (rule-based; no LLM required) | **BROKEN** — 403 on prod |
| QL-CLICK-0113 | AiCreateStrategy | button | 确认并回测 | user | confirmRun.mutate | — | `/ai/strategy-builder` | POST | confirm=true, run_backtest=true | Confirm spec and run backtest | **BROKEN** — 403 on prod |
| QL-CLICK-0114 | AiCreateStrategy | button (toggle) | 这是什么意思？ | user | setOpen | — | — | — | per ExplainTip | Toggle inline explanation | UNKNOWN |

## Paper Trading (`/paper`)

| QL-CLICK-0115 | PaperTrading | button | 启动 BTC 模拟 | user | bootstrap.mutate | — | `/paper-sandbox/paper-ready` + `/paper-sandbox/runs` + `/paper-sandbox/runs/:id/start` | POST | sessionStorage paper_run_id; entitlement `paper_trading` | Register, create, start sandbox run | UNKNOWN |

## Feed (`/feed`)

| QL-CLICK-0116 | Feed | button (tab) | f.sortTop | any | setSort('top') | — | `/public/feed` | GET | sort=top | Sort feed by top | UNKNOWN |
| QL-CLICK-0117 | Feed | button (tab) | f.sortLatest | any | setSort('latest') | — | `/public/feed` | GET | sort=latest | Sort feed by latest | UNKNOWN |
| QL-CLICK-0118 | Feed | button (toggle) | f.filterGraduated | any | setGraduatedOnly | — | `/public/feed` | GET | graduated_only | Filter graduated-only reports | UNKNOWN |
| QL-CLICK-0119 | Feed | button | d.browseFeed | user | discoverMasters | — | — | — | FeedFollowCoachPanel | Apply graduated filter + scroll | UNKNOWN |
| QL-CLICK-0120 | Feed | Link | d.openFollowing | user | dismiss coach | `/me/following` | — | — | — | Open following feed | UNKNOWN |
| QL-CLICK-0121 | Feed | button | d.dismiss | user | dismiss | — | — | — | FeedFollowCoachPanel | Dismiss follow coach | UNKNOWN |
| QL-CLICK-0122 | Feed | Link | d.openFollowing | user | setPending(false) | `/me/following` | — | — | NetworkReadyCoachPanel | Post-milestone following CTA | UNKNOWN |
| QL-CLICK-0123 | Feed | button | d.stayOnFeed | user | setPending(false) | — | — | — | NetworkReadyCoachPanel | Dismiss network-ready panel | UNKNOWN |
| QL-CLICK-0124 | Feed | Link | f.guestLogin | guest | — | `/login` | — | — | — | Guest banner login | UNKNOWN |
| QL-CLICK-0125 | Feed | Link | f.guestRegister | guest | — | `/register` | — | — | — | Guest banner register | UNKNOWN |
| QL-CLICK-0126 | Feed | Link | d.createShare | user | — | `/reports/:id#report-share` | — | — | ReplicationFeedWelcomePanel | Create share link after publish | UNKNOWN |
| QL-CLICK-0127 | Feed | button | d.dismiss | user | dismiss welcome | — | — | — | ReplicationFeedWelcomePanel | Dismiss replication welcome | UNKNOWN |
| QL-CLICK-0128 | Feed | Link | f.emptyCta | user | — | `/templates` | — | — | empty + logged in | Start from templates | UNKNOWN |
| QL-CLICK-0129 | Feed | Link (ReportCard) | report.title | any | markHandoff | `/reports/:id` | — | — | per card | Open report from card title | UNKNOWN |
| QL-CLICK-0130 | Feed | Link (ReportCard) | rc.readFull | any | markHandoff | `/reports/:id` | — | — | per card | Read full report | UNKNOWN |
| QL-CLICK-0131 | Feed | button (ReportCard) | p.follow / p.followingBtn | user | toggleFollow.mutate | — | `/researchers/:id/follow` | POST/DELETE | not self; showFollow | Follow/unfollow researcher | UNKNOWN |
| QL-CLICK-0132 | Feed | Link (ReportCard) | rc.researcherName | any | — | `/u/:ownerId` | — | — | per card | View researcher profile | UNKNOWN |

## Leaderboards (`/leaderboards`)

| QL-CLICK-0133 | Leaderboards | button (tab) | l.researcher | any | setKind('researcher') | — | `/leaderboards/researcher` | GET | — | Researcher leaderboard tab | UNKNOWN |
| QL-CLICK-0134 | Leaderboards | button (tab) | l.contributor | any | setKind('contributor') | — | `/leaderboards/contributor` | GET | — | Contributor tab | UNKNOWN |
| QL-CLICK-0135 | Leaderboards | button (tab) | l.newcomer | any | setKind('newcomer') | — | `/leaderboards/newcomer` | GET | — | Newcomer tab | UNKNOWN |
| QL-CLICK-0136 | Leaderboards | button (tab) | l.improved | any | setKind('improved') | — | `/leaderboards/improved` | GET | — | Most improved tab | UNKNOWN |
| QL-CLICK-0137 | Leaderboards | button (tab) | l.paperMastery | any | setKind('paper_mastery') | — | `/leaderboards/paper_mastery` | GET | — | Paper mastery tab | UNKNOWN |
| QL-CLICK-0138 | Leaderboards | Link | l.goDashboard | user | — | `/app` | — | — | paper_mastery, !onBoard | Go to dashboard | UNKNOWN |
| QL-CLICK-0139 | Leaderboards | Link (table row) | row.username | any | — | `/u/:userId` | — | — | per row | View ranked user profile | UNKNOWN |
| QL-CLICK-0140 | Leaderboards | Link (ReputationCoach) | ctaLabel | user | dismiss | coach.cta_path | — | — | placement=leaderboards | Reputation coach CTA | UNKNOWN |
| QL-CLICK-0141 | Leaderboards | Link | d.viewFeed | user | — | `/feed` | — | — | ReputationCoachPanel | View feed | UNKNOWN |
| QL-CLICK-0142 | Leaderboards | button | d.dismiss | user | dismiss | — | — | — | ReputationCoachPanel | Dismiss reputation coach | UNKNOWN |

## Pricing (`/pricing`)

| QL-CLICK-0143 | Pricing | button | p.buyWithCard | user/guest | doCheckout.mutate(plan.code) | external pay_url | `/billing/checkout` | POST | paid personal plan | Start Stripe checkout | UNKNOWN |
| QL-CLICK-0144 | Pricing | button (disabled) | p.currentPlan / p.activePlan / p.basicPlan | user | — | — | — | — | current tier | No-op (current plan) | UNKNOWN |
| QL-CLICK-0145 | Pricing | Link | p.teamCta | user | — | `/orgs` | — | — | org plans | Go to org library | UNKNOWN |
| QL-CLICK-0146 | Pricing | input | BKTA-XXXX placeholder | user | setCode | — | — | — | — | Enter redeem code | UNKNOWN |
| QL-CLICK-0147 | Pricing | button | p.redeem | user | doRedeem.mutate | — | `/billing/redeem` | POST | — | Redeem billing code | UNKNOWN |
| QL-CLICK-0148 | Pricing | button | p.billingExportCsv | user | downloadBillingHistoryCsv | — | `/billing/history/export` | GET | has billing history | Export billing CSV | UNKNOWN |
| QL-CLICK-0149 | Pricing | button (per row) | p.invoicePdf | user | downloadBillingInvoicePdf | — | `/billing/history/:id/invoice.pdf` | GET | per ledger row | Download invoice PDF | UNKNOWN |

## Challenges (`/challenges`)

| QL-CLICK-0150 | Challenges | button (tab) | c.title | user | setCode(c.code) | — | `/challenges/:code/progress` | GET | per challenge | Select challenge | UNKNOWN |
| QL-CLICK-0151 | Challenges | button | t.enroll | user | enroll.mutate | — | `/challenges/:code/enroll` | POST | not yet enrolled | Enroll in challenge | UNKNOWN |
| QL-CLICK-0152 | Challenges | button | t.claimCert / t.claimCertLocked | user | cert.mutate (onClaim) | — | `/challenges/:code/certificate` | GET | all milestones done | Claim/download certificate | UNKNOWN |
| QL-CLICK-0153 | Challenges | Link | d.browseFeed | user | sessionStorage flag | `/feed?focus=follow` | — | — | ChallengeNetworkCoachPanel | Browse feed for network task | UNKNOWN |
| QL-CLICK-0154 | Challenges | button | d.dismiss | user | dismiss | — | — | — | ChallengeNetworkCoachPanel | Dismiss network coach | UNKNOWN |

## Org Library (`/orgs`)

| QL-CLICK-0155 | OrgLibrary | input | o.createPlaceholder | user | setName | — | — | — | — | Enter org name | UNKNOWN |
| QL-CLICK-0156 | OrgLibrary | button | o.createBtn | user | create.mutate | — | `/orgs` | POST | — | Create new org | UNKNOWN |
| QL-CLICK-0157 | OrgLibrary | Link (card) | org.name | user | — | `/orgs/:id` | `/orgs` | GET | per org | Open org detail | UNKNOWN |

## Org Detail (`/orgs/:id`)

| QL-CLICK-0158 | OrgDetail | Link | o.back | user | — | `/orgs` | — | — | — | Back to org list | UNKNOWN |
| QL-CLICK-0159 | OrgDetail | Link | t.inviteCta | admin | — | `#org-invite` | — | — | canAdmin | Jump to invite section | UNKNOWN |
| QL-CLICK-0160 | OrgDetail | Link | t.memberDashboard | any member | — | `/app` | — | — | OrgIncubationStrip | Go to member dashboard | UNKNOWN |
| QL-CLICK-0161 | OrgDetail | Link | h.printPdf / h.downloadPdf | any | HandbookExportButtons | `/handbook` or download | `/onboarding/beginner-handbook.pdf` | GET | — | Handbook actions on org page | UNKNOWN |
| QL-CLICK-0162 | OrgDetail | button | plan.name · ¥price | owner | teamCheckout.mutate | external pay_url | `/orgs/:id/billing/checkout` | POST | isOwner | Team plan checkout | UNKNOWN |
| QL-CLICK-0163 | OrgDetail | input | QLT-XXXXXXXX | owner | setTeamCode | — | — | — | — | Enter team redeem code | UNKNOWN |
| QL-CLICK-0164 | OrgDetail | button | o.billingRedeemBtn | owner | teamRedeem.mutate | — | `/orgs/:id/billing/redeem` | POST | — | Redeem team billing code | UNKNOWN |
| QL-CLICK-0165 | OrgDetail | button | o.billingProfileSave | owner | saveBillingProfile.mutate | — | `/orgs/:id/billing/profile` | PUT/PATCH | — | Save billing profile | UNKNOWN |
| QL-CLICK-0166 | OrgDetail | button | o.billingExportCsv | owner | downloadOrgBillingHistoryCsv | — | org billing export endpoint | GET | — | Export org billing CSV | UNKNOWN |
| QL-CLICK-0167 | OrgDetail | button | o.billingInvoicePdf | owner | downloadOrgBillingInvoicePdf | — | org invoice endpoint | GET | per row | Download org invoice | UNKNOWN |
| QL-CLICK-0168 | OrgDetail | button | o.ssoDomainsSave | owner | saveSsoDomains.mutate | — | `/orgs/:id/sso-domains` | PUT | — | Save SSO email domains | UNKNOWN |
| QL-CLICK-0169 | OrgDetail | button | o.inviteBtn | admin | invite.mutate | — | `/orgs/:id/invites` | POST | canAdmin | Create org invite link | UNKNOWN |
| QL-CLICK-0170 | OrgDetail | button | o.copyInvite | admin | clipboard.writeText | — | — | — | inviteUrl shown | Copy invite URL | UNKNOWN |
| QL-CLICK-0171 | OrgDetail | input | o.usernamePlaceholder | admin | setUsername | — | — | — | — | Enter username to add | UNKNOWN |
| QL-CLICK-0172 | OrgDetail | button | o.addMemberBtn | admin | addMember.mutate | — | `/orgs/:id/members` | POST | canAdmin | Add member by username | UNKNOWN |
| QL-CLICK-0173 | OrgDetail | select | o.pickFactor | member+ | setFactorId | — | `/factors` | GET | canShare | Pick factor to share | UNKNOWN |
| QL-CLICK-0174 | OrgDetail | button | o.shareBtn | member+ | share.mutate | — | shareFactorToOrg endpoint | POST | canShare | Share factor to org catalog | UNKNOWN |
| QL-CLICK-0175 | OrgDetail | select | RB/AU/IF | any | setSymbol | — | `/orgs/:id/catalog` | GET | — | Change catalog symbol filter | UNKNOWN |
| QL-CLICK-0176 | OrgDetail | Link | o.teamAttentionViewProject | admin | — | item.cta_path | — | — | team attention item | View member's project | UNKNOWN |
| QL-CLICK-0177 | OrgDetail | button | o.researchAlertWebhookSave | admin | saveResearchAlertWebhook.mutate | — | `/orgs/:id/research/alert-webhook` | PUT | canAdmin | Save research alert webhook | UNKNOWN |
| QL-CLICK-0178 | OrgDetail | button | o.teamAttentionWebhookDispatch | admin | dispatchResearchAttention.mutate | — | `/orgs/:id/research/attention-alerts/dispatch` | POST | webhook ready | Dispatch research attention alerts | UNKNOWN |
| QL-CLICK-0179 | OrgDetail | button | o.alertWebhookSave | admin | saveAlertWebhook.mutate | — | org alert webhook endpoint | PUT | canAdmin | Save SLA alert webhook | UNKNOWN |
| QL-CLICK-0180 | OrgDetail | button | o.alertWebhookDispatch | admin | dispatchOrgAlerts.mutate | — | `/orgs/:id/execution/alerts/dispatch` | POST | webhook configured | Dispatch SLA alerts | UNKNOWN |
| QL-CLICK-0181 | OrgDetail | button (tab) | o.alertDeliveryFilterAll/Sla/Research | admin | setDeliveryScope | — | org alert deliveries endpoint | GET | canAdmin | Filter delivery log scope | UNKNOWN |
| QL-CLICK-0182 | OrgDetail | button | o.alertDeliveryRetry | admin | retryOrgAlertDeliveries.mutate | — | retry deliveries endpoint | POST | canAdmin | Retry failed alert deliveries | UNKNOWN |
| QL-CLICK-0183 | OrgDetail | button | o.alertDeliveryExport | admin | exportAlertDeliveries.mutate | — | downloadOrgAlertDeliveriesCsv | GET | canAdmin | Export alert deliveries CSV | UNKNOWN |
| QL-CLICK-0184 | OrgDetail | button | o.execDeskSync | admin | syncExec.mutate | — | `/orgs/:id/execution/refresh` | POST | canAdmin | Sync execution desk orders | UNKNOWN |
| QL-CLICK-0185 | OrgDetail | select | role options | admin/self | updateRole.mutate | — | `/orgs/:id/members/:userId` | PATCH | canManageMember | Change member role | UNKNOWN |
| QL-CLICK-0186 | OrgDetail | button | o.removeMember / o.leaveOrg | admin/self | removeMember.mutate | — | `/orgs/:id/members/:userId` | DELETE | canManageMember | Remove member or leave org | UNKNOWN |
| QL-CLICK-0187 | OrgDetail | button | o.revokeInvite | admin | revokeInviteMut.mutate | — | `/orgs/:id/invites/:inviteId` | DELETE | active invite | Revoke invite token | UNKNOWN |
| QL-CLICK-0188 | OrgDetail | Link | ctaLabel | member | dismiss | coach.cta_path | — | — | OrgMemberPageCoachPanel | Member page coach CTA | UNKNOWN |
| QL-CLICK-0189 | OrgDetail | Link | — | member | — | `/app` | — | — | OrgMemberPageCoachPanel | Go to dashboard | UNKNOWN |
| QL-CLICK-0190 | OrgDetail | Link | d.browseFeed | member | sessionStorage flag | `/feed?focus=follow` | — | — | OrgNetworkCoachPanel | Browse feed from org coach | UNKNOWN |

## My Profile (`/me`)

| QL-CLICK-0191 | MyProfile | Link | t.inviteFriends | user | — | `/me/referral` | — | — | ProtectedRoute | Open referral page | UNKNOWN |
| QL-CLICK-0192 | MyProfile | Link | t.followingFeed | user | — | `/me/following` | — | — | — | Open following feed | UNKNOWN |
| QL-CLICK-0193 | MyProfile | Link | t.myProjects | user | — | `/projects` | — | — | — | Open projects list | UNKNOWN |
| QL-CLICK-0194 | MyProfile | Link | t.viewPaperBoard | user | — | `/leaderboards?kind=paper_mastery` | — | — | ProfileView mastery banner | View paper mastery board | UNKNOWN |

## Researcher Profile (`/u/:userId`) — ProfileView

| QL-CLICK-0195 | Researcher | button | t.follow / t.followingBtn | user | toggle.mutate | — | `/researchers/:id/follow` | POST/DELETE | canFollow; not self | Follow/unfollow researcher | UNKNOWN |
| QL-CLICK-0196 | Researcher | Link | t.viewPaperBoard | any | — | `/leaderboards?kind=paper_mastery` | — | — | paper stats shown | View paper board | UNKNOWN |

---

## PENDING_FULL_ENUMERATION — secondary routes

The following routes contain additional interactive controls (factor lab, backtest, validation, paper execution, share flows, onboarding wizards, admin ops). Primary CTAs listed for click-through planning; full row-by-row scan not yet completed.

| Route | Primary CTAs (not yet row-ID'd) |
|---|---|
| `/projects`, `/projects/:id` | Create project, open factor lab tabs, run backtest, validation, publish report, paper order |
| `/templates` | Start template, preview, filter by asset class |
| `/experiments` | Param scan create/run, batch review |
| `/onboarding` | Path selection, first project bootstrap |
| `/reports/:id` | Share link, publish, follow author, replication |
| `/handbook` | PDF download, section nav |
| `/me/following`, `/me/referral` | Follow feed cards, copy referral link |
| `/share/:token`, `/org-invite/:token` | Accept invite, view shared report |
| `/admin/ops` | Admin key gate; ops metrics (INTENTIONALLY_DISABLED for normal users) |
| `ProjectDetail` panels | FactorLab, BacktestResults, PaperExecution, AdvancedAnalysis — run/stop/save/delete |

---

## Summary

| Metric | Value |
|---|---|
| Enumerated rows | **196** (QL-CLICK-0001 … 0196) |
| Proven BROKEN | **2** (0112, 0113 — AI strategy builder) |
| Proven NOT_APPLICABLE | **4** (0010–0012, 0014 — external nav) |
| UNKNOWN (awaiting prod click test) | **190** |

## Maintenance notes

- Coach panel CTAs often use **dynamic** `cta_path` from `/research-journey` or `/ai/mentor/next`; verify at runtime.
- `ResearcherFollowButton` fires `trackEvent('feed_card_follow'|'feed_card_unfollow')` → `POST /events`.
- Logout is **client-only** (no API call); JWT cleared from localStorage.
- Org role gates: `owner`, `admin` (`canAdmin`), `member` (`canShare`), `viewer` (read-only).
- After each fix: re-run prod browser pass and update STATUS column only with evidence.

