import { Page } from '@playwright/test';

export const TEST_USER = process.env.E2E_USER ?? 'admin';
export const TEST_PASSWORD = process.env.E2E_PASSWORD ?? '1234';

export async function login(page: Page) {
  await page.goto('/login');
  await page.getByRole('textbox', { name: /usuário/i }).fill(TEST_USER);
  await page.getByRole('textbox', { name: /senha/i }).fill(TEST_PASSWORD);
  await page.getByRole('button', { name: /entrar/i }).click();
  // Wait for redirect away from /login
  await page.waitForURL((url) => !url.pathname.includes('/login'), {
    timeout: 10000,
  });
}
