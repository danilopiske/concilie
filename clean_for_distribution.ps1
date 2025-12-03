# Script de preparacao para distribuicao - Financial Checker
# Cria pacote ZIP limpo com banco SQLite incluido

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PREPARACAO PARA DISTRIBUICAO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se base_concilie.db existe
$baseBanco = "data\base_concilie.db"
if (-not (Test-Path $baseBanco)) {
    Write-Host "[ERRO] Banco master nao encontrado: $baseBanco" -ForegroundColor Red
    Write-Host "[INFO] Execute create_clean_sqlite.py primeiro" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] Criando banco para distribuicao..." -ForegroundColor Green
Copy-Item $baseBanco "data\concilie.db" -Force
Write-Host "  OK concilie.db criado (copia de base_concilie.db)" -ForegroundColor Gray
Write-Host ""

Write-Host "[2/4] Preparando arquivos..." -ForegroundColor Green
$tempDist = "dist_temp"
if (Test-Path $tempDist) {
    Remove-Item $tempDist -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDist | Out-Null

Write-Host "  OK Copiando arquivos da raiz..." -ForegroundColor Gray
Copy-Item "main.py" -Destination $tempDist
Copy-Item "install.py" -Destination $tempDist
Copy-Item "requirements.txt" -Destination $tempDist
Copy-Item "Instalar.bat" -Destination $tempDist
Copy-Item "Iniciar Sistema.bat" -Destination $tempDist
Copy-Item "README.md" -Destination $tempDist -ErrorAction SilentlyContinue

Write-Host "  OK Copiando instalador Python..." -ForegroundColor Gray
if (Test-Path "python-3.13.9-amd64.exe") {
    Copy-Item "python-3.13.9-amd64.exe" -Destination $tempDist
} else {
    Write-Host "  [AVISO] python-3.13.9-amd64.exe nao encontrado (ignorando)" -ForegroundColor Yellow
}

Write-Host "  OK Copiando modulos..." -ForegroundColor Gray
Copy-Item "conf" -Destination $tempDist -Recurse
Copy-Item "modules" -Destination $tempDist -Recurse
Copy-Item "proc" -Destination $tempDist -Recurse

Write-Host "  OK Copiando assets..." -ForegroundColor Gray
Copy-Item "assets" -Destination $tempDist -Recurse -ErrorAction SilentlyContinue

Write-Host "  OK Criando estrutura de diretorios..." -ForegroundColor Gray
New-Item -ItemType Directory -Path "$tempDist\data" -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDist\relatorios" -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDist\temp" -Force | Out-Null

Write-Host "  OK Incluindo banco de dados..." -ForegroundColor Gray
Copy-Item "data\concilie.db" -Destination "$tempDist\data" -Force
Write-Host ""

Write-Host "[3/4] Limpando arquivos temporarios..." -ForegroundColor Green
Get-ChildItem -Path $tempDist -Include "__pycache__","*.pyc" -Recurse -Force | Remove-Item -Force -Recurse
Write-Host "  OK Cache Python removido" -ForegroundColor Gray
Write-Host ""

Write-Host "[4/4] Criando arquivo ZIP..." -ForegroundColor Green
$nomeZip = "Financial_Checker_SQLite_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
if (Test-Path $nomeZip) {
    Remove-Item $nomeZip -Force
}
Compress-Archive -Path "$tempDist\*" -DestinationPath $nomeZip -CompressionLevel Optimal
Write-Host "  OK Pacote criado: $nomeZip" -ForegroundColor Gray

Remove-Item $tempDist -Recurse -Force
Write-Host ""

$tamanho = (Get-Item $nomeZip).Length / 1MB
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OK DISTRIBUICAO PRONTA!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Arquivo: $nomeZip" -ForegroundColor White
Write-Host "Tamanho: $([Math]::Round($tamanho, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "Conteudo incluido:" -ForegroundColor Yellow
Write-Host "  - Codigo Python (main.py + modulos)" -ForegroundColor Gray
Write-Host "  - Banco SQLite (concilie.db com schema e usuario admin)" -ForegroundColor Gray
Write-Host "  - Script de instalacao simplificado (install.py)" -ForegroundColor Gray
Write-Host "  - Dependencias (requirements.txt)" -ForegroundColor Gray
Write-Host "  - Instalador Python 3.13.9 (se disponivel)" -ForegroundColor Gray
Write-Host ""
Write-Host "Instrucoes para o cliente:" -ForegroundColor Yellow
Write-Host "  1. Extrair ZIP em uma pasta" -ForegroundColor Gray
Write-Host "  2. Se nao tiver Python: executar python-3.13.9-amd64.exe" -ForegroundColor Gray
Write-Host "     (marcar 'Add to PATH' na instalacao)" -ForegroundColor Gray
Write-Host "  3. Dar duplo clique em: Instalar.bat" -ForegroundColor Gray
Write-Host "     (cria ambiente virtual + instala dependencias)" -ForegroundColor Gray
Write-Host "  4. Dar duplo clique em: Iniciar Sistema.bat" -ForegroundColor Gray
Write-Host "  5. Acessar: http://localhost:8500" -ForegroundColor Gray
Write-Host "  6. Login: admin / 1234" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
