# ============================================================================
# SCRIPT DE LIMPEZA PARA DISTRIBUICAO
# Remove arquivos temporarios e locais antes de distribuir
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CONCILIE - LIMPEZA PARA DISTRIBUICAO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$itemsRemoved = 0
$spaceFreed = 0

function Remove-ItemSafe {
    param($Path, $Description)
    
    if (Test-Path $Path) {
        try {
            $size = (Get-ChildItem $Path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Remove-Item $Path -Recurse -Force -ErrorAction Stop
            $script:itemsRemoved++
            $script:spaceFreed += $size
            Write-Host "  [OK] Removido: $Description" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "  [AVISO] Erro ao remover: $Description - $($_.Exception.Message)" -ForegroundColor Yellow
            return $false
        }
    } else {
        Write-Host "  [INFO] Nao encontrado: $Description" -ForegroundColor Gray
        return $false
    }
}

# 1. Remover Ambientes Virtuais
Write-Host ""
Write-Host "[1/8] Removendo ambientes virtuais..." -ForegroundColor Cyan
Remove-ItemSafe ".venv" "Ambiente virtual (.venv)"
Remove-ItemSafe ".venv_test" "Ambiente virtual de teste (.venv_test)"
Remove-ItemSafe "venv" "Ambiente virtual (venv)"
Remove-ItemSafe "venv2" "Ambiente virtual (venv2)"
Remove-ItemSafe "env" "Ambiente virtual (env)"

# 2. Remover Cache Python
Write-Host ""
Write-Host "[2/8] Removendo cache Python..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\.venv_backup_*\*" } | ForEach-Object {
    Remove-ItemSafe $_.FullName "Cache Python: $($_.FullName)"
}
Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\.venv_backup_*\*" } | ForEach-Object {
    Remove-ItemSafe $_.FullName "Bytecode: $($_.Name)"
}
Get-ChildItem -Path . -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\.venv_backup_*\*" } | ForEach-Object {
    Remove-ItemSafe $_.FullName "Bytecode otimizado: $($_.Name)"
}

# 3. Remover Banco de Dados Local
Write-Host ""
Write-Host "[3/8] Removendo bancos de dados locais..." -ForegroundColor Cyan
Remove-ItemSafe "data/concilie.db" "Banco SQLite (concilie.db)"
Remove-ItemSafe "data/concilie.db-shm" "Arquivo compartilhado (concilie.db-shm)"
Remove-ItemSafe "data/concilie.db-wal" "Write-Ahead Log (concilie.db-wal)"

# 4. Remover Planilhas de Teste
Write-Host ""
Write-Host "[4/8] Removendo planilhas de teste..." -ForegroundColor Cyan
Remove-ItemSafe "lancamento_planilhas" "Planilhas de lancamento"
Remove-ItemSafe "venda_planilhas" "Planilhas de venda"
Remove-ItemSafe "arquivos_processados" "Arquivos processados"

Get-ChildItem -Path "data" -Recurse -Filter "*.xlsx" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafe $_.FullName "Planilha: $($_.Name)"
}
Get-ChildItem -Path "data" -Recurse -Filter "*.xls" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafe $_.FullName "Planilha: $($_.Name)"
}

# 5. Remover Relatorios Gerados
Write-Host ""
Write-Host "[5/8] Removendo relatorios gerados..." -ForegroundColor Cyan
Get-ChildItem -Path "relatorios" -Filter "*.html" -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne "template_relatorio.html" } | ForEach-Object {
    Remove-ItemSafe $_.FullName "Relatorio HTML: $($_.Name)"
}
Get-ChildItem -Path "relatorios" -Filter "*.png" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemSafe $_.FullName "Grafico: $($_.Name)"
}

# 6. Remover Arquivos Temporarios
Write-Host ""
Write-Host "[6/8] Removendo arquivos temporarios..." -ForegroundColor Cyan
Remove-ItemSafe "temp" "Diretorio temporario"

# 7. Remover Schemas JSON (usados para migracao)
Write-Host ""
Write-Host "[7/8] Removendo schemas de migracao..." -ForegroundColor Cyan
Remove-ItemSafe "mysql_schema.json" "Schema MySQL"
Remove-ItemSafe "sqlite_schema.json" "Schema SQLite"

# 8. Remover Diretorios Nao Relacionados
Write-Host ""
Write-Host "[8/8] Removendo diretorios nao relacionados..." -ForegroundColor Cyan
Remove-ItemSafe "spotify_downloader" "Spotify Downloader"
Remove-ItemSafe "bd_structures" "Estruturas BD"

# Relatorio Final
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RELATORIO FINAL" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Itens removidos: $itemsRemoved" -ForegroundColor White
$spaceMB = [math]::Round($spaceFreed / 1MB, 2)
Write-Host "  Espaco liberado: $spaceMB MB" -ForegroundColor White
Write-Host ""
Write-Host "[OK] Limpeza concluida!" -ForegroundColor Green
Write-Host ""

# Criar ZIP de distribuicao
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CRIANDO ZIP DE DISTRIBUICAO" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Remover ZIPs antigos primeiro
Write-Host "[INFO] Removendo ZIPs antigos..." -ForegroundColor Cyan
Get-ChildItem -Filter "Concilie_v2.0_Distribuicao_*.zip" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  [OK] Removido: $($_.Name)" -ForegroundColor Green
}
Write-Host ""

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "Concilie_v2.0_Distribuicao_$timestamp.zip"

Write-Host "[INFO] Selecionando arquivos..." -ForegroundColor Cyan
$files = Get-ChildItem -Recurse | Where-Object { 
    $_.FullName -notlike "*\.venv\*" -and 
    $_.FullName -notlike "*\.venv_backup_*\*" -and 
    $_.Name -notlike "*.db" -and 
    $_.Name -notlike "*.db-shm" -and 
    $_.Name -notlike "*.db-wal" -and 
    $_.Name -notlike "*.zip" -and 
    $_.PSIsContainer -eq $false 
}

$fileCount = $files.Count
Write-Host "  Arquivos selecionados: $fileCount" -ForegroundColor Gray
Write-Host ""

Write-Host "[INFO] Compactando arquivos..." -ForegroundColor Cyan
try {
    Compress-Archive -Path $files.FullName -DestinationPath $zipName -Force -CompressionLevel Optimal
    
    $zipSize = [math]::Round((Get-Item $zipName).Length / 1MB, 2)
    
    Write-Host ""
    Write-Host "[OK] ZIP criado com sucesso!" -ForegroundColor Green
    Write-Host "  Nome: $zipName" -ForegroundColor White
    Write-Host "  Tamanho: $zipSize MB" -ForegroundColor White
    Write-Host "  Arquivos: $fileCount" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERRO] Falha ao criar ZIP: $_" -ForegroundColor Red
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "  1. Teste a instalacao em ambiente limpo" -ForegroundColor White
Write-Host "  2. Extraia o ZIP e execute: python install.py" -ForegroundColor White
Write-Host "  3. Execute: python main.py --mode singleuser" -ForegroundColor White
Write-Host "  4. Para restaurar venv: .\backup_restore_venv.ps1 -Restore" -ForegroundColor White
Write-Host ""
