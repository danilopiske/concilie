Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PREPARACAO PARA MIGRACAO" -ForegroundColor Cyan
Write-Host "  Next.js + TypeScript + FastAPI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/7] Validando ferramentas necessarias..." -ForegroundColor Yellow
Write-Host ""

$allOk = $true

Write-Host "  Verificando Node.js..." -ForegroundColor Cyan
try {
    $nodeVersion = node --version
    Write-Host "    OK Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERRO Node.js NAO encontrado" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  Verificando pnpm..." -ForegroundColor Cyan
try {
    $pnpmVersion = pnpm --version
    Write-Host "    OK pnpm: $pnpmVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERRO pnpm NAO encontrado" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  Verificando Poetry..." -ForegroundColor Cyan
try {
    $poetryVersion = poetry --version
    Write-Host "    OK Poetry: $poetryVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERRO Poetry NAO encontrado" -ForegroundColor Red
    $allOk = $false
}

Write-Host "  Verificando Git..." -ForegroundColor Cyan
try {
    $gitVersion = git --version
    Write-Host "    OK Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "    ERRO Git NAO encontrado" -ForegroundColor Red
    $allOk = $false
}

Write-Host ""

if (-not $allOk) {
    Write-Host "ERRO: Algumas ferramentas estao faltando!" -ForegroundColor Red
    exit 1
}

Write-Host "[2/7] Verificando branch Git..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
Write-Host "  Branch atual: $currentBranch" -ForegroundColor Cyan
Write-Host ""

Write-Host "[3/7] Verificando status do repositorio..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "  Existem mudancas nao commitadas" -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "  Repositorio limpo" -ForegroundColor Green
}
Write-Host ""

Write-Host "[4/7] Criando estrutura monorepo..." -ForegroundColor Yellow

$dirs = @(
    "apps",
    "apps/web",
    "apps/api",
    "packages",
    "packages/shared-types"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Ja existe: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

Write-Host "[5/7] Resumo das ferramentas..." -ForegroundColor Yellow
Write-Host "  Node.js: $nodeVersion" -ForegroundColor White
Write-Host "  pnpm: $pnpmVersion" -ForegroundColor White
Write-Host "  Poetry: $poetryVersion" -ForegroundColor White
Write-Host "  Git: $gitVersion" -ForegroundColor White
Write-Host ""

Write-Host "[6/7] Proximos passos..." -ForegroundColor Yellow
Write-Host "  1. Executar: .\setup_monorepo.ps1" -ForegroundColor Cyan
Write-Host "  2. Executar: .\setup_fastapi.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "[7/7] Preparacao concluida!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PREPARACAO CONCLUIDA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
