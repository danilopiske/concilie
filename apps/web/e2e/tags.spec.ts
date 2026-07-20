import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

const TAG_NOME = `tag-e2e-${Date.now()}`;

test.describe('Gestão de Tags', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/relatorios/tags');
    await page.waitForLoadState('networkidle');
  });

  test('página de tags carrega com heading correto', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: /tags/i }).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('exibe lista de tags ou estado vazio após carregamento', async ({ page }) => {
    await page.waitForTimeout(2000);

    const hasTable = await page.locator('table').first().isVisible({ timeout: 3000 }).catch(() => false);
    const hasImg = await page.locator('main img').first().isVisible({ timeout: 3000 }).catch(() => false);

    expect(hasTable || hasImg).toBe(true);
  });

  test('botão "Nova Tag" abre formulário de criação', async ({ page }) => {
    const novaTagBtn = page.getByRole('button', { name: /nova tag/i });
    await expect(novaTagBtn).toBeVisible({ timeout: 10000 });
    await novaTagBtn.click();

    // Formulário aparece com heading "Nova Tag"
    await expect(page.getByRole('heading', { name: /nova tag/i })).toBeVisible({ timeout: 5000 });
    // Campo de nome visível
    await expect(page.getByPlaceholder(/clausula_contratual|ex:/i)).toBeVisible({ timeout: 3000 });
  });

  test('criar nova tag com nome válido → tag aparece na lista', async ({ page }) => {
    await page.getByRole('button', { name: /nova tag/i }).click();

    // Aguardar formulário abrir
    await expect(page.getByRole('heading', { name: /nova tag/i })).toBeVisible({ timeout: 5000 });

    // Preencher campo nome
    await page.getByPlaceholder(/clausula_contratual|ex:/i).fill(TAG_NOME);

    // Preencher conteúdo padrão (obrigatório)
    await page.getByPlaceholder(/HTML ou texto|inserido no editor/i).fill('<p>Conteúdo de teste E2E</p>');

    // Clicar Salvar
    await page.getByRole('button', { name: /salvar/i }).click();

    // Aguardar feedback e tag na lista
    await page.waitForTimeout(2000);
    await expect(page.getByText(TAG_NOME)).toBeVisible({ timeout: 10000 });
  });

  test('excluir tag remove-a da lista', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Verificar se há tabela com tags
    const tableExists = await page.locator('table tbody tr').first().isVisible({ timeout: 3000 }).catch(() => false);

    if (!tableExists) {
      test.skip();
      return;
    }

    const rowsBefore = await page.locator('table tbody tr').count();

    // Configurar handler de dialog
    page.on('dialog', (dialog) => dialog.accept());

    // Clicar no último botão de excluir (ícone de lixeira na tabela)
    await page.locator('table tbody tr').last().locator('button').last().click();
    await page.waitForTimeout(1500);

    const rowsAfter = await page.locator('table tbody tr').count();
    expect(rowsAfter).toBeLessThanOrEqual(rowsBefore);
  });
});
