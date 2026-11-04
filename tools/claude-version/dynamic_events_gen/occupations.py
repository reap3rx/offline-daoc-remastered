"""Failure consequences for the zones' event chains (owner 2026-11-02: "if you fail to hold the spot, or fail to defeat
the boss ... those mobs move down to ambush people on the road, and stay there until they are defeated" - like GW2's
Queensdale bandits taking the water pipes, then the workers repairing them).

Every chain gets two stages after its own:
  o1 occupy  - its monsters (and a leader) hold a spot on the way to the nearest town, no time limit; the fallen are
               replaced while nobody presses them. Started when the chain's boss, escort or hold fails.
  o2 defend  - a roadwarden sets the place right while they come back for it; failing it, they hold it again (o1).
The spot: from the chain's last fight towards the nearest town (a third of the way, 120-450 m), on dry, gentle ground
away from towns and other events. CUSTOM below gives hand-written people and words for some chains; the rest are
written from the chain's own monsters and the town's name.

  python occupations.py <zones dir>          (re-running replaces the o1 / o2 it wrote; then dynamic_events_fill_z.py)
Needs DAOC_SURVEY (zones3.json from survey.py) and the client's zone folders (DAOC_ZONES), as gen.py.
"""
import glob, hashlib, json, math, os, re, sys
from terrain import Terrain

HERE = os.path.dirname(os.path.abspath(__file__))
SURV = json.load(open(os.environ.get('DAOC_SURVEY') or os.path.join(HERE, 'zones3.json')))

WARDENS = {1: ['Roadwarden Hal', 'Roadwarden Edith', 'Roadwarden Cuthbert', 'Roadwarden Mabyn'],
           2: ['Roadwarden Sten', 'Roadwarden Ylva', 'Roadwarden Gunnar', 'Roadwarden Hild'],
           3: ['Roadwarden Fiona', 'Roadwarden Cormac', 'Roadwarden Aine', 'Roadwarden Ruadh']}

# hand-written ones: chain id -> words (spot still found the same way unless 'center' is given)
CUSTOM = {
    'bri_druim_cain_rangers': dict(
        center=[872, 320], name='The Siog Hold the South Road',
        objective='Drive the siog off the south road',
        announce="With Ronan's rangers beaten back, the siog have come down out of the fold and hold the south road. "
                 "No herder can get past them. Drive them off.",
        boss=('Ferdiad Road-Thief', None), success="The south road is clear of siog. The herders' road-mender is on his way.",
        worker=('Herder Dallan', 'mending the fold gate the siog broke'),
        restore_announce='Herder Dallan has come out to mend the broken fold gate. The siog are coming back for it!',
        restore_success='"That will hold them. Thank you - the flocks can come home tonight."'),
    'bri_coruscating_mine': dict(
        center=[318, 160], name='The Siog Hold the Mine', objective='Drive the siog out of the Coruscating Mine',
        announce="Gelbhan's footpads have taken the Coruscating Mine itself. The lurikeen won't get their ore back "
                 "until someone throws them out.",
        boss=('Gelbhan\'s Second', None), success='The mine is clear. Tobar is already coming up the road with a cart.',
        worker=('Tobar the Miner', 'shoring up the mine entrance'),
        restore_announce='Tobar is shoring up the mine entrance. The siog want it back!',
        restore_success='"She\'ll hold now. The Coruscating Mine is ours again!"'),
    'camelot_hills_bandit_hollow': dict(
        name="Ranulf's Men Hold the Cotswold Road", objective='Drive the bandits off the Cotswold road',
        announce="Ranulf Blackhand's bandits have come down out of the hollow and set a toll on the Cotswold road. "
                 "Nobody passes without paying - in coin or in blood.",
        boss=('Toll-Keeper Wat', None), success='The bandits are gone from the road. The watch will want their toll gate down.',
        worker=('Wainwright Godric', 'pulling down the bandits\' toll gate'),
        restore_announce='Wainwright Godric is pulling down the toll gate. The bandits are coming back for it!',
        restore_success='"Down it comes! Cotswold\'s road is free again."'),
    'vale_of_mularn_vendo_barrow': dict(
        name='The Vendo Hold the Veldon Road', objective='Drive the vendo off the road to Fort Veldon',
        announce='The vendo have come down from the barrow and hold the road to Fort Veldon. They are hanging bones from '
                 'the trees.',
        boss=('Gnarn\'s Bone-Bearer', None), success='The vendo are gone. The bone charms still hang from the trees.',
        worker=('Skald Orm', 'cutting down the vendo bone charms'),
        restore_announce='Skald Orm is cutting down the vendo bone charms. The vendo want them back!',
        restore_success='"Burn them all. The road to Fort Veldon is clean again."'),
    'lough_derg_curmudgeon_harvest': dict(
        name='The Curmudgeons Hold the Mill Road', objective='Drive the curmudgeons off the mill road',
        announce='The curmudgeons have the whole mill road now, and every cart that comes down it.',
        boss=('Grogan\'s Nephew', None), success='The mill road is free. The miller will want her carts back.',
        worker=('Miller Brigid', 'righting the overturned carts'),
        restore_announce='Miller Brigid is righting the overturned carts. The curmudgeons are coming back!',
        restore_success='"The carts are rolling again - and not to the curmudgeons\' store this time!"'),
    'avalon_marsh_ghoul_court': dict(
        name='The Ghouls Hold the Causeway', objective='Drive the ghouls off the causeway',
        announce='The ghoul lord\'s knights have come out of the drowned court and hold the causeway to Caer Witrin.',
        boss=('Ghoul Banneret', None), success='The causeway is clear. The marsh is already pulling at the stones.',
        worker=('Brother Anselm', 'blessing the causeway stones'),
        restore_announce='Brother Anselm is blessing the causeway stones. The dead are coming back!',
        restore_success='"Rest now, all of you. The causeway is holy ground again."'),
}


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def realm_of(z):
    return 1 if z < 100 else 2 if z < 200 else 3


