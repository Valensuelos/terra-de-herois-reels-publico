"""Layout editorial 9:16 Terra de Heróis com logo oficial transparente."""
import urllib.error
from PIL import Image, ImageDraw, ImageOps

WIDTH, HEIGHT = 1080, 1920

def _fit_logo(logo, width=900, height=310):
    if logo is None:
        return None
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    bbox = logo.getchannel('A').getbbox()
    if bbox:
        logo = logo.crop(bbox)
    logo.thumbnail((width, height), Image.Resampling.LANCZOS)
    return logo

def make_news_frame(meta, path, photo, logo, image_from_url, safe_text,
                    font, wrapped_lines, write_lines):
    """Preserva proporções, ajusta manchete e evita o quadro quadrado da logo."""
    if not isinstance(meta, dict):
        raise ValueError('Metadados de Reels inválidos.')
    title = safe_text(meta.get('title'), 250)
    summary = safe_text(meta.get('summary'), 800)
    if not title or not summary:
        raise ValueError('Título ou resumo ausente.')
    if photo is None:
        photo = image_from_url(meta['image_url'])
    if logo is None and meta.get('logo_url'):
        try:
            logo = image_from_url(meta['logo_url'])
        except (ValueError, OSError, urllib.error.URLError):
            print('Logo indisponível; será usado o nome do portal.')
    bg = Image.new('RGBA', (WIDTH, HEIGHT), '#051639')
    dr = ImageDraw.Draw(bg)
    for y in range(0, HEIGHT, 3):
        v = y / HEIGHT
        dr.rectangle((0, y, WIDTH, y + 2),
                     fill=(4, int(22 + 24*v), int(61 + 61*v), 255))
    dr.polygon([(0, 0), (260, 0), (0, 215)], fill='#0455bd')
    dr.polygon([(0, 0), (135, 0), (0, 107)], fill='#00d8f5')
    dr.polygon([(WIDTH, 315), (WIDTH, 365), (760, 365)], fill='#0660b7')
    logo = _fit_logo(logo)
    if logo is not None:
        bg.alpha_composite(logo, ((WIDTH-logo.width)//2, 22+(302-logo.height)//2))
    else:
        write_lines(dr, 'TERRA DE HERÓIS', 114, font(80, True), 2, '#ffdb23', 930)
    dr = ImageDraw.Draw(bg)
    dr.rectangle((0, 363, WIDTH, 371), fill='#00dbf3')
    pic = ImageOps.fit(photo.convert('RGBA'), (WIDTH, 765),
                       method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    bg.alpha_composite(pic, (0, 371))
    dr = ImageDraw.Draw(bg)
    dr.polygon([(35, 1050), (536, 1050), (510, 1119), (8, 1119)],
               fill='#ffdc17')
    dr.text((53, 1065), 'ÚLTIMAS NOTÍCIAS',
            font=font(45, True), fill='#061b45')
    for x in (544, 580, 616):
        dr.polygon([(x, 1063), (x+24, 1063), (x+3, 1107), (x-21, 1107)],
                   fill='#00e4f5')
    dr.rectangle((0, 1136, WIDTH, 1145), fill='#00dcef')
    dr.rectangle((0, 1146, WIDTH, 1484), fill='#06183f')
    dr.rectangle((0, 1146, 17, 1484), fill='#05dffc')
    headline_font = None
    lines = []
    for size in range(62, 39, -2):
        ff = font(size, True)
        ll = wrapped_lines(dr, title, ff, 965, 4)
        if len(ll)*int(size*1.20) <= 315:
            headline_font, lines = ff, ll
            break
    if headline_font is None:
        headline_font = font(40, True)
        lines = wrapped_lines(dr, title, headline_font, 965, 4)
    h = int(headline_font.size * 1.18)
    ty = 1165 + max(0, (307 - h*len(lines))//2)
    for i, line in enumerate(lines):
        bb = dr.textbbox((0, 0), line, font=headline_font)
        xx = max(38, (WIDTH-(bb[2]-bb[0]))//2)
        col = '#ffdb24' if i == len(lines)-1 and len(lines) > 1 else 'white'
        dr.text((xx, ty+i*h), line, font=headline_font, fill=col,
                stroke_fill='#081025', stroke_width=2)
    dr.rectangle((0, 1484, WIDTH, 1733), fill='#09306c')
    dr.rectangle((48, 1525, 57, 1693), fill='#00e0f5')
    sf = font(33)
    for i, line in enumerate(wrapped_lines(dr, summary, sf, 903, 4)):
        dr.text((81, 1513+48*i), line, fill='white', font=sf)
    dr.rectangle((0, 1735, WIDTH, 1745), fill='#00d9f6')
    dr.rounded_rectangle((22, 1785, 1058, 1875), radius=37,
                         fill='#054fa2', outline='#00e0ef', width=5)
    dr.rounded_rectangle((27, 1790, 566, 1870), radius=32, fill='#ffda19')
    dr.text((48, 1803), 'terradeherois.com.br',
            font=font(38, True), fill='#05193e')
    dr.text((594, 1811), 'LEIA A MATÉRIA COMPLETA',
            font=font(28, True), fill='white')
    dr.line((0, 1898, WIDTH, 1898), fill='#0076dc', width=10)
    bg.convert('RGB').save(path, optimize=True)
