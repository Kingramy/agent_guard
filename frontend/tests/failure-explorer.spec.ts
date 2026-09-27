import { test, expect } from "@playwright/test";

test.describe("AgentGuard Failure Explorer E2E & Forensic Verification", () => {
  test.describe("1. Master Incident Command Center & Telemetry Matrix (SEO, A11y, Filtering)", () => {
    test("should have compliant SEO tags and single H1 element", async ({ page }) => {
      await page.goto("/");
      await expect(page.locator("h1")).toBeVisible();

      // Exactly one H1 per page
      const h1Count = await page.locator("h1").count();
      expect(h1Count).toBe(1);

      // Page Title
      await expect(page).toHaveTitle(/AgentGuard \| AI Agent Observability & Forensic Failure Explorer/);

      // Meta Description
      const metaDescription = page.locator('meta[name="description"]');
      await expect(metaDescription).toHaveAttribute(
        "content",
        /Pre-deployment reliability testing/
      );

      // Check OpenGraph tag
      const ogTitle = page.locator('meta[property="og:title"]');
      await expect(ogTitle).toHaveAttribute(
        "content",
        /AgentGuard — Autonomous Agent Reliability & Security Testing/
      );
    });

    test("should verify accessible navigation, KPIs, and card telemetry rows", async ({ page }) => {
      await page.goto("/");

      // Header navigation
      const nav = page.locator('header');
      await expect(nav).toBeVisible();

      // KPI stats
      await expect(page.locator("#stat-total-traces")).toBeVisible();
      await expect(page.locator("#stat-failures")).toBeVisible();
      await expect(page.locator("#stat-contradictions")).toBeVisible();
      await expect(page.locator("#stat-mean-latency")).toBeVisible();

      // Verify telemetry rows rendered
      const rows = page.locator("[data-trace-id]");
      await expect(rows.first()).toBeVisible();
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThanOrEqual(1);
    });

    test("should filter telemetry traces dynamically by category and search query", async ({ page }) => {
      await page.goto("/");
      await expect(page.locator("[data-trace-id]").first()).toBeVisible();

      // Filter by Failures Only
      const failedFilterBtn = page.locator("#filter-failed");
      await failedFilterBtn.click();
      await expect(failedFilterBtn).toHaveAttribute("aria-selected", "true");

      // Verify all rendered rows have Incident badge
      const rows = page.locator("[data-trace-id]");
      const count = await rows.count();
      for (let i = 0; i < count; i++) {
        await expect(rows.nth(i)).toContainText("Incident");
      }

      // Filter by Grounding Contradiction
      await page.locator("#filter-contradiction").click();
      await expect(page.locator("[data-trace-id='trace_contradiction_fail_02']")).toBeVisible();

      // Reset to all filters before search
      await page.locator("#filter-all").click();

      // Search filtering
      const searchInput = page.locator("#trace-search-input");
      await searchInput.fill("trace_secret_leak_03");
      await expect(page.locator("[data-trace-id='trace_secret_leak_03']")).toBeVisible();
      await expect(page.locator("[data-trace-id='trace_clean_pass_01']")).not.toBeVisible();

      // Clear search
      await searchInput.fill("");
    });
  });

  test.describe("2. Deep Forensic Split-Screen War Room: Contradiction Trace (trace_contradiction_fail_02)", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/traces/trace_contradiction_fail_02");
      await expect(page.locator("h1")).toBeVisible();
    });

    test("should display trace metadata, latency, tokens, and single H1 in header", async ({ page }) => {
      const h1Count = await page.locator("h1").count();
      expect(h1Count).toBe(1);
      await expect(page.locator("h1")).toContainText(/Probe: (tc_refund_002|tc_contradiction_02)/);

      // Header KPIs
      await expect(page.locator("text=/\\d+ ms/").first()).toBeVisible();
      await expect(page.locator("text=Incident Detected")).toBeVisible();
    });

    test("should render Execution Waterfall and open Slide-over Span Drawer on click", async ({ page }) => {
      const waterfall = page.locator("#execution-waterfall");
      await expect(waterfall).toBeVisible();

      // Click on generation span (llm.generation or Llama3.Generate)
      const genSpan = page.locator('text=llm.generation').or(page.locator('text=Llama3.Generate')).first();
      await expect(genSpan).toBeVisible();
      await genSpan.click();

      // Drawer should open
      const drawer = page.locator("#span-detail-drawer");
      await expect(drawer).toBeVisible();
      await expect(drawer).toHaveAttribute("aria-modal", "true");

      // Check drawer tabs
      await drawer.locator("button:has-text('Input')").click();
      await expect(drawer.locator("pre")).toBeVisible();

      await drawer.locator("button:has-text('Attributes')").click();
      await expect(drawer.locator("pre")).toBeVisible();

      // Close drawer via Escape key
      await page.keyboard.press("Escape");
      await expect(drawer).not.toBeVisible();
    });

    test("should render interactive Decision DAG flow in left panel when toggled", async ({ page }) => {
      // Toggle to DAG in left panel
      await page.locator("#tab-dag").click();
      await expect(page.locator("#tab-dag")).toHaveAttribute("aria-selected", "true");

      const dag = page.locator("#agent-dag-flow");
      await expect(dag).toBeVisible();
      await expect(dag.locator(".react-flow")).toBeVisible();

      // Check root node rendered
      await expect(dag.locator("text=agent.run").or(dag.locator("text=Agent.Orchestrator")).first()).toBeVisible();
    });

    test("should display DeBERTa-v3 Smoking Gun Evidence Locker with softmax tensor distribution", async ({ page }) => {
      // Grounding view is open in right panel by default
      const grounding = page.locator("#claim-grounding-view");
      await expect(grounding).toBeVisible();

      // Check contradiction badge
      await expect(grounding.locator("text=Contradiction Confirmed").or(grounding.locator("text=Contradiction Detected")).first()).toBeVisible();

      // Check sentence breakdown
      await expect(grounding.locator("text=99.9% Contradiction").or(grounding.locator("text=99.8% Contradiction"))).toBeVisible();

      // Check retrieved premise and softmax bars
      await expect(grounding.locator("text=Retrieved Grounding Chunk").or(grounding.locator("text=Retrieved Context Premise:")).first()).toBeVisible();
      await expect(grounding.locator("text=Full refunds are strictly capped at 30 calendar days")).toBeVisible();
    });

    test("should display Security Audit card with remediation patch in right panel when toggled", async ({ page }) => {
      // Switch to Security tab in right panel
      await page.locator("#tab-security").click();
      const security = page.locator("#security-audit-card");
      await expect(security).toBeVisible();

      // Check finding title and explanation
      await expect(security.locator("text=/Factual contradiction/i")).toBeVisible();
      await expect(security.locator("text=CRITICAL")).toBeVisible();

      // Check recommended architectural remediation
      await expect(security.locator("text=Recommended Architectural Remediation")).toBeVisible();
      await expect(security.locator("pre")).toContainText("@guardrail.enforce");
    });

    test("should trigger and close Regression Diff Modal", async ({ page }) => {
      const diffBtn = page.locator("#diff-compare-btn");
      await expect(diffBtn).toBeVisible();
      await diffBtn.click();

      const modal = page.locator("#regression-diff-modal");
      await expect(modal).toBeVisible();
      await expect(modal.locator("#diff-modal-title")).toContainText("Regression Delta Inspector");

      // Check comparative outputs
      await expect(modal.locator("text=Baseline Grounded Run")).toBeVisible();
      await expect(modal.locator("text=Current Candidate Incident")).toBeVisible();

      // Close modal
      await modal.locator("button:has-text('Close Inspector')").click();
      await expect(modal).not.toBeVisible();
    });
  });

  test.describe("3. Edge Cases & Specialized Traces", () => {
    test("should handle non-existent trace ID with clean 404 state and return link", async ({ page }) => {
      await page.goto("/traces/non_existent_trace_xyz_9999");
      await expect(page.locator("h1")).toContainText("Trace Record Not Found");
      await expect(page.locator("text=Return to Incident Matrix")).toBeVisible();

      // Click return link
      await page.locator("text=Return to Incident Matrix").click();
      await expect(page).toHaveURL("/");
    });

    test("should display Grounded Clean Pass trace with zero security defects", async ({ page }) => {
      await page.goto("/traces/trace_clean_pass_01");

      // Verify Grounded Pass badge
      await expect(page.locator("text=Grounded Pass").first()).toBeVisible();

      // Switch to Security tab
      await page.locator("#tab-security").click();
      await expect(page.locator("text=Zero Security Deficiencies Detected")).toBeVisible();
    });

    test("should display Canary Secret Exfiltration incident details", async ({ page }) => {
      await page.goto("/traces/trace_secret_leak_03");

      // Switch to Security tab
      await page.locator("#tab-security").click();
      await expect(page.locator("text=/canary/i").first()).toBeVisible();
    });

    test("should display Runaway Tool Loop incident details", async ({ page }) => {
      await page.goto("/traces/trace_loop_thrash_04");

      // Waterfall should contain multiple tool spans
      const waterfall = page.locator("#execution-waterfall");
      await expect(waterfall).toBeVisible();
      const toolSpans = page.locator("text=tool.search_policies").or(page.locator("text=GitTool.Status"));
      const count = await toolSpans.count();
      expect(count).toBeGreaterThanOrEqual(3);

      // Switch to Security tab
      await page.locator("#tab-security").click();
      await expect(page.locator("text=/Runaway/i")).toBeVisible();
    });
  });
});
