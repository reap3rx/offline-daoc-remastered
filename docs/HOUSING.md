# Player housing (new client)

Housing has been in the server all along: OpenDAoC's HouseMgr, the three housing regions (Albion 2, Midgard 102,
Hibernia 202), 1,800 lots per realm, the deed and furniture shops. The new client now draws and uses it
(2026-11-02).

## Getting there

- **Walk in** through the realm's housing gate, as on live: Albion from Camelot Hills (the *Caerwent* exits), Midgard
  from Vale of Mularn (*Erikstaad*), Hibernia from Connacht (*Meath*). The housing entrance zone's own exit takes you
  back out to the same spot. (These are the old client's zone jumps and the server's ZonePoints 108-113; the new
  client had left them out while the housing zones weren't built.)
- Or talk to a capital teleporter (Master Visur, Stor Gothi Annark, Channeler Glasny) and say **[Housing]**, then
  **[entrance]**.

Each realm's housing is nine zones built from the old client's `phousing/zones`, with the same Real-ESRGAN texture
pass as the rest of the world (`pipeline/upscale_built.py`, for content first built with `--no-upscale`).

## Buying a lot and building

- **Lot markers** stand on every empty lot. Right click one (or target it and press Use / Get) to buy it: the price
  starts high and falls over time, down to 300 gold. "You won't be able to delete this character."
- Right click your own lot marker again for its **deeds**: cottage (1 platinum), house, villa, mansion. Drag the deed
  onto your lot marker and the house goes up.
- A bigger deed dragged onto your **house** upgrades it (the server warns that it clears the house). The porch deed
  adds a porch, the consignment deed a consignment merchant on the porch, the house removal deed takes it down.

## Your house

- **Left click the door** to go in, the door inside to come out. In Action Combat, the **interact key** (F) does the
  same: the door (or the house) under the crosshair, else the nearest door a few metres in front of you.
- Torches, candles, lamps and hearths give light - the house's own wall sconces and the furniture you place (the four
  wall torches, the candle tables, the tiki torch, the forge).
- **Right click the house** (or the door inside) for its menu:
  - outside: Enter, the garden shop, the exterior looks (roof, walls, door, supports, porch, awning, guild banner and
    shield), deeds, house information, lockbox;
  - inside: Leave, the furniture shop, the interior looks (carpets, indoor banner and shield), the four hookpoint shops
    (servants, vaults, crafting, bindstones), show hookpoints, deeds, house information, lockbox.
- Looks bought in the exterior / interior looks windows change the house at once (HouseEdit), for everyone near.
- **Lockbox** puts gold in for the rent (10 or 100 gold at a time; the server asks you to confirm).

## Decorating

- **Furniture**: buy it from the furniture shop, then drag it from your backpack onto the floor (floor pieces) or a
  wall (wall pieces: maps, tapestries, trophies). It lands where you let go. Right click a piece to turn it (45
  degrees) or take it back.
- **Hookpoint pieces** (servants, vaults, crafting tables, bindstones): choose *Show hookpoints* in the house menu and
  drag the piece onto one of the glowing markers.
- **Garden**: buy garden pieces from the garden shop and drag them onto the ground around your house: they take the
  nearest free garden spot. Right click one to take it back.

## How it works

- `source/new-client/pipeline/build_housing.py` converts the house exteriors and interiors (`phousing.mpk`
  `ph_houses.csv`), the lot markers and every housing item's model into `new-client/godot/content/housing`
  (`housing.json`: houses with their garden spots, interiors with their points and hookpoints, objects). The houses'
  choosable parts are tagged in the conversion (roofN, wallN, doorN, porch, tent, banners, shields, carpetN, and the
  interiors' placement planes floorpN / wallpN). The hookpoints come from the server database (HouseHookpointOffset,
  read only).
- `source/new-client/pipeline/build_zone.py <zone>` builds a housing zone like any other; `--exits-only` rewrites
  a built zone's exits alone (how Camelot Hills, Vale of Mularn and Connacht got their housing gates).
- `game/world/housing.gd` builds houses, interiors and objects; `game/net/server_world.gd` handles the packets
  (HouseCreate 0xD1, HouseChangeGarden 0xD2, HouseEnter 0x08, HouseExit 0x0A, HousingItem 0x09) and the clicks and
  drops; `game/net/DaocClient.cs` sends HouseEnterLeave, HouseMenu, HousePlaceItem, HousePickup, HouseRotate,
  HouseEdit.
- Conventions the new client uses (only it reads them): a floor piece's Position is the floor plane's number and its
  X / Y are DAoC units east / south of the house's spot; a wall piece's Position is the wall plane's number, X along
  the plane and Y up from its lowest corner; a garden piece's Position is the garden spot (the house NIF's GPointN).
  Houses' headings are degrees (DBHouse.Heading); interiors are never turned and hang 25000 units up.

## Not done yet

- Permissions (friends, guild access) have no window: only the owner can decorate.
- Guild emblems are not painted on banners and shields; the awning and carpets take their colour, the shutters and
  porch materials don't change yet.
- Market (consignment) windows on the porch merchant and house vault windows depend on the existing merchant / vault
  windows and haven't been tried.