def town_for(s, at):
    """The nearest town (guards) and its name (the nearest named area to it)."""
    towns = s['towns']
    if towns:
        t = min(towns, key=lambda t: dist((t['x'], t['y']), at))
        tc = (t['x'], t['y'])
        names = sorted(s['areas'], key=lambda a: dist((a[1], a[2]), tc))
        name = names[0][0] if names and dist((names[0][1], names[0][2]), tc) < 350 else None
        return tc, name, t
    pts = s['realm_pts']
    if pts:
        p = min(pts, key=lambda p: dist(p, at))
        return (p[0], p[1]), None, None
    return None, None, None


def find_spot(t, s, frm, toward, used):
    import numpy as np
    realm = np.array(s['realm_pts'] or [[-9999, -9999]], float)
    d = dist(frm, toward) if toward else 0
    ideal = min(450, max(120, d / 3)) if toward else 200
    ang0 = math.atan2(toward[1] - frm[1], toward[0] - frm[0]) if toward else 0.0
    best = None
    for relax in (0, 1):
        for r in range(80, 600, 15):
            for k in range(-8, 9):
                a = ang0 + k * (0.18 if toward else 0.4)
                p = (frm[0] + r * math.cos(a), frm[1] + r * math.sin(a))
                if any(dist(p, u) < (180 if relax else 230) for u in used):
                    continue
                if np.min(np.hypot(realm[:, 0] - p[0], realm[:, 1] - p[1])) < (130 if relax else 160):
                    continue
                dh = t.ok_area(*p, r=40 if not relax else 30, maxdh=12 if not relax else 18)
                if dh is None:
                    continue
                score = abs(r - ideal) / 30 + abs(k) * 0.6 + dh / 3
                if best is None or score < best[0]:
                    best = (score, p)
        if best:
            return best[1]
    return None


def plural(name):
    """'siog footpad' -> 'siog footpads', 'red dwarf thief' -> 'red dwarf thieves', 'outrider of bri leith' ->
    'outriders of bri leith', 'moor wolf' -> 'moor wolves', 'highwayman' -> 'highwaymen'."""
    head, sep, tail = name.partition(' of ')
    words = head.split(' ')
    w = words[-1]
    if w.endswith('man'):
        w = w[:-3] + 'men'
    elif w in ('siog', 'vendo', 'huldu', 'drakulv', 'sheevra', 'eriu', 'muryan', 'annwn', 'bucca') or w.endswith(('s', 'kin')):
        pass
    elif w.endswith(('thief', 'wolf', 'elf', 'dwarf')) and not w.endswith('dwarf'):
        w = w[:-1] + 'ves'
    elif w.endswith('y') and w[-2:-1] not in 'aeiou':
        w = w[:-1] + 'ies'
    elif w.endswith(('x', 'ch', 'sh')):
        w += 'es'
    else:
        w += 's'
    words[-1] = w
    return ' '.join(words) + (sep + tail if sep else '')


def title(s):
    small = {'of', 'the', 'to', 'a', 'and', 'in'}
    out = []
    for i, w in enumerate(s.split(' ')):
        out.append(w if (i and w in small) else w[:1].upper() + w[1:])
    return ' '.join(out)


