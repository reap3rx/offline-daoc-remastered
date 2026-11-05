using System;
using System.Collections.Generic;
using DOL.Database;
using System.Reflection;
using System.Threading;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// Special drops made worth having (owner 2026-11-02, "Item and weapon bonuses"): a named monster's drop, an event
    /// reward and a rare random drop come back as a one-off item the taker can use, with
    ///  - Trials-of-Atlantis bonuses (melee / spell / archery damage and speed, healing, power pool, stat caps ...) from
    ///    the taker's class's pool, fewer and smaller at low level (SpecialLoot.Factor);
    ///  - a proc when it has none (the ROG proc spells 8010+ / 8020+ for weapons, 8030+ / 8040+ for body armour);
    ///  - a weapon luster or enamel and a matching glow (spweapons.csv effects 1-94 by weapon family), likelier as the
    ///    level rises;
    ///  - at higher levels, the look of a higher-level item of its kind (the plain starter models stay on low loot);
    ///  - when the taker's class can't use it at all (a hammer for a Blademaster, chain for a Druid), a fresh item of the
    ///    class's kind in the same slot, keeping the drop's name and lore.
    /// Applied in AbstractServerRules.DropLoot (named "nu*" templates and 99-quality ROGs) and the dynamic events'
    /// rewards (DynamicEventRuntime). docs/LEVEL_BANDS.md.
    /// </summary>
    public static class SpecialLoot
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public const int RARE_ROG_QUALITY = 99;        // a random drop rolled this good (the top of the ROG's 95-99: one in five) is a "rare" one

        /// <summary>A drop that deserves it: a named unique (named_uniques.py, Id_nb nu&lt;zone&gt;_...) or a rare ROG.</summary>
        public static bool IsSpecial(DbItemTemplate t) =>
            t != null && (t.Id_nb?.StartsWith("nu", StringComparison.OrdinalIgnoreCase) == true && t.Id_nb.Length > 4 && char.IsDigit(t.Id_nb[2])
                          || t is GeneratedUniqueItem g && g.Quality >= RARE_ROG_QUALITY);

        /// <summary>How much of the top-level treatment a drop gets: 0.2 at level 10, 1 at 50.</summary>
        public static double Factor(int level) => Math.Clamp(level / 50.0, 0.15, 1.0);

        /// <summary>The drop, enriched for its taker - a new one-off template (DbItemUnique) the inventory saves with the
        /// item - or the template itself when nothing applies (no player taker, money, stackables).</summary>
        public static DbItemTemplate Enrich(DbItemTemplate t, GamePlayer taker, string why)
        {
            if (t == null || taker == null || t.IsStackable || t.MaxCount > 1 || GameMoney.IsItemMoney(t.Name))
                return t;
            try
            {
                int level = Math.Clamp(t.Level > 0 ? t.Level : taker.Level, 1, 51);
                DbItemUnique u = Fit(t, taker, level);
                bool weapon = u.Object_Type >= (int) eObjectType._FirstWeapon && u.Object_Type <= (int) eObjectType._LastWeapon;
                bool armor = u.Object_Type >= (int) eObjectType._FirstArmor && u.Object_Type <= (int) eObjectType._LastArmor;
                AddToaBonuses(u, taker, level);
                if (u.ProcSpellID == 0 && (weapon || armor && u.Item_Type == Slot.TORSO))
                    AddProc(u, level, weapon);
                if (weapon)
                    Finish(u, level);
                if (Util.Chance((int) Math.Round(Factor(level) * 100)) && (weapon || armor) && level >= 20)
                    BetterLook(u, level);
                u.Description = string.IsNullOrEmpty(u.Description) ? why : u.Description;
                u.AllowAdd = true;          // saved with the item (the inventory row's relation, UTemplate_Id): without it
                                            // the unique is never written and the item is a blank after a restart
                return u;
            }
            catch (Exception e)
            {
                log.Error($"SpecialLoot: {t.Id_nb} for {taker.Name}", e);
                return t;
            }
        }

        /// <summary>The drop as a one-off, remade for the taker's class when they couldn't use it: an armour piece of
        /// the class's armour type in the same slot, a weapon of the class's weapon type - the ROG's roll at this level,
        /// with ToA stats, keeping the drop's name, lore and proc.</summary>
        private static DbItemUnique Fit(DbItemTemplate t, GamePlayer taker, int level)
        {
            bool weapon = t.Object_Type >= (int) eObjectType._FirstWeapon && t.Object_Type <= (int) eObjectType._LastWeapon;
            bool armor = t.Object_Type >= (int) eObjectType._FirstArmor && t.Object_Type <= (int) eObjectType._LastArmor;
            if ((weapon || armor) && !taker.HasAbilityToUseItem(t))
            {
                eCharacterClass cls = (eCharacterClass) taker.CharacterClass.ID;
                eObjectType type;
                eInventorySlot slot;
                if (armor)
                {
                    type = taker.Realm switch
                    {
                        eRealm.Albion => GeneratedUniqueItem.GetAlbionArmorType(cls, (byte) level),
                        eRealm.Midgard => GeneratedUniqueItem.GetMidgardArmorType(cls, (byte) level),
                        _ => GeneratedUniqueItem.GetHiberniaArmorType(cls, (byte) level)
                    };
                    slot = (eInventorySlot) t.Item_Type;
                }
                else
                {
                    type = taker.Realm switch
                    {
                        eRealm.Albion => GeneratedUniqueItem.GetAlbionWeapon(cls),
                        eRealm.Midgard => GeneratedUniqueItem.GetMidgardWeapon(cls),
                        _ => GeneratedUniqueItem.GetHiberniaWeapon(cls)
                    };
                    slot = GeneratedUniqueItem.GenerateItemType(type);
                }
                GeneratedUniqueItem g = new(true, taker.Realm, cls, (byte) level, type, slot);
                g.Name = t.Name;
                g.Description = t.Description;
                g.Quality = Math.Max(g.Quality, Math.Min(99, t.Quality));
                if (t.ProcSpellID > 0 && ((g.Object_Type >= (int) eObjectType._FirstWeapon && g.Object_Type <= (int) eObjectType._LastWeapon) || g.Item_Type == Slot.TORSO))
                {
                    g.ProcSpellID = t.ProcSpellID;
                    g.ProcChance = (byte) (t.ProcChance > 0 ? t.ProcChance : 10);
                }
                g.CanDropAsLoot = t.CanDropAsLoot;
                return g;
            }
            return t is DbItemUnique u && !u.IsPersisted ? u : new DbItemUnique(t);
        }

        // ---- Trials of Atlantis bonuses -------------------------------------------------------------------------------

        private enum Kind { Melee, Caster, Healer, Archer }

        private static readonly HashSet<eCharacterClass> Healers = new()
        {
            eCharacterClass.Cleric, eCharacterClass.Friar, eCharacterClass.Healer, eCharacterClass.Shaman,
            eCharacterClass.Druid, eCharacterClass.Bard, eCharacterClass.Warden
        };

        private static readonly HashSet<eCharacterClass> Archers = new()
        {
            eCharacterClass.Scout, eCharacterClass.Hunter, eCharacterClass.Ranger
        };

        // (property, top value at level 50): the ToA caps are 10% for damage / speed / range, 25% for healing, buffs and
        // power pool, 26 stat cap, 400 hits cap, 50 power cap - one item carries a share of each
        private static readonly (eProperty, int)[] MeleePool =
        {
            (eProperty.MeleeDamage, 5), (eProperty.MeleeSpeed, 5), (eProperty.StyleDamage, 5), (eProperty.StrCapBonus, 6),
            (eProperty.ConCapBonus, 6), (eProperty.DexCapBonus, 5), (eProperty.MaxHealthCapBonus, 40), (eProperty.FatigueConsumption, 5),
            (eProperty.ResistPierce, 4)
        };

        private static readonly (eProperty, int)[] CasterPool =
        {
            (eProperty.SpellDamage, 5), (eProperty.CastingSpeed, 5), (eProperty.SpellRange, 5), (eProperty.PowerPool, 10),
            (eProperty.SpellDuration, 8), (eProperty.DebuffEffectiveness, 6), (eProperty.AcuCapBonus, 6), (eProperty.PowerPoolCapBonus, 5),
            (eProperty.MaxHealthCapBonus, 40), (eProperty.ResistPierce, 4)
        };

        private static readonly (eProperty, int)[] HealerPool =
        {
            (eProperty.HealingEffectiveness, 10), (eProperty.BuffEffectiveness, 8), (eProperty.PowerPool, 10), (eProperty.CastingSpeed, 5),
            (eProperty.SpellDuration, 8), (eProperty.SpellRange, 5), (eProperty.AcuCapBonus, 6), (eProperty.PowerPoolCapBonus, 5),
            (eProperty.MaxHealthCapBonus, 40)
        };

        private static readonly (eProperty, int)[] ArcherPool =
        {
            (eProperty.ArcherySpeed, 5), (eProperty.RangedDamage, 5), (eProperty.ArcheryRange, 5), (eProperty.DexCapBonus, 6),
            (eProperty.StyleDamage, 5), (eProperty.MeleeDamage, 4), (eProperty.QuiCapBonus, 5), (eProperty.MaxHealthCapBonus, 40),
            (eProperty.FatigueConsumption, 5)
        };

        private static (eProperty, int)[] PoolFor(GamePlayer p)
        {
            eCharacterClass cls = (eCharacterClass) p.CharacterClass.ID;
            if (Archers.Contains(cls))
                return ArcherPool;
            if (Healers.Contains(cls))
                return HealerPool;
            if (p.CharacterClass.ClassType == eClassType.ListCaster)
                return CasterPool;
            // a hybrid with a mana stat (Thane, Champion, Reaver, Spiritmaster-ish): half its rolls from the caster pool
            if (p.CharacterClass.ClassType == eClassType.Hybrid && p.CharacterClass.ManaStat != eStat.UNDEFINED && Util.Chance(40))
                return CasterPool;
            return MeleePool;
        }

        /// <summary>1 bonus under level 20, up to 2 under 35, up to 3 under 45, 3 from 45 - each a share of the ToA cap
        /// scaled by Factor, on the item's free bonus lines (templates carry ten).</summary>
        public static void AddToaBonuses(DbItemTemplate u, GamePlayer taker, int level)
        {
            int count = level < 20 ? 1 : level < 35 ? Util.Random(1, 2) : level < 45 ? Util.Random(2, 3) : 3;
            double f = Factor(level);
            (eProperty, int)[] pool = PoolFor(taker);
            List<int> order = new();
            for (int i = 0; i < pool.Length; i++)
                order.Add(i);
            for (int i = order.Count - 1; i > 0; i--)       // shuffle
            {
                int j = Util.Random(0, i);
                (order[i], order[j]) = (order[j], order[i]);
            }
            int added = 0;
            foreach (int i in order)
            {
                if (added >= count)
                    break;
                (eProperty prop, int top) = pool[i];
                if (Has(u, prop))
                    continue;
                int amount = Math.Max(1, (int) Math.Round(top * f * (0.5 + Util.Random(0, 50) / 100.0)));
                if (!Write(u, prop, amount))
                    break;
                added++;
            }
        }

        private static bool Has(DbItemTemplate u, eProperty prop)
        {
            int p = (int) prop;
            return u.Bonus1Type == p || u.Bonus2Type == p || u.Bonus3Type == p || u.Bonus4Type == p || u.Bonus5Type == p
                || u.Bonus6Type == p || u.Bonus7Type == p || u.Bonus8Type == p || u.Bonus9Type == p || u.Bonus10Type == p;
        }

        private static bool Write(DbItemTemplate u, eProperty prop, int amount)
        {
            int p = (int) prop;
            if (u.Bonus1 == 0) { u.Bonus1 = amount; u.Bonus1Type = p; }
            else if (u.Bonus2 == 0) { u.Bonus2 = amount; u.Bonus2Type = p; }
            else if (u.Bonus3 == 0) { u.Bonus3 = amount; u.Bonus3Type = p; }
            else if (u.Bonus4 == 0) { u.Bonus4 = amount; u.Bonus4Type = p; }
            else if (u.Bonus5 == 0) { u.Bonus5 = amount; u.Bonus5Type = p; }
            else if (u.Bonus6 == 0) { u.Bonus6 = amount; u.Bonus6Type = p; }
            else if (u.Bonus7 == 0) { u.Bonus7 = amount; u.Bonus7Type = p; }
            else if (u.Bonus8 == 0) { u.Bonus8 = amount; u.Bonus8Type = p; }
            else if (u.Bonus9 == 0) { u.Bonus9 = amount; u.Bonus9Type = p; }
            else if (u.Bonus10 == 0) { u.Bonus10 = amount; u.Bonus10Type = p; }
            else return false;
            return true;
        }

        // ---- procs ----------------------------------------------------------------------------------------------------

        /// <summary>The ROG proc spells: 8010-8017 lifetap / 8020-8027 direct damage on a weapon, 8030-8037 heal /
        /// 8040-8047 ablative on body armour, by level band (the band's level is the proc's requirement).</summary>
        public static void AddProc(DbItemTemplate u, int level, bool weapon)
        {
            int band = level < 10 ? 0 : level < 15 ? 1 : level < 20 ? 2 : level < 25 ? 3 : level < 30 ? 4 : level < 35 ? 5 : level < 40 ? 6 : 7;
            int family = weapon ? (Util.Chance(50) ? 8010 : 8020) : (Util.Chance(50) ? 8030 : 8040);
            u.ProcSpellID = family + band;
            u.ProcChance = 10;
            u.LevelRequirement = band == 0 ? 1 : new[] { 1, 10, 15, 20, 25, 30, 35, 40 }[band];
        }

        // ---- finish: luster / enamel and a glow --------------------------------------------------------------------

        private static readonly int[] Lusters = { 16, 17, 18, 19, 20, 21, 22, 25, 26 };              // bronze .. adamantium
        private static readonly int[] Enamels = { 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38 };   // red .. the blues

        /// <summary>A luster or enamel on a special weapon (likelier with level: a third at 10, always at 40) and, from
        /// level 15, a glow from its family's spweapons rows (build_weapon_effects.py: longsword 1-20, two-hander 21-33,
        /// hammer 34-43, crusher 44-55, axe 56-66, short sword 67-73, battle spear 74-80, lugged spear 81-89, staff 90-94).</summary>
        public static void Finish(DbItemTemplate u, int level)
        {
            if (u.Color == 0 && Util.Chance(Math.Min(100, 20 + level * 2)))
                u.Color = level < 25 || Util.Chance(50) ? Lusters[Util.Random(0, Math.Min(Lusters.Length - 1, level / 6))]
                                                        : Enamels[Util.Random(0, Enamels.Length - 1)];
            if (u.Effect == 0 && level >= 15 && Util.Chance(Math.Min(100, level * 2)))
            {
                (int lo, int hi) = EffectRange((eObjectType) u.Object_Type, u.Item_Type == Slot.TWOHAND || u.Hand == 1);
                if (hi > 0)
                    u.Effect = Util.Random(lo, hi);
            }
        }

        public static (int, int) EffectRange(eObjectType type, bool twoHanded)
        {
            switch (type)
            {
                case eObjectType.SlashingWeapon: case eObjectType.ThrustWeapon: case eObjectType.Blades: case eObjectType.Piercing:
                    return (1, 20);
                case eObjectType.Sword:
                    return twoHanded ? (21, 33) : (1, 20);
                case eObjectType.TwoHandedWeapon: case eObjectType.LargeWeapons:
                    return (21, 33);
                case eObjectType.CrushingWeapon: case eObjectType.Blunt:
                    return (34, 43);
                case eObjectType.Hammer:
                    return twoHanded ? (44, 55) : (34, 43);
                case eObjectType.Axe: case eObjectType.LeftAxe:
                    return (56, 66);
                case eObjectType.Spear: case eObjectType.CelticSpear:
                    return (74, 80);
                case eObjectType.PolearmWeapon:
                    return (81, 89);
                case eObjectType.Staff:
                    return (90, 94);
            }
            return (0, 0);
        }

        // ---- a better look --------------------------------------------------------------------------------------------

        private static readonly Dictionary<(int, int, int), List<DbItemTemplate>> _looks = new();
        private static readonly Lock _looksLock = new();

        /// <summary>The model of a higher-level plain item of the same kind, slot and realm (10 to 25 levels up, within
        /// 50), so a level-30 named sword looks like a level-45 one rather than the smith's basic blade.</summary>
        public static void BetterLook(DbItemTemplate u, int level)
        {
            if (level >= 48)
                return;
            List<DbItemTemplate> pool;
            (int, int, int) key = (u.Object_Type, u.Item_Type, u.Realm);
            lock (_looksLock)
            {
                if (!_looks.TryGetValue(key, out pool))
                {
                    pool = new List<DbItemTemplate>();
                    try
                    {
                        WhereClause w = DB.Column("Object_Type").IsEqualTo(u.Object_Type).And(DB.Column("Item_Type").IsEqualTo(u.Item_Type))
                            .And(DB.Column("Model").IsGreaterThan(0)).And(DB.Column("Level").IsGreaterOrEqualTo(25));
                        foreach (DbItemTemplate t in GameServer.Database.SelectObjects<DbItemTemplate>(w))
                            if ((t.Realm == u.Realm || t.Realm == 0) && t.Id_nb?.StartsWith("nu", StringComparison.OrdinalIgnoreCase) != true
                                && t.Id_nb?.Contains('#') != true && t.Id_nb?.StartsWith("Unique_") != true && t.Level <= 50)
                                pool.Add(t);
                    }
                    catch (Exception e)
                    {
                        log.Warn($"SpecialLoot.BetterLook: {key}: {e.Message}");
                    }
                    _looks[key] = pool;
                }
            }
            int lo = level + 10, hi = Math.Min(50, level + 25);
            List<DbItemTemplate> fit = pool.FindAll(t => t.Level >= lo && t.Level <= hi && t.Model != u.Model);
            if (fit.Count == 0)
                return;
            DbItemTemplate pick = fit[Util.Random(0, fit.Count - 1)];
            u.Model = pick.Model;
            if (u.Extension == 0 && pick.Extension > 0)
                u.Extension = pick.Extension;
        }
    }
}
