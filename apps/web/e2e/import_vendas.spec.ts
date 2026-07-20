
import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.beforeEach(async ({ page }) => {
    await login(page);
});

test('Fluxo de Importação de Vendas: deve realizar upload e iniciar processamento no banco', async ({ page }) => {
    // Capturar logs do console do navegador
    page.on('console', msg => console.log(`[BROWSER-LOG] ${msg.text()}`));
    
    // Navegar para a página de importação de vendas
    await page.goto('/importar/vendas');
    await page.waitForLoadState('networkidle');

    // Selecionar Cliente
    const clienteSelect = page.locator('div:has(label:text("Cliente")) select');
    await clienteSelect.waitFor({ state: 'visible' });
    
    // Usar o valor '1' (ID do cliente) - SUPREMA EMBALAGENS
    await clienteSelect.selectOption('1'); 
    await page.waitForTimeout(1000);

    // Selecionar Layout
    const layoutSelect = page.locator('div:has(label:text("Layout / Adquirente")) select');
    await layoutSelect.waitFor({ state: 'visible' });
    await layoutSelect.selectOption('Cielo');
    await page.waitForTimeout(1000);

    // Informar o EC
    const ecSelect = page.locator('div:has(label:text("EC (Estabelecimento)")) select');
    const ecInput = page.locator('div:has(label:text("EC (Estabelecimento)")) input');
    
    if (await ecInput.isVisible() && !(await ecInput.isDisabled())) {
        await ecInput.fill('1051121873');
    } else {
        await page.waitForTimeout(2000);
        await ecSelect.selectOption('1051121873');
    }

    // Caminho do arquivo
    const filePath = 'D:\\0a0a\\Ec 1051121873\\Vendas\\Vendas_cielo_historico_detalhe-20241118-20250516-1_5-xlsx.xlsx';
    
    // Upload do arquivo
    await page.setInputFiles('input[type="file"]', filePath);

    // Processar
    const previewBtn = page.getByRole('button', { name: /Processar|Normalizar/i });
    await expect(previewBtn).toBeEnabled({ timeout: 15000 });
    await previewBtn.click();

    // Verifica se a amostra carregou (tabela de preview)
    await expect(page.locator('table')).toBeVisible({ timeout: 120000 }); 
    await expect(page.locator('text=/Arquivos analisados|Preview do lote/i')).toBeVisible();

    // Clica em Gravar no Banco
    const gravarBtn = page.getByRole('button', { name: /Gravar no Banco/i });
    await expect(gravarBtn).toBeVisible();
    await gravarBtn.click();

    // Verifica se a barra de progresso / status de processamento aparece
    await expect(page.locator('text=/Processando dados|Aguardando Início/i')).toBeVisible();
    
    // Espera a mensagem de sucesso final
    await expect(page.locator('text=/Importação finalizada com sucesso/i')).toBeVisible({ timeout: 120000 });
});
