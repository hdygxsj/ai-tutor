import { expect, test } from "@playwright/test";

test("M1 teacher loop creates a learning plan from dashboard", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByText("今日学习面板")).toBeVisible();
  await expect(page.getByText("机器学习教师 Agent")).toBeVisible();

  await page.getByRole("button", { name: "创建 M1 示例学习计划" }).click();

  await expect(page.getByText("机器学习教师计划")).toBeVisible();
  await expect(page.getByText("完成 autograd 概念作业")).toBeVisible();
});
