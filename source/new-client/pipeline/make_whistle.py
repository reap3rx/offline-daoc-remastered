"""A two-note horse whistle for the summon-mount emote (owner 2026-11-16: "a whistle sound and animation that can be tied
with the summon mount ability"; the 1.65 data has no whistle). A rising note then a falling one, a little vibrato and
breath, 0.95 s, 22,050 Hz mono 16-bit.  python make_whistle.py out.wav"""
import math, random, struct, sys, wave

RATE = 22050
random.seed(7)
notes = [  # (start s, length s, from Hz, to Hz)
    (0.00, 0.30, 1650, 2450),
    (0.38, 0.50, 2500, 1500),
]
total = 0.95
n = int(RATE * total)
out = [0.0] * n
for start, length, f0, f1 in notes:
    phase = 0.0
    a = int(start * RATE)
    m = int(length * RATE)
    for i in range(m):
        t = i / m
        f = f0 + (f1 - f0) * (t * t * (3 - 2 * t))          # smooth glide
        f *= 1 + 0.012 * math.sin(2 * math.pi * 6.5 * i / RATE)   # vibrato
        phase += 2 * math.pi * f / RATE
        env = min(1.0, t / 0.08) * min(1.0, (1 - t) / 0.18)     # attack / release
        s = math.sin(phase) + 0.18 * math.sin(2 * phase)          # a touch of the overtone
        s += 0.06 * (random.random() * 2 - 1)                      # breath
        if a + i < n:
            out[a + i] += 0.42 * env * s
peak = max(abs(x) for x in out) or 1
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.8 * 32767)) for x in out))
