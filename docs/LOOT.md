# Loot: quality, forged drops, dyes, novelty potions and Marks of Valor

The loot overhaul (November 2026). Code: `server/GameServer/gameutils/LootOverhaul.cs`, `LootUses.cs`,
`NoveltyPotions.cs`, `ValorQuartermasters.cs`, `scripts/dbupdater/LootOverhaulDatabase.cs`; the special drops on top of
it are described in [SPECIAL_LOOT.md](SPECIAL_LOOT.md).

## Quality tiers

Every random armour, weapon or jewellery drop rolls a tier. The tier sets its quality and puts a word in its name.

| Tier | Share | Quality | Weapon words | Armour words | Jewellery words |
|---|---|---|---|---|---|
| Shoddy | 30% | 85-88 | Chipped, Dulled, Bent, Notched | Frayed, Dented, Patched, Scuffed | Tarnished, Scratched, Cloudy |
| Plain | 40.5% | 89-92 | - | - | - |
| Fine | 20% | 93-95 | Keen, Balanced, Honed | Sturdy, Fitted, Reinforced | Polished, Bright |
| Superior | 8% | 96-98 | Masterwork, Tempered | Masterwork, Warded | Masterwork, Gleaming |
| Legendary | 1.5% | 99-100 | own name | own name | own name |

- Superior and Legendary drops carry one more bonus line from your class's pool.
- A Legendary drop gets a name of its own: a hero of its realm and a word for its kind ("Brannoc's Reaver"), or its kind
  and a place ("Aegis of Connacht"). Its description keeps what it is ("Heroic Spell-forged Broadsword"). Everyone near
  sees "Legendary!" in the chat. Legendary drops also get the special-loot treatment (ToA bonuses, a finish).
- One Legendary weapon in ten is an **heirloom**: it counts its kills and grows +1 on its first bonus at 100, 500 and
  2,000 kills.
- Named monsters' drops and event rewards keep their own names; their quality word goes in the description.

## Forged drops

3% of Fine, 10% of Superior and 35% of Legendary weapons and body armour are forged: they carry a proc, and a word says
which. A weapon's glow is its proc's (the client's own weapon effects, picked from the weapon family's rows), so a
glowing weapon always has a proc, and a proc weapon always glows - named and event weapons too.

| Proc | Word | Glow |
|---|---|---|
| Fire / frost / spark damage (spells 8100-8127) | Spell-forged | flame, frost, spark |
| Lifetap (8010-8017) | Blood-forged | red |
| Snare, 35% for 8 s (8130-8137) | Rune-forged | blue / purple / green runes |
| Heal or ablative on body armour (8030 / 8040) | Blessed | (armour doesn't glow) |

## Looks and dyes

- Fine drops take the model of a plain item 5-10 levels higher; Superior and Legendary 10-25 higher. End-game looks
  (level 48+, epic, dragon, Atlantean, champion ...) are never picked.
- 15% of Superior and 40% of Legendary drops come dyed in an ordinary colour.
- **Dye drops:** about one kill in 150 (one in 90 for humanoids) drops an ordinary dye - cloth, leather or enamel, never
  a crafted-only one; the richer colours come at higher levels. **Use** a dye: the pieces you wear that take it are
  offered (cloth dye on cloth, leather dye on leather / studded / reinforced, enamel on metal and weapons).

## Other drops

- **Trophies:** about one kill in five (always from a named monster) drops a stackable trophy named after it ("Grey
  Wolf Pelt", "Grimwold's Tusk"); any merchant buys them.
- **Treasure maps:** about one kill in 400. Use one out in the wild: a chest is placed somewhere 1,500-9,000 units away
  in the same zone and marked on your map.
- **Novelty potions:** about the dye rate. They change how you look or move, never how strong you are:

| Potion | Effect | Time |
|---|---|---|
| Draught of the Wee Folk | two-thirds your size | 10 min |
| Giant's Brew | a third bigger (held lower in dungeons) | 10 min |
| Beast Tonic | a fixed list of shapes: wolf, bear, boar, badger, skeleton, and one of your realm's (goblin, snow cat, brownie) | 5 min |
| Shadowmilk | stealth as a stealther of your level has it (monsters well above you still find you); your companion hides too | 2 min |
| Feather Draught | a higher jump and no falling damage | 5 min |
| Glowcap Juice | a soft glow in a random colour | 15 min |
| Bubbling Flask | unlabelled: one of the above, or a harmless backfire (hiccups, a puff of smoke, a minute very small). A merchant names your flasks for 5 silver each: `/identify` | - |

They end when you change region or die. Your companion has a word for each.

## Marks of Valor and the Quartermasters

A **Quartermaster of Valor** stands beside a merchant in every town and capital (62 at the last count). Prices in
marks:

| Item | Marks |
|---|---|
| Fine armour piece fitted to your class and level (5-level steps): helm, chest, sleeves, gloves, leggings, boots | 4 |
| Fine weapon fitted to your class and level | 6 |
| Healing or power draught for your level | 1 |
| A satchel of dye (an ordinary colour) | 1 |
| Elixir of Strength / Fortitude / Dexterity (20 min) | 2 |
| Any novelty potion | 2 |
| Companion Kit Token (refits your companion's own kit at your level) | 10 |
| Single-line respec stone | 25 |

Marks come from events (as before), a named monster near your level (1), every 10 kills that aren't grey (1) and every
story quest done at your level (2, or 3 from level 30).

## Testing (GM)

- `/mob viewloot random inv` on a targeted monster rolls its loot into your bags (with the tiers and extras).
- `/item create novelty_flask 5`, `/item create loot_treasure_map`, `/item create event_mark 30` and so on.
- Unit tests: `dotnet test Tests/Tests.csproj --filter UT_LootOverhaul`.
