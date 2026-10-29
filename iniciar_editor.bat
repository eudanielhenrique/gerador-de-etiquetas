@echo off
title Editor de Etiquetas Termicas - Salgados & Cia
cd /d "E:\dev\mPhone"
echo ====================================================
echo   Iniciando Editor de Etiquetas Termicas (80mm)
echo ====================================================
echo.
echo Abrindo o navegador em: http://127.0.0.1:5000
start "" http://127.0.0.1:5000
python app.py
pause
