# Tarmatambo en imágenes — versão pública

Este repositório publica, pelo GitHub Pages, a versão pública da página
"Tarmatambo en imágenes": https://gbianchi-pixel.github.io/tarmatambo/

A fonte é a página completa, um artefato privado do Claude:
https://claude.ai/code/artifact/53a85a48-a0fc-4461-b462-04105c0503a3

Não edite `index.html`, `img/` ou `th/` à mão. Eles são gerados a partir da
página completa por `_ferramentas/gerar_publica.py`.

## Depois de qualquer alteração na página completa

1. Ler o artefato completo com Artifact `read` (salva o HTML localmente).
2. Listar os arquivos dele (`scope: "files"`) e baixar com `read` + `paths`
   para uma pasta de mídia as imagens novas ou alteradas em `img/` e `th/`
   (na dúvida, todas as que não são de acervos restritos).
3. Rodar, na raiz do repositório:
   `python3 _ferramentas/gerar_publica.py --html <html salvo> --midia <pasta>`
   O script para com erro se a estrutura da página mudou ou se faltar imagem.
4. Conferir `git status`, fazer commit em `main` com mensagem em português
   descrevendo a mudança, e `git push`. O site atualiza em cerca de um minuto.

## Acervos restritos

`_ferramentas/restritos.json` lista os acervos que aparecem só com ficha e link
para a fonte (sem imagem), e a nota que vai no rodapé. Quando chegar uma
autorização, retirar o acervo da lista, ajustar a nota e regenerar.
