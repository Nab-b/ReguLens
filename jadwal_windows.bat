@echo off
REM Menjadwalkan sinkronisasi Regulens setiap hari pukul 07.00 (Windows Task Scheduler)
schtasks /create /tn "Regulens Sinkron" /tr "python \"%~dp0src\sinkron.py\"" /sc daily /st 07:00 /f
pause
