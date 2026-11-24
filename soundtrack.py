"""Trilha eletrônica original criada por síntese, sem amostras de terceiros.

Abertura curta de Breaking News e instrumental suave no restante do Reels.
Não utiliza áudio comercial nem serviços pagos de geração musical.
"""
import array
import math
import wave

SAMPLE_RATE = 22050
TWO_PI = 2.0 * math.pi

def make_music(seconds, filename='breaking-news.wav'):
    """Gera WAV PCM mono 16 bits usado no MP4 pelo FFmpeg."""
    seconds = max(20, min(45, int(seconds)))
    bpm = 114
    beat = 60.0 / bpm
    half = beat / 2.0
    notes = (
        (57, 60, 64, 69),  # Am
        (53, 57, 60, 65),  # F
        (48, 52, 55, 60),  # C
        (55, 59, 62, 67),  # G
    )
    freq = {n: 440.0 * 2.0 ** ((n-69)/12.0) for chord in notes for n in chord}
    freq.update({n+12: 440.0*2.0**((n+12-69)/12.0)
                 for chord in notes for n in chord})
    pcm = array.array('h')
    for ix in range(SAMPLE_RATE*seconds):
        t = ix/SAMPLE_RATE
        beat_num = int(t/beat)
        phase_beat = t - beat_num*beat
        chord = notes[(beat_num//4) % len(notes)]
        pad = 0.0
        for n in chord[:3]:
            f = freq[n]
            pad += (math.sin(TWO_PI*f*t) +
                    0.19*math.sin(TWO_PI*(2*f)*t))
        pad *= 0.0105*(0.9 + 0.1*math.sin(TWO_PI*0.35*t))
        low = 0.023*math.sin(TWO_PI*(freq[chord[0]]/2)*t)
        step_index = int(t/half)
        offset = t - step_index*half
        pitch = chord[(0, 2, 1, 3, 1, 2, 0, 3)[step_index % 8]] + 12
        f = freq[pitch]
        attack = min(1.0, offset/0.028)
        pluck = (0.036*attack*math.exp(-7.5*offset) *
                 (math.sin(TWO_PI*f*offset) +
                  0.18*math.sin(TWO_PI*f*2*offset)))
        kick = 0.0
        if beat_num % 2 == 0 and phase_beat < 0.22:
            u = phase_beat
            kick = 0.062*math.exp(-24.0*u)*math.sin(TWO_PI*(67-30*u)*u)
        hat = 0.0
        if offset < 0.063:
            h = (((ix*1103515245+12345)>>9) & 0xffff)/32768.0 - 1.0
            hat = h*0.012*math.exp(-53*offset)
        intro = 0.0
        for start, note, power in ((0.0, 76, 0.095),
                                   (0.31, 79, 0.074),
                                   (0.65, 83, 0.061)):
            delta = t-start
            if 0 <= delta < 0.72:
                f0 = 440.0*2.0**((note-69)/12.0)
                intro += (power*(1-math.exp(-39*delta))*math.exp(-4.1*delta) *
                          (math.sin(TWO_PI*f0*delta) +
                           0.28*math.sin(TWO_PI*f0*1.998*delta)))
        fade_in = min(1.0, t/0.08)
        fade_out = min(1.0, max(0.0, (seconds-t)/1.25))
        amplitude = 2.2*(pad+low+pluck+kick+hat+intro)*fade_in*fade_out
        pcm.append(max(-32767, min(32767, int(amplitude*32767))))
    with wave.open(filename, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        out.writeframes(pcm.tobytes())
    return filename