def build(zone_doc, chain, s, t, used):
    z = zone_doc['zone']
    cid = chain['id']
    cu = CUSTOM.get(cid, {})
    fights = [st for st in chain['stages'] if st['id'] not in ('o1', 'o2') and st.get('center')]
    last = [st for st in fights if st['type'] == 'boss'] or fights
    frm = tuple(last[-1]['center'][:2])
    toward, town, tinfo = town_for(s, frm)
    if 'center' in cu:
        at = tuple(cu['center'])
    else:
        at = find_spot(t, s, frm, toward, used)
        if at is None:
            return None
    used.append(at)
    # its monsters: the main fight's kinds
    mobs = None
    for st in chain['stages']:
        if st['type'] == 'cull' and st.get('mobs'):
            mobs = st['mobs']
            break
    if mobs is None:
        for st in chain['stages']:
            if st['type'] == 'defend' and st.get('waves'):
                mobs = st['waves']['mobs']
                break
    if mobs is None:
        mobs = last[-1].get('adds', {}).get('mobs') or []
    if not mobs:
        return None
    top = chain['levels'][-1]
    foe = plural(mobs[0]['name'])
    road = 'the road to %s' % town if town else 'the old road'
    boss_name = cu.get('boss', (None,))[0] or ('%s warleader' % mobs[0]['name']).capitalize()
    ctitle = chain['title']
    h = int(hashlib.md5(cid.encode()).hexdigest(), 16)
    worker, task = cu.get('worker') or (WARDENS[realm_of(z)][h % 4], 'clearing the road and putting up a new waymarker')
    # who the worker looks like: a protected NPC of the chain, else its giver, else its guards
    look = None
    for st in chain['stages']:
        if st.get('protect'):
            look = st['protect']
            break
    look = look or chain.get('giver') or (chain.get('guards') or [None])[0]
    protect = {'name': worker, 'level': top, 'pos': [round(at[0]), round(at[1])], 'health_mult': 10}
    if look:
        for k in ('template', 'model', 'equipment'):
            if look.get(k):
                protect[k] = look[k]
    ang = math.atan2(frm[1] - at[1], frm[0] - at[0])
    froms = []
    for da in (-0.8, 0, 0.8):
        q = (at[0] + 85 * math.cos(ang + da), at[1] + 85 * math.sin(ang + da))
        froms.append([round(q[0]), round(q[1])])
    o1 = {
        'id': 'o1', 'type': 'occupy',
        'name': cu.get('name') or title('the %s hold %s' % (foe, road)),
        'objective': cu.get('objective') or 'Drive the %s off %s' % (foe, road),
        'announce': cu.get('announce') or ('With %s lost, the %s have spread down onto %s and stop anyone who passes. '
                                           'They will stay until someone drives them out.' % (ctitle, foe, road)),
        'center': [round(at[0]), round(at[1])], 'radius': 70, 'count': 10, 'reinforce_s': 90,
        'mobs': mobs,
        'boss': {'template': mobs[0]['template'], 'name': boss_name, 'level': top + 1,
                 'pos': [round(at[0]), round(at[1])], 'health_mult': 2},
        'success': cu.get('success') or 'The %s are gone from %s. It will need setting right.' % (foe, road),
        'fail': '',
        'on_success': 'o2', 'on_fail': 'o1',
        'reward': {'xp_pct': 15, 'copper_per_level': 100, 'tokens': 6},
    }
    o2 = {
        'id': 'o2', 'type': 'defend', 'name': 'Set It Right',
        'objective': 'Protect %s, who is %s' % (worker, task),
        'announce': cu.get('restore_announce') or '%s has come out to set %s right. The %s are coming back for it!' % (worker, road, foe),
        'center': [round(at[0]), round(at[1])], 'radius': 70, 'duration_s': 120,
        'protect': protect,
        'waves': {'every_s': 30, 'count': 2, 'from': froms, 'mobs': mobs},
        'thanks': cu.get('restore_success') or '"That\'s done - %s is safe again. Thank you."' % road,
        'success': 'The %s break and scatter. %s is open again.' % (foe, road[0].upper() + road[1:]),
        'fail': '%s falls, and the %s take the road back.' % (worker, foe),
        'on_success': 'end', 'on_fail': 'o1',
        'reward': {'xp_pct': 10, 'copper_per_level': 80, 'tokens': 4},
    }
    return o1, o2


def main():
    zdir = sys.argv[1]
    for f in sorted(glob.glob(os.path.join(zdir, 'zone*.json'))):
        doc = json.load(open(f, encoding='utf-8'))
        z = doc['zone']
        s = SURV.get(str(z))
        if s is None:
            print('no survey for', z)
            continue
        t = Terrain(z)
        used = [tuple(st['center'][:2]) for c in doc['chains'] for st in c['stages'] if st.get('center') and st['id'] not in ('o1', 'o2')]
        for c in doc['chains']:
            if c.get('tower'):
                continue                                  # towers have their own capture stages
            c['stages'] = [st for st in c['stages'] if st['id'] not in ('o1', 'o2')]
            built = build(doc, c, s, t, used)
            if not built:
                print('  !! no occupation for', c['id'])
                continue
            c['stages'] += list(built)
            for st in c['stages']:
                if st['id'] in ('o1', 'o2'):
                    continue
                if st['type'] in ('boss', 'escort') or (st['type'] == 'defend' and st.get('protect_leader')):
                    st['on_fail'] = 'o1'
            print(z, c['id'], '->', built[0]['name'], built[0]['center'])
        json.dump(doc, open(f, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
