"""A figure hair texture redrawn as strands (claude 2026-11-05, owner: the hair test's look - "I like the way the
texture looks on this prototype's hair ... trying to match the original's [shape]"): the painted hair's own flow
(which way its strokes run, from the texture's structure tensor) drawn as fine strands by line integral convolution of
noise along it; the colour the painting's, softly; beside it (<out>_mask.png) the strand mask the game's outer hair layers cut with.
    python hair_strands.py <in png> <out png> [--len=40] [--keep=0.45]
--keep: how much of the painting's own light and dark stays under the strands (0: only its colour)."""
import sys
import numpy as np, cv2

src, dst = sys.argv[1], sys.argv[2]
arg = lambda k, d: float(next((a.split('=')[1] for a in sys.argv if a.startswith(f'--{k}=')), d))
L = int(arg('len', 40)); keep = arg('keep', 0.15)
im = cv2.imread(src, cv2.IMREAD_UNCHANGED).astype(np.float32) / 255.0
if im.ndim == 2:
    im = np.dstack([im, im, im])
bgr = im[..., :3]
alpha0 = im[..., 3] if im.shape[2] == 4 else np.ones(bgr.shape[:2], np.float32)
h, w = bgr.shape[:2]
s = w / 1024.0
lum = cv2.GaussianBlur(bgr @ np.array([0.11, 0.59, 0.3], np.float32), (0, 0), 1.5 * s)
gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
sig = 10.0 * s
jxx = cv2.GaussianBlur(gx * gx, (0, 0), sig); jyy = cv2.GaussianBlur(gy * gy, (0, 0), sig); jxy = cv2.GaussianBlur(gx * gy, (0, 0), sig)
# the strokes run across the strongest gradient: the tensor's minor eigenvector
theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
fx, fy = np.cos(theta).astype(np.float32), np.sin(theta).astype(np.float32)
# noise: fine, a little stretched along the flow already, then convolved along it both ways
rng = np.random.default_rng(7)
noise = rng.random((h, w), dtype=np.float32)
noise = np.where(noise > 0.7, 1.0, 0.0).astype(np.float32) + 0.15 * rng.random((h, w), dtype=np.float32)
ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
acc = noise.copy(); wsum = np.ones_like(noise)
for sign in (1.0, -1.0):
    px, py = xs.copy(), ys.copy()
    dxp, dyp = fx * sign, fy * sign
    for i in range(1, L + 1):
        dx = cv2.remap(fx, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        dy = cv2.remap(fy, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        flip = np.where(dx * dxp + dy * dyp < 0, -1.0, 1.0).astype(np.float32)   # keep going the same way
        dx, dy = dx * flip, dy * flip
        px, py = px + dx * s, py + dy * s
        dxp, dyp = dx, dy
        wt = 1.0 - i / (L + 1)
        acc += wt * cv2.remap(noise, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        wsum += wt
lic = acc / wsum
lic = (lic - lic.mean()) / (lic.std() + 1e-6)
strands = np.clip(0.5 + arg('contrast', 0.2) * lic, 0, 1)
# colour: the painting softened (its colour and broad light), the strands' light and dark on it
isl = (bgr.max(axis=2) > 0.02).astype(np.float32) * alpha0          # the painted islands (not the atlas's black)
blur = arg('blur', 24.0) * s                      # the painting's colour, its baked light and dark mostly let go
base = cv2.GaussianBlur(bgr * isl[..., None], (0, 0), blur) / np.maximum(cv2.GaussianBlur(isl, (0, 0), blur), 1e-3)[..., None]
detail = bgr / np.maximum(cv2.GaussianBlur(bgr, (0, 0), 4.0 * s), 1e-3)
paint = base * (1.0 + keep * (np.clip(detail, 0.3, 2.0) - 1.0))
out_rgb = np.clip(paint * (0.45 + 1.1 * strands[..., None]), 0, 1)
mask = np.clip((strands - 0.35) / 0.4, 0, 1) * isl
# the colour keeps the painting's own alpha (the hair's cut-out edges); the strand mask goes beside it
cv2.imwrite(dst, (np.dstack([out_rgb, alpha0]) * 255 + 0.5).astype(np.uint8))
cv2.imwrite(dst.replace('.png', '_mask.png'), (mask * 255 + 0.5).astype(np.uint8))
# the flow for the strands' highlight (anisotropic: a band across the strands): its doubled angle, which has no
# 'which way along' to flip and so blends smoothly between texels - R cos, G sin (BGR order for cv2)
flow = np.dstack([np.full_like(theta, 0.5), 0.5 + 0.5 * np.sin(2 * theta), 0.5 + 0.5 * np.cos(2 * theta)])
cv2.imwrite(dst.replace('.png', '_flow.png'), (flow * 255 + 0.5).astype(np.uint8))
print('strands', dst, w, h)





