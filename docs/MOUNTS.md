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
(`game/world/mounts.gd`) draws each horse with the model it has built:

- **Standard and heavy horses**: the classic saddled horse (Classic_Body01_Mount_Horse - what monsters.csv draws the
  Catacombs horses 2033 / 2035 with) in the horse's own coat. horsemap.csv gives each horse a coat column of
  fig3haircolormap.csv (rows 48 Standard, 50 Heavy, 52 Unicorn); `pipeline/build_mount_coats.py` writes every coat
  that fits that body (brown, black, white, grey, palomino, spotted, chocolate, Clydesdale, appaloosa, dappled grey,
  leopard, primitive and red dun, Shire dappled, strawberry roan, arboreal; Real-ESRGAN x4) beside the horse's model
  with `content/monsters/mount_coats.json`, and the client paints the horse with it.
- **Unicorns, nightmare, undead, epic, sea horse, flying mounts**: the nearest model of their own (the classic
  unicorns, the nightmare ...). Their Catacombs coats (rainbow, nightmare, undead) belong to other bodies.
- The Catacombs part horses themselves (Body01_Mount_Horse with its Armor01 saddle and Barding01 barding parts) are not
  in this client - only their `cathorse_*.kfa` clips are - so barding has no mesh to draw yet.

## Next

Barding and saddle colours (ControlledHorse carries them; the part meshes would have to come from a later client),
saddlebags.
