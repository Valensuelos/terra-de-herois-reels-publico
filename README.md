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


## Atualização visual e música — Novembro de 2026

O renderizador agora usa um novo layout editorial vertical:
- Logo transparente na parte superior sem quadrado de fundo;
- Imagem destacada ocupando o painel fotográfico central;
- Faixa amarela "ÚLTIMAS NOTÍCIAS";
- Manchete em branco/amarelo com ajuste de fonte;
- Resumo curto e CTA "LEIA A MATÉRIA COMPLETA" no rodapé.

### Como usar a nova logo enviada pelo usuário
No **WordPress > AutoNews Reels > 2. Identidade visual e vídeo**,
clique em **Selecionar logo da Biblioteca**, envie a PNG oficial transparente
(TERRA em dourado e DE HERÓIS em azul), selecione-a e salve.
A imagem é acessada pelo GitHub através do campo \`logo_url\`.
**O repositório público não armazena essa marca nem fotos de matérias.**
Se a logo continuar quadrada, a mídia antiga ainda está selecionada.

### Trilha Breaking News original
\`soundtrack.py\` gera uma composição instrumental sintetizada: abertura
de três notas marcantes, pulso rítmico discreto, e fade-out.
Não reutiliza músicas, trechos ou amostras comerciais.

A música fica **ativada por padrão**, sem precisar mudar nada no WordPress.
Para desligar, crie em GitHub > Settings > Secrets and variables > Actions >
**Variables** a variável \`ANR_MUSIC_ENABLED\` com o valor \`false\`.
Para religar, altere para \`true\` ou remova a variável.

Não ative a publicação automática no Instagram sem antes conferir no WordPress
o vídeo da primeira execução, o volume da música e a leitura da manchete.
As imagens das notícias devem ter autorização de uso. O vídeo usa foto fixa
(com sobreposição gráfica) e uma trilha sem narração. A prévia ilustrativa
não é uma filmagem de uma repórter real.

Teste local:
\`\`\`bash
python3 -m unittest discover -s tests -v
\`\`\`


## Versão visual oficial 1.2.3 — layout fixo e logo branca/azul

O AutoNews Reels para WordPress v1.2.3 inclui duas mídias no próprio plugin:
`assets/terra-logo-oficial.webp` e `assets/moldura-reels-oficial.webp`.
A API do WordPress envia `template_url` e `logo_url` no manifesto do Reels.

O compositor `approved_skin.py` prioriza essa **moldura gráfica oficial**, em vez
do layout de fallback gerado somente com formas. Como a moldura tem a imagem
central e os textos jornalísticos transparentes/vazios, o renderizador insere
a fotografia da notícia, a manchete e o resumo dinamicamente. A logo é a
imagem oficial branca/azul sem quadrado, preservada no topo.

O modelo de fallback ainda existe para uma instalação WordPress antiga sem
`template_url`. A substituição do plugin WordPress pela versão 1.2.3 é
necessária para a moldura oficial; somente atualizar o GitHub não altera
a logo antiga previamente configurada.

**Teste:** manter publicação automática desativada; gerar um novo Reels após
instalar o plugin 1.2.3; conferir o MP4 no painel antes de publicar.
Jobs anteriores com status PRONTO não mudam retroativamente.


## Ajustes de definição e cor (24/11/2026)

O renderizador aplica melhorias **somente na mídia da matéria**, preservando a
logo, a moldura e as cores originais do Terra de Heróis:

- Fotografias: `photo_quality.py` aplica contraste 1,08, cor 1,11, luminosidade
  1,035 e máscara de nitidez moderada após o enquadramento 1080px.
  Imagens pequenas recebem nitidez mais leve para evitar realçar artefatos.
- Vídeos: `video_media.py` usa filtros FFmpeg `eq` e `unsharp` somente na
  faixa da filmagem, mantendo a narração original quando existente.
- Codificação: MP4s de fotografia passaram a H.264 CRF 20/preset fast,
  e MP4s com vídeo original a H.264 CRF 21/preset fast. Áudio AAC e o limite de
  45 MB de upload ao WordPress permanecem.
- Testes: `python3 -m unittest discover -s tests -v`; além deles, convém gerar
  um Reels real para conferir a qualidade e tamanho de arquivo.
- Fotos originalmente desfocadas/comprimidas não recuperam detalhes perdidos.
  Evite realce exagerado em fotografias já muito saturadas.

As alterações são aplicadas a novas renderizações. Vídeos existentes não são
modificados retroativamente. Mantenha a publicação automática desligada
até aprovar o resultado.


## Correção de timeout do GitHub Actions (24/11/2026)

As execuções **#9682** e **#9675** ficaram paradas na instalação de
`ffmpeg`/`python3-pil` via `apt-get` e foram canceladas pelo limite de
15 minutos, antes da renderização. A execução **#9681** concluiu em
aproximadamente 36 segundos; o erro era intermitente na preparação.

O workflow agora usa `actions/checkout@v6`, `actions/setup-python@v6`
e instala por wheels pré-compilados `Pillow==12.0.0` e
`imageio-ffmpeg==0.6.0`. Não executa `apt-get update` e limita
a etapa de instalação a quatro minutos. O renderizador verifica
`libx264` e `unsharp` antes de renderizar. Em vídeo MP4, se não
houver `ffprobe`, os metadados são extraídos da saída do FFmpeg.

**Testar:** no WordPress, faça uma nova tentativa de processamento de
um único Reels com publicação no Instagram desativada. Confira
que as etapas Preparar dependências, Verificar dependências e Gerar MP4
terminaram verdes. Uma nova tentativa de um job antigo pelo botão
"Re-run jobs" pode usar o commit antigo, por isso prefira acionar
`Processar agora` pelo WordPress após este ajuste.

Os arquivos MP4 antigos não são alterados, e não é necessário
reinstalar o plugin WordPress para corrigir essa etapa do GitHub.
