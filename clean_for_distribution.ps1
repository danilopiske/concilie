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
$tempDist = ".dist_temp"

Write-Host "[INFO] Preparando estrutura de distribuicao..." -ForegroundColor Cyan

# Remover pasta temp se existir
if (Test-Path $tempDist) {
    Remove-Item $tempDist -Recurse -Force
}

# Criar pasta temporaria
New-Item -ItemType Directory -Path $tempDist -Force | Out-Null

# Copiar arquivos mantendo estrutura
Write-Host "[INFO] Copiando arquivos essenciais..." -ForegroundColor Cyan

# Arquivos raiz
$rootFiles = @(
    "main.py", "install.py", "requirements.txt", "README.md", "README_NEW.md",
    ".gitignore", "backup_restore_venv.ps1", "clean_for_distribution.ps1",
    "INSTALL_QUICK.md", "REQUISITOS_INSTALACAO.md", "RESUMO_DISTRIBUICAO.md",
    "ESTRUTURA_DISTRIBUICAO.md", "GUIA_INSTALACAO_DISTRIBUICAO.md",
    "COMPATIBILIDADE_SQL.md", "ANALISE_COMPLETA_SISTEMA.md",
    "compare_schemas.py", "migrate_mysql_to_sqlite.py"
)

foreach ($file in $rootFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $tempDist -Force
    }
}

# Copiar pastas inteiras (com estrutura)
$folders = @("conf", "modules", "proc", "assets")
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        # Copiar apenas arquivos .py e imagens
        $destFolder = Join-Path $tempDist $folder
        New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
        
        Get-ChildItem -Path $folder -Filter "*.py" -File | ForEach-Object {
            Copy-Item $_.FullName -Destination $destFolder -Force
        }
        
        # Copiar imagens da pasta assets
        if ($folder -eq "assets") {
            Get-ChildItem -Path $folder -Include "*.png","*.jpg","*.jpeg" -Recurse -File | ForEach-Object {
                Copy-Item $_.FullName -Destination $destFolder -Force
            }
        }
    }
}

# Criar estrutura de diretórios vazios com .gitkeep
@("data", "relatorios", "temp") | ForEach-Object {
    $dir = Join-Path $tempDist $_
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $dir ".gitkeep") -Force | Out-Null
}

# Copiar template de relatório se existir
if (Test-Path "relatorios\template_relatorio.html") {
    Copy-Item "relatorios\template_relatorio.html" -Destination (Join-Path $tempDist "relatorios") -Force
}
if (Test-Path "relatorios\README.md") {
    Copy-Item "relatorios\README.md" -Destination (Join-Path $tempDist "relatorios") -Force
}

# Contar arquivos
$fileCount = (Get-ChildItem $tempDist -Recurse -File).Count
Write-Host "  Arquivos preparados: $fileCount" -ForegroundColor Gray
Write-Host ""

Write-Host "[INFO] Compactando distribuicao..." -ForegroundColor Cyan
try {
    # Compactar a pasta temp inteira
    Compress-Archive -Path "$tempDist\*" -DestinationPath $zipName -Force -CompressionLevel Optimal
    
    # Remover pasta temp
    Remove-Item $tempDist -Recurse -Force
    
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
    # Limpar pasta temp em caso de erro
    if (Test-Path $tempDist) {
        Remove-Item $tempDist -Recurse -Force
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "  1. Teste a instalacao em ambiente limpo" -ForegroundColor White
Write-Host "  2. Extraia o ZIP e execute: python install.py" -ForegroundColor White
Write-Host "  3. Execute: python main.py --mode singleuser" -ForegroundColor White
Write-Host "  4. Para restaurar venv: .\backup_restore_venv.ps1 -Restore" -ForegroundColor White
Write-Host ""
