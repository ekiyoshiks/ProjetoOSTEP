@echo off
rem Frente RAM: roda 0,25,50,75,90,100,110 % x 3 repeticoes. Salve seu trabalho antes!
rem Precisa estar na pasta com ocupador.exe e vitima.exe
if not exist saida mkdir saida
del resumo.csv 2>nul
for %%P in (0 25 50 75 90 100 110) do (
  for %%R in (1 2 3) do call :rodar %%P %%R
)
echo.
echo Fim. Resultados em resumo.csv e na pasta saida.
goto :eof

:rodar
del pronto.flag 2>nul
if not "%1"=="0" start "" /b ocupador.exe %1
if not "%1"=="0" call :espera
vitima.exe 156 30 saida\ram_%1_%2.csv %1
taskkill /im ocupador.exe /f >nul 2>&1
timeout /t 10 >nul
goto :eof

:espera
if exist pronto.flag goto :eof
timeout /t 2 >nul
goto espera
