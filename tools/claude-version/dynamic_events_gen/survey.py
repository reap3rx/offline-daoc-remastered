import sqlite3, collections, json, math, re
import sys
c=sqlite3.connect(sys.argv[1])
ZONES=[0,1,2,3,4,6,7,8,9,10,100,101,102,103,104,105,106,107,108,116,200,201,202,203,204,205,206,207,208,216]
zones={r[0]:r for r in c.execute('select ZoneID,RegionID,Name,OffsetX,OffsetY,Width,Height from Zones')}
T={r[0]:r for r in c.execute('select TemplateId,Name,Level,Model,Size,ClassType,EquipmentTemplateID from NpcTemplate')}
byname={}
for t in T.values(): byname.setdefault(t[1].lower(),t)
def lv(s):
    n=[int(x) for x in re.findall(r'\d+',str(s))]; return [min(n),max(n)] if n else [0,0]
out={}
for z in ZONES:
    zid,reg,name,ox,oy,w,h=zones[z]; x0,y0=ox*8192,oy*8192
    rows=list(c.execute('select Name,X,Y,Z,Level,Realm,ClassType,Model,EquipmentTemplateID,NPCTemplateID,Guild,Size from Mob where Region=? and X>=? and X<? and Y>=? and Y<?',(reg,x0,x0+w*8192,y0,y0+h*8192)))
    mobs=[r for r in rows if r[5]==0]; realm=[r for r in rows if r[5]!=0]
    by=collections.defaultdict(list)
    for m in mobs: by[m[0]].append(m)
    types=[]
    for n,l in by.items():
        tids=[m[9] for m in l if m[9] and m[9] in T]
        t=T[tids[0]] if tids else byname.get(n.lower())
        if not t: continue
        L=lv(t[2]); 
        if L[1]==0: L=[min(m[4] for m in l),max(m[4] for m in l)]
        pts=[((m[1]-x0)/40,(m[2]-y0)/40) for m in l]
        # cluster: 100m grid cells
        cell=collections.Counter((int(p[0]//150),int(p[1]//150)) for p in pts)
        cl=[]
        for (cx,cy),k in cell.most_common(3):
            ps=[p for p in pts if (int(p[0]//150),int(p[1]//150))==(cx,cy)]
            cl.append([round(sum(p[0] for p in ps)/len(ps)),round(sum(p[1] for p in ps)/len(ps)),k])
        types.append(dict(name=n,n=len(l),lv=L,tpl=t[0],model=t[3],named=n[:1].isupper(),cl=cl))
    types.sort(key=lambda t:t['lv'][0])
    guards=[r for r in realm if 'Guard' in (r[6] or '')]
    gcell=collections.Counter((int((g[1]-x0)/40//250),int((g[2]-y0)/40//250)) for g in guards)
    towns=[]
    for (cx,cy),k in gcell.most_common(6):
        if k<3: continue
        gs=[g for g in guards if (int((g[1]-x0)/40//250),int((g[2]-y0)/40//250))==(cx,cy)]
        g=gs[0]
        towns.append(dict(x=round(sum((q[1]-x0)/40 for q in gs)/len(gs)),y=round(sum((q[2]-y0)/40 for q in gs)/len(gs)),n=k,guard=[g[0],g[7],g[8],g[9],g[4],g[11],g[10],g[6]]))
    areas=[(r[0],round((r[1]-x0)/40),round((r[2]-y0)/40)) for r in c.execute('select Description,X,Y from Area where Region=?',(reg,)) if x0<=r[1]<x0+w*8192 and y0<=r[2]<y0+h*8192]
    allpts=[[round((m[1]-x0)/40),round((m[2]-y0)/40)] for m in rows]
    out[z]=dict(name=name,region=reg,off=[ox,oy],size=[w,h],types=types,towns=towns,areas=areas,realm_pts=[[round((m[1]-x0)/40),round((m[2]-y0)/40)] for m in realm],mob_pts=[[round((m[1]-x0)/40),round((m[2]-y0)/40)] for m in mobs])
json.dump(out,open(sys.argv[2] if len(sys.argv)>2 else 'zones3.json','w'))
import sys
for z,d in out.items():
    print('==',z,d['name'],d['size'],'areas:',', '.join('%s@%d,%d'%a for a in d['areas'][:10]))
    for t in d['towns']: print('   town %d,%d n=%d guard=%s'%(t['x'],t['y'],t['n'],t['guard']))
    print('   '+' ; '.join('%s %d-%d x%d @%s'%(t['name'],t['lv'][0],t['lv'][1],t['n'],'/'.join('%d,%d'%(a,b) for a,b,k in t['cl'][:1])) for t in d['types'] if not t['named'] and t['n']>=4))
