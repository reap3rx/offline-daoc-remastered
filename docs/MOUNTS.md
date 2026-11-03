# Mounts (first pass, 2026-11-02)

## Getting a horse

A **Horse Dealer** stands beside every stable master (125 of them, spawned at server start: `scripts/mounts/MountDealers.cs`).
They sell the database's horses: standard horses at level 10 (100 gold), mounts at level 20 (200 gold), heavy horses at
level 50 (350 gold). A horse's level is also its speed tier (server properties `mount_under_level_35_speed` 135% and
`mount_over_level_35_speed` 145%, on top of the out-of-combat run).

## Riding

- **Shift+H** (Options > Controls, *Mount / Dismount*) or **/summon** / **/mount**: calls your horse. The first time, the
  best horse in your backpack you can ride goes into the Horse slot. Calling takes five seconds standing still, out of
  combat; not in dungeons, capitals or instances, and in RvR only a horse above level 35. Shift+H again (or /dismount)
  gets you off.
- You sit in the horse's saddle; standing still you hold the riding pose, moving you ride in step with its gait.
- You steer as always - modern or classic movement, mouse and keys, jumping - at the horse's speed. The horse walks,
  trots and gallops under you at your pace and you sit in its saddle.
- **Action Combat**: a swing, a dodge, a parry / block or drawing a bow gets you off at once and plays on foot (the
  server dismounts you on any attack, being hit, or a hostile cast anyway).

## Bots

- World bots of level 10 or more with no horse buy one when they come within reach of a horse dealer (every stable
  master they board at) and have at least three times its price saved; the horse stays in their Horse slot.
- They ride after walking on for a few seconds out of combat where horses are allowed, at the horse's speed, and get off
  in any fight, cast, stable route, stealth, or after standing still a while (`bots/autonomous/AutonomousBotMounts.cs`).
- Companions ride whenever their player rides (the player's horse's look and speed), so they keep up.

## How it shows

The server says who rides what with ControlledHorse (0x4E) - the bots' through the same packet. The client
(`game/world/mounts.gd`) draws the horses as the client's own Catacombs horse, `content/monsters/cathorse`
(`pipeline/build_cathorse.py`): one skinned figure (figures/fig3/sfig003.mpk horse_medium_skeleton, the parts in
fig016.mpk, the cathorse_*.kfa clips), with

- the body for its kind - standard, heavy (Clydesdale), unicorn, nightmare, undead - in the horse's own coat
  (horsemap.csv -> fig3haircolormap rows 48-53 -> the Horse_Medium_* / Horse_Heavy_* / Horse_nightmare ... skins;
  `pipeline/build_mount_coats.py` writes `content/monsters/mount_coats.json`);
- the saddle: the Armor01 part's shapes for horsematerialmap.csv's choice (meshmateriallist: shapes 7, 53, 14). Every
  shape of the saddle / armour and barding parts is its own node by its material id, so the other choices (light /
  medium / heavy armour, the barding trims) are a matter of showing other ids.

The epic, sea horse, clockwork / gemstone and flying mounts keep the nearest model the client has (their own monster
models). Without the Catacombs horse built, the classic saddled horse stands in, in the coat when it fits.

## Next

Barding and armour choices and their colours (ControlledHorse carries them; the shapes are in the model - the barding's
skin weights still need its bone list, it is skinned to the root for now), saddlebags.

## 2026-11-03: the Catacombs horse tearing apart at a walk or gallop

Each of the horse's parts is many shapes (one per material id), and each shape's skin lists its bones in its own order
(its own NiStringsExtraData). The converter (`pipeline/nif_character.py` build_cata) read every shape's bones from the
part's first list, so most of the horse was bound to the wrong bones: invisible at rest and in the small idle, torn
apart once the legs swung. It now takes each shape's own list (or the skin's own bone node). The characters' parts are
one shape each and come out the same. Rebuild: `build_cathorse.py`.
