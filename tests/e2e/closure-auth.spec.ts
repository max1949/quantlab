import { test, expect, Page } from "@playwright/test";

/**
 * Authenticated closure E2E against production.
 * Env:
 *   QUANTLAB_BASE_URL=https://q.ziyingke.com
 *   QUANTLAB_E2E_TOKEN=<jwt>
 */

const token = process.env.QUANTLAB_E2E_TOKEN || "";
const base = process.env.QUANTLAB_BASE_URL || "https://q.ziyingke.com";

const AUTH_PAGES = [
  "/app/app",
  "/app/paper",
  "/app/ai-strategy",
  "/app/feed",
  "/app/leaderboards",
  "/app/orgs",
  "/app/challenges",
  "/app/pricing",
  "/app/me",
  "/app/projects",
  "/app/experiments",
  "/app/templates",
  "/app/me/following",
  "/app/me/referral",
  "/app/handbook",
];

const PUBLIC_PAGES = [
  "/app/",
  "/app/login",
  "/app/register",
  "/app/feed",
  "/app/leaderboards",
  "/app/pricing",
];

async function injectAuth(page: Page) {
  await page.addInitScript((t) => {
    localStorage.setItem("ql_token", t);
    localStorage.setItem("ql-locale", "zh");
  }, token);
}

async function collectConsole(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(`pageerror:${e.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`console.error:${msg.text()}`);
  });
  page.on("response", (res) => {
    const u = res.url();
    if (!u.includes("/api/")) return;
    const s = res.status();
    if (s >= 500) errors.push(`api500:${s}:${u}`);
  });
  return errors;
}

test.describe("public surfaces", () => {
  for (const path of PUBLIC_PAGES) {
    test(`loads ${path}`, async ({ page }) => {
      const errors = await collectConsole(page);
      const res = await page.goto(path, { waitUntil: "domcontentloaded" });
      expect(res?.ok() || (res?.status() ?? 0) < 500).toBeTruthy();
      await page.waitForTimeout(800);
      expect(errors.filter((e) => e.startsWith("pageerror:") || e.startsWith("api500:"))).toEqual([]);
    });
  }
});

test.describe("authenticated primary nav", () => {
  test.skip(!token, "QUANTLAB_E2E_TOKEN required");

  test.beforeEach(async ({ page }) => {
    await injectAuth(page);
  });

  for (const path of AUTH_PAGES) {
    test(`auth page ${path}`, async ({ page }) => {
      const errors = await collectConsole(page);
      await page.goto(path, { waitUntil: "networkidle" });
      await expect(page.getByText(/ziyingke|QuantLab/i).first()).toBeVisible({ timeout: 20000 });
      // must not bounce to login
      expect(page.url()).not.toMatch(/\/login/);
      const critical = errors.filter(
        (e) => e.startsWith("pageerror:") || e.startsWith("api500:") || e.includes("Uncaught"),
      );
      expect(critical, critical.join("\n")).toEqual([]);
    });
  }

  test("AI strategy builder draft", async ({ page }) => {
    const errors = await collectConsole(page);
    await page.goto("/app/ai-strategy", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /让 AI 理解规则|Understand/i }).click();
    await expect(page.getByText(/我理解的策略|还需要确认|交易品种|Ambigu/i).first()).toBeVisible({
      timeout: 30000,
    });
    expect(errors.filter((e) => e.startsWith("pageerror:") || e.includes("未启用"))).toEqual([]);
  });

  test("challenges shows pending hint for paper_graduated", async ({ page }) => {
    await page.goto("/app/challenges", { waitUntil: "networkidle" });
    await expect(page.getByText(/30|挑战|Challenge/i).first()).toBeVisible({ timeout: 20000 });
    // Owner account: 7/8 missing graduation
    const body = await page.locator("body").innerText();
    expect(body).toMatch(/毕业|Paper|7\/8|已完成/);
  });

  test("theme light dark auto", async ({ page }) => {
    await page.goto("/app/app", { waitUntil: "networkidle" });
    const html = page.locator("html");
    await page.getByRole("button", { name: /日间|Light/i }).click();
    await page.waitForTimeout(300);
    await expect(html).not.toHaveClass(/dark/);
    await page.getByRole("button", { name: /夜间|Dark/i }).click();
    await page.waitForTimeout(300);
    await expect(html).toHaveClass(/dark/);
    await page.getByRole("button", { name: /自动|Auto|System/i }).click();
    await page.waitForTimeout(300);
  });

  test("locale zh en", async ({ page }) => {
    await page.goto("/app/app", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: "中文" }).click();
    await page.waitForTimeout(400);
    await expect(page.getByRole("link", { name: /工作台|模拟交易|广场/ }).first()).toBeVisible();
    await page.getByRole("button", { name: "EN" }).click();
    await page.waitForTimeout(400);
    await expect(page.getByRole("link", { name: /Desk|Paper|Feed/ }).first()).toBeVisible();
  });

  test("paper trading start stop", async ({ page }) => {
    await page.goto("/app/paper", { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /启动|重新启动|Start/i }).click();
    await page.waitForTimeout(4000);
    const stop = page.getByRole("button", { name: /^停止$|Stop/i });
    if (await stop.isVisible().catch(() => false)) {
      await stop.click();
      await page.waitForTimeout(1500);
    }
  });
});

test.describe("mobile viewports", () => {
  test.skip(!token, "QUANTLAB_E2E_TOKEN required");
  for (const vp of [
    { w: 390, h: 844, name: "iphone" },
    { w: 430, h: 932, name: "iphone-pro" },
  ]) {
    test(`mobile ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.w, height: vp.h });
      await injectAuth(page);
      await page.goto("/app/app", { waitUntil: "networkidle" });
      await expect(page.getByText(/ziyingke/i).first()).toBeVisible({ timeout: 20000 });
      await page.goto("/app/paper", { waitUntil: "networkidle" });
      await expect(page.getByRole("button", { name: /启动|Start/i })).toBeVisible();
      await page.goto("/app/challenges", { waitUntil: "networkidle" });
      await expect(page.getByText(/挑战|Challenge|30/i).first()).toBeVisible();
    });
  }
});
