"""Figure hair textures redrawn as strands (claude 2026-11-05, owner: the hair test - "I like the way the texture looks
on this prototype's hair ... trying to match the original's [shape]"; then "Let's do all of the vanilla hair styles").

The painted hair's own flow (which way its strokes run: the texture's structure tensor) is drawn as fine strands by
line integral convolution of noise along it; the colour is the painting's, softened (its baked light let go); the
alpha stays the painting's (the hair's cut-out edges). Beside each, a small flow map for the game's hair shader
(Fig3Figure: the strands' highlight and the broken-up outline): R, G the flow's doubled angle (cos, sin - no 'which way
along' to flip, so it blends smoothly), B the strand mask.

    python hair_strands.py <in png> <out png> <out flow png> [--len=40] [--keep=0.1]
    python hair_strands.py --all <list.txt> <src dir> <out dir> <flow dir> [--jobs=8]
--all: every texture stem in the list (the hair styles' textures, from the race figures), from the untouched sources
(fig3_textures/hair_src: the upscaled paintings) into the game's set; ones already newer than their source skipped.
--keep: how much of the painting's own light and dark stays under the strands (0: only its colour)."""
import sys
from pathlib import Path
import numpy as np, cv2


def arg(k, d):
    return float(next((a.split('=')[1] for a in sys.argv if a.startswith(f'--{k}=')), d))


def strands(src, dst, flow_dst, L=40, keep=0.1, contrast=0.2, blur_px=24.0, flow_size=512):
    im = cv2.imread(str(src), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255.0
    if im.ndim == 2:
        im = np.dstack([im, im, im])
    bgr = np.ascontiguousarray(im[..., :3])
    alpha0 = im[..., 3] if im.shape[2] == 4 else np.ones(bgr.shape[:2], np.float32)
    h, w = bgr.shape[:2]
    s = w / 1024.0
    lum = cv2.GaussianBlur(bgr @ np.array([0.11, 0.59, 0.3], np.float32), (0, 0), 1.5 * s)
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    sig = 10.0 * s
    jxx = cv2.GaussianBlur(gx * gx, (0, 0), sig)
    jyy = cv2.GaussianBlur(gy * gy, (0, 0), sig)
    jxy = cv2.GaussianBlur(gx * gy, (0, 0), sig)
    # the strokes run across the strongest gradient: the tensor's minor eigenvector
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
    fx, fy = np.cos(theta).astype(np.float32), np.sin(theta).astype(np.float32)
    rng = np.random.default_rng(7)
    noise = rng.random((h, w), dtype=np.float32)
    noise = np.where(noise > 0.7, 1.0, 0.0).astype(np.float32) + 0.15 * rng.random((h, w), dtype=np.float32)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    acc = noise.copy()
    wsum = np.ones_like(noise)
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
    st = np.clip(0.5 + contrast * lic, 0, 1)
    # colour: the painting softened (its colour; its baked light and dark mostly let go), the strands' light and dark
    isl = (bgr.max(axis=2) > 0.02).astype(np.float32) * alpha0          # the painted islands (not the atlas's black)
    blur = blur_px * s
    base = cv2.GaussianBlur(bgr * isl[..., None], (0, 0), blur) / np.maximum(cv2.GaussianBlur(isl, (0, 0), blur), 1e-3)[..., None]
    detail = bgr / np.maximum(cv2.GaussianBlur(bgr, (0, 0), 4.0 * s), 1e-3)
    paint = base * (1.0 + keep * (np.clip(detail, 0.3, 2.0) - 1.0))
    out_rgb = np.clip(paint * (0.45 + 1.1 * st[..., None]), 0, 1)
    mask = np.clip((st - 0.35) / 0.4, 0, 1) * isl
    cv2.imwrite(str(dst), (np.dstack([out_rgb, alpha0]) * 255 + 0.5).astype(np.uint8))
    # the flow map (BGR for cv2: B mask, G sin, R cos), smaller - the flow is smooth
    flow = np.dstack([mask, 0.5 + 0.5 * np.sin(2 * theta), 0.5 + 0.5 * np.cos(2 * theta)])
    fs = min(flow_size, w)
    flow = cv2.resize(flow, (fs, fs * h // w), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(flow_dst), (np.clip(flow, 0, 1) * 255 + 0.5).astype(np.uint8))


def _one(job):
    src, dst, flow = job
    try:
        strands(src, dst, flow)
        return dst.name
    except Exception as e:                                 # (one bad texture shouldn't stop the rest)
        return f'FAILED {src.name}: {e}'


def main():
    if sys.argv[1] == '--all':
        from concurrent.futures import ProcessPoolExecutor
        stems = [l.strip().lower() for l in Path(sys.argv[2]).read_text().splitlines() if l.strip()]
        src_dir, out_dir, flow_dir = Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5])
        flow_dir.mkdir(parents=True, exist_ok=True)
        files = {p.stem.lower(): p for p in src_dir.glob('*.png')}
        jobs = []
        for st in stems:
            src = files.get(st)
            if src is None:
                print('missing', st)
                continue
            dst, flow = out_dir / src.name, flow_dir / (st + '.png')
            if flow.exists() and dst.exists() and flow.stat().st_mtime >= src.stat().st_mtime and dst.stat().st_mtime >= src.stat().st_mtime:
                continue
            jobs.append((src, dst, flow))
        done = 0
        with ProcessPoolExecutor(int(arg('jobs', 8))) as ex:
            for r in ex.map(_one, jobs):
                done += 1
                if r.startswith('FAILED') or done % 25 == 0:
                    print(done, r, flush=True)
        print('finished', done, 'of', len(jobs))
        return
    strands(sys.argv[1], sys.argv[2], sys.argv[3], L=int(arg('len', 40)), keep=arg('keep', 0.1))
    print('strands', sys.argv[2])


if __name__ == '__main__':
    main()
