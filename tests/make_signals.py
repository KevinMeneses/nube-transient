"""Señales de prueba (48 kHz, float32). Las de la librería urbana solo se crean si está en esta máquina."""
import numpy as np, soundfile as sf, pathlib
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
LIB = pathlib.Path.home() / "Music/ClaudeBeats/libreria_urbana"
def a(db): return 10 ** (db / 20)
def save(name, *ch): sf.write(D / name, np.stack(ch, 1).astype(np.float32), SR, subtype="FLOAT")

t2 = np.arange(SR * 2) / SR; t3 = np.arange(SR * 3) / SR
x = a(-12) * np.sin(2 * np.pi * 1000 * t2); save("sine1k.wav", x, x)
x = a(-6) * np.sin(2 * np.pi * 45 * t2); save("sine45.wav", x, x)

# golpes: 6 golpes cada 0.5 s desde 0.25 s; 200 Hz que empieza en el pico y cae con tau 80 ms
def hits(level, f=200, tau=0.08, phase=np.pi / 2):
    d = np.zeros(SR * 3)
    for k in range(6):
        i = int((0.25 + 0.5 * k) * SR); m = len(d) - i; tt = np.arange(m) / SR
        d[i:] += a(level) * np.sin(2 * np.pi * f * tt + phase) * np.exp(-tt / tau)
    return d
x = hits(-6); save("hits.wav", x, x)
x = hits(-36); save("hits_m30.wav", x, x)
# bandas: golpes de 60 Hz (empiezan en cero: sin clic) + 4 kHz fijo a -20 dBFS
x = hits(-6, 60, 0.3, 0.0) + a(-20) * np.sin(2 * np.pi * 4000 * t3); save("bands.wav", x, x)

# librería: el mismo sample repetido 3 veces cada 0.75 s (808: 2 notas de 1.2 s), y a -30 dB
LIBS = {"kick": ("Trap/01 Kicks/trap_kick_02_Gs1.wav", 0.75, 3), "snare": ("Trap/02 Snares/trap_snare_01.wav", 0.75, 3),
        "clap": ("Trap/03 Claps/trap_clap_01.wav", 0.75, 3), "b808": ("Trap/07 808 y Bajos/trap_bajo_01_Fs1.wav", 1.2, 2),
        "dkick": ("Drill/01 Kicks/drill_kick_01_E1.wav", 0.75, 3), "dsnare": ("Drill/02 Snares/drill_snare_02.wav", 0.75, 3),
        "d808": ("Drill/07 808 y Bajos/drill_bajo_02_A1.wav", 1.2, 2), "rsnare": ("Reggaeton/02 Snares/reggaeton_snare_01.wav", 0.75, 3),
        "hat": ("Trap/04 Hats/trap_hat_01.wav", 0.25, 8)}
if LIB.exists():
    for name, (rel, step, n) in LIBS.items():
        s, sr = sf.read(LIB / rel); assert sr == SR
        if s.ndim == 2: s = s[:, 0]
        if "808" in name:   # 808 ligado (la nota anterior sigue hasta la siguiente): sin transitorio que detectar
            sl = s[:int(step * SR)]; out = np.zeros(int((0.1 + step * n + 0.2) * SR))
            for k in range(n): i = int((0.1 + step * k) * SR); out[i:i + len(sl)] += sl
            save(f"lib_{name}_ligado.wav", out, out)
        # como un sampler con choke: cada golpe se corta con un fade de 15 ms al 90 % del paso
        m = min(len(s), int(0.9 * step * SR)); s = s[:m].copy(); f = int(0.015 * SR)
        s[-f:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(f) / f)
        out = np.zeros(int((0.1 + step * n + 0.2) * SR))
        for k in range(n):
            i = int((0.1 + step * k) * SR); out[i:i + len(s)] += s
        save(f"lib_{name}.wav", out, out)
        save(f"lib_{name}_m30.wav", out * a(-30), out * a(-30))
    # loop de batería (kick, snare y clap juntos, 150 bpm) para los presets de Continuo
    seq = [("kick", 0.0), ("snare", 0.4), ("kick", 0.6), ("kick", 0.8), ("snare", 1.2), ("clap", 1.2)]
    out = np.zeros(int(2.0 * SR))
    for name, t0 in seq:
        s = sf.read(LIB / LIBS[name][0])[0]; s = s if s.ndim == 1 else s[:, 0]
        i = int((0.1 + t0) * SR); m = min(len(s), len(out) - i); out[i:i + m] += 0.7 * s[:m]
    save("lib_loop.wav", out, out)
print("ok", sorted(p.name for p in D.iterdir()))
