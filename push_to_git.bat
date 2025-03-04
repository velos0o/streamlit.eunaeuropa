@echo off
echo Iniciando o processo de push para o Git...
git add .
git commit -m "Atualizacao automatica - nova versao"
git push origin main
echo Processo concluido!
pause 