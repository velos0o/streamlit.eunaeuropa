# Instruções para Enviar Alterações para o GitHub

Siga os passos abaixo para enviar suas alterações para o repositório do GitHub:

## 1. Abrir o Terminal (PowerShell ou Prompt de Comando)

- Pressione `Win + R`, digite `cmd` ou `powershell` e pressione Enter
- Navegue até a pasta do seu projeto:
  ```
  cd C:\Users\Assessoria\Documents\Projeto\streamlit.eunaeuropa-main
  ```

## 2. Adicionar Alterações ao Git

Execute o seguinte comando para adicionar todas as alterações:
```
git add .
```

## 3. Criar um Commit

Execute o seguinte comando para criar um commit com suas alterações:
```
git commit -m "Atualização do dashboard com novas funcionalidades e integração com API Bitrix24"
```

## 4. Enviar Alterações para o GitHub

Execute o seguinte comando para enviar as alterações para o GitHub:
```
git push origin master:main
```

Este comando enviará as alterações da branch local `master` para a branch `main` no GitHub.

## 5. Verificar Alterações no GitHub

Após enviar as alterações, você pode verificar se elas foram aplicadas acessando:
https://github.com/velos0o/streamlit.eunaeuropa

## Nota Sobre Credenciais

Se o Git solicitar suas credenciais do GitHub, use:
- Usuário: velos0o
- Token: [TOKEN DE ACESSO PESSOAL - NÃO COMPARTILHAR]

## Solução de Problemas

### Se o push for rejeitado devido a divergências

Se você receber uma mensagem informando que o push foi rejeitado porque a branch remota contém trabalhos que você não possui localmente, execute:

```
git pull origin main --rebase
```

E depois tente o push novamente:

```
git push origin master:main
```

### Se ocorrerem conflitos durante o rebase

Se ocorrerem conflitos durante o rebase, siga estas etapas:

1. Resolva os conflitos em cada arquivo (os arquivos com conflitos serão listados)
2. Após resolver os conflitos, execute:
   ```
   git add .
   git rebase --continue
   ```
3. Quando o rebase estiver concluído, faça o push:
   ```
   git push origin master:main
   ``` 