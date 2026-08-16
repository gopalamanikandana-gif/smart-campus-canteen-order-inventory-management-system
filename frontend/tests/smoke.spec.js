import { test, expect } from "@playwright/test";

test("login page loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Smart Campus Canteen")).toBeVisible();
  await expect(page.getByPlaceholder("Email")).toBeVisible();
});

test("student can login and see menu", async ({ page }) => {
  await page.goto("/");
  await page.getByPlaceholder("Email").fill("student@canteen.local");
  await page.getByPlaceholder("Password").fill("Student@123");
  await page.getByRole("button", { name: "Login" }).click();

  await expect(page.getByRole("heading", { name: "Menu" })).toBeVisible();
  await expect(page.getByText("Veg Burger")).toBeVisible();
});
