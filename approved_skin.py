"""Renderização baseada na moldura gráfica oficial aprovada.

A moldura é um arquivo WebP transparente entregue pelo plugin do WordPress.
Contém o cabeçalho com a LOGO ORIGINAL, a faixa 'Últimas Notícias', o
fundo de tipografia e o rodapé, mas não contém foto ou texto jornalístico.
Somente imagens/URLs do portal são aceitas pelo render.py.
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps
from photo_quality import prepare_photo

W, H = 1080, 1920
PHOTO_TOP, PHOTO_BOTTOM = 410, 1147

def font(size, oblique=True):
    name = 'DejaVuSansCondensed-BoldOblique.ttf' if oblique else 'DejaVuSansCondensed-Bold.ttf'
    for candidate in ('/usr/share/fonts/truetype/dejavu/' + name,
                      name, 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)

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

def _summary_lines(draw, text, ft, max_width):
    """Quebra palavras e tokens excepcionalmente longos sem sair do painel."""
    def fits(value):
        x0, _, x1, _ = draw.textbbox((0, 0), value, font=ft, stroke_width=1)
        return x1-x0 <= max_width
    rows, line = [], ''
    for word in str(text).split():
        candidate = (line + ' ' + word).strip()
        if fits(candidate):
            line = candidate
            continue
        if line:
            rows.append(line)
        while word and not fits(word):
            end = len(word)-1
            while end > 1 and not fits(word[:end]):
                end -= 1
            rows.append(word[:end])
            word = word[end:]
        line = word
    if line:
        rows.append(line)
    return rows


def _draw_summary(draw, summary):
    """Usa toda a altura do painel, com até quatro linhas e respiro."""
    left, top, right, bottom = 262, 1509, 1054, 1719
    gap = 7

    def boxes_for(rows, ft):
        return [draw.textbbox((0, 0), row, font=ft, stroke_width=1)
                for row in rows]

    def height(boxes):
        return sum(y1-y0 for _, y0, _, y1 in boxes) + gap*max(0, len(boxes)-1)

    for size in range(56, 39, -1):
        ft = font(size, False)
        rows = _summary_lines(draw, summary, ft, right-left)
        boxes = boxes_for(rows, ft)
        if len(rows) <= 4 and height(boxes) <= bottom-top:
            break
    else:
        # Prioriza leitura: mantém quatro linhas e sinaliza texto excedente.
        rows = rows[:4]
        while rows:
            tail = rows[-1]
            while tail:
                x0, _, x1, _ = draw.textbbox((0, 0), tail+'…',
                                             font=ft, stroke_width=1)
                if x1-x0 <= right-left:
                    break
                tail = tail[:-1]
            rows[-1] = tail.rstrip()+'…'
            boxes = boxes_for(rows, ft)
            if height(boxes) <= bottom-top:
                break
            rows.pop()

    y = top + (bottom-top-height(boxes))//2
    for row, (x0, y0, x1, y1) in zip(rows, boxes):
        draw.text((left-x0, y-y0), row, font=ft, fill='#ffffff',
                  stroke_fill='#061636', stroke_width=1)
        y += y1-y0+gap
    return rows


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
    photo = prepare_photo(photo, (W, PHOTO_BOTTOM-PHOTO_TOP))
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

    # Sem endereço duplicado: o rodapé oficial já contém a URL do portal.
    _draw_summary(dr, summary)
    # O CTA original da moldura permanece intacto, sem contorno duplicado.
    base.convert('RGB').save(path,optimize=True)
    return True
