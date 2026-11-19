"""Compara los renders de tests/out con el original (claude_cola_corta), con el prototipo numpy (proto.py) y con la
teoría. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import proto
D = pathlib.Path(__file__).parent / "out"; S = pathlib.Path(__file__).parent / "signals"; SR = 48000
def a(db): return 10 ** (db / 20)
def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def load(name):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR; return x
def sig(name): return sf.read(S / name)[0]
def have(name): return (D / f"{name}.wav").exists()
SRC = {}
for line in (D / "log.txt").read_text().splitlines():
    p = line.split()
    if p[:1] == ["caso"]: SRC[p[1]] = p[2]

fails = 0
def scalar(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:46s} {got:+9.3f}   (esperado {want:+.3f} ± {tol})")
def inrange(name, got, lo, hi):
    global fails
    ok = lo <= got <= hi
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:46s} {got:+9.3f}   (entre {lo:+.3f} y {hi:+.3f})")
def gain_ms(out, inp, ms=1.0):
    """ganancia (dB) por ventana de ms: mediana de salida/entrada muestra a muestra donde la entrada no es ~0"""
    n = int(SR * ms / 1000); m = min(len(out), len(inp)) // n
    o = out[:m * n].reshape(m, n); i = inp[:m * n].reshape(m, n)
    pk = np.abs(inp).max(); ok = np.abs(i) > pk * 1e-3
    r = np.where(ok, np.abs(o) / np.maximum(np.abs(i), 1e-30), np.nan)
    with np.errstate(all="ignore"):
        return db(np.nanmedian(np.where(ok.any(1)[:, None], r, 1.0), 1))

# NaN / explosiones en todo
for p in sorted(D.glob("*.wav")):
    if p.stem.startswith("perf_"): continue
    x = load(p.stem)
    if not np.all(np.isfinite(x)) or np.abs(x).max() > 4:
        fails += 1; print("MAL", p.stem, "tiene NaN o pasa de +12 dBFS")

print("== igual al claude_cola_corta original (diferencia máxima, dB; -300 = idéntico bit a bit)")
for o, n in (("orig_def_hits", "p3_hits"), ("orig_def_snare", "p3_snare"), ("orig_def_808", "p3_808"),
             ("orig_nb_snare", "p1_snare"), ("orig_nb_clap", "p2_clap"), ("orig_nb_kick", "p1_kick")):
    if have(o) and have(n):
        x, y = load(o), load(n)
        print(f"    {o} vs {n}: {np.sum(x != y)} muestras distintas de {x.size}")
        inrange(f"{n} = {o}", db(np.abs(x - y).max()), -400, -140)

print("== contra el prototipo numpy (diferencia máxima, dB)")
PK = {1: "ataque", 2: "cola", 3: "modo", 4: "sens", 5: "dur", 6: "hold", 7: "caida", 8: "la", 9: "banda", 10: "corte",
      11: "escuchar", 12: "mezcla", 13: "ganancia"}
PR = {"pr_g_at": {1: 6, 8: 2}, "pr_g_mix": {1: -6, 2: -10, 12: 50, 13: 3}, "pr_c": {3: 1, 1: 6, 2: -10, 7: 200},
      "pr_band_lo": {9: 1, 10: 200, 2: -20}, "pr_band_hi": {9: 2, 10: 200, 2: -20},
      "pr_listen1": {9: 1, 10: 200, 2: -20, 11: 1}, "pr_listen2": {2: -12, 11: 2},
      "pr_kick_c": {3: 1, 1: 5, 2: -6, 7: 300, 8: 1.5}, "pr_808_g": {1: 4, 2: -10, 5: 25, 6: 150, 7: 200, 8: 1}}
for name, prm in PR.items():
    if not have(name): continue
    x = sig(SRC[name]); y, _ = proto.run(x, SR, **{PK[k]: v for k, v in prm.items()})
    la = int(np.floor(prm.get(8, 0) * 0.001 * SR + 0.5)); r = load(name)
    if la: y = y[la:]; r = r[:len(r) - la]      # REAPER compensa la latencia del lookahead; el prototipo no
    inrange(f"{name} = prototipo", db(np.abs(r - y).max()), -400, -100)

print("== teoría")
h = sig("hits.wav"); ons = [int((0.25 + 0.5 * k) * SR) for k in range(6)]
if have("neutral"):
    inrange("neutro (Golpe, 0/0) = intacto", db(np.abs(load("neutral") - h).max()), -400, -140)
    inrange("neutro (Continuo, 0/0) = intacto", db(np.abs(load("neutral_c") - h).max()), -400, -140)
if have("lvl_g0"):
    for m in ("g", "c"):
        g0 = gain_ms(load(f"lvl_{m}0")[:, 0], h[:, 0]); g1 = gain_ms(load(f"lvl_{m}30")[:, 0], sig("hits_m30.wav")[:, 0])
        k = np.isfinite(g0) & np.isfinite(g1)
        inrange(f"nivel 0 vs -30 dB ({'Golpe' if m == 'g' else 'Continuo'}): dif. máx. dB", np.abs(g0 - g1)[k].max(), 0, 0.01)
if have("la_off"):
    for nm in ("la_off", "la_3"):
        x = load(nm)[:, 0]; on = np.argmax(np.abs(x) > 1e-4)
        print(f"    {nm}: arranca en la muestra {on} (debe ser {ons[0]})")
        if abs(on - ons[0]) > 1: fails += 1; print("MAL", nm, "desalineado: la latencia no se compensó")
    g = gain_ms(load("la_3")[:, 0], h[:, 0], 0.25)   # ventanas de 0.25 ms
    i0 = ons[1] // 12
    scalar("lookahead 3: el primer 1/4 ms ya sube +6", g[i0], 6, 0.05)
    g2 = gain_ms(load("la_off")[:, 0], h[:, 0], 0.25)
    inrange("sin lookahead: el primer 1/4 ms sube menos", g2[i0], 0, 4)
    g = gain_ms(load("la_3")[:, 0], h[:, 0])
    scalar("ataque +6 a los 5 ms", np.mean([g[o // 48 + 5] for o in ons]), 6, 0.05)
    scalar("ataque: a duración + 1 tau (13.3 ms) = 6/e", np.mean([np.mean(g[o // 48 + 13:o // 48 + 14]) for o in ons]), 6 / np.e, 0.35)
    inrange("ataque: a los 40 ms ya no sube", np.mean([g[o // 48 + 40] for o in ons]), -0.05, 0.05)
if have("tail_g"):
    g = gain_ms(load("tail_g")[:, 0], h[:, 0])
    # teoría: objetivo 1 durante Mantener, luego cae a -12 (a -60 dB del exceso en Caída), con el suavizado de 1 ms
    flo, kg = a(-12), np.exp(-1 / (0.001 * SR)); gs = flo; tg = []
    for n in range(int(0.3 * SR)):
        tgt = 1 if n < 40 * 48 else flo + (1 - flo) * np.exp(-6.9 * (n - 40 * 48) / (60 * 48))
        gs = tgt if tgt > gs else kg * gs + (1 - kg) * tgt; tg.append(gs)
    for t in (20, 45, 50, 60, 70, 100, 200):
        scalar(f"cola -12 (mantener 40, caída 60): a {t} ms", np.mean([g[o // 48 + t] for o in ons[1:]]), db(tg[t * 48 + 24]), 0.1)
if have("s45_c"):
    for nm, lab in (("s45_c", "Continuo"), ("s45_g", "Golpe")):
        g = gain_ms(load(nm)[:, 0], sig("sine45.wav")[:, 0], 5)
        st = g[100:380]
        inrange(f"45 Hz fijo ({lab}): la ganancia no tiembla (dB p-p)", st.max() - st.min(), 0, 0.1)
    st = gain_ms(load("s45_g")[:, 0], sig("sine45.wav")[:, 0], 5)[100:380]
    scalar("45 Hz fijo (Golpe): queda en la cola (-6)", np.median(st), -6, 0.05)
def lvl(x, t0, t1): x = x[int(t0 * SR):int(t1 * SR)]; return db(np.sqrt(np.mean(x ** 2)) * np.sqrt(2))
def tone(x, f, t0=0.5, t1=2.9):
    x = x[int(t0 * SR):int(t1 * SR)]; n = len(x); w = np.hanning(n)
    X = np.abs(np.fft.rfft(x * w)); k = int(round(f * n / SR)); return db(X[k - 2:k + 3].max() * 2 / w.sum())
if have("band_flat"):
    scalar("cruce LR4 (sin efecto): 1 kHz en el corte, plano", lvl(load("band_flat")[:, 0], 0.5, 1.9), -12, 0.02)
if have("pr_band_lo"):
    scalar("solo graves, cola -20: 4 kHz intacto", tone(load("pr_band_lo")[:, 0], 4000), -20, 0.1)
    scalar("solo agudos, cola -20 (4 kHz sin golpes): baja 20", tone(load("pr_band_hi")[:, 0], 4000), -40, 0.2)
    b = sig("bands.wav")[:, 0]
    lo_in = tone(b, 60, 0.25, 2.9); lo_o = tone(load("pr_band_hi")[:, 0], 60, 0.25, 2.9)
    scalar("solo agudos: los golpes de 60 Hz intactos", lo_o - lo_in, 0, 0.1)
if have("mix50"):
    g = gain_ms(load("mix50")[:, 0], h[:, 0])
    scalar("mezcla 50 %, cola -12: en la cola", np.mean([g[o // 48 + 300] for o in ons[:-1]]), db(0.5 + 0.5 * a(-12)), 0.05)
    scalar("ganancia +6", lvl(load("gain6")[:, 0], 0.5, 1.9), -6, 0.02)

# muestras reales: independencia del nivel
print("== samples reales: 0 dB vs -30 dB (dif. de ganancia por ms, dB)")
for s in ("kick", "snare", "b808", "clap"):
    for m, lab in (("g", "Golpe"), ("c", "Continuo")):
        n0, n1 = f"lvl_{s}_{m}0", f"lvl_{s}_{m}30"
        if not (have(n0) and have(n1)): continue
        x0 = sig(f"lib_{s}.wav")[:, 0]; x1 = sig(f"lib_{s}_m30.wav")[:, 0]
        g0 = gain_ms(load(n0)[:, 0], x0); g1 = gain_ms(load(n1)[:, 0], x1)
        k = np.isfinite(g0) & np.isfinite(g1); d = np.abs(g0 - g1)[k]
        print(f"    {s:5s} {lab:8s}: mediana {np.median(d):.4f}  p99 {np.percentile(d, 99):.3f}  máx {d.max():.3f}  "
              f"(ms con diferencia > 0.1 dB: {np.sum(d > 0.1)} de {d.size})")
        if m == "c": inrange(f"{s} Continuo: igual a -30 dB (máx)", d.max(), 0, 0.01)
        # Golpe conserva el piso absoluto de -80 dBFS del original: a -30 dB algún re-golpe muy bajo deja de contar
        else: inrange(f"{s} Golpe: % de ms distintos (> 0.1 dB) a -30 dB", 100 * np.mean(d > 0.1), 0, 5)

# presets: efecto medido por golpe (ventanas desde cada golpe)
print("== presets sobre samples reales (dB de salida / entrada por ventana, promedio de los golpes)")
STEP = {"b808": 1.2, "d808": 1.2, "hat": 0.25}
LOOP = [0.1, 0.5, 0.7, 0.9, 1.3]
WIN = {"drum": ((0, 6), (12, 40), (150, 250)), "808": ((0, 6), (12, 40), (600, 1100)), "hat": ((0, 4), (6, 15), (60, 150)),
       "loop": ((0, 6), (12, 40), (120, 190))}
PRE = {1: (0, -4), 2: (0, -8), 3: (0, -12), 4: (5, 0), 5: (0, -12), 6: (8, 0), 7: (4, 0), 8: (6, 0), 9: (0, 4), 10: (-5, 0),
       11: (5, 0), 12: (0, -10), 13: (4, 0), 14: (0, -14), 15: (0, 5), 16: (6, 0), 17: (0, -12), 18: (5, -2), 19: (-4, 0),
       20: (0, -10), 21: (2, -8), 22: (4, -8), 23: (-6, 0), 24: (0, 0)}
BANDP = {6: (2, 2500), 7: (1, 150), 8: (2, 1500)}     # presets por banda: se miden dentro de su banda
def band_of(x, b, f):
    s = [proto.SVF(f, SR) for _ in range(3)]; y = np.empty(len(x))
    for n, v in enumerate(x):
        l1, h1 = s[0](v); y[n] = s[1](l1)[0] if b == 1 else s[2](h1)[1]
    return y
def wgain(o, i, onsets, w):
    """ventanas desde el comienzo real de cada golpe (la entrada pasa el 10 % de su pico; algunos samples traen
    un pre-ruido de varios ms antes del golpe)"""
    r = []
    for t in onsets:
        s0 = int(t * SR); seg = np.abs(i[s0:s0 + int(0.05 * SR)]); s0 += int(np.argmax(seg > 0.1 * seg.max()))
        i0, i1 = s0 + int(w[0] * 48), s0 + int(w[1] * 48)
        ri = np.sqrt(np.mean(i[i0:i1] ** 2)); ro = np.sqrt(np.mean(o[i0:i1] ** 2))
        if ri > 1e-5: r.append(db(ro / ri))
    return np.mean(r) if r else np.nan
for p in range(1, 25):
    nm = f"preset{p}"
    if not have(nm): continue
    src = SRC[nm]; x = sig(src)[:, 0]; y = load(nm)[:, 0]
    key = src[4:-4] if src.startswith("lib_") else "hits"
    if key == "loop": onsets, kind = LOOP, "loop"
    elif key == "hits": onsets, kind = [0.25 + 0.5 * k for k in range(6)], "drum"
    else:
        st = STEP.get(key, 0.75); n = 2 if "808" in key else 8 if key == "hat" else 3
        onsets, kind = [0.1 + st * k for k in range(n)], "808" if "808" in key else "hat" if key == "hat" else "drum"
    if p in BANDP:
        # banda procesada = banda de referencia + (salida - salida sin efecto); el cruce es el del prototipo (= render)
        b, f = BANDP[p]; x2 = sig(src)
        ref = proto.run(x2, SR, banda=b, corte=f)[0][:, 0]; x = proto.run(x2, SR, banda=b, corte=f, escuchar=1)[0][:, 0]
        y = x + (y - ref)
    wins = list(WIN[kind])
    if p == 21: wins[2] = (60, 85)      # el snare de reggaetón dura 90 ms
    ga, gb, gt = (wgain(y, x, onsets, w) for w in wins)
    at, co = PRE[p]
    print(f"    preset {p:2d} ({src:16s}{' en su banda' if p in BANDP else ''}) ataque {ga:+6.2f}  cuerpo {gb:+6.2f}  cola {gt:+6.2f}")
    # que actúe en la dirección correcta con al menos 1/4 de lo nominal (en Continuo depende del material)
    if at > 0: inrange(f"preset {p}: el ataque sube", ga, at * 0.25, at + 0.5)
    if at < 0: inrange(f"preset {p}: el ataque baja", ga, at - 0.5, at * 0.25)
    if co < 0: inrange(f"preset {p}: la cola baja", gt, co - 0.5, co * 0.25)
    if co > 0: inrange(f"preset {p}: la cola sube", gt, co * 0.25, co + 0.5)
    if at == 0 and co == 0: inrange(f"preset {p}: no cambia nada", max(abs(ga), abs(gb), abs(gt)), 0, 0.01)
for nm in ("leg_d808_p14", "leg_b808_p14"):
    if have(nm):
        x = sig(SRC[nm])[:, 0]; y = load(nm)[:, 0]
        print(f"    (límite) {nm}: 808 ligado con el preset 14, nota 1 {wgain(y, x, [0.1], (0, 40)):+.1f} dB, "
              f"nota 2 {wgain(y, x, [1.3], (0, 40)):+.1f} dB (la 2a no salta: no se detecta como golpe)")
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
