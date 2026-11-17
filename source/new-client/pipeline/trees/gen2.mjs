// Offline DAoC Remastered tree generator (claude 2026-11-17). EZ-Tree (MIT, Daniel Greenheck) in headless Chromium.
//   node gen2.mjs specs.json outdir
// Per spec: one tree (or a clump of 2-3 stems), scaled to the spec's height in metres, sunk into the ground like the
// original, leaf normals bent out from the crown (soft, painterly light), exported as <name>.glb with two meshes:
// "bark" and "leaves" (geometry and UVs; the game gives the materials). A preview <name>.png with the DAoC textures.
import { createRequire } from 'module'; const require = createRequire(import.meta.url); const { chromium } = require(process.env.NODE_PATH + '/playwright');
import fs from 'fs'; import path from 'path';
const [, , specFile, outDir] = process.argv;
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8')); fs.mkdirSync(outDir, { recursive: true });
const map = { '/three/': 'node_modules/three/', '/ez-tree/': 'node_modules/@dgreenheck/ez-tree/', '/': 'web/' };
const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 900, height: 900 } });
page.on('pageerror', e => console.log('[pageerror]', e.message));
page.on('console', m => { if (m.type() === 'error' && !m.text().includes('texImage3D')) console.log('[page]', m.text()); });
await page.route('http://trees.local/**', async route => {
  const u = new URL(route.request().url()).pathname; const pre = Object.keys(map).find(p => u.startsWith(p));
  const f = path.join(path.resolve('.'), map[pre], u.slice(pre.length) || 'index.html');
  const ct = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : f.endsWith('.png') ? 'image/png' : 'application/octet-stream';
  try { await route.fulfill({ body: fs.readFileSync(f), contentType: ct }); } catch { await route.fulfill({ status: 404 }); }
});
await page.goto('http://trees.local/index.html'); await page.waitForFunction(() => window.ready === true);
const log = fs.existsSync(path.join(outDir, 'generated.json')) ? JSON.parse(fs.readFileSync(path.join(outDir, 'generated.json'))) : [];
const have = new Set(log.map(e => e.name));   // (a run picks up where a stopped one left off)
for (const spec of specs) {
  if (have.has(spec.name)) continue;
  const res = await page.evaluate(async (spec) => {
    const T = window.THREE;
    const { mergeGeometries } = await import('three/addons/utils/BufferGeometryUtils.js');
    const deep = (a, b) => { for (const k in b) { if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) { a[k] = a[k] || {}; deep(a[k], b[k]); } else a[k] = b[k]; } };
    const barks = [], leaves = [];
    const n = spec.clump || 1;
    for (let i = 0; i < n; i++) {
      const tree = new window.Tree();
      tree.loadPreset(spec.preset); deep(tree.options, spec.options || {});
      tree.options.seed = spec.seed + i * 7919;
      if (n > 1) tree.options.branch.length[0] *= 1 - 0.12 * i;
      tree.generate();
      const m = new T.Matrix4();
      if (n > 1) {
        const a = (i / n) * Math.PI * 2 + spec.seed % 7, off = 2.2 + i * 0.4;
        m.makeRotationAxis(new T.Vector3(Math.sin(a), 0, -Math.cos(a)), 0.09 + 0.04 * i).setPosition(Math.cos(a) * off, 0, Math.sin(a) * off);
      }
      const strip = g => { const c = new T.BufferGeometry(); c.setAttribute('position', g.attributes.position.clone()); c.setAttribute('normal', g.attributes.normal.clone()); c.setAttribute('uv', g.attributes.uv.clone()); c.setIndex(g.index.clone()); return c.applyMatrix4(m); };
      barks.push(strip(tree.branchesMesh.geometry)); leaves.push(strip(tree.leavesMesh.geometry));
    }
    const bark = mergeGeometries(barks), leaf = mergeGeometries(leaves);
    // to metres: the tallest point at the spec's height, the trunk's foot sunk into the ground like the original
    const bb = new T.Box3().setFromBufferAttribute(bark.attributes.position).union(new T.Box3().setFromBufferAttribute(leaf.attributes.position));
    const s = spec.height / (bb.max.y - bb.min.y);
    for (const g of [bark, leaf]) { g.translate(0, -bb.min.y, 0); g.scale(s, s, s); g.translate(0, -spec.sink, 0); }
    // leaf normals: out from the crown's centre (a soft round light on the crown, not flat cards)
    const lb = new T.Box3().setFromBufferAttribute(leaf.attributes.position), c = lb.getCenter(new T.Vector3());
    const ext = lb.getSize(new T.Vector3()), p = leaf.attributes.position, nr = leaf.attributes.normal, v = new T.Vector3(), o = new T.Vector3();
    for (let i = 0; i < p.count; i++) {
      v.set((p.getX(i) - c.x) / ext.x, (p.getY(i) - c.y) / ext.y * 1.4 + 0.25, (p.getZ(i) - c.z) / ext.z).normalize();
      o.set(nr.getX(i), nr.getY(i), nr.getZ(i)); v.lerp(o, 0.15).normalize(); nr.setXYZ(i, v.x, v.y, v.z);
    }
    // the crown's own shade: leaves deep inside it darker, the outer ones in full light (vertex colour; the far
    // pictures are taken with it too, so near and far trees have the same depth)
    const col = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) {
      const rr = Math.hypot((p.getX(i) - c.x) / (ext.x / 2), (p.getY(i) - c.y) / (ext.y / 2), (p.getZ(i) - c.z) / (ext.z / 2));
      const t = Math.min(Math.max((rr - 0.25) / 0.75, 0), 1), ao = 0.42 + 0.58 * t * t * (3 - 2 * t);
      col[i * 3] = col[i * 3 + 1] = col[i * 3 + 2] = ao;
    }
    leaf.setAttribute('color', new T.BufferAttribute(col, 3));
    const fb = new T.Box3().setFromBufferAttribute(bark.attributes.position).union(lb);
    const tris = g => g.index.count / 3;
    let shot = null;
    if (spec.shot) {
      const load = u => new Promise(r => new T.TextureLoader().load(u, t => { t.colorSpace = T.SRGBColorSpace; r(t); }));
      const bt = await load('/tex/' + spec.bark + '.png'); bt.wrapS = bt.wrapT = T.RepeatWrapping;
      const lt = await load('/tex/' + spec.leaf + '.png');
      const r = new T.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
      const sc = new T.Scene(); sc.background = new T.Color(0x9fb4c0);
      sc.add(new T.HemisphereLight(0xdfe8ff, 0x3c4a30, 1.6)); const sun = new T.DirectionalLight(0xfff2dd, 2.2); sun.position.set(40, 60, 30); sc.add(sun);
      sc.add(new T.Mesh(bark, new T.MeshLambertMaterial({ map: bt })));
      sc.add(new T.Mesh(leaf, new T.MeshLambertMaterial({ map: lt, color: new T.Color(spec.leafTint), alphaTest: 0.45, side: T.DoubleSide, vertexColors: true })));
      const h = fb.max.y - fb.min.y, w = Math.max(fb.max.x - fb.min.x, fb.max.z - fb.min.z);
      const cam = new T.PerspectiveCamera(35, 1, 0.1, 2000); const d = Math.max(h, w) * 1.75; cam.position.set(d * 0.7, h * 0.45, d * 0.7); cam.lookAt(0, h * 0.42, 0);
      r.render(sc, cam); shot = r.domElement.toDataURL('image/png'); r.dispose();
    }
    // far views (impostors): the tree photographed unlit (texture x tint only - the game lights it like the near one)
    // from VIEWS directions around it, every 360/VIEWS degrees, square on, into one row of VIEWS pictures (each
    // 512 x 1024, stored at half that); every view the same frame: the tree's widest reach round its trunk and its
    // full height, so the far card can turn to the camera and swap pictures without changing size
    const VIEWS = 8;
    let imp = null;
    {
      const load = u => new Promise(r => new T.TextureLoader().load(u, t => { t.colorSpace = T.SRGBColorSpace; r(t); }));
      const bt = await load('/tex/' + spec.bark + '.png'); bt.wrapS = bt.wrapT = T.RepeatWrapping;
      const lt = await load('/tex/' + spec.leaf + '.png');
      const cv = document.createElement('canvas'); cv.width = 512; cv.height = 1024;
      const r = new T.WebGLRenderer({ canvas: cv, antialias: true, alpha: true, preserveDrawingBuffer: true }); r.setClearColor(0x000000, 0);
      const sc = new T.Scene();
      // (the game draws the far card at the near leaves' brightness, 1.75; the bark here at the near bark's 1.15 of it,
      // so near and far match by construction - owner 2026-11-17: the hand-over showed a darker tree)
      sc.add(new T.Mesh(bark, new T.MeshBasicMaterial({ map: bt, color: new T.Color(1.15 / 1.75, 1.15 / 1.75, 1.15 / 1.75) })));
      sc.add(new T.Mesh(leaf, new T.MeshBasicMaterial({ map: lt, color: new T.Color(spec.leafTint), alphaTest: 0.45, side: T.DoubleSide, vertexColors: true })));
      let reach = 0;
      for (const g of [bark, leaf]) { const q = g.attributes.position; for (let i = 0; i < q.count; i++) reach = Math.max(reach, Math.hypot(q.getX(i), q.getZ(i))); }
      const half = reach * 1.01;
      const hh = (fb.max.y - fb.min.y) / 2 * 1.01, cy = fb.min.y + (fb.max.y - fb.min.y) / 2;
      const cam = new T.OrthographicCamera(-half, half, hh, -hh, 0.1, 1000);
      const out = document.createElement('canvas'); out.width = 256 * VIEWS; out.height = 512; const ctx = out.getContext('2d');
      for (let k = 0; k < VIEWS; k++) {
        const a = k * Math.PI * 2 / VIEWS; cam.position.set(Math.sin(a) * 400, cy, Math.cos(a) * 400); cam.lookAt(0, cy, 0);
        r.render(sc, cam); ctx.drawImage(cv, k * 256, 0, 256, 512);
      }
      imp = { png: out.toDataURL('image/png'), half, bottom: cy - hh, top: cy + hh, views: VIEWS };
      r.dispose();
    }
    const grp = new T.Group();
    const bm = new T.Mesh(bark, new T.MeshStandardMaterial({ name: 'bark' })); bm.name = 'bark'; grp.add(bm);
    const lm = new T.Mesh(leaf, new T.MeshStandardMaterial({ name: 'leaves' })); lm.name = 'leaves'; grp.add(lm);
    const glb = await new window.GLTFExporter().parseAsync(grp, { binary: true });
    const b = new Uint8Array(glb); let str = ''; for (let i = 0; i < b.length; i += 0x8000) str += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
    return { glb: btoa(str), imp, shot, size: [fb.max.x - fb.min.x, fb.max.y - fb.min.y, fb.max.z - fb.min.z], barkTris: tris(bark), leafTris: tris(leaf) };
  }, spec);
  fs.writeFileSync(path.join(outDir, spec.name + '.glb'), Buffer.from(res.glb, 'base64'));
  fs.writeFileSync(path.join(outDir, spec.name + '_far.png'), Buffer.from(res.imp.png.split(',')[1], 'base64'));
  if (res.shot) fs.writeFileSync(path.join(outDir, spec.name + '.png'), Buffer.from(res.shot.split(',')[1], 'base64'));
  const line = `${spec.name}\t${res.size.map(v => v.toFixed(1)).join('x')}\tbark ${res.barkTris}\tleaves ${res.leafTris}`;
  console.log(line); log.push({ name: spec.name, species: spec.species, far: { half: res.imp.half, bottom: res.imp.bottom, top: res.imp.top, views: res.imp.views }, sink: spec.sink, size: res.size, barkTris: res.barkTris, leafTris: res.leafTris });
  fs.writeFileSync(path.join(outDir, 'generated.json'), JSON.stringify(log, null, 1));
}
fs.writeFileSync(path.join(outDir, 'generated.json'), JSON.stringify(log, null, 1));
await browser.close();
