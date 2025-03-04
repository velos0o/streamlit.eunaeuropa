@echo off
echo Adicionando alteracoes ao Git...
git add .

echo Criando commit...
git commit -m "Atualizacao do dashboard com novas funcionalidades e integracao com API Bitrix24"

echo Enviando alteracoes para o GitHub...
git push origin master:main

echo Processo concluido!
pause 