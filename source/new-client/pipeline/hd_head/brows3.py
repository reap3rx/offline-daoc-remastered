"""The HD brows' hair (the HD look, owner 2026-11-25: "better eyebrows"): hd_brow_hair.png, shared by every race - the
hairs in the brow's own frame, which the client lays along the brow it draws in face space (Fig3Figure's head shader:
the shape, its thickness, arch, tail and spacing are the player's sliders; the hairs come from here).

  x: along the brow, repeating every SPAN eye spacings (the hairs lean out, towards the tail)
  y: across it, s = -1.4 .. 1.4 of the brow's half-thickness (top half of the texture: the brow's head, the hairs
     standing up; bottom half: the body and tail, the hairs lying along it)
  r: fine hairs, g: coarse hairs (the Bushy shapes) - each 0 .. 1 coverage
"""
import numpy as np, cv2

W, H = 1024, 256                       # each half
SPAN = 0.4                             # eye spacings along the brow per repeat
S_MAX = 1.4


def strokes(rng, n, ang_deg, ang_jit, length, width, w_px, h_px, coarse):
    c = np.zeros((h_px, w_px * 3), np.float32)    # (drawn three wide, the middle kept: the repeat seamless)
    for _ in range(n):
        x = rng.uniform(0, w_px * 3)
        s = rng.normal(0, 0.55)
        if abs(s) > S_MAX:
            continue
        y = (0.5 - s / (2 * S_MAX)) * h_px
        a = np.radians(ang_deg + rng.normal(0, ang_jit) - 10 * s)   # (fanning: the top hairs lean up, the bottom down)
        L = length * rng.uniform(0.6, 1.25) * (1 - 0.35 * min(abs(s) / S_MAX, 1))
        pts = []
        bend = rng.normal(0, 0.15)
        for k in range(8):
            t = k / 7
            aa = a + bend * t
            pts.append((x + np.cos(aa) * L * t, y - np.sin(aa) * L * t))
        pts = np.array(pts, np.float32)
        val = rng.uniform(0.55, 1.0)
        th = max(1, int(round(width * (1.6 if coarse else 1.0))))
        cv2.polylines(c, [np.round(pts * 4).astype(np.int32)], False, val, th, cv2.LINE_AA, shift=2)
    return np.clip(c[:, w_px:2 * w_px], 0, 1)


def make(path):
    rng = np.random.default_rng(11)
    px_per = W / SPAN                              # pixels an eye spacing, along
    halves = []
    for ang, jit in ((68, 10), (22, 7)):           # the head's hairs stand up; the body's lie along, leaning up and out
        fine = strokes(rng, 4200, ang, jit, 0.07 * px_per, 1.0, W, H, False)
        coarse = strokes(rng, 2400, ang, jit, 0.09 * px_per, 1.6, W, H, True)
        halves.append(np.dstack([np.zeros_like(fine), coarse, fine]))   # (BGR: r fine, g coarse)
    img = np.vstack(halves)
    img = cv2.GaussianBlur(img, (0, 0), 0.6)
    cv2.imwrite(str(path), np.clip(img * 255, 0, 255).astype(np.uint8))
    return img


if __name__ == '__main__':
    import sys
    make(sys.argv[1] if len(sys.argv) > 1 else 'hd_brow_hair.png')
