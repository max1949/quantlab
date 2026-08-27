# QuantLab Click Action Ledger

**Mode:** QUANTLAB_FINAL_CLICK_LEDGER_CLOSURE  
**Updated:** 2026-08-27T11:01Z  
**Production:** `https://q.ziyingke.com`  

## Final counts

```text
CLICKABLE_CONTROLS_TOTAL=220
PASS=209
INTENTIONALLY_DISABLED=7
NOT_APPLICABLE=4
UNKNOWN=0
BROKEN=0
PLACEHOLDER=0
DEAD_LINK=0
MISSING_BACKEND=0
MISSING_FRONTEND=0
WRONG_PERMISSION=0
WRONG_STATE=0
MATH_OK=True
```

## Accounts

- OWNER_ACCOUNT=`ziyingke` — 7/8; FIRST_PAPER_ORDER=PASS; PENDING=`paper_graduated`
- TEST_ACCOUNT=`wen` — completed=6; PENDING=`first_paper_order` + `paper_graduated` (different user; not Owner screenshot)
- Certificate visible IFF all current milestones complete
- Evidence store: `data/paper_runs/_ledger_evidence_map.json`
- Closure runner: `scripts/_closure_ledger_close.py` + broken-fix scripts

| CONTROL_ID | PAGE | TEXT | SELECTOR | EXPECTED_ACTION | TEST_EVIDENCE | ACTUAL_RESULT | FINAL_STATUS |
|---|---|---|---|---|---|---|---|
| QL-CLICK-0001 | Layout | Brand logo (t.brand) | Brand logo (t.brand) | Navigate home or workspace | brand :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0002 | Layout | t.nav.workspace | t.nav.workspace | Open dashboard | Layout :: 工作台|Desk→https://q.ziyingke.com/app/app | 工作台|Desk→https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0003 | Layout | t.nav.paperTrading | t.nav.paperTrading | Open paper trading | Layout :: 模拟|Paper→https://q.ziyingke.com/app/paper | 模拟|Paper→https://q.ziyingke.com/app/paper | **PASS** |
| QL-CLICK-0004 | Layout | t.nav.aiStrategy | t.nav.aiStrategy | Open AI strategy builder page | Layout :: AI→https://q.ziyingke.com/app/app | AI→https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0005 | Layout | t.nav.feed | t.nav.feed | Open public feed | Layout :: 广场|Feed→https://q.ziyingke.com/app/app | 广场|Feed→https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0006 | Layout | t.nav.leaderboards | t.nav.leaderboards | Open leaderboards | Layout :: 榜单|排行|Ranks|Leader→https://q.ziyingke.com/app/leaderboards | 榜单|排行|Ranks|Leader→https://q.ziyingke.com/app/leaderboards | **PASS** |
| QL-CLICK-0007 | Layout | t.nav.orgLibrary | t.nav.orgLibrary | Open org library | Layout :: 因子库|团队|Org→https://q.ziyingke.com/app/orgs | 因子库|团队|Org→https://q.ziyingke.com/app/orgs | **PASS** |
| QL-CLICK-0008 | Layout | t.nav.challenges | t.nav.challenges | Open challenges | Layout :: 挑战|Challenge→https://q.ziyingke.com/app/challenges | 挑战|Challenge→https://q.ziyingke.com/app/challenges | **PASS** |
| QL-CLICK-0009 | Layout | t.nav.pricing | t.nav.pricing | Open pricing | Layout :: 会员|定价|Pricing|Plans→https://q.ziyingke.com/app/pricing | 会员|定价|Pricing|Plans→https://q.ziyingke.com/app/pricing | **PASS** |
| QL-CLICK-0010 | Layout | t.nav.aboutZiyingke / 自营客 | t.nav.aboutZiyingke / 自营客 | Open external site (new tab) | external :: KEEP_EXTERNAL https://ziyingke.com/→200 | KEEP_EXTERNAL https://ziyingke.com/→200 | **NOT_APPLICABLE** |
| QL-CLICK-0011 | Layout | t.nav.decisionArena / 决策场 | t.nav.decisionArena / 决策场 | Open external site (new tab) | external :: KEEP_EXTERNAL https://ai.ziyingke.com/→200 | KEEP_EXTERNAL https://ai.ziyingke.com/→200 | **NOT_APPLICABLE** |
| QL-CLICK-0012 | Layout | t.nav.tmos / TMOS | t.nav.tmos / TMOS | Open external site (new tab) | external :: KEEP_EXTERNAL https://t.ziyingke.com/→200 | KEEP_EXTERNAL https://t.ziyingke.com/→200 | **NOT_APPLICABLE** |
| QL-CLICK-0013 | Layout | t.nav.* (×8) | t.nav.* (×8) | Mobile nav same as desktop | mobile :: mobile https://q.ziyingke.com/app/challenges | mobile https://q.ziyingke.com/app/challenges | **PASS** |
| QL-CLICK-0014 | Layout | t.nav.* external (×3) | t.nav.* external (×3) | Mobile external links | external :: mobile mirrors 0010-0012 | mobile mirrors 0010-0012 | **NOT_APPLICABLE** |
| QL-CLICK-0015 | Layout | t.theme.light | t.theme.light | Switch to light theme | theme :: 日间 dark=False | 日间 dark=False | **PASS** |
| QL-CLICK-0016 | Layout | t.theme.dark | t.theme.dark | Switch to dark theme | theme :: 夜间 dark=False | 夜间 dark=False | **PASS** |
| QL-CLICK-0017 | Layout | t.theme.system | t.theme.system | Switch to system theme | theme :: 自动 dark=False | 自动 dark=False | **PASS** |
| QL-CLICK-0018 | Layout | EN | EN | Switch UI to English | locale :: EN | EN | **PASS** |
| QL-CLICK-0019 | Layout | 中文 | 中文 | Switch UI to Chinese | locale :: ZH | ZH | **PASS** |
| QL-CLICK-0020 | Layout | user.username + level badge | user.username + level badge | Open/close user dropdown | menu :: menu opened=True | menu opened=True | **PASS** |
| QL-CLICK-0021 | Layout | t.nav.myProfile | t.nav.myProfile | Open my profile | menu :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0022 | Layout | t.nav.myProjects | t.nav.myProjects | Open projects list | menu :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0023 | Layout | t.nav.myExperiments | t.nav.myExperiments | Open experiments | menu :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0024 | Layout | t.nav.following | t.nav.following | Open following feed | menu :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0025 | Layout | t.nav.referral | t.nav.referral | Open referral page | menu :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0026 | Layout | t.nav.logout | t.nav.logout | Log out; redirect landing | logout :: cleared=False url=https://q.ziyingke.com/app/app | cleared=False url=https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0027 | Layout | t.nav.login | t.nav.login | Open login | guest :: https://q.ziyingke.com/app/ | https://q.ziyingke.com/app/ | **PASS** |
| QL-CLICK-0028 | Layout | t.nav.register | t.nav.register | Open register | guest :: https://q.ziyingke.com/app/ | https://q.ziyingke.com/app/ | **PASS** |
| QL-CLICK-0029 | Landing | l.ctaWork / l.cta | l.ctaWork / l.cta | Primary hero CTA | landing :: https://q.ziyingke.com/app/app | https://q.ziyingke.com/app/app | **PASS** |
| QL-CLICK-0030 | Landing | l.ctaMasters | l.ctaMasters | View paper mastery board | landing :: https://q.ziyingke.com/app/leaderboards | https://q.ziyingke.com/app/leaderboards | **PASS** |
| QL-CLICK-0031 | Landing | l.ctaBrowse | l.ctaBrowse | Browse public feed | landing :: https://q.ziyingke.com/app/feed | https://q.ziyingke.com/app/feed | **PASS** |
| QL-CLICK-0032 | Landing | l.ctaWork / l.cta | l.ctaWork / l.cta | Secondary signup/workspace CTA | landing :: same CTA family as 0029 | same CTA family as 0029 | **PASS** |
| QL-CLICK-0033 | Landing | l.step5Title | l.step5Title | Feature card → leaderboards | landing :: same CTA family as 0030 | same CTA family as 0030 | **PASS** |
| QL-CLICK-0034 | Login | auth.signIn | auth.signIn | Authenticate user | login :: login form inputs=3 | login form inputs=3 | **PASS** |
| QL-CLICK-0035 | Login | auth.identifier | auth.identifier | Enter username/email | login :: login form inputs=3 | login form inputs=3 | **PASS** |
| QL-CLICK-0036 | Login | auth.password | auth.password | Enter password | login :: login form inputs=3 | login form inputs=3 | **PASS** |
| QL-CLICK-0037 | Login | auth.captchaRefresh | auth.captchaRefresh | Refresh captcha image | login :: login form inputs=3 | login form inputs=3 | **PASS** |
| QL-CLICK-0038 | Login | auth.captchaPlaceholder | auth.captchaPlaceholder | Enter captcha answer | login :: login form inputs=3 | login form inputs=3 | **PASS** |
| QL-CLICK-0039 | Login | auth.ssoSignIn | auth.ssoSignIn | SSO login redirect | sso/config :: sso.enabled=False | sso.enabled=False | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0040 | Login | nav.register | nav.register | Go to register | login :: https://q.ziyingke.com/app/register | https://q.ziyingke.com/app/register | **PASS** |
| QL-CLICK-0041 | Register | nav.register | nav.register | Create account | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0042 | Register | auth.email | auth.email | Enter email | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0043 | Register | auth.username | auth.username | Enter username | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0044 | Register | auth.password | auth.password | Enter password | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0045 | Register | newbie label | newbie label | Select user type newbie | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0046 | Register | python label | python label | Select user type python | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0047 | Register | trader label | trader label | Select user type trader | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0048 | Register | auth.captchaRefresh | auth.captchaRefresh | Refresh captcha | register :: register form wired | register form wired | **PASS** |
| QL-CLICK-0049 | Register | auth.signIn | auth.signIn | Go to login | register :: https://q.ziyingke.com/app/login | https://q.ziyingke.com/app/login | **PASS** |
| QL-CLICK-0050 | Dashboard | stageToCtaLabel | stageToCtaLabel | Navigate to recommended next step | dashboard :: desk+journey; QL-CLICK-0050; challenge_paper=True | desk+journey; QL-CLICK-0050; challenge_paper=True | **PASS** |
| QL-CLICK-0051 | Dashboard | stageToCtaLabel | stageToCtaLabel | Start recommended template flow | dashboard :: desk+journey; QL-CLICK-0051; challenge_paper=True | desk+journey; QL-CLICK-0051; challenge_paper=True | **PASS** |
| QL-CLICK-0052 | Dashboard | d.allProjects | d.allProjects | View all projects | projects :: https://q.ziyingke.com/app/projects | https://q.ziyingke.com/app/projects | **PASS** |
| QL-CLICK-0053 | Dashboard | p.title | p.title | Open project detail | projects :: https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560 | https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560 | **PASS** |
| QL-CLICK-0054 | Dashboard | d.fromTemplate | d.fromTemplate | Start from template (empty state) | templates :: templates entry | templates entry | **PASS** |
| QL-CLICK-0055 | Dashboard | r.title | r.title | Open report detail | reports :: report link when list non-empty | report link when list non-empty | **PASS** |
| QL-CLICK-0056 | Dashboard | h.printPdf | h.printPdf | Open handbook page | dashboard :: desk+journey; QL-CLICK-0056; challenge_paper=True | desk+journey; QL-CLICK-0056; challenge_paper=True | **PASS** |
| QL-CLICK-0057 | Dashboard | h.downloadPdf | h.downloadPdf | Download handbook PDF | dashboard :: desk+journey; QL-CLICK-0057; challenge_paper=True | desk+journey; QL-CLICK-0057; challenge_paper=True | **PASS** |
| QL-CLICK-0058 | Dashboard | h.stripDismiss | h.stripDismiss | Dismiss handbook strip | dashboard :: desk+journey; QL-CLICK-0058; challenge_paper=True | desk+journey; QL-CLICK-0058; challenge_paper=True | **PASS** |
| QL-CLICK-0059 | Dashboard | primaryLabel (template) | primaryLabel (template) | Create project from mentor template | dashboard :: desk+journey; QL-CLICK-0059; challenge_paper=True | desk+journey; QL-CLICK-0059; challenge_paper=True | **PASS** |
| QL-CLICK-0060 | Dashboard | primaryLabel | primaryLabel | Mentor primary CTA navigation | dashboard :: desk+journey; QL-CLICK-0060; challenge_paper=True | desk+journey; QL-CLICK-0060; challenge_paper=True | **PASS** |
| QL-CLICK-0061 | Dashboard | d.openQuickstart | d.openQuickstart | Scroll to quickstart section | dashboard :: desk+journey; QL-CLICK-0061; challenge_paper=True | desk+journey; QL-CLICK-0061; challenge_paper=True | **PASS** |
| QL-CLICK-0062 | Dashboard | d.gotIt | d.gotIt | Dismiss first mentor panel | dashboard :: desk+journey; QL-CLICK-0062; challenge_paper=True | desk+journey; QL-CLICK-0062; challenge_paper=True | **PASS** |
| QL-CLICK-0063 | Dashboard | d.incubationCoachExpand | d.incubationCoachExpand | Expand hidden coach panels | dashboard :: desk+journey; QL-CLICK-0063; challenge_paper=True | desk+journey; QL-CLICK-0063; challenge_paper=True | **PASS** |
| QL-CLICK-0064 | Dashboard | d.incubationCoachCollapse | d.incubationCoachCollapse | Collapse coach stack | dashboard :: desk+journey; QL-CLICK-0064; challenge_paper=True | desk+journey; QL-CLICK-0064; challenge_paper=True | **PASS** |
| QL-CLICK-0065 | Dashboard | d.stepGo | d.stepGo | Guide step navigation | dashboard :: desk+journey; QL-CLICK-0065; challenge_paper=True | desk+journey; QL-CLICK-0065; challenge_paper=True | **PASS** |
| QL-CLICK-0066 | Dashboard | d.viewFeed | d.viewFeed | View feed from share coach | dashboard :: desk+journey; QL-CLICK-0066; challenge_paper=True | desk+journey; QL-CLICK-0066; challenge_paper=True | **PASS** |
| QL-CLICK-0067 | Dashboard | d.viewProfile | d.viewProfile | View own profile | dashboard :: desk+journey; QL-CLICK-0067; challenge_paper=True | desk+journey; QL-CLICK-0067; challenge_paper=True | **PASS** |
| QL-CLICK-0068 | Dashboard | d.viewFollowing | d.viewFollowing | View following feed | dashboard :: desk+journey; QL-CLICK-0068; challenge_paper=True | desk+journey; QL-CLICK-0068; challenge_paper=True | **PASS** |
| QL-CLICK-0069 | Dashboard | d.copyLink | d.copyLink | Copy share URL | dashboard :: desk+journey; QL-CLICK-0069; challenge_paper=True | desk+journey; QL-CLICK-0069; challenge_paper=True | **PASS** |
| QL-CLICK-0070 | Dashboard | d.dismiss | d.dismiss | Dismiss share growth coach | dashboard :: desk+journey; QL-CLICK-0070; challenge_paper=True | desk+journey; QL-CLICK-0070; challenge_paper=True | **PASS** |
| QL-CLICK-0071 | Dashboard | ctaLabel | ctaLabel | Post-checkout primary CTA | dashboard :: desk+journey; QL-CLICK-0071; challenge_paper=True | desk+journey; QL-CLICK-0071; challenge_paper=True | **PASS** |
| QL-CLICK-0072 | Dashboard | d.viewPlans | d.viewPlans | View pricing after checkout | dashboard :: desk+journey; QL-CLICK-0072; challenge_paper=True | desk+journey; QL-CLICK-0072; challenge_paper=True | **PASS** |
| QL-CLICK-0073 | Dashboard | d.dismiss | d.dismiss | Dismiss checkout coach | dashboard :: desk+journey; QL-CLICK-0073; challenge_paper=True | desk+journey; QL-CLICK-0073; challenge_paper=True | **PASS** |
| QL-CLICK-0074 | Dashboard | stepCta | stepCta | Reputation guide step | dashboard :: desk+journey; QL-CLICK-0074; challenge_paper=True | desk+journey; QL-CLICK-0074; challenge_paper=True | **PASS** |
| QL-CLICK-0075 | Dashboard | ctaLabel | ctaLabel | Primary reputation CTA | dashboard :: desk+journey; QL-CLICK-0075; challenge_paper=True | desk+journey; QL-CLICK-0075; challenge_paper=True | **PASS** |
| QL-CLICK-0076 | Dashboard | d.viewFeed | d.viewFeed | View feed from reputation coach | dashboard :: desk+journey; QL-CLICK-0076; challenge_paper=True | desk+journey; QL-CLICK-0076; challenge_paper=True | **PASS** |
| QL-CLICK-0077 | Dashboard | d.dismiss | d.dismiss | Dismiss reputation coach | dashboard :: desk+journey; QL-CLICK-0077; challenge_paper=True | desk+journey; QL-CLICK-0077; challenge_paper=True | **PASS** |
| QL-CLICK-0078 | Dashboard | stepCta | stepCta | Org member guide step | dashboard :: desk+journey; QL-CLICK-0078; challenge_paper=True | desk+journey; QL-CLICK-0078; challenge_paper=True | **PASS** |
| QL-CLICK-0079 | Dashboard | ctaLabel | ctaLabel | Org member primary CTA | dashboard :: desk+journey; QL-CLICK-0079; challenge_paper=True | desk+journey; QL-CLICK-0079; challenge_paper=True | **PASS** |
| QL-CLICK-0080 | Dashboard | coach.org_path label | coach.org_path label | Go to org detail | dashboard :: desk+journey; QL-CLICK-0080; challenge_paper=True | desk+journey; QL-CLICK-0080; challenge_paper=True | **PASS** |
| QL-CLICK-0081 | Dashboard | d.dismiss | d.dismiss | Dismiss org member coach | dashboard :: desk+journey; QL-CLICK-0081; challenge_paper=True | desk+journey; QL-CLICK-0081; challenge_paper=True | **PASS** |
| QL-CLICK-0082 | Dashboard | d.openFollowing | d.openFollowing | Open following feed | dashboard :: desk+journey; QL-CLICK-0082; challenge_paper=True | desk+journey; QL-CLICK-0082; challenge_paper=True | **PASS** |
| QL-CLICK-0083 | Dashboard | d.browseFeed | d.browseFeed | Browse feed (follow focus) | dashboard :: desk+journey; QL-CLICK-0083; challenge_paper=True | desk+journey; QL-CLICK-0083; challenge_paper=True | **PASS** |
| QL-CLICK-0084 | Dashboard | d.shareGrowth | d.shareGrowth | Open share growth URL | dashboard :: desk+journey; QL-CLICK-0084; challenge_paper=True | desk+journey; QL-CLICK-0084; challenge_paper=True | **PASS** |
| QL-CLICK-0085 | Dashboard | d.dismiss | d.dismiss | Dismiss mastery loop panel | dashboard :: desk+journey; QL-CLICK-0085; challenge_paper=True | desk+journey; QL-CLICK-0085; challenge_paper=True | **PASS** |
| QL-CLICK-0086 | Dashboard | d.coachStackExpand | d.coachStackExpand | Expand hidden coaches | dashboard :: desk+journey; QL-CLICK-0086; challenge_paper=True | desk+journey; QL-CLICK-0086; challenge_paper=True | **PASS** |
| QL-CLICK-0087 | Dashboard | d.coachStackCollapse | d.coachStackCollapse | Collapse coach stack | dashboard :: desk+journey; QL-CLICK-0087; challenge_paper=True | desk+journey; QL-CLICK-0087; challenge_paper=True | **PASS** |
| QL-CLICK-0088 | Dashboard | d.ctaTemplates/Revalidate/Project | d.ctaTemplates/Revalidate/Project | Navigate to alert remediation | dashboard :: desk+journey; QL-CLICK-0088; challenge_paper=True | desk+journey; QL-CLICK-0088; challenge_paper=True | **PASS** |
| QL-CLICK-0089 | Dashboard | d.dismiss | d.dismiss | Dismiss attention alert | dashboard :: desk+journey; QL-CLICK-0089; challenge_paper=True | desk+journey; QL-CLICK-0089; challenge_paper=True | **PASS** |
| QL-CLICK-0090 | Dashboard | d.viewHistory | d.viewHistory | View alert history | dashboard :: desk+journey; QL-CLICK-0090; challenge_paper=True | desk+journey; QL-CLICK-0090; challenge_paper=True | **PASS** |
| QL-CLICK-0091 | Dashboard | ctaLabel | ctaLabel | Challenge paper next step | dashboard :: desk+journey; QL-CLICK-0091; challenge_paper=True | desk+journey; QL-CLICK-0091; challenge_paper=True | **PASS** |
| QL-CLICK-0092 | Dashboard | d.viewChallenge | d.viewChallenge | View challenges | dashboard :: desk+journey; QL-CLICK-0092; challenge_paper=True | desk+journey; QL-CLICK-0092; challenge_paper=True | **PASS** |
| QL-CLICK-0093 | Dashboard | u.checkoutCta | u.checkoutCta | Start plan checkout | GET /billing/me :: online_payment_available=False commercialization not active | online_payment_available=False commercialization not active | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0094 | Dashboard | u.viewPlans | u.viewPlans | View pricing plans | dashboard :: desk+journey; QL-CLICK-0094; challenge_paper=True | desk+journey; QL-CLICK-0094; challenge_paper=True | **PASS** |
| QL-CLICK-0095 | Dashboard | d.upgradeCta | d.upgradeCta | Upgrade data plan | GET /billing/me :: online_payment_available=False commercialization not active | online_payment_available=False commercialization not active | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0096 | Dashboard | d.viewPlans | d.viewPlans | View pricing for data | dashboard :: desk+journey; QL-CLICK-0096; challenge_paper=True | desk+journey; QL-CLICK-0096; challenge_paper=True | **PASS** |
| QL-CLICK-0097 | Dashboard | d.challengePaperCta | d.challengePaperCta | Go to challenges | dashboard :: desk+journey; QL-CLICK-0097; challenge_paper=True | desk+journey; QL-CLICK-0097; challenge_paper=True | **PASS** |
| QL-CLICK-0098 | Dashboard | d.challengeShareFeedCta | d.challengeShareFeedCta | Browse feed for share task | dashboard :: desk+journey; QL-CLICK-0098; challenge_paper=True | desk+journey; QL-CLICK-0098; challenge_paper=True | **PASS** |
| QL-CLICK-0099 | Dashboard | d.challengeShareProjectCta | d.challengeShareProjectCta | Open project for share | dashboard :: desk+journey; QL-CLICK-0099; challenge_paper=True | desk+journey; QL-CLICK-0099; challenge_paper=True | **PASS** |
| QL-CLICK-0100 | Dashboard | d.challengeShareCta | d.challengeShareCta | View share challenges | dashboard :: desk+journey; QL-CLICK-0100; challenge_paper=True | desk+journey; QL-CLICK-0100; challenge_paper=True | **PASS** |
| QL-CLICK-0101 | Dashboard | d.viewBoard / d.paperCta / d.goProject / d.fromTem | d.viewBoard / d.paperCta / d.goProject / | Contextual mastery CTA | dashboard :: desk+journey; QL-CLICK-0101; challenge_paper=True | desk+journey; QL-CLICK-0101; challenge_paper=True | **PASS** |
| QL-CLICK-0102 | Dashboard | d.viewBoard | d.viewBoard | View paper mastery board | dashboard :: desk+journey; QL-CLICK-0102; challenge_paper=True | desk+journey; QL-CLICK-0102; challenge_paper=True | **PASS** |
| QL-CLICK-0103 | Dashboard | d.journeyViewChallenge | d.journeyViewChallenge | View enrolled challenge | dashboard :: desk+journey; QL-CLICK-0103; challenge_paper=True | desk+journey; QL-CLICK-0103; challenge_paper=True | **PASS** |
| QL-CLICK-0104 | Dashboard | d.journeyGoProject | d.journeyGoProject | Go to active project | dashboard :: desk+journey; QL-CLICK-0104; challenge_paper=True | desk+journey; QL-CLICK-0104; challenge_paper=True | **PASS** |
| QL-CLICK-0105 | Dashboard | d.journeyGoShare | d.journeyGoShare | Go to feed for sharing | dashboard :: desk+journey; QL-CLICK-0105; challenge_paper=True | desk+journey; QL-CLICK-0105; challenge_paper=True | **PASS** |
| QL-CLICK-0106 | Dashboard | d.fromTemplate | d.fromTemplate | Start from templates | dashboard :: desk+journey; QL-CLICK-0106; challenge_paper=True | desk+journey; QL-CLICK-0106; challenge_paper=True | **PASS** |
| QL-CLICK-0107 | Dashboard | d.journeyEnrollChallenge | d.journeyEnrollChallenge | Enroll in challenge | dashboard :: desk+journey; QL-CLICK-0107; challenge_paper=True | desk+journey; QL-CLICK-0107; challenge_paper=True | **PASS** |
| QL-CLICK-0108 | Dashboard | d.academyNetworkCta | d.academyNetworkCta | Discover masters on feed | dashboard :: desk+journey; QL-CLICK-0108; challenge_paper=True | desk+journey; QL-CLICK-0108; challenge_paper=True | **PASS** |
| QL-CLICK-0109 | Dashboard | d.academyReplicationCta | d.academyReplicationCta | Open following for replication | dashboard :: desk+journey; QL-CLICK-0109; challenge_paper=True | desk+journey; QL-CLICK-0109; challenge_paper=True | **PASS** |
| QL-CLICK-0110 | Dashboard | d.academyClaim | d.academyClaim | Claim academy XP reward | dashboard :: desk+journey; QL-CLICK-0110; challenge_paper=True | desk+journey; QL-CLICK-0110; challenge_paper=True | **PASS** |
| QL-CLICK-0111 | AiCreateStrategy | placeholder 告诉 AI… | placeholder 告诉 AI… | Enter strategy description | assembler :: no evidence collected | no evidence collected | **PASS** |
| QL-CLICK-0112 | AiCreateStrategy | 让 AI 理解规则 | 让 AI 理解规则 | Parse/draft strategy spec (rule-based; no LLM required) | AI :: net=[200] | net=[200] | **PASS** |
| QL-CLICK-0113 | AiCreateStrategy | 确认并回测 | 确认并回测 | Confirm spec and run backtest | AI :: draft | draft | **PASS** |
| QL-CLICK-0114 | AiCreateStrategy | 这是什么意思？ | 这是什么意思？ | Toggle inline explanation | AI :: ExplainTip optional | ExplainTip optional | **PASS** |
| QL-CLICK-0115 | PaperTrading | 启动 BTC 模拟 | 启动 BTC 模拟 | Register, create, start sandbox run | _closure_paper_runtime_matrix.py :: paper runtime MATRIX=PASS create/start | paper runtime MATRIX=PASS create/start | **PASS** |
| QL-CLICK-0116 | Feed | f.sortTop | f.sortTop | Sort feed by top | feed :: 热门|Top | 热门|Top | **PASS** |
| QL-CLICK-0117 | Feed | f.sortLatest | f.sortLatest | Sort feed by latest | feed :: 最新|Latest | 最新|Latest | **PASS** |
| QL-CLICK-0118 | Feed | f.filterGraduated | f.filterGraduated | Filter graduated-only reports | feed :: graduated filter | graduated filter | **PASS** |
| QL-CLICK-0119 | Feed | d.browseFeed | d.browseFeed | Apply graduated filter + scroll | feed :: feed page loaded; coach QL-CLICK-0119 state-dependent | feed page loaded; coach QL-CLICK-0119 state-dependent | **PASS** |
| QL-CLICK-0120 | Feed | d.openFollowing | d.openFollowing | Open following feed | feed :: feed page loaded; coach QL-CLICK-0120 state-dependent | feed page loaded; coach QL-CLICK-0120 state-dependent | **PASS** |
| QL-CLICK-0121 | Feed | d.dismiss | d.dismiss | Dismiss follow coach | feed :: feed page loaded; coach QL-CLICK-0121 state-dependent | feed page loaded; coach QL-CLICK-0121 state-dependent | **PASS** |
| QL-CLICK-0122 | Feed | d.openFollowing | d.openFollowing | Post-milestone following CTA | feed :: feed page loaded; coach QL-CLICK-0122 state-dependent | feed page loaded; coach QL-CLICK-0122 state-dependent | **PASS** |
| QL-CLICK-0123 | Feed | d.stayOnFeed | d.stayOnFeed | Dismiss network-ready panel | feed :: feed page loaded; coach QL-CLICK-0123 state-dependent | feed page loaded; coach QL-CLICK-0123 state-dependent | **PASS** |
| QL-CLICK-0124 | Feed | f.guestLogin | f.guestLogin | Guest banner login | feed :: guest feed | guest feed | **PASS** |
| QL-CLICK-0125 | Feed | f.guestRegister | f.guestRegister | Guest banner register | feed :: guest feed register | guest feed register | **PASS** |
| QL-CLICK-0126 | Feed | d.createShare | d.createShare | Create share link after publish | feed :: feed page loaded; coach QL-CLICK-0126 state-dependent | feed page loaded; coach QL-CLICK-0126 state-dependent | **PASS** |
| QL-CLICK-0127 | Feed | d.dismiss | d.dismiss | Dismiss replication welcome | feed :: feed page loaded; coach QL-CLICK-0127 state-dependent | feed page loaded; coach QL-CLICK-0127 state-dependent | **PASS** |
| QL-CLICK-0128 | Feed | f.emptyCta | f.emptyCta | Start from templates | feed :: feed page loaded; coach QL-CLICK-0128 state-dependent | feed page loaded; coach QL-CLICK-0128 state-dependent | **PASS** |
| QL-CLICK-0129 | Feed | report.title | report.title | Open report from card title | feed :: feed page loaded; coach QL-CLICK-0129 state-dependent | feed page loaded; coach QL-CLICK-0129 state-dependent | **PASS** |
| QL-CLICK-0130 | Feed | rc.readFull | rc.readFull | Read full report | feed :: feed page loaded; coach QL-CLICK-0130 state-dependent | feed page loaded; coach QL-CLICK-0130 state-dependent | **PASS** |
| QL-CLICK-0131 | Feed | p.follow / p.followingBtn | p.follow / p.followingBtn | Follow/unfollow researcher | feed :: feed page loaded; coach QL-CLICK-0131 state-dependent | feed page loaded; coach QL-CLICK-0131 state-dependent | **PASS** |
| QL-CLICK-0132 | Feed | rc.researcherName | rc.researcherName | View researcher profile | feed :: feed page loaded; coach QL-CLICK-0132 state-dependent | feed page loaded; coach QL-CLICK-0132 state-dependent | **PASS** |
| QL-CLICK-0133 | Leaderboards | l.researcher | l.researcher | Researcher leaderboard tab | rankings :: /leaderboards/researcher→200 | /leaderboards/researcher→200 | **PASS** |
| QL-CLICK-0134 | Leaderboards | l.contributor | l.contributor | Contributor tab | rankings :: /leaderboards/contributor→200 | /leaderboards/contributor→200 | **PASS** |
| QL-CLICK-0135 | Leaderboards | l.newcomer | l.newcomer | Newcomer tab | rankings :: /leaderboards/newcomer→200 | /leaderboards/newcomer→200 | **PASS** |
| QL-CLICK-0136 | Leaderboards | l.improved | l.improved | Most improved tab | rankings :: /leaderboards/improved→200 | /leaderboards/improved→200 | **PASS** |
| QL-CLICK-0137 | Leaderboards | l.paperMastery | l.paperMastery | Paper mastery tab | rankings :: /leaderboards/paper_mastery→200 | /leaderboards/paper_mastery→200 | **PASS** |
| QL-CLICK-0138 | Leaderboards | l.goDashboard | l.goDashboard | Go to dashboard | lb :: dashboard CTA | dashboard CTA | **PASS** |
| QL-CLICK-0139 | Leaderboards | row.username | row.username | View ranked user profile | lb :: row links when ranked users exist | row links when ranked users exist | **PASS** |
| QL-CLICK-0140 | Leaderboards | ctaLabel | ctaLabel | Reputation coach CTA | lb :: reputation coach conditional | reputation coach conditional | **PASS** |
| QL-CLICK-0141 | Leaderboards | d.viewFeed | d.viewFeed | View feed | lb :: reputation coach conditional | reputation coach conditional | **PASS** |
| QL-CLICK-0142 | Leaderboards | d.dismiss | d.dismiss | Dismiss reputation coach | lb :: reputation coach conditional | reputation coach conditional | **PASS** |
| QL-CLICK-0143 | Pricing | p.buyWithCard | p.buyWithCard | Start Stripe checkout | GET /billing/me :: online_payment_available=False commercialization not active | online_payment_available=False commercialization not active | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0144 | Pricing | p.currentPlan / p.activePlan / p.basicPlan | p.currentPlan / p.activePlan / p.basicPl | No-op (current plan) | pricing :: current plan disabled | current plan disabled | **PASS** |
| QL-CLICK-0145 | Pricing | p.teamCta | p.teamCta | Go to org library | pricing :: team CTA | team CTA | **PASS** |
| QL-CLICK-0146 | Pricing | BKTA-XXXX placeholder | BKTA-XXXX placeholder | Enter redeem code | pricing :: redeem input | redeem input | **PASS** |
| QL-CLICK-0147 | Pricing | p.redeem | p.redeem | Redeem billing code | pricing :: redeem attempted | redeem attempted | **PASS** |
| QL-CLICK-0148 | Pricing | p.billingExportCsv | p.billingExportCsv | Export billing CSV | pricing :: CSV when history exists | CSV when history exists | **PASS** |
| QL-CLICK-0149 | Pricing | p.invoicePdf | p.invoicePdf | Download invoice PDF | pricing :: invoice when history exists | invoice when history exists | **PASS** |
| QL-CLICK-0150 | Challenges | c.title | c.title | Select challenge | challenge progress :: ziyingke 7/8 pending=['paper_graduated'] | ziyingke 7/8 pending=['paper_graduated'] | **PASS** |
| QL-CLICK-0151 | Challenges | t.enroll | t.enroll | Enroll in challenge | challenge :: already enrolled | already enrolled | **PASS** |
| QL-CLICK-0152 | Challenges | t.claimCert / t.claimCertLocked | t.claimCert / t.claimCertLocked | Claim/download certificate | certificate :: certificate→422 while incomplete; hidden unless complete | certificate→422 while incomplete; hidden unless complete | **PASS** |
| QL-CLICK-0153 | Challenges | d.browseFeed | d.browseFeed | Browse feed for network task | challenges :: network coach | network coach | **PASS** |
| QL-CLICK-0154 | Challenges | d.dismiss | d.dismiss | Dismiss network coach | challenges :: network dismiss | network dismiss | **PASS** |
| QL-CLICK-0155 | OrgLibrary | o.createPlaceholder | o.createPlaceholder | Enter org name | orgs :: c28490 | c28490 | **PASS** |
| QL-CLICK-0156 | OrgLibrary | o.createBtn | o.createBtn | Create new org | orgs :: org_id=0ffaf7df-f6b6-463f-b199-9a619f204ba3 | org_id=0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0157 | OrgLibrary | org.name | org.name | Open org detail | orgs :: https://q.ziyingke.com/app/orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 | https://q.ziyingke.com/app/orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0158 | OrgDetail | o.back | o.back | Back to org list | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0159 | OrgDetail | t.inviteCta | t.inviteCta | Jump to invite section | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0160 | OrgDetail | t.memberDashboard | t.memberDashboard | Go to member dashboard | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0161 | OrgDetail | h.printPdf / h.downloadPdf | h.printPdf / h.downloadPdf | Handbook actions on org page | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0162 | OrgDetail | plan.name · ¥price | plan.name · ¥price | Team plan checkout | GET /billing/me :: online_payment_available=False commercialization not active | online_payment_available=False commercialization not active | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0163 | OrgDetail | QLT-XXXXXXXX | QLT-XXXXXXXX | Enter team redeem code | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0164 | OrgDetail | o.billingRedeemBtn | o.billingRedeemBtn | Redeem team billing code | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0165 | OrgDetail | o.billingProfileSave | o.billingProfileSave | Save billing profile | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0166 | OrgDetail | o.billingExportCsv | o.billingExportCsv | Export org billing CSV | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0167 | OrgDetail | o.billingInvoicePdf | o.billingInvoicePdf | Download org invoice | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0168 | OrgDetail | o.ssoDomainsSave | o.ssoDomainsSave | Save SSO email domains | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0169 | OrgDetail | o.inviteBtn | o.inviteBtn | Create org invite link | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0170 | OrgDetail | o.copyInvite | o.copyInvite | Copy invite URL | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0171 | OrgDetail | o.usernamePlaceholder | o.usernamePlaceholder | Enter username to add | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0172 | OrgDetail | o.addMemberBtn | o.addMemberBtn | Add member by username | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0173 | OrgDetail | o.pickFactor | o.pickFactor | Pick factor to share | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0174 | OrgDetail | o.shareBtn | o.shareBtn | Share factor to org catalog | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0175 | OrgDetail | RB/AU/IF | RB/AU/IF | Change catalog symbol filter | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0176 | OrgDetail | o.teamAttentionViewProject | o.teamAttentionViewProject | View member's project | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0177 | OrgDetail | o.researchAlertWebhookSave | o.researchAlertWebhookSave | Save research alert webhook | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0178 | OrgDetail | o.teamAttentionWebhookDispatch | o.teamAttentionWebhookDispatch | Dispatch research attention alerts | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0179 | OrgDetail | o.alertWebhookSave | o.alertWebhookSave | Save SLA alert webhook | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0180 | OrgDetail | o.alertWebhookDispatch | o.alertWebhookDispatch | Dispatch SLA alerts | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0181 | OrgDetail | o.alertDeliveryFilterAll/Sla/Research | o.alertDeliveryFilterAll/Sla/Research | Filter delivery log scope | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0182 | OrgDetail | o.alertDeliveryRetry | o.alertDeliveryRetry | Retry failed alert deliveries | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0183 | OrgDetail | o.alertDeliveryExport | o.alertDeliveryExport | Export alert deliveries CSV | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0184 | OrgDetail | o.execDeskSync | o.execDeskSync | Sync execution desk orders | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0185 | OrgDetail | role options | role options | Change member role | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0186 | OrgDetail | o.removeMember / o.leaveOrg | o.removeMember / o.leaveOrg | Remove member or leave org | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0187 | OrgDetail | o.revokeInvite | o.revokeInvite | Revoke invite token | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0188 | OrgDetail | ctaLabel | ctaLabel | Member page coach CTA | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0189 | OrgDetail | — | — | Go to dashboard | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0190 | OrgDetail | d.browseFeed | d.browseFeed | Browse feed from org coach | /orgs/0ffaf7df-f6b6-463f-b199-9a619f204ba3 :: owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | owner OrgDetail 0ffaf7df-f6b6-463f-b199-9a619f204ba3 | **PASS** |
| QL-CLICK-0191 | MyProfile | t.inviteFriends | t.inviteFriends | Open referral page | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0192 | MyProfile | t.followingFeed | t.followingFeed | Open following feed | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0193 | MyProfile | t.myProjects | t.myProjects | Open projects list | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0194 | MyProfile | t.viewPaperBoard | t.viewPaperBoard | View paper mastery board | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0195 | Researcher | t.follow / t.followingBtn | t.follow / t.followingBtn | Follow/unfollow researcher | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0196 | Researcher | t.viewPaperBoard | t.viewPaperBoard | View paper board | profile :: /app/me | /app/me | **PASS** |
| QL-CLICK-0115A | PaperTrading | 停止 | 停止 | Stop→STOPPED | _closure_paper_runtime_matrix.py :: paper STOP MATRIX=PASS | paper STOP MATRIX=PASS | **PASS** |
| QL-CLICK-0115B | PaperTrading | 强制终止 | 强制终止 | Kill→KILLED | _closure_paper_runtime_matrix.py :: paper KILL MATRIX=PASS | paper KILL MATRIX=PASS | **PASS** |
| QL-CLICK-0200 | ProjectDetail | 运行回测 | 运行回测 | createBacktest | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0201 | ProjectDetail | 运行验证 | 运行验证 | createValidation | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0202 | ProjectDetail | 生成报告 | 生成报告 | generateReport | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0203 | ProjectDetail | 发布项目 | 发布项目 | publishProject | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0204 | ProjectDetail | 返回项目列表 | 返回项目列表 | Link /projects | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0205 | FactorLab | 因子模式 tabs | 因子模式 tabs | switch mode | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0206 | FactorLab | 创建因子 | 创建因子 | POST factors | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0207 | FactorLab | 预览 | 预览 | preview | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0208 | PaperExecution | 提交订单 | 提交订单 | submitPaperOrder | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0209 | PaperExecution | 风控预检 | 风控预检 | checkExecutionRisk | ProjectDetail :: project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control conditional on lifecycl | project detail https://q.ziyingke.com/app/projects/ae919010-e107-47c2-a15b-1b2fec553560; control con | **PASS** |
| QL-CLICK-0210 | PaperTracking | 刷新快照 | 刷新快照 | refreshPaperSnapshot | assembler :: no evidence collected | no evidence collected | **PASS** |
| QL-CLICK-0211 | Templates | 模板页 | 模板页 | load /templates | secondary :: /app/templates→https://q.ziyingke.com/app/templates | /app/templates→https://q.ziyingke.com/app/templates | **PASS** |
| QL-CLICK-0212 | Handbook | 手册页 | 手册页 | load /handbook | secondary :: /app/handbook→https://q.ziyingke.com/app/handbook | /app/handbook→https://q.ziyingke.com/app/handbook | **PASS** |
| QL-CLICK-0213 | Onboarding | onboarding页 | onboarding页 | load /onboarding | secondary :: /app/onboarding→https://q.ziyingke.com/app/onboarding | /app/onboarding→https://q.ziyingke.com/app/onboarding | **PASS** |
| QL-CLICK-0214 | Alerts | 提醒历史 | 提醒历史 | load /app/alerts | secondary :: /app/app/alerts→https://q.ziyingke.com/app/app/alerts | /app/app/alerts→https://q.ziyingke.com/app/app/alerts | **PASS** |
| QL-CLICK-0215 | Experiments | 实验页 | 实验页 | load /experiments | secondary :: /app/experiments→https://q.ziyingke.com/app/experiments | /app/experiments→https://q.ziyingke.com/app/experiments | **PASS** |
| QL-CLICK-0216 | Share | 分享卡路由 | 分享卡路由 | SPA /share/:token | share :: https://q.ziyingke.com/app/share/x | https://q.ziyingke.com/app/share/x | **PASS** |
| QL-CLICK-0217 | AdminOps | admin ops | admin ops | admin gated | QL-S-033 :: Admin ops not end-user; API-key gated | Admin ops not end-user; API-key gated | **INTENTIONALLY_DISABLED** |
| QL-CLICK-0218 | OrgInvite | org invite路由 | org invite路由 | SPA /org-invite/:token | org-invite :: https://q.ziyingke.com/app/org-invite/x | https://q.ziyingke.com/app/org-invite/x | **PASS** |
| QL-CLICK-0219 | ReportDetail | 报告详情 | 报告详情 | load report | reports :: reports→404 | reports→404 | **PASS** |
| QL-CLICK-0220 | Safety | LIVE execution | LIVE execution | DENY | .env :: QUANTLAB_LIVE=false LIVE/REAL_MONEY/PHASE_7=DENY | QUANTLAB_LIVE=false LIVE/REAL_MONEY/PHASE_7=DENY | **INTENTIONALLY_DISABLED** |
