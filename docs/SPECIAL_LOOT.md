# Special loot: named drops, event rewards and rare random drops

Owner (2026-11-02, "Item and weapon bonuses"): named mob drops, event drops and rare random drops should carry
Trials-of-Atlantis bonuses (a lower factor at lower levels), be usable by the character who gets them, have random
weapon dyes and matching weapon effects, better models at higher levels and procs on basically every special drop.

`server/GameServer/gameutils/SpecialLoot.cs` does it at the moment a drop is made for a player:

| where | what counts as special |
|---|---|
| `AbstractServerRules.DropLoot` (every monster kill) | a named unique (`Id_nb` `nu<zone>_...`, `tools/claude-version/named_uniques.py`, level versions included) or a random object (ROG) rolled at quality 99 (the top of the ROG's 95-99: about one in five ROGs) |
| `DynamicEventRuntime` stage rewards | every item reward |

The taker is the killer, or the first player among the loot owners; a drop taken by a bot is left as it is.

What `SpecialLoot.Enrich` does, in order:

1. **Fit the class.** When the taker can't use the drop at all (`HasAbilityToUseItem`: a hammer for a Blademaster,
   chain for a Druid) it is rolled afresh for the class at the drop's level - the ROG generator with its ToA pass
   (`GeneratedUniqueItem(toa: true, ...)`): the class's armour type in the same slot, or the class's weapon kind -
   keeping the drop's name, lore and proc. Otherwise the drop becomes a one-off copy (`DbItemUnique`) of its template,
   saved with the inventory item like any ROG.
2. **ToA bonuses** on the free bonus lines (templates carry ten): 1 under level 20, up to 2 under 35, up to 3 under 45,
   3 from 45. Each is a share of the ToA cap scaled by `Factor(level)` = level / 50 (0.15 at the bottom): a level-10
   drop carries +1 melee damage, a level-50 one +3 to +5. The pool follows the class: archers (Scout, Hunter, Ranger)
   archery speed / damage / range, dex and qui caps; healers (Cleric, Friar, Healer, Shaman, Druid, Bard, Warden)
   healing and buff effectiveness, power pool, casting speed; list casters spell damage, casting speed, range, power
   pool, duration, acuity cap; everyone else melee damage / speed, style damage, str / con / dex caps, fatigue - with
   hits cap and resist pierce in most pools. Hybrids with a mana stat draw from the caster pool two rolls in five.
3. **A proc** on every special weapon and body armour that has none: the ROG proc spells by level band (8010+ lifetap /
   8020+ direct damage on weapons, 8030+ heal / 8040+ ablative on torso), 10% chance, the band's level requirement.
4. **A finish** on weapons: a luster (bronze .. adamantium by level) or an enamel, likelier with level (a third at 10,
   always at 40); from level 15 a glow from the weapon family's `spweapons.csv` rows (`build_weapon_effects.py`:
   longsword 1-20, two-hander 21-33, hammer 34-43, crusher 44-55, axe 56-66, short sword 67-73, battle spear 74-80,
   lugged spear 81-89, staff 90-94) - drawn in hand only (`player.gd` `dress`).
5. **A better look** from level 20, with `Factor` as the chance: the model of a plain item of the same kind, slot and
   realm 10 to 25 levels above (within 50), so a mid-level named sword doesn't look like the smith's starter blade.

Tests: `server/Tests/UnitTests/UT_SpecialLoot.cs` (`dotnet test ... --filter UT_SpecialLoot`).

Tuning: `SpecialLoot.RARE_ROG_QUALITY`, the pools and their tops, `Factor`. Nothing is read from the database at
load; the better-look pools are queried once per (kind, slot, realm) and cached.
