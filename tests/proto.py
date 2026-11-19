"""Prototipo en numpy de Nube Transient (mismo algoritmo que el JSFX, muestra a muestra).
Sirve para probar ideas fuera de REAPER y como referencia de las pruebas (check.py).

    proto.run(x, sr, **params) -> (y, gain_db)     x: (n, 2)
"""
import math
import numpy as np

DEF = dict(ataque=0.0, cola=0.0, modo=0, sens=6.0, dur=15.0, hold=40.0, caida=60.0, la=0.0,
           banda=0, corte=200.0, escuchar=0, mezcla=100.0, ganancia=0.0)


def cola_corta(x, sr, hold=40, dec=60, cola=-12, sens=6):
    """claude_cola_corta.jsfx, literal"""
    ef = es = 0.0; tt = 100000; g = 1.0
    kfa = math.exp(-1 / (0.0005 * sr)); kfr = math.exp(-1 / (0.005 * sr))
    ksa = math.exp(-1 / (0.020 * sr)); ksr = math.exp(-1 / (0.150 * sr))
    kg = math.exp(-1 / (0.001 * sr))
    hold = hold * 0.001 * sr; dec = dec * 0.001 * sr; flo = 10 ** (cola / 20); jump = 10 ** (sens / 20)
    y = x.copy(); gg = np.empty(len(x))
    for i in range(len(x)):
        v = max(abs(x[i, 0]), abs(x[i, 1]))
        ef = kfa * ef + (1 - kfa) * v if v > ef else kfr * ef + (1 - kfr) * v
        es = ksa * es + (1 - ksa) * v if v > es else ksr * es + (1 - ksr) * v
        if ef > es * jump and ef > 0.0001 and tt > hold: tt = 0
        target = 1 if tt < hold else flo + (1 - flo) * math.exp(-6.9 * (tt - hold) / dec)
        g = target if target > g else kg * g + (1 - kg) * target
        y[i] *= g; gg[i] = g; tt += 1
    return y, gg


class SVF:
    """SVF trapezoidal (Simper), una etapa"""
    def __init__(self, f, sr, k=math.sqrt(2)):
        g = math.tan(math.pi * f / sr)
        self.k = k; self.a1 = 1 / (1 + g * (g + k)); self.a2 = g * self.a1; self.a3 = g * self.a2
        self.s0 = self.s1 = 0.0

    def __call__(self, x):
        s0, s1 = self.s0, self.s1
        v3 = x - s1; v1 = self.a1 * s0 + self.a2 * v3; v2 = s1 + self.a2 * s0 + self.a3 * v3
        self.s0 = 2 * v1 - s0; self.s1 = 2 * v2 - s1
        return v2, x - self.k * v1 - v2      # lp, hp


def run(x, sr, **kw):
    p = dict(DEF); p.update(kw)
    n = len(x); y = np.zeros_like(x); gdb = np.zeros(n)
    A = p["ataque"]; flo = 10 ** (p["cola"] / 20); jump = 10 ** (p["sens"] / 20)
    la = min(int(math.floor(p["la"] * 0.001 * sr + 0.5)), 16383)
    hold = p["hold"] * 0.001 * sr + la; dec = p["caida"] * 0.001 * sr
    dur = p["dur"] * 0.001 * sr + la; dtau = max(p["dur"] * 0.001 * sr / 3, 1)
    kfa = math.exp(-1 / (0.0005 * sr)); kfr = math.exp(-1 / (0.005 * sr))
    ksa = math.exp(-1 / (0.020 * sr)); ksr = math.exp(-1 / (0.150 * sr))
    kg = math.exp(-1 / (0.001 * sr))
    kga = 1 - math.exp(-1 / (0.0002 * sr))          # suavizado del ataque (0.2 ms)
    # continuo
    wn = int(math.floor(0.015 * sr)); kas = 1 - math.exp(-1 / (p["dur"] * 0.001 * sr))
    krf = 1 - math.exp(-1 / (0.010 * sr)); krs = 1 - math.exp(-1 / (p["caida"] * 0.001 * sr))
    ksm = 1 - math.exp(-1 / (0.0005 * sr))
    sens = p["sens"]; mix = p["mezcla"] / 100; mk = 10 ** (p["ganancia"] / 20)
    band = p["banda"]
    if band:
        f = [SVF(p["corte"], sr) for _ in range(6)]   # por canal: etapa 1, lp2, hp2
    ef = es = 0.0; tt = 100000; g = 1.0; gadb = 0.0; ta = 100000; et = 0.0
    wc = 0; cm = pm = 0.0; as_ = sf_ = ss_ = 0.0; gc = 0.0
    DL = np.zeros((16384, 4)); w = 0
    for i in range(n):
        xl, xr = x[i]
        if band:
            l1, h1 = f[0](xl); bl = f[1](l1)[0]; hl = f[2](h1)[1]
            l1, h1 = f[3](xr); br = f[4](l1)[0]; hr = f[5](h1)[1]
            if band == 1: bL, bR, rL, rR = bl, br, hl, hr
            else: bL, bR, rL, rR = hl, hr, bl, br
        else:
            bL, bR, rL, rR = xl, xr, 0.0, 0.0
        v = max(abs(bL), abs(bR))
        if p["modo"] == 0:
            ef = kfa * ef + (1 - kfa) * v if v > ef else kfr * ef + (1 - kfr) * v
            es = ksa * es + (1 - ksa) * v if v > es else ksr * es + (1 - ksr) * v
            if ef > es * jump and ef > 0.0001 and tt > hold: tt = 0; ta = 0; et = ef
            target = 1 if tt < hold else flo + (1 - flo) * math.exp(-6.9 * (tt - hold) / dec)
            g = target if target > g else kg * g + (1 - kg) * target
            if ta < dur and ef > et * jump: ta = 0; et = ef      # re-arma la ventana del ataque
            if A != 0 or gadb != 0:
                s = 1.0 if ta < dur else math.exp(-(ta - dur) / dtau)
                gadb += (A * s - gadb) * kga
                if abs(gadb) < 0.000001: gadb = 0.0
                gain = g * math.exp(gadb * 0.11512925464970229)
            else:
                gain = g
            tt += 1; ta += 1
        else:
            wc -= 1
            if wc <= 0: wc = wn; pm = cm; cm = 0.0
            if v > cm: cm = v
            h = max(cm, pm) + 1e-9
            as_ = as_ + (h - as_) * kas if h > as_ else h
            sf_ = h if h > sf_ else sf_ + (h - sf_) * krf
            ss_ = h if h > ss_ else ss_ + (h - ss_) * krs
            da = 20 * math.log10(h / as_); ds = 20 * math.log10(ss_ / sf_)
            t = A * min(da / sens, 1) + p["cola"] * min(ds / sens, 1)
            gc += (t - gc) * ksm
            gain = 10 ** (gc / 20)
        DL[w] = (bL, bR, rL, rR); r = (w - la) % 16384; dbL, dbR, drL, drR = DL[r]; w = (w + 1) % 16384
        gm = gain if mix >= 1 else 1 + (gain - 1) * mix
        if p["escuchar"] == 2:
            y[i] = ((gm - 1) * dbL, (gm - 1) * dbR)
        elif p["escuchar"] == 1:
            y[i] = (dbL * gm * mk, dbR * gm * mk)
        else:
            y[i] = ((drL + dbL * gm) * mk, (drR + dbR * gm) * mk)
        gdb[i] = 20 * math.log10(max(gain, 1e-12))
    return y, gdb
