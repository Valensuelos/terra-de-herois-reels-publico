"""Trilha instrumental editorial original, gerada por síntese.

Pulso moderado, baixo macio, piano elétrico e percussão discreta.
Sem amostras externas, vozes, sirenes ou dependências adicionais.
"""
import array
import math
import sys
import wave

SAMPLE_RATE = 22050
TWO_PI = 2.0 * math.pi


def make_music(seconds, filename='breaking-news.wav'):
    """Usa trilha do portal quando configurada, ou síntese original de reserva."""
    from licensed_music import prepare_music
    try:
        if prepare_music(seconds, filename):
            print('Trilha editorial do portal selecionada.')
            return filename
    except Exception:
        # Nunca registrar URL, credenciais ou conteúdo de respostas.
        print('Trilha do portal indisponível; usando trilha original de reserva.')
    seconds = max(20, min(45, math.ceil(float(seconds))))
    beat = 60.0 / 100
    eighth = beat / 2
    # Harmonia e motivo próprios: Dadd9, Bm7, Gmaj7, Asus4.
    chords = ((50, 57, 64, 66), (47, 54, 62, 69),
              (43, 55, 59, 66), (45, 57, 62, 64))
    freq = {n: 440.0 * 2.0 ** ((n-69)/12.0) for n in range(36, 96)}
    sin, exp = math.sin, math.exp
    pcm = array.array('h')
    for ix in range(SAMPLE_RATE * seconds):
        t = ix / SAMPLE_RATE
        bn = int(t / beat)
        u = t - bn * beat
        chord = chords[(bn // 4) % len(chords)]
        bar_t = (bn % 4) * beat + u
        chord_env = min(1.0, bar_t / 0.09, (4*beat-bar_t) / 0.10)
        pad = 0.018 * chord_env * sum(
            sin(TWO_PI * freq[n] * t) +
            0.12 * sin(TWO_PI * freq[n] * 2.003 * t)
            for n in chord[1:])
        bass = 0.075 * min(1.0, u / 0.024) * exp(-3.8*u) * (
            sin(TWO_PI * freq[chord[0]] * u) +
            0.18 * sin(TWO_PI * 2 * freq[chord[0]] * u))
        step = int(t / eighth)
        v = t - step * eighth
        # Motivo de piano elétrico com pausas e acentos, sem bipes agudos.
        index = (2, -1, 1, 3, -1, 2, 1, -1)[step % 8]
        keys = 0.0
        if index >= 0:
            f = freq[chord[index]]
            keys = 0.085 * min(1.0, v/0.014) * exp(-7.0*v) * (
                sin(TWO_PI*f*v) + 0.26*sin(TWO_PI*2*f*v) +
                0.08*sin(TWO_PI*3*f*v))
        noise = (((ix*1103515245+12345) >> 9) & 0xffff)/32768.0-1.0
        kick = 0.0
        if bn % 4 in (0, 2) and u < 0.23:
            kick = 0.12 * min(1.0,u/0.005) * exp(-21*u) * sin(
                TWO_PI*(55*u+0.8*(1-exp(-28*u))))
        snare = 0.0
        if bn % 2 == 1 and u < 0.12:
            snare = 0.034 * min(1.0,u/0.005) * exp(-38*u) * noise
        hat = 0.0
        if v < 0.055:
            hat = 0.012 * min(1.0,v/0.004) * exp(-65*v) * noise
        fade = min(1.0, t/0.20, max(0.0,(seconds-t)/1.40))
        sample = 1.65*(pad+bass+keys+kick+snare+hat)*fade
        pcm.append(max(-32767, min(32767, int(sample*32767))))
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(filename, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm.tobytes())
    return filename
