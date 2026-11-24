# Terra de Heróis — Renderizador público de Reels (GitHub Actions)

Este repositório contém **somente o renderizador**. O WordPress continua hospedado normalmente e gerencia a fila, os vídeos recebidos e a publicação no Instagram.

## Por que público?

Nos repositórios públicos, o runner GitHub-hosted padrão `ubuntu-latest` pode executar gratuitamente, conforme as [regras de cobrança do GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Não é uma garantia de execução ilimitada caso exista outro bloqueio administrativo ou de faturamento na conta.

## Segurança

- `workflow_dispatch` é o **único** gatilho. Não adicionar `pull_request`, `pull_request_target`, `push` ou `workflow_run` a este workflow com acesso a secrets.
- Não enviar tokens, capturas de credenciais, arquivos MP4, dados de visitantes, `wp-config.php` ou backups ao repositório.
- GitHub Secrets: `ANR_SITE_URL` = `https://terradeherois.com.br` (URL canônica; teste se há redirecionamento) e `ANR_SHARED_SECRET` = **o segredo compartilhado que já consta no WordPress** em AutoNews Reels > 2B.
- O token GitHub para despachar o workflow deve ficar **somente no WordPress**, com acesso ao repositório escolhido e permissão **Actions: Read and write**. É preciso criar ou ajustar token específico para este novo repositório.
- Os secrets do repositório anterior não são copiados automaticamente; configure-os novamente neste repositório.
- Não conceda acesso de escrita a terceiros: colaboradores com escrita podem alterar o workflow que utiliza os Secrets.
- A API do WordPress recebe o MP4 via HTTPS e exige o segredo de renderização. As imagens carregadas são limitadas ao domínio do Terra de Heróis.

## Arquivos

- `render.py`: obtém os dados da notícia no WordPress, renderiza MP4 H.264/AAC vertical 9:16, envia o MP4 ao WordPress.
- `.github/workflows/render-reel.yml`: recebe o ID numérico do Reels e executa `render.py`.
- `tests/test_render.py`: testes locais de validação e de geração de quadro estático.

## Instalação

1. Repositório **PÚBLICO** separado, sem converter o repositório privado existente.
2. Em Settings > Secrets and variables > Actions, configure os dois secrets indicados acima.
3. No WordPress, em AutoNews Reels > 2B, use `Valensuelos/terra-de-herois-reels-publico`. Preserve o modo GitHub Actions (externo).
4. Edite o token fine-grained para incluir o **novo** repositório, com permissão Actions: Read and write; salve-o no plugin. Não cole o token no GitHub Actions.
5. Deixe **Publicar automaticamente no Instagram** desativado durante a primeira execução.
6. Execute `Testar conexão GitHub (sem publicar)` no WordPress e confirme HTTP 200 para repositório e workflow.
7. Escolha um Reels `NA_FILA` ou `FALHA_RENDERIZACAO`, clique em `Processar agora` e acompanhe o Actions. O status deverá chegar a `PRONTO` se tudo funcionar.
8. Confira o vídeo no navegador antes de ativar a publicação automática no Instagram.

## Teste sem WordPress

No PC com Python 3, Pillow e FFmpeg instalados:

```shell
python3 -m unittest discover -s tests -v
```

**Limitações:** layout simplificado, sem narração por IA nem logotipos de patrocinadores; para reproduzir exatamente o layout editorial definitivo do portal, é necessário desenvolver o template gráfico específico. Uma falha de execução não é reenviada automaticamente por este repositório; ela aparece no GitHub Actions e o WordPress mantém seu histórico.
