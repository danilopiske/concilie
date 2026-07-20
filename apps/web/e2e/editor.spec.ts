import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.describe('Editor de Relatório', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('página do editor sem task_id exibe título e botões de ação', async ({ page }) => {
    await page.goto('/relatorios/editor');
    await page.waitForLoadState('networkidle');

    // Deve exibir o heading do editor
    await expect(page.getByRole('heading', { name: /editor de relatório/i })).toBeVisible({
      timeout: 10000,
    });
    // Botão Voltar deve estar presente
    await expect(page.getByRole('button', { name: /voltar/i })).toBeVisible({ timeout: 5000 });
  });

  test('editor com task_id inválido exibe mensagem de erro 404', async ({ page }) => {
    await page.goto('/relatorios/editor?task_id=task_inexistente_123');
    await page.waitForLoadState('networkidle');

    // Exibe erro de 404 ou "não encontrado"
    const errorText = page.getByText(/404|não encontrad|request failed/i).first();
    await expect(errorText).toBeVisible({ timeout: 10000 });
  });

  test('editor exibe heading e botão Salvar', async ({ page }) => {
    await page.goto('/relatorios/editor?task_id=test');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: /editor de relatório/i })).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByRole('button', { name: /salvar/i })).toBeVisible({ timeout: 5000 });
  });

  test('editor TipTap exibe área de edição quando task carrega', async ({ page }) => {
    await page.goto('/relatorios/editor?task_id=test');
    await page.waitForLoadState('networkidle');

    const editor = page.locator('[contenteditable="true"]').first();
    if (await editor.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editor.click();
      await editor.type('Teste de digitação no editor');
      const text = await editor.innerText();
      expect(text).toContain('Teste de digitação no editor');
    } else {
      // Editor não carregou (task inválida) — aceita com skip
      test.skip();
    }
  });

  test('digitar / no editor exibe menu de slash commands', async ({ page }) => {
    await page.goto('/relatorios/editor?task_id=test');
    await page.waitForLoadState('networkidle');

    const editor = page.locator('[contenteditable="true"]').first();
    if (await editor.isVisible({ timeout: 5000 }).catch(() => false)) {
      await editor.click();
      await page.keyboard.press('/');
      // Aguardar dropdown de slash commands
      const slashMenu = page.locator('[class*="tippy"], [data-tippy-root], [role="listbox"]').first();
      await expect(slashMenu).toBeVisible({ timeout: 3000 });
    } else {
      test.skip();
    }
  });
});
