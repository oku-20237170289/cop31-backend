@echo off
chcp 65001 > nul
title COP31 Veritabanı Yedekleyici

echo ========================================================
echo        COP31 PostgreSQL Veritabanı Yedekleme
echo ========================================================
echo.

set BACKUP_FILE=backup_cop31_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql
set BACKUP_FILE=%BACKUP_FILE: =0%

echo Yedek alınıyor: %BACKUP_FILE% ...

docker exec cop31_db_v2 pg_dump -U cop31_admin cop31_db > "%~dp0%BACKUP_FILE%"
copy /Y "%~dp0%BACKUP_FILE%" "%~dp0latest_backup.sql" > nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [BAŞARILI] Veritabanı yedeği alındı!
    echo Dosya: %BACKUP_FILE%
    echo Ayrıca 'latest_backup.sql' olarak güncellendi.
) else (
    echo.
    echo [HATA] Yedek alınırken sorun oluştu. Docker'ın çalıştığından emin olun.
)

echo.
pause
