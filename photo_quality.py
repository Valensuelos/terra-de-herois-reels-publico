"""Aprimoramento moderado da fotografia, somente na área da notícia.

Ajusta contraste, luminosidade, cor e nitidez após o enquadramento.
Mantém a logo e a moldura do Terra de Heróis intactas.
"""
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def prepare_photo(photo, size, centering=(0.5, 0.45)):
    """Enquadra e realça com intensidade controlada, sem inventar detalhes."""
    source = photo.convert("RGB")
    fitted = ImageOps.fit(
        source, size, method=Image.Resampling.LANCZOS, centering=centering
    )
    fitted = ImageEnhance.Contrast(fitted).enhance(1.08)
    fitted = ImageEnhance.Color(fitted).enhance(1.11)
    fitted = ImageEnhance.Brightness(fitted).enhance(1.035)

    # Se a foto é pequena, evite amplificar demais os blocos de compressão.
    original_min = min(source.size)
    sharpen_percent = 100 if original_min < 600 else 125
    fitted = fitted.filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=sharpen_percent, threshold=3)
    )
    return fitted.convert("RGBA")
