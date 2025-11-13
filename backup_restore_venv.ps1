# ============================================================================
# Script: Backup e Restore do Ambiente Virtual (.venv)
# Descricao: Faz backup do .venv antes de limpar para distribuicao
#           e permite restaurar depois
# Uso:
#   Backup:  .\backup_restore_venv.ps1
#   Restore: .\backup_restore_venv.ps1 -Restore
# ============================================================================

param(
    [switch]$Restore
)

# ============================================================================
# MODO BACKUP (padrao)
# ============================================================================
if (-not $Restore) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  BACKUP DO AMBIENTE VIRTUAL (.venv)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $venvPath = ".venv"
    
    # Verificar se .venv existe
    if (-not (Test-Path $venvPath)) {
        Write-Host "[ERRO] Ambiente virtual .venv nao encontrado" -ForegroundColor Red
        Write-Host "   Nada a fazer backup." -ForegroundColor Gray
        exit 1
    }
    
    # Calcular tamanho
    Write-Host "[INFO] Calculando tamanho do ambiente..." -ForegroundColor Cyan
    $size = (Get-ChildItem $venvPath -Recurse -Force | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "   Tamanho: $sizeMB MB" -ForegroundColor Gray
    Write-Host ""
    
    # Confirmacao se muito grande
    if ($sizeMB -gt 500) {
        Write-Host "[AVISO] O ambiente e grande ($sizeMB MB)" -ForegroundColor Yellow
        $confirm = Read-Host "   Continuar com backup? (s/N)"
        if ($confirm -ne 's' -and $confirm -ne 'S') {
            Write-Host "   Backup cancelado." -ForegroundColor Gray
            exit 0
        }
    }
    
    # Criar nome do backup com timestamp
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = ".venv_backup_$timestamp"
    
    Write-Host "[INFO] Criando backup..." -ForegroundColor Cyan
    Write-Host "   Origem: $venvPath" -ForegroundColor Gray
    Write-Host "   Destino: $backupName" -ForegroundColor Gray
    Write-Host ""
    
    $startTime = Get-Date
    
    try {
        # Copiar .venv para backup
        Copy-Item -Path $venvPath -Destination $backupName -Recurse -Force
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host "[OK] Backup criado com sucesso!" -ForegroundColor Green
        Write-Host "   Tempo: $([math]::Round($duration, 2)) segundos" -ForegroundColor Gray
        Write-Host "   Local: $backupName" -ForegroundColor Gray
        Write-Host ""
        
        # Criar arquivo de controle com info do backup
        $backupInfo = @{
            Timestamp = $timestamp
            OriginalPath = $venvPath
            BackupPath = $backupName
            SizeMB = $sizeMB
            CreatedBy = $env:USERNAME
            CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }
        
        $backupInfoFile = Join-Path $backupName ".backup_info.txt"
        $backupInfo.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" } | Out-File $backupInfoFile
        
        Write-Host "[INFO] Informacoes do backup salvas em:" -ForegroundColor Cyan
        Write-Host "   $backupInfoFile" -ForegroundColor Gray
        Write-Host ""
        
        # Instrucoes de proximos passos
        Write-Host "[INFO] Proximos passos:" -ForegroundColor Cyan
        Write-Host "   1. Execute: .\clean_for_distribution.ps1" -ForegroundColor White
        Write-Host "   2. Crie a distribuicao (ZIP, Git, etc.)" -ForegroundColor White
        Write-Host "   3. Para restaurar: .\backup_restore_venv.ps1 -Restore" -ForegroundColor White
        Write-Host ""
        
    } catch {
        Write-Host "[ERRO] Erro ao criar backup: $_" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# MODO RESTORE
# ============================================================================
else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  RESTORE DO AMBIENTE VIRTUAL (.venv)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Procurar backups disponiveis
    $backups = Get-ChildItem -Directory -Filter ".venv_backup_*" | Sort-Object Name -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "[ERRO] Nenhum backup encontrado" -ForegroundColor Red
        Write-Host "   Procurado: .venv_backup_*" -ForegroundColor Gray
        exit 1
    }
    
    Write-Host "[INFO] Backups disponiveis:" -ForegroundColor Cyan
    Write-Host ""
    
    # Listar backups com indice
    $index = 1
    $backupList = @()
    
    foreach ($backup in $backups) {
        $backupInfoFile = Join-Path $backup.FullName ".backup_info.txt"
        $sizeMB = 0
        $createdAt = "N/A"
        
        if (Test-Path $backupInfoFile) {
            $info = Get-Content $backupInfoFile | ConvertFrom-StringData
            $sizeMB = $info.SizeMB
            $createdAt = $info.CreatedAt
        } else {
            # Calcular tamanho se nao tiver info
            $size = (Get-ChildItem $backup.FullName -Recurse -Force | Measure-Object -Property Length -Sum).Sum
            $sizeMB = [math]::Round($size / 1MB, 2)
        }
        
        $backupList += [PSCustomObject]@{
            Index = $index
            Name = $backup.Name
            Path = $backup.FullName
            SizeMB = $sizeMB
            CreatedAt = $createdAt
        }
        
        Write-Host "   [$index] $($backup.Name)" -ForegroundColor White
        Write-Host "       Tamanho: $sizeMB MB" -ForegroundColor Gray
        Write-Host "       Criado: $createdAt" -ForegroundColor Gray
        Write-Host ""
        
        $index++
    }
    
    # Selecionar backup
    $selectedBackup = $null
    
    if ($backups.Count -eq 1) {
        Write-Host "[OK] Apenas um backup disponivel - sera usado automaticamente" -ForegroundColor Green
        $selectedBackup = $backupList[0]
    } else {
        $selection = Read-Host "Selecione o backup [1-$($backups.Count)]"
        
        if ($selection -match '^\d+$' -and [int]$selection -ge 1 -and [int]$selection -le $backups.Count) {
            $selectedBackup = $backupList[[int]$selection - 1]
        } else {
            Write-Host "[ERRO] Selecao invalida" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host ""
    Write-Host "[INFO] Backup selecionado: $($selectedBackup.Name)" -ForegroundColor Cyan
    Write-Host ""
    
    $venvPath = ".venv"
    
    # Avisar se .venv ja existe
    if (Test-Path $venvPath) {
        Write-Host "[AVISO] Ja existe um .venv no diretorio atual" -ForegroundColor Yellow
        Write-Host "   Ele sera removido e substituido pelo backup" -ForegroundColor Yellow
        Write-Host ""
        
        $confirm = Read-Host "   Deseja continuar? (s/N)"
        if ($confirm -ne 's' -and $confirm -ne 'S') {
            Write-Host "   Restauracao cancelada." -ForegroundColor Gray
            exit 0
        }
    }
    
    Write-Host "[INFO] Restaurando ambiente virtual..." -ForegroundColor Cyan
    Write-Host "   Origem: $($selectedBackup.Name)" -ForegroundColor Gray
    Write-Host "   Destino: $venvPath" -ForegroundColor Gray
    Write-Host ""
    
    $startTime = Get-Date
    
    try {
        # Remover .venv atual se existir
        if (Test-Path $venvPath) {
            Write-Host "   [INFO] Removendo .venv atual..." -ForegroundColor Yellow
            Remove-Item $venvPath -Recurse -Force
        }
        
        # Copiar backup para .venv
        Write-Host "   [INFO] Copiando arquivos..." -ForegroundColor Cyan
        Copy-Item -Path $selectedBackup.Path -Destination $venvPath -Recurse -Force
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        Write-Host ""
        Write-Host "[OK] Ambiente virtual restaurado com sucesso!" -ForegroundColor Green
        Write-Host "   Tempo: $([math]::Round($duration, 2)) segundos" -ForegroundColor Gray
        Write-Host "   Local: $venvPath" -ForegroundColor Gray
        Write-Host ""
        
        # Perguntar se quer remover backup
        Write-Host "[INFO] Deseja remover o backup usado? (s/N): " -NoNewline -ForegroundColor Yellow
        $removeBackup = Read-Host
        
        if ($removeBackup -eq 's' -or $removeBackup -eq 'S') {
            Remove-Item $selectedBackup.Path -Recurse -Force
            Write-Host "   [OK] Backup removido: $($selectedBackup.Name)" -ForegroundColor Green
        } else {
            Write-Host "   [INFO] Backup mantido: $($selectedBackup.Name)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "[OK] Pronto! O ambiente virtual esta restaurado." -ForegroundColor Green
        Write-Host "   Voce pode ativar com: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host ""
        
    } catch {
        Write-Host "[ERRO] Erro ao restaurar backup: $_" -ForegroundColor Red
        exit 1
    }
}
