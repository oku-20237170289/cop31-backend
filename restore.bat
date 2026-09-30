@echo off
chcp 65001 > nul
title COP31 Veritabanı Geri Yükleyici

echo ========================================================
echo        COP31 PostgreSQL Veritabanı Geri Yükleme
echo ========================================================
echo.

if not exist "%~dp0latest_backup.sql" (
    echo [HATA] 'latest_backup.sql' dosyası bulunamadı!
    echo Lütfen önce backup.bat çalıştırarak yedek alınız.
    pause
    exit /b 1
)

echo DİKKAT: Bu işlem 'latest_backup.sql' dosyasındaki verileri 'cop31_db_v2' veritabanına geri yükleyecektir.
echo.
set /p CONFIRM=Devam etmek istiyor musunuz? (E/H): 

if /I "%CONFIRM%" NEQ "E" (
    echo İşlem iptal edildi.
    pause
    exit /b 0
)

echo Geri yükleniyor...
docker exec -i cop31_db_v2 psql -U cop31_admin -d cop31_db < "%~dp0latest_backup.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [BAŞARILI] Veritabanı başarıyla geri yüklendi!
) else (
    echo.
    echo [HATA] Geri yükleme sırasında hata oluştu.
)

echo.
pause
