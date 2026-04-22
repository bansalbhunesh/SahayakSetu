const { test, expect } = require("@playwright/test");

const mockSearchResponse = {
  answer: "E2E mock: PM Kisan summary for testing.",
  provider: "e2e-mock",
  sources: [],
  moderation_blocked: false,
  redirect_message: null,
  reasoning_why: null,
  near_miss_text: null,
  near_miss_sources: [],
  session_user_id: "e2e-session-user",
  confidence: "high",
  next_step: null,
  retrieval_debug: null,
  query_debug: { original: "PM Kisan", rewritten: "PM Kisan" },
  plan: null,
  eligibility_hints: [],
};

test.beforeEach(async ({ page }) => {
  await page.route("**/api/search", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "X-Trace-Id": "e2e-trace-1",
      },
      body: JSON.stringify(mockSearchResponse),
    });
  });
});

test("home page loads with branding", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/SahayakSetu/);
  await expect(page.locator(".logo-name")).toContainText("SahayakSetu");
});

test("text send shows mocked assistant answer", async ({ page }) => {
  await page.goto("/");
  await page.locator("#textInput").fill("PM Kisan eligibility");
  await page.locator("#sendBtn").click();
  await expect(page.locator("#conversation")).toContainText("E2E mock:", { timeout: 20_000 });
});

test("finder mode toggle shows finder panel", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-action="mode-finder"]').click();
  await expect(page.locator("#finderPanel")).not.toHaveClass(/hidden/);
  await expect(page.locator("#eligibilityForm")).toBeVisible();
});

test("language pill switches to English", async ({ page }) => {
  await page.goto("/");
  await page.locator('[data-action="select-language"][data-lang="en-IN"]').click();
  await expect(page.locator('[data-action="select-language"][data-lang="en-IN"]')).toHaveClass(/active/);
});
