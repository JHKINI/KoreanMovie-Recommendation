@echo off
chcp 65001 >nul
rem run.bat 으로 켠 서버(백엔드 8000, 프론트 5173)를 종료합니다.
rem 이 두 포트를 사용 중인 프로세스만 종료합니다.
powershell -NoProfile -Command "foreach ($port in 8000,5173) { $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }; Write-Host ('포트 ' + $port + ' 종료') } else { Write-Host ('포트 ' + $port + ' 은(는) 실행 중이 아닙니다') } }"
rem 남아 있는 최소화 창(cmd)을 닫습니다.
taskkill /fi "WINDOWTITLE eq 영화 백엔드*" >nul 2>&1
taskkill /fi "WINDOWTITLE eq 영화 프론트*" >nul 2>&1
exit /b 0
