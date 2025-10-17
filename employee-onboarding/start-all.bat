@echo off
echo Starting Employee Onboarding System...

cd /d %~dp0
go work sync

start "IT Setup" powershell -NoExit -Command "cd it-setup-service; go run ./cmd/server/main.go"
timeout /t 2 /nobreak >nul
start "Email Provisioner" powershell -NoExit -Command "cd email-provisioner-service; go run ./cmd/server/main.go"
timeout /t 2 /nobreak >nul
start "Access Rights" powershell -NoExit -Command "cd access-rights-service; go run ./cmd/server/main.go"
timeout /t 2 /nobreak >nul
start "HR Orchestrator" powershell -NoExit -Command "cd hr-service; go run ./cmd/server/main.go"

echo All services started! Close windows to stop.
pause
