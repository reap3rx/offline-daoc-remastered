import json, math, struct
import numpy as np
from PIL import Image
import os
from pathlib import Path
ZROOT=os.environ.get('DAOC_ZONES') or str(Path(__file__).resolve().parents[3] / 'new-client/godot/content/zones')
class Terrain:
    def __init__(self, zone):
        d='%s/zone%03d'%(ZROOT,zone)
        info=json.load(open(d+'/zone.json',encoding='utf-8'))
        self.n=info['heights_size']; self.size=info['size_m']
        self.h=np.fromfile(d+'/'+info['heights'],'<f4')[:self.n*self.n].reshape(self.n,self.n)
        self.levels={b['id']:b['height'] for b in info.get('water',[])}
        try: self.water=np.asarray(Image.open(d+'/water.png'))
        except Exception: self.water=None
        self.fix=[f['pos'] for f in info.get('fixtures',[]) if f.get('collide',True) and not f.get('no_collision')]
        self.fix=np.array([[p[0],p[2]] for p in self.fix]) if self.fix else np.zeros((0,2))
        self.exits=[s['pos'] for s in info.get('spots',[])]
    def z(self,x,y):
        n=self.n; gx=min(max(x/self.size*(n-1),0),n-1.001); gy=min(max(y/self.size*(n-1),0),n-1.001)
        ix,iy=int(gx),int(gy); fx,fy=gx-ix,gy-iy; h=self.h
        top=h[iy,ix]*(1-fx)+h[iy,ix+1]*fx; bot=h[iy+1,ix]*(1-fx)+h[iy+1,ix+1]*fx
        return float(top*(1-fy)+bot*fy)
    def wet(self,x,y):
        if self.water is None: return False
        m=self.water.shape[0]
        i=int(self.water[min(max(int(y/self.size*m),0),m-1),min(max(int(x/self.size*m),0),m-1)])
        lv=self.levels.get(i)
        return lv is not None and self.z(x,y)<lv+0.4
    def ok_area(self,x,y,r=40,maxdh=10):
        if not(110<x<self.size-110 and 110<y<self.size-110): return None
        pts=[(x,y)]+[(x+rr*math.cos(a),y+rr*math.sin(a)) for rr in (r*0.5,r) for a in np.linspace(0,2*math.pi,8,endpoint=False)]
        if any(self.wet(*p) for p in pts): return None
        zs=[self.z(*p) for p in pts]
        dh=max(zs)-min(zs)
        if dh>maxdh: return None
        if len(self.fix) and np.min(np.hypot(self.fix[:,0]-x,self.fix[:,1]-y))<18: return None
        return dh
    def ok_segment(self,a,b,maxgrade=0.55):
        L=math.dist(a,b); n=max(2,int(L/6))
        prev=None
        for i in range(n+1):
            t=i/n; x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
            if self.wet(x,y): return False
            zz=self.z(x,y)
            if prev is not None and abs(zz-prev)/(L/n)>maxgrade: return False
            prev=zz
        return True

    def ok_area_nofix(self, x, y):
        """A spot to stand on (a giver, a quartermaster): dry and nearly flat, buildings allowed nearby."""
        if self.wet(x, y):
            return False
        zs = [self.z(x + dx, y + dy) for dx, dy in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4))]
        return max(zs) - min(zs) < 2.0
