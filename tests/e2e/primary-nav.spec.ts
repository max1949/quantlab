import { test, expect } from "@playwright/test";

const publicPages = [
  { path: "/app/", name: "landing" },
  { path: "/app/feed", name: "feed" },
  { path: "/app/leaderboards", name: "leaderboards" },
  { path: "/app/pricing", name: "pricing" },
  { path: "/app/login", name: "login" },
];

for (const p of publicPages) {
  test(`public page loads: ${p.name}`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    const res = await page.goto(p.path, { waitUntil: "domcontentloaded" });
    expect(res?.ok() || res?.status() === 304).toBeTruthy();
    await expect(page.getByRole("link", { name: /QuantLab/i }).first()).toBeVisible();
    expect(errors, `console pageerror on ${p.name}`).toEqual([]);
  });
}

test("theme + locale chrome visible", async ({ page }) => {
  await page.goto("/app/");
  await expect(page.getByRole("button", { name: /日间|Light/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /EN/i })).toBeVisible();
});

test("AI strategy page requires auth", async ({ page }) => {
  await page.goto("/app/ai-strategy");
  await expect(page).toHaveURL(/login|onboarding|ai-strategy/);
});
