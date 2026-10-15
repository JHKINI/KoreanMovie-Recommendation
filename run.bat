@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
rem 영화 추천 서버(백엔드 8000 + React 5173)를 한 번에 켭니다. 종료는 stop.bat.
rem   run.bat            서버를 켜고 브라우저를 엽니다. (탐색기에서 더블클릭해도 됩니다)
rem   run.bat nobrowser  브라우저는 열지 않습니다.
rem 괄호 블록 안에서는 %errorlevel%이 미리 치환되어 틀리므로, goto와 if errorlevel로 흐름을 만든다.

set "PY=.venv\Scripts\python.exe"
set "URL=http://127.0.0.1:8000/"

if not exist "%PY%" goto :no_venv
if not exist "artifacts\recommendation\CURRENT.json" goto :no_data

rem ---------- 백엔드 ----------
call :is_up http://127.0.0.1:8000/health
if not errorlevel 1 goto :backend_ready
echo 백엔드를 시작합니다...
start "영화 백엔드 (닫으면 종료)" /min "%PY%" -m uvicorn api:app --host 127.0.0.1 --port 8000
call :wait_for http://127.0.0.1:8000/health 40
if errorlevel 1 goto :backend_failed
goto :frontend

:backend_ready
echo 백엔드는 이미 실행 중입니다.

rem ---------- 프론트 ----------
:frontend
where npm >nul 2>&1
if errorlevel 1 goto :no_node
if not exist "frontend\node_modules" goto :no_modules
call :is_up http://127.0.0.1:5173/
if not errorlevel 1 goto :frontend_ready
echo 프론트를 시작합니다...
pushd frontend
start "영화 프론트 (닫으면 종료)" /min cmd /c npm run dev -- --host 127.0.0.1
popd
call :wait_for http://127.0.0.1:5173/ 30
if errorlevel 1 goto :frontend_failed
goto :frontend_up

:frontend_ready
echo 프론트는 이미 실행 중입니다.
:frontend_up
set "URL=http://127.0.0.1:5173/"
goto :done

:no_node
echo Node.js 가 없어 React 화면은 건너뜁니다. 단일 HTML 화면을 엽니다.
goto :done

:no_modules
echo frontend\node_modules 가 없어 React 화면은 건너뜁니다. frontend 폴더에서 npm ci --ignore-scripts 를 먼저 실행하세요.
echo 단일 HTML 화면을 엽니다.
goto :done

:done
echo.
echo 실행 중: %URL%
echo 종료하려면 stop.bat 을 실행하세요.
if /i not "%~1"=="nobrowser" start "" "%URL%"
exit /b 0

:no_venv
echo [오류] .venv 가 없습니다. 먼저 아래를 실행하세요.
echo   py -m venv .venv
echo   .venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if /i not "%~1"=="nobrowser" pause
exit /b 1

:no_data
echo [오류] 추천 데이터가 없습니다. 먼저 아래를 실행하세요.
echo   .venv\Scripts\python.exe run_pipeline.py
if /i not "%~1"=="nobrowser" pause
exit /b 1

:backend_failed
echo [오류] 백엔드가 40초 안에 시작되지 않았습니다. 최소화된 "영화 백엔드" 창의 메시지를 확인하세요.
if /i not "%~1"=="nobrowser" pause
exit /b 1

:frontend_failed
echo [오류] 프론트가 30초 안에 시작되지 않았습니다. 최소화된 "영화 프론트" 창의 메시지를 확인하세요.
if /i not "%~1"=="nobrowser" pause
exit /b 1

rem 주소가 응답하면 0, 아니면 1
:is_up
powershell -NoProfile -Command "try { $null = Invoke-WebRequest '%~1' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%

rem 주소가 응답할 때까지 1초 간격으로 최대 N번 확인. 응답하면 0, 시간 초과면 1
:wait_for
set /a tries=0
:wait_loop
call :is_up %~1
if not errorlevel 1 exit /b 0
set /a tries+=1
if %tries% geq %~2 exit /b 1
rem timeout은 입력이 연결되지 않은 환경에서 오류가 나므로 ping으로 1초 기다린다.
ping -n 2 127.0.0.1 >nul
goto :wait_loop
