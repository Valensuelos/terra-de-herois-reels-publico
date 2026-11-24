"""Renderização baseada na moldura gráfica oficial aprovada.

A moldura é um arquivo WebP transparente entregue pelo plugin do WordPress.
Contém o cabeçalho com a LOGO ORIGINAL, a faixa 'Últimas Notícias', o
fundo de tipografia e o rodapé, mas não contém foto ou texto jornalístico.
Somente imagens/URLs do portal são aceitas pelo render.py.
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1920
PHOTO_TOP, PHOTO_BOTTOM = 410, 1147

def font(size, oblique=True):
    name = 'DejaVuSansCondensed-BoldOblique.ttf' if oblique else 'DejaVuSansCondensed-Bold.ttf'
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/' + name, size)
    except OSError:
        return ImageFont.truetype('DejaVuSans-Bold.ttf', size)

def _wrap(draw, text, ft, maxw, maxlines):
    """Quebra linhas sem cortar palavra e sinaliza truncamento."""
    words = str(text).split()
    lines = []
    line = ''
    for word in words:
        part = (line + ' ' + word).strip()
        if draw.textbbox((0, 0), part, font=ft)[2] <= maxw or not line:
            line = part
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        tail = lines[-1]
        while tail and draw.textbbox((0,0), tail + '…', font=ft)[2] > maxw:
            tail = tail[:-1]
        lines[-1] = tail.rstrip() + '…'
    return lines

def make_official_frame(meta, path, photo, image_from_url, safe_text):
    """Retorna False se o manifesto não fornece a moldura oficial."""
    template_url = meta.get('template_url', '') if isinstance(meta, dict) else ''
    if not template_url:
        return False
    skin = image_from_url(template_url).convert('RGBA')
    if skin.size != (W, H):
        raise ValueError('Moldura oficial do WordPress precisa ter 1080 x 1920 pixels.')
    if skin.getpixel((540, 675))[3] > 25:
        raise ValueError('A moldura oficial contém uma foto onde deveria ser transparente.')
    if photo is None:
        photo = image_from_url(meta['image_url'])
    photo = ImageOps.fit(photo.convert('RGBA'), (W, PHOTO_BOTTOM-PHOTO_TOP),
                         method=Image.Resampling.LANCZOS, centering=(0.5,0.45))
    base = Image.new('RGBA', (W,H), '#061638')
    base.alpha_composite(photo, (0,PHOTO_TOP))
    base.alpha_composite(skin)
    dr = ImageDraw.Draw(base)
    dr.text((52,1083), 'ÚLTIMAS NOTÍCIAS',font=font(49),fill='#07163a',
            stroke_fill='#0d1d3e',stroke_width=1)

    title = safe_text(meta.get('title'), 280)
    summary = safe_text(meta.get('summary'), 850)
    if not title or not summary:
        raise ValueError('Título e resumo são obrigatórios na moldura oficial.')
    # Manchete: maximizar tamanho sem perder a leitura nem ultrapassar o painel.
    # A arte oficial disponibiliza o espaço vertical 1155-1495.
    title_font = font(50)
    title_rows = []
    title_step = 58
    for size in range(124, 47, -2):
        candidate_font = font(size)
        candidate_rows = _wrap(dr, title, candidate_font, 902, 4)
        step = round(size * 1.07)
        if len(candidate_rows) * step <= 302:
            title_font, title_rows, title_step = candidate_font, candidate_rows, step
            break
    if not title_rows:
        title_rows = _wrap(dr, title, title_font, 902, 4)
    title_top = 1166 + max(0, (310-title_step * len(title_rows))//2)
    for i, line in enumerate(title_rows):
        bounds = dr.textbbox((0, 0), line, font=title_font)
        x = max(85, (W-(bounds[2]-bounds[0]))//2)
        y = title_top + i*title_step
        color = '#ffe21c' if i == len(title_rows)-1 and len(title_rows)>1 else '#ffffff'
        dr.text((x+5, y+8), line, font=title_font, fill='#00091b',
                stroke_width=6, stroke_fill='#00091b')
        dr.text((x, y), line, font=title_font, fill=color,
                stroke_width=2, stroke_fill='#133263')

    # Resumo: melhor leitura em tela pequena, até três linhas com respiro.
    # Prefere preservar o texto inteiro quando cabe; caso contrário usa reticências.
    summary_font = font(45, False)
    for size in range(56, 47, -2):
        candidate_font = font(size, False)
        if len(_wrap(dr, summary, candidate_font, 792, 99)) <= 3:
            summary_font = candidate_font
            break
    summary_rows = _wrap(dr, summary, summary_font, 798, 3)
    # Painel de 1497 a 1731: texto legível e assinatura acima dos controles.
    summary_y = 1507
    line_spacing = 52
    for i, line in enumerate(summary_rows):
        dr.text((262, summary_y + i*line_spacing), line, font=summary_font,
                fill='#ffffff', stroke_fill='#061636', stroke_width=1)

    # Endereço maior e afastado do resumo, sem disputar espaço com o CTA.
    dr.rounded_rectangle((262, 1677, 815, 1724), radius=13,
                         fill='#052451', outline='#0fcce8', width=2)
    dr.text((278, 1682), 'terradeherois.com.br',
            font=font(46, True), fill='#ffe329',
            stroke_fill='#071533', stroke_width=1)
    # O CTA original da moldura permanece intacto, sem contorno duplicado.
    base.convert('RGB').save(path,optimize=True)
    return True
