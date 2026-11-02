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
(`game/world/mounts.gd`) draws each horse with the nearest model it has built: the classic saddled horse, the old horse
figure's colours, the unicorns, the nightmare, the flying mounts. horsemap.csv's own Catacombs horse models (2033 and
on) aren't built yet.

## Next

Barding and saddles (ControlledHorse carries them), the Catacombs horse models and their colours, saddlebags.
