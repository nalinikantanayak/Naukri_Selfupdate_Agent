@echo off

cd /d D:\DevOps_lab\Naukri-Daily-Profile-Agent

echo ============================================================ >> logs\scheduler.log
echo Scheduler run started: %date% %time% >> logs\scheduler.log
echo ============================================================ >> logs\scheduler.log

D:\DevOps_lab\Naukri-Daily-Profile-Agent\venv\Scripts\python.exe agent.py >> logs\scheduler.log 2>&1

echo Python exit code: %ERRORLEVEL% >> logs\scheduler.log
echo Scheduler run ended: %date% %time% >> logs\scheduler.log

exit /b %ERRORLEVEL%