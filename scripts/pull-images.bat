@echo off
rem ============================================================
rem SecureVault Pro - Descarga imagenes desde Docker Hub
rem
rem Uso: doble clic o ejecutar desde terminal
rem ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pull-images.ps1"
pause
