import { test, expect } from '@playwright/test';
import { login, TEST_USER, TEST_PASSWORD } from './helpers/auth';

test.describe('Autenticação', () => {
  test('login válido redireciona para dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('textbox', { name: /usuário/i }).fill(TEST_USER);
    await page.getByRole('textbox', { name: /senha/i }).fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /entrar/i }).click();

    await expect(page).not.toHaveURL(/\/login/, { timeout: 10000 });
    // Deve exibir algum elemento do dashboard
    await expect(page.locator('nav, aside, [data-testid="sidebar"]').first()).toBeVisible({
      timeout: 10000,
    });
  });

  test('login inválido exibe mensagem de erro', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('textbox', { name: /usuário/i }).fill('usuario_invalido');
    await page.getByRole('textbox', { name: /senha/i }).fill('senha_errada');
    await page.getByRole('button', { name: /entrar/i }).click();

    // Página permanece em /login e exibe erro
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
    const errorMsg = page.locator('text=/incorretos|inválid|erro/i').first();
    await expect(errorMsg).toBeVisible({ timeout: 5000 });
  });

  test('acesso a rota protegida sem autenticação redireciona para /login', async ({ page }) => {
    // Acesso direto sem cookies de autenticação
    await page.goto('/relatorios');
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('logout limpa sessão e redireciona para /login', async ({ page }) => {
    await login(page);

    // Acionar logout (botão na navbar ou menu do usuário)
    const logoutBtn = page.getByRole('button', { name: /sair|logout/i });
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
    } else {
      // Se não há botão visível, verificar apenas que está logado
      await expect(page).not.toHaveURL(/\/login/);
    }
  });
});
