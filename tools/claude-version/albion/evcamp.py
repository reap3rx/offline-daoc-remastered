"""Albion's campaign chains (claude 2026-11-24, round 4): the four posts' assaults and counters and the raid, made the way the
Southern Muster's are (zone216: sh_cpN_assault / sh_cpN_counter / sh_princes_hollow) - AlbionCampaign.cs arms them."""
from evcommon import R

def giver(LOOK, name, level, pos, greet, accept, reply, thanks, regret, hp=5, size=None):
    g = dict(LOOK, name=name, level=level, pos=pos, health_mult=hp, greet=greet, accept=accept, reply=reply,
             busy="Not yet. The host is still forming up - rest, and gather.", cooldown_s=120, thanks=thanks, regret=regret)
    if size:
        g['size'] = size
    return g

def assault(prefix, n, title, levels, minp, hint, giv, guards, stages, bots=12, bot_min=45):
    return {"id": f"{prefix}{n}_assault", "title": title, "levels": levels, "manual": True, "bots": bots, "bot_min_level": bot_min,
            "min_people": minp, "hint": hint, "rest_s": 15, "start": "s1", "giver": giv, "guards": guards, "stages": stages}

def cull(name, objective, announce, center, mobs, kill, nxt, xp=14, cp=140, tok=10, r=75):
    return {"id": "s1", "type": "cull", "name": name, "objective": objective, "announce": announce, "center": center, "radius": r,
            "time_s": 1200, "kill": kill, "alive": 8, "mobs": mobs, "success": "The post breaks.", "fail": "The host is thrown back.",
            "on_success": nxt, "on_fail": "end", "reward": R(xp, cp, tok)}

def wards(sid, name, objective, announce, center, points, names, mobs, nxt, flag_name, xp=14, cp=140, tok=10):
    return {"id": sid, "type": "wards", "name": name, "objective": objective, "announce": announce, "wards": points,
            "ward_names": names, "ward_radius": 22, "hold_s": 30, "time_s": 900, "alive": 2, "mobs": mobs, "reinforce_s": 40,
            "flag": 466, "flag_name": flag_name, "center": center, "radius": 75, "success": "Done - on to whoever holds the place!",
            "fail": "It's lost - the host falls back.", "on_success": nxt, "on_fail": "end", "reward": R(xp, cp, tok)}

def hold(sid, name, objective, announce, center, protect, froms, mobs, nxt, thanks, xp=14, cp=140, tok=10):
    return {"id": sid, "type": "defend", "name": name, "objective": objective, "announce": announce, "center": center, "radius": 80,
            "duration_s": 240, "protect": dict(protect, pos=center), "waves": {"every_s": 28, "count": 4, "from": froms, "mobs": mobs},
            "thanks": thanks, "success": "They break - and whoever leads them comes out.", "fail": "The banner falls.",
            "on_success": nxt, "on_fail": "end", "reward": R(xp, cp, tok)}

def boss_stage(sid, name, announce, center, boss, adds, success, xp=20, cp=200, tok=14, items=None, every=40, count=3, r=80, time_s=1200):
    return {"id": sid, "type": "boss", "name": name, "objective": f"Defeat {name}", "announce": announce, "center": center,
            "radius": r, "time_s": time_s, "boss": boss, "adds": {"every_s": every, "count": count, "mobs": adds},
            "success": success, "fail": "The host is driven back.", "on_success": "end", "on_fail": "end",
            "reward": R(xp, cp, tok, items, 60) if items else R(xp, cp, tok)}

def counter(prefix, n, place, enemy, levels, center, protect, froms, mobs, bots=12, bot_min=45, title=None):
    return {"id": f"{prefix}{n}_counter", "title": title or f"{enemy[0].upper() + enemy[1:]} Strike{'s' if not enemy.endswith('s') else ''} Back at {place[0].upper() + place[1:]}",
            "levels": levels, "manual": True, "bots": bots, "bot_min_level": bot_min, "wake_m": 200,
            "hint": f"{enemy[0].upper() + enemy[1:]} {'are' if enemy.endswith('s') else 'is'} coming back for {place}!", "start": "c1",
            "stages": [{"id": "c1", "type": "defend", "name": f"Hold {place}", "objective": f"Keep the host's captain alive at {place}",
                        "announce": f"{enemy[0].upper() + enemy[1:]} {'are' if enemy.endswith('s') else 'is'} coming back for {place}! The host will hold as long as it can - help them, or it falls!",
                        "center": center, "radius": 80, "duration_s": 600, "protect": dict(protect, pos=center, health_mult=14),
                        "waves": {"every_s": 32, "count": 4, "from": froms, "mobs": mobs},
                        "thanks": "They broke on us. The line holds.",
                        "success": f"{enemy[0].upper() + enemy[1:]} break{'' if enemy.endswith('s') else 's'} against the line. {place[0].upper() + place[1:]} holds - and the clock starts again.",
                        "fail": f"The banner falls. {enemy[0].upper() + enemy[1:]} {'have' if enemy.endswith('s') else 'has'} {place} again.",
                        "on_success": "end", "on_fail": "end", "reward": R(20, 180, 14)}]}

def around(P, c, d=60):
    return [P(c[0] - d, c[1] - d // 2), P(c[0] + d, c[1] + d // 2), P(c[0], c[1] - d)]
