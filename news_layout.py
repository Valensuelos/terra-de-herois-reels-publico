"""Layout editorial premium do Terra de Heróis para Reels 9:16."""
import urllib.error
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from photo_quality import prepare_photo

WIDTH, HEIGHT = 1080, 1920

def gradient(w,h,a,b):
    strip=Image.new('RGB',(1,h))
    pix=strip.load()
    for y in range(h):
        t=y/max(1,h-1)
        t=t*t*(3-2*t)
        pix[0,y]=tuple(round(x+(z-x)*t) for x,z in zip(a,b))
    return strip.resize((w,h))

def bold_font(size, italic=False):
    filename='DejaVuSansCondensed-BoldOblique.ttf' if italic else 'DejaVuSansCondensed-Bold.ttf'
    for candidate in ('/usr/share/fonts/truetype/dejavu/'+filename,
                      filename, 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(candidate, int(size))
        except OSError:
            pass
    return ImageFont.load_default(size=int(size))

def draw_logo(bg,logo):
    logo=logo.convert('RGBA')
    bounds=logo.getchannel('A').getbbox()
    if bounds:
        logo=logo.crop(bounds)
    logo.thumbnail((760,365),Image.Resampling.LANCZOS)
    bg.alpha_composite(logo,((WIDTH-logo.width)//2,31+(341-logo.height)//2))

def lettered(bg,point,text,ft,color,shadow=(4,7),outline=2):
    d=ImageDraw.Draw(bg)
    x,y=point
    d.text((x+shadow[0],y+shadow[1]),text,font=ft,fill='#01102b',
           stroke_width=outline+2,stroke_fill='#01102b')
    d.text((x,y),text,font=ft,fill=color,
           stroke_width=outline,stroke_fill='#0e214d')

def make_news_frame(meta,path,photo,logo,image_from_url,safe_text,
                    font,wrapped_lines,write_lines):
    if not isinstance(meta,dict):
        raise ValueError('Metadados inválidos')
    title=safe_text(meta.get('title'),250)
    summary=safe_text(meta.get('summary'),800)
    if not title or not summary:
        raise ValueError('Título e resumo são obrigatórios')
    if photo is None:
        photo=image_from_url(meta['image_url'])
    if logo is None and meta.get('logo_url'):
        try:
            logo=image_from_url(meta['logo_url'])
        except (ValueError,OSError,urllib.error.URLError):
            print('Logo não pôde ser carregada; será usado o nome do portal')
    bg=gradient(WIDTH,HEIGHT,(3,19,60),(8,54,112)).convert('RGBA')
    d=ImageDraw.Draw(bg)
    d.polygon([(0,0),(260,0),(0,220)],fill='#005eaf')
    d.polygon([(0,0),(153,0),(0,130)],fill='#08d6f2')
    d.polygon([(WIDTH,285),(WIDTH,390),(735,391)],fill='#0061bf')
    d.polygon([(WIDTH,333),(WIDTH,389),(870,388)],fill='#04cce9')
    halo=Image.new('RGBA',(WIDTH,430),(0,0,0,0))
    ImageDraw.Draw(halo).ellipse((230,-80,850,450),fill=(0,98,240,55))
    bg.alpha_composite(halo.filter(ImageFilter.GaussianBlur(100)),(0,0))
    if logo is not None:
        draw_logo(bg,logo)
    else:
        lettered(bg,(205,135),'TERRA DE HERÓIS',bold_font(70),'#ffde20')
    photo=prepare_photo(photo, (WIDTH,810))
    bg.alpha_composite(photo,(0,403))
    d=ImageDraw.Draw(bg)
    d.polygon([(0,399),(0,445),(160,420),(510,439),(820,433),
               (WIDTH,397),(WIDTH,384),(0,384)],fill='#082764')
    d.line([(0,420),(260,428),(540,438),(850,429),(WIDTH,410)],
           fill='#00dafa',width=7,joint='curve')
    lower=Image.new('RGBA',(WIDTH,240),(0,0,0,0))
    px=lower.load()
    for yy in range(240):
        opacity=int(230*(yy/239)**1.65)
        for xx in range(WIDTH):
            px[xx,yy]=(1,12,42,opacity)
    bg.alpha_composite(lower,(0,973))
    d=ImageDraw.Draw(bg)
    d.polygon([(20,1077),(513,1077),(487,1159),(5,1159)],fill='#061435')
    d.polygon([(25,1072),(509,1072),(483,1148),(3,1148)],fill='#ffd91e')
    d.text((44,1090),'ÚLTIMAS NOTÍCIAS',font=bold_font(47,True),
           fill='#041b47',stroke_width=1)
    for xx in (522,564,606):
        d.polygon([(xx,1088),(xx+24,1088),(xx-4,1140),(xx-28,1140)],
                  fill='#04e6f5')
    d.rectangle((0,1151,WIDTH,1497),fill='#061438')
    d.rectangle((0,1151,WIDTH,1158),fill='#00a7f5')
    d.rectangle((24,1194,37,1445),fill='#00e6f4')
    for cy in range(1190,1450,24):
        for cx in range(914,1062,24):
            if (cx-910)+(cy-1190)<300:
                d.ellipse((cx,cy,cx+4,cy+4),fill='#075a9b')
    lines=[]
    ff=bold_font(42,True)
    lh=49
    for size in range(110,41,-2):
        tf=bold_font(size,True)
        rows=wrapped_lines(d,title,tf,958,4)
        line_height=round(size*1.15)
        if len(rows)*line_height<=280:
            ff,lines,lh=tf,rows,line_height
            break
    if not lines:
        lines=wrapped_lines(d,title,ff,958,4)
    yy=1193+max(0,(258-lh*len(lines))//2)
    for idx,line in enumerate(lines):
        rect=d.textbbox((0,0),line,font=ff)
        xx=max(74,(WIDTH-(rect[2]-rect[0]))//2)
        color='#ffe125' if idx==len(lines)-1 and len(lines)>1 else '#ffffff'
        lettered(bg,(xx,yy+idx*lh),line,ff,color,shadow=(4,6),outline=2)
    d.rectangle((0,1497,WIDTH,1731),fill='#09306b')
    d.line((0,1497,WIDTH,1497),fill='#07b9f5',width=4)
    d.rounded_rectangle((63,1574,177,1658),radius=10,outline='white',width=6)
    d.rectangle((79,1589,104,1616),outline='white',width=3)
    for i in range(3):
        y=1591+i*13
        d.line((116,y,159,y),fill='white',width=3)
    for i in range(2):
        y=1630+i*11
        d.line((79,y,157,y),fill='white',width=3)
    d.rectangle((217,1540,226,1689),fill='#00dfee')
    sf=font(35)
    for idx,line in enumerate(wrapped_lines(d,summary,sf,802,4)):
        d.text((256,1537+idx*47),line,font=sf,fill='white')
    d.line((0,1731,WIDTH,1731),fill='#0087e9',width=9)
    d.polygon([(0,1750),(0,HEIGHT),(185,HEIGHT)],fill='#044595')
    d.polygon([(770,HEIGHT),(WIDTH,1810),(WIDTH,HEIGHT)],fill='#0688b9')
    d.rounded_rectangle((24,1786,1054,1876),radius=42,
                        fill='#052158',outline='#00e7f0',width=6)
    d.rounded_rectangle((30,1792,587,1870),radius=36,fill='#ffdf22')
    d.ellipse((60,1813,105,1853),outline='#081d43',width=4)
    d.line((83,1813,83,1853),fill='#081d43',width=3)
    d.arc((72,1814,94,1853),90,270,fill='#081d43',width=2)
    d.line((64,1833,101,1833),fill='#081d43',width=2)
    d.text((119,1806),'terradeherois.com.br',
           font=bold_font(38,True),fill='#041b45')
    d.ellipse((606,1828,617,1839),fill='#ffdc24')
    d.text((633,1813),'LEIA A MATÉRIA COMPLETA',
           font=bold_font(29,True),fill='white')
    bg.convert('RGB').save(path,optimize=True)
