#!/usr/bin/env python3
"""Gera a versão pública de "Tarmatambo en imágenes" a partir da página completa.

Uso:
  python3 _ferramentas/gerar_publica.py --html COMPLETA.html --midia PASTA [--repo .]

--html   o HTML da página completa (artefato privado), como salvo pelo Artifact read
--midia  pasta com img/ e th/ baixadas do artefato completo (basta conter as
         imagens novas ou alteradas; as que já estão no repositório são mantidas)
--repo   raiz do repositório (padrão: pasta acima deste script)

Regra: os acervos listados em restritos.json aparecem só com ficha e link para a
fonte. Tudo o mais é publicado. O script reescreve index.html, copia as imagens
necessárias e apaga do repositório as que deixaram de ser usadas.
"""
import argparse, json, re, shutil, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def transformar(s, restritos, nota, titulo='', h1='', subtitulo='', miniaturas=(), link_qb='', miniaturas_ids=None):
    m = re.search(r'const D = (\{.*?\});\n', s, re.S)
    if not m:
        sys.exit('Não encontrei "const D = {...};" no HTML.')
    D = json.loads(m.group(1))
    for f in D['fotos']:
        f.pop('res', None)
        if f['camp'] in restritos and f['forma'] != 'ausente':
            f['res'] = True
            if f['forma'] in miniaturas:
                f['mini'] = True
        if link_qb and (f.get('orig') or '').startswith('quai Branly '):
            f['link'] = link_qb + f['orig'].split()[-1]
        if f.get('mini'):
            f['fonte'] = 'Ver el negativo en el archivo del quai Branly'
            f['credito'] = 'Miniatura, © musée du quai Branly – Jacques Chirac'
        if f['id'] in (miniaturas_ids or {}):
            f.update(miniaturas_ids[f['id']], res=True, mini=True)
    s = s[:m.start(1)] + json.dumps(D, ensure_ascii=False) + s[m.end(1):]

    def rep(a, b):
        nonlocal s
        if s.count(a) != 1:
            sys.exit(f'O trecho esperado não aparece exatamente uma vez; a página mudou de estrutura:\n  {a[:90]}')
        s = s.replace(a, b)

    rep("const card = f => {\n",
        "const card = f => {\n  if (f.mini) return `<div class=\"card aus mini\"><a href=\"${esc(f.link)}\" target=\"_blank\" rel=\"noopener\"><img src=\"th/mini_${f.id}.jpg\" alt=\"Miniatura de ${esc(f.titulo)}\" loading=\"lazy\"></a><span class=\"cap\"><b>${esc(f.titulo)}</b><span class=\"small\">${esc(f.data)} ${f.orig ? ' · ' + esc(f.orig) : ''} · ${esc(f.credito)}</span><span class=\"small\">${esc(f.desc)}</span></span><a class=\"fonte\" href=\"${esc(f.link)}\" target=\"_blank\" rel=\"noopener\">${esc(f.fonte)}</a></div>`;\n  if (f.res) return `<div class=\"card aus\"><span class=\"frame\"><span>Derechos reservados</span></span><span class=\"cap\"><b>${esc(f.titulo)}</b><span class=\"small\">${esc(f.data)}${f.orig ? ' · ' + esc(f.orig.split(';')[0]) : ''}</span><span class=\"small\">${esc(f.desc)}${f.link ? ` <a href=\"${esc(f.link)}\" target=\"_blank\" rel=\"noopener\">Ver en la fuente</a>` : ''}</span></span></div>`;\n")
    rep("lista.push(...it.filter(f => f.forma !== 'ausente'));",
        "lista.push(...it.filter(f => f.forma !== 'ausente' && !f.res));")
    rep("const tiras = it.every(f => f.forma === 'tira');",
        "const tiras = it.every(f => f.forma === 'tira' && (!f.res || f.mini));")
    rep("</style>\n\n<header>", ".mini img { width: 100%; max-width: 900px; height: auto; display: block; background: var(--frame) }\n.mini .fonte { justify-self: start; background: var(--anil); color: #fff; font-weight: 600; font-size: .88rem; padding: 8px 13px; text-decoration: none }\n.mini .fonte:hover { text-decoration: underline }\n</style>\n\n<header>")
    rep("lista.push(...ctx);",
        "lista.push(...ctx.filter(f => f.forma !== 'ausente' && !f.res));")
    if nota:
        rep("</div></footer>", " " + nota + "</div></footer>")
    if titulo:
        rep("<title>Tarmatambo en imágenes</title>", f"<title>{titulo}</title>")
    if h1:
        rep("<h1>Tarmatambo<br>en imágenes</h1>", f"<h1>{h1}</h1>")
    if subtitulo:
        sitio = [f for f in D['fotos'] if f['forma'] in ('foto', 'tira') and f['grupo'] == 'sitio' and f['camp'] != 'bianchi']
        texto = subtitulo.format(n_visiveis=sum(not f.get('res') for f in sitio),
                                 n_fotos_res=sum(bool(f.get('res')) and not f.get('mini') and f['forma'] == 'foto' for f in sitio),
                                 n_tiras_mini=sum(bool(f.get('mini')) and f['forma'] == 'tira' for f in sitio))
        s, n = re.subn(r"\$\('lead'\)\.textContent = `.*?`;", lambda _: f"$('lead').textContent = {json.dumps(texto, ensure_ascii=False)};", s, flags=re.S)
        if n != 1:
            sys.exit('Não encontrei a linha do subtítulo; a página mudou de estrutura.')
    usados = ['img/hero.jpg'] + [f'{d}/{f["id"]}.jpg' for f in D['fotos']
                                 if f['forma'] != 'ausente' and not f.get('res') for d in ('img', 'th')]
    usados += [f'th/mini_{f["id"]}.jpg' for f in D['fotos'] if f.get('mini')]
    return s, usados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--midia', required=True)
    ap.add_argument('--repo', default=str(AQUI.parent))
    a = ap.parse_args()
    cfg = json.loads((AQUI / 'restritos.json').read_text())
    repo, midia = Path(a.repo), Path(a.midia)

    s, usados = transformar(Path(a.html).read_text(), set(cfg['acervos']), cfg.get('nota_rodape', ''),
                           cfg.get('titulo', ''), cfg.get('h1', ''), cfg.get('subtitulo', ''),
                           set(cfg.get('miniaturas', [])), cfg.get('link_quai_branly', ''), cfg.get('miniaturas_ids', {}))

    faltam, copiados = [], 0
    for p in usados:
        src, dst = midia / p, repo / p
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst); copiados += 1
        elif not dst.exists():
            faltam.append(p)
    if faltam:
        sys.exit('Imagens necessárias que não estão nem na pasta de mídia nem no repositório:\n  ' + '\n  '.join(faltam))

    apagados = 0
    for d in ('img', 'th'):
        for f in (repo / d).glob('*'):
            if f'{d}/{f.name}' not in usados:
                f.unlink(); apagados += 1

    (repo / 'index.html').write_text(s)
    print(f'index.html gerado; {len(usados)} imagens publicadas; {copiados} copiadas/atualizadas; {apagados} removidas.')


if __name__ == '__main__':
    main()
