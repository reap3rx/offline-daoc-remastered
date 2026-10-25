"""Add the King / Queen class (server class 64) to the new (Godot) client's content.

    python tools/king/patch_newclient.py          apply (safe to run again)
    python tools/king/patch_newclient.py --undo   restore the originals

The client's content folder (new-client/godot/content) is not in git, so this script is the
record of what changed. It backs up each file once to E:/Offline DAOC 036c/claude-work/client-originals
before the first change, and --undo copies those originals back.
Close the new client before running it.
"""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]                       # playable-v0.36c
CONTENT = ROOT / 'new-client' / 'godot' / 'content'
ORIGINALS = ROOT.parent / 'claude-work' / 'client-originals'

KING_ID = '64'
LORE = ("Kings and Queens are sovereigns of Pendragon's line who lead Albion from the front. They wear chain, "
        "wield a single slashing blade without a shield, and turn aside blows with peerless parry and evasion. "
        "A sworn retinue fights at their side: a Squire who rises to Knight, commanding armsmen, clerics, scouts, "
        "sorcerers and wizards, while royal decrees shield and empower all who ride with the Crown.")

STYLE_ANIMS = {}     # filled by later steps (new style id -> existing style id whose animation it borrows)


def load(rel):
    return json.loads((CONTENT / rel).read_text(encoding='utf-8'))


def save(rel, data):
    path = CONTENT / rel
    backup = ORIGINALS / rel
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('patched', rel)


def apply():
    rel = 'rules/server_classes.json'
    d = load(rel)
    d['classes'][KING_ID] = {"name": "King", "female": "Queen", "realm": "alb", "races": [1, 2],
                             "stats": ["STR", "DEX", "QUI"]}
    if int(KING_ID) not in d['realms']['alb']:
        d['realms']['alb'].append(int(KING_ID))
    save(rel, d)

    rel = 'items/class_names.json'
    d = load(rel)
    d[KING_ID] = "King"
    save(rel, d)

    rel = 'pregame/pregame.json'
    d = load(rel)
    d.setdefault('class_lore', {})['King'] = LORE
    d['class_lore']['Queen'] = LORE
    save(rel, d)

    if STYLE_ANIMS:
        for rel in ('rules/style_anims.json', 'rules/style_fx.json'):
            d = load(rel)
            for new_id, borrow in STYLE_ANIMS.items():
                if str(borrow) in d:
                    d[str(new_id)] = d[str(borrow)]
            save(rel, d)


def undo():
    for backup in ORIGINALS.rglob('*.json'):
        target = CONTENT / backup.relative_to(ORIGINALS)
        shutil.copy2(backup, target)
        print('restored', target.relative_to(CONTENT))


if __name__ == '__main__':
    undo() if '--undo' in sys.argv else apply()
