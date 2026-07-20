import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.describe('Módulo de Relatórios', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/relatorios');
    await page.waitForLoadState('networkidle');
  });

  test('página de relatórios carrega com heading correto', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /relatório/i }).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('exibe formulário de configuração ou histórico de relatórios', async ({ page }) => {
    // A página exibe formulário de geração OU histórico de relatórios gerados
    const form = page.locator('form, [role="form"]').first();
    const hasForm = await form.isVisible({ timeout: 3000 }).catch(() => false);

    // Alternativamente verifica combobox de cálculo ou mensagem de info
    const combobox = page.locator('select, [role="combobox"]').first();
    const hasCombo = await combobox.isVisible({ timeout: 3000 }).catch(() => false);

    const infoMsg = page.getByText(/configure|gerar|relatório/i).first();
    const hasInfo = await infoMsg.isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasForm || hasCombo || hasInfo).toBe(true);
  });

  test('botão "Gerar Relatório" está presente na página', async ({ page }) => {
    const gerarBtn = page.getByRole('button', { name: /gerar/i });
    await expect(gerarBtn).toBeVisible({ timeout: 10000 });
  });

  test('formulário de geração de relatório tem campos de seleção', async ({ page }) => {
    // Deve ter ao menos um combobox/select ou radio button para os parâmetros
    const selects = page.locator('select, [role="combobox"], input[type="radio"]');
    const count = await selects.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('link "Gerenciar Tags" está visível e navegável', async ({ page }) => {
    const tagsLink = page.getByRole('link', { name: /gerenciar tags/i });
    await expect(tagsLink).toBeVisible({ timeout: 5000 });
    await tagsLink.click();
    await expect(page).toHaveURL(/\/relatorios\/tags/, { timeout: 5000 });
  });
});
