# Backup Script for Final Freelance Project
# This script creates a complete backup of your project

$projectPath = "C:\Users\dell\Desktop\Final freelance project"
$backupPath = "C:\Users\dell\Desktop\Final_freelance_project_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"

Write-Host "Creating backup of your project..." -ForegroundColor Green
Write-Host "Project path: $projectPath" -ForegroundColor Yellow
Write-Host "Backup will be saved to: $backupPath" -ForegroundColor Yellow

# Create the backup
try {
    Compress-Archive -Path "$projectPath\*" -DestinationPath $backupPath -Force
    Write-Host "✅ Backup created successfully!" -ForegroundColor Green
    Write-Host "Backup file: $backupPath" -ForegroundColor Cyan
    
    # Get file size
    $fileSize = (Get-Item $backupPath).Length / 1MB
    Write-Host "Backup size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error creating backup: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy the backup file to an external drive or cloud storage" -ForegroundColor White
Write-Host "2. Also ensure your Git repository is pushed to remote" -ForegroundColor White
Write-Host "3. Keep this backup file safe until your laptop is repaired" -ForegroundColor White

# Also create a Git backup
Write-Host "`n🔄 Creating Git backup..." -ForegroundColor Green
try {
    Set-Location $projectPath
    git add .
    git commit -m "Backup before laptop repair - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git push origin main
    Write-Host "✅ Git backup completed!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Git backup failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "You can manually run: git add . && git commit -m 'backup' && git push" -ForegroundColor White
}

