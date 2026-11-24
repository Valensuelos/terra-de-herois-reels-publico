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
    # Prioridade: título grande em até quatro linhas, como arte aprovada.
    ft = font(82)
    lines = []
    height = 88
    for size in range(108, 43, -2):
        candidate_font=font(size)
        candidate = _wrap(dr,title,candidate_font,953,4)
        line_height = round(size*1.11)
        if len(candidate)*line_height <= 285:
            ft, lines, height = candidate_font, candidate, line_height
            break
    if not lines:
        lines = _wrap(dr,title,ft,953,4)
    top = 1193 + max(0, (280-height*len(lines))//2)
    for i,line in enumerate(lines):
        box=dr.textbbox((0,0),line,font=ft)
        x=max(68,(W-(box[2]-box[0]))//2)
        color='#ffe11a' if i==len(lines)-1 and len(lines)>1 else '#ffffff'
        dr.text((x+4, top+i*height+7),line,font=ft,fill='#000b25',
                stroke_width=5,stroke_fill='#000b25')
        dr.text((x,top+i*height),line,font=ft,fill=color,
                stroke_width=2,stroke_fill='#16335f')

    sf=font(40,False)
    rows = _wrap(dr,summary,sf,790,4)
    if len(rows)>4:
        rows=rows[:4]
    for i, line in enumerate(rows):
        dr.text((268,1520+i*47), line, font=sf,fill='#ffffff',
                stroke_fill='#071833',stroke_width=1)
    base.convert('RGB').save(path,optimize=True)
    return True
