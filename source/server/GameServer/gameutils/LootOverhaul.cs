using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.Logging;

namespace DOL.GS
{
    /// <summary>
    /// The loot overhaul (owner 2026-11-18, "Loot Overhaul &amp; Mark of Valor Merchants - Proposal", every proposal agreed):
    ///  - every random armour / weapon / jewel drop (a ROG) rolls a quality tier - Shoddy 30%, Plain 40%, Fine 20%,
    ///    Superior 8%, Legendary 1.5% - and wears its tier's word ("Notched Broadsword", "Masterwork Broadsword");
    ///    Superior and Legendary carry one more bonus line; Legendary ones get a name of their own ("Brannoc's Reaver");
    ///  - forged drops: 3% of Fine, 10% of Superior, 35% of Legendary weapons and body armour carry a proc, and a
    ///    weapon's glow is its proc's (fire, frost, spark - Spell-forged; lifetap - Blood-forged; snare - Rune-forged;
    ///    body armour's heal / ablative - Blessed); a proc weapon always glows, a glowing one always has a proc;
    ///  - looks: Fine takes the model of a plain item 5-10 levels up, Superior and Legendary 10-25 up; the end-game sets
    ///    are never picked; Superior (15%) and Legendary (40%) drops can come dyed in an ordinary colour;
    ///  - extras on a kill (LootOverhaul.ForKill): dyes, novelty potions (NoveltyPotions.cs), monster trophies and
    ///    treasure maps (LootUses.cs).
    /// </summary>
    public static class LootOverhaul
    {
        private static readonly Logger log = LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        public enum Tier { Shoddy, Plain, Fine, Superior, Legendary }

        // per thousand drops, and each tier's quality
        private static readonly (Tier Tier, int Per1000, int QLo, int QHi)[] Tiers =
        [
            (Tier.Shoddy, 300, 85, 88), (Tier.Plain, 405, 89, 92), (Tier.Fine, 200, 93, 95),
            (Tier.Superior, 80, 96, 98), (Tier.Legendary, 15, 99, 100),
        ];

        public static Tier RollTier()
        {
            int r = Util.Random(0, 999);
            foreach (var t in Tiers)
            {
                if (r < t.Per1000)
                    return t.Tier;
                r -= t.Per1000;
            }
            return Tier.Plain;
        }

        public static Tier TierOf(int quality) => quality >= 99 ? Tier.Legendary : quality >= 96 ? Tier.Superior :
            quality >= 93 ? Tier.Fine : quality >= 89 ? Tier.Plain : Tier.Shoddy;

        private static readonly Dictionary<Tier, string[]> WeaponWords = new()
        {
            [Tier.Shoddy] = ["Chipped", "Dulled", "Bent", "Notched"],
            [Tier.Fine] = ["Keen", "Balanced", "Honed"],
            [Tier.Superior] = ["Masterwork", "Tempered"],
            [Tier.Legendary] = ["Heroic", "Storied"],
        };
        private static readonly Dictionary<Tier, string[]> ArmorWords = new()
        {
            [Tier.Shoddy] = ["Frayed", "Dented", "Patched", "Scuffed"],
            [Tier.Fine] = ["Sturdy", "Fitted", "Reinforced"],
            [Tier.Superior] = ["Masterwork", "Warded"],
            [Tier.Legendary] = ["Heroic", "Storied"],
        };
        private static readonly Dictionary<Tier, string[]> JewelWords = new()
        {
            [Tier.Shoddy] = ["Tarnished", "Scratched", "Cloudy"],
            [Tier.Fine] = ["Polished", "Bright"],
            [Tier.Superior] = ["Masterwork", "Gleaming"],
            [Tier.Legendary] = ["Heroic", "Storied"],
        };

        /// <summary>Every word a tier puts on a name (the client's loot beams and tooltips read them too).</summary>
        public static readonly HashSet<string> AllWords = new(WeaponWords.Values.Concat(ArmorWords.Values).Concat(JewelWords.Values)
            .SelectMany(w => w).Concat(["Spell-forged", "Blood-forged", "Rune-forged", "Blessed"]), StringComparer.OrdinalIgnoreCase);

        public static bool IsWeapon(DbItemTemplate t) => t.Object_Type >= (int) eObjectType._FirstWeapon && t.Object_Type <= (int) eObjectType._LastWeapon
            && t.Object_Type != (int) eObjectType.Shield;
        public static bool IsArmor(DbItemTemplate t) => t.Object_Type >= (int) eObjectType._FirstArmor && t.Object_Type <= (int) eObjectType._LastArmor
            || t.Object_Type == (int) eObjectType.Shield;

        public static string Word(Tier tier, DbItemTemplate t)
        {
            var words = IsWeapon(t) ? WeaponWords : IsArmor(t) ? ArmorWords : JewelWords;
            return words.TryGetValue(tier, out string[] w) ? w[Util.Random(0, w.Length - 1)] : null;
        }

        /// <summary>A random drop made over by its tier: its quality, its word, a bonus line, maybe a proc and its glow,
        /// a better model, a dye; a Legendary one its own name. Returns the tier.</summary>
        public static Tier Apply(GeneratedUniqueItem g, GamePlayer taker)
        {
            Tier tier = RollTier();
            var row = Tiers.First(x => x.Tier == tier);
            g.Quality = Util.Random(row.QLo, row.QHi);
            int level = Math.Clamp(g.Level, 1, 50);
            g.Price = Money.SetAutoPrice(g.Level, g.Quality);
            bool weapon = IsWeapon(g), armor = IsArmor(g);
            string baseName = g.Name;
            try
            {
                if (tier >= Tier.Superior && taker != null)
                    SpecialLoot.AddOneBonus(g, taker, level);
                string forged = null;
                int forgeChance = tier switch { Tier.Fine => 3, Tier.Superior => 10, Tier.Legendary => 35, _ => 0 };
                if ((weapon || armor && g.Item_Type == Slot.TORSO) && g.Object_Type != (int) eObjectType.Shield && Util.Chance(forgeChance))
                    forged = Forge(g, level, weapon);
                if (weapon || armor)
                {
                    if (tier == Tier.Fine)
                        SpecialLoot.BetterLook(g, level, 5, 10);
                    else if (tier >= Tier.Superior)
                        SpecialLoot.BetterLook(g, level, 10, 25);
                    int dyeChance = tier switch { Tier.Superior => 15, Tier.Legendary => 40, _ => 0 };
                    if (g.Color == 0 && Util.Chance(dyeChance))
                        g.Color = DyeColorFor(g, level);
                }
                if (tier == Tier.Legendary)
                {
                    g.Name = LegendaryNames.Make((eRealm) g.Realm, g);
                    g.Description = $"{Word(tier, g)} {(forged != null ? forged + " " : "")}{baseName}".Trim();
                }
                else
                {
                    string word = Word(tier, g);
                    g.Name = string.Join(" ", new[] { word, forged, baseName }.Where(s => !string.IsNullOrEmpty(s)));
                }
            }
            catch (Exception e)
            {
                log.Error($"LootOverhaul.Apply {g.Name}", e);
            }
            return tier;
        }

        /// <summary>A named monster's drop or an event reward: its quality word in its description (its name is its own).</summary>
        public static void MarkQuality(DbItemTemplate t)
        {
            if (t == null || t.IsStackable || !(IsWeapon(t) || IsArmor(t)) || t.Quality <= 0)
                return;
            string w = Word(TierOf(t.Quality), t);
            if (w != null && (t.Description == null || !t.Description.Contains(w)))
                t.Description = string.IsNullOrEmpty(t.Description) ? $"{w} quality." : $"{w} quality. {t.Description}";
        }

        // ---------------------------------------------------------------- forging: a proc and its glow

        public const int ProcHeat = 8100, ProcCold = 8110, ProcEnergy = 8120, ProcSnare = 8130;   // + band 0..7 (LootOverhaulDatabase)
        public const int ProcLifetap = 8010, ProcHeal = 8030, ProcAblative = 8040;

        public static int Band(int level) => level < 10 ? 0 : level < 15 ? 1 : level < 20 ? 2 : level < 25 ? 3 : level < 30 ? 4 : level < 35 ? 5 : level < 40 ? 6 : 7;
        public static readonly int[] BandLevel = [1, 10, 15, 20, 25, 30, 35, 40];

        /// <summary>A proc and, on a weapon, the glow that goes with it. Returns the name word.</summary>
        public static string Forge(DbItemTemplate u, int level, bool weapon)
        {
            int band = Band(level);
            string word;
            char glow;
            if (!weapon)
            {
                u.ProcSpellID = (Util.Chance(50) ? ProcHeal : ProcAblative) + band;
                word = "Blessed";
                glow = '\0';
            }
            else
            {
                int r = Util.Random(0, 99);
                if (r < 50)
                {
                    int kind = Util.Random(0, 2);
                    u.ProcSpellID = (kind == 0 ? ProcHeat : kind == 1 ? ProcCold : ProcEnergy) + band;
                    glow = kind == 0 ? 'F' : kind == 1 ? 'C' : 'E';
                    word = "Spell-forged";
                }
                else if (r < 75)
                {
                    u.ProcSpellID = ProcLifetap + band;
                    glow = 'B';
                    word = "Blood-forged";
                }
                else
                {
                    u.ProcSpellID = ProcSnare + band;
                    glow = 'R';
                    word = "Rune-forged";
                }
            }
            u.ProcChance = 10;
            u.LevelRequirement = Math.Max(u.LevelRequirement, BandLevel[band]);
            if (weapon)
                u.Effect = GlowFor(u, glow);
            return word;
        }

        // spweapons.csv rows 1-94 by what they look like (build_weapon_effects.py names): Fire, Cold, Energy (sparks, mana,
        // blue heat), Blood (red, black), Rune (blue / purple / silver / green / gold glows)
        private const string GlowKinds = "FFFFFFFFREFFBCCERBERFFFFCCCBBFRRRBFFFFRRRREEEEFFFFERFRCFFFFCCREERRFFCRBRBCRBFRFBRRCEFFRRRRRRRB";
        private static readonly Dictionary<char, string> GlowFallback = new()
        {
            ['F'] = "FBR", ['C'] = "CER", ['E'] = "ERC", ['B'] = "BFR", ['R'] = "REC",
        };

        /// <summary>The glow of a proc's kind from the weapon family's own rows (the nearest kind when it has none).</summary>
        public static int GlowFor(DbItemTemplate u, char kind)
        {
            (int lo, int hi) = SpecialLoot.EffectRange((eObjectType) u.Object_Type, u.Item_Type == Slot.TWOHAND || u.Hand == 1);
            if (hi <= 0)
                return u.Effect;
            foreach (char k in GlowFallback.TryGetValue(kind, out string order) ? order : "R")
            {
                var fit = Enumerable.Range(lo, hi - lo + 1).Where(id => id - 1 < GlowKinds.Length && GlowKinds[id - 1] == k).ToList();
                if (fit.Count > 0)
                    return fit[Util.Random(0, fit.Count - 1)];
            }
            return Util.Random(lo, hi);
        }

        /// <summary>The glow kind of a proc spell (for the special loot's finish).</summary>
        public static char KindOfProc(int procSpellId) => procSpellId switch
        {
            >= ProcHeat and < ProcHeat + 8 => 'F',
            >= ProcCold and < ProcCold + 8 => 'C',
            >= ProcEnergy and < ProcEnergy + 8 => 'E',
            >= ProcSnare and < ProcSnare + 8 => 'R',
            >= ProcLifetap and < ProcLifetap + 8 => 'B',
            >= 8020 and < 8028 => 'F',
            _ => "FCEBR"[Math.Abs(procSpellId) % 5],
        };

        // ---------------------------------------------------------------- dyes

        private static List<DbItemTemplate> _dyes;
        private static readonly object DyeLock = new();

        /// <summary>The ordinary dyes (the dye merchants' list - never the crafted-only ones): cloth, leather, enamel.</summary>
        public static List<DbItemTemplate> Dyes()
        {
            lock (DyeLock)
            {
                if (_dyes != null)
                    return _dyes;
                _dyes = [];
                try
                {
                    foreach (var mi in GameServer.Database.SelectObjects<DbMerchantItem>(DB.Column("ItemListID").IsEqualTo("housing_dye")))
                        if (GameServer.Database.FindObjectByKey<DbItemTemplate>(mi.ItemTemplateID) is DbItemTemplate t && t.Color > 0)
                            _dyes.Add(t);
                }
                catch (Exception e)
                {
                    log.Warn($"LootOverhaul: dyes: {e.Message}");
                }
                return _dyes;
            }
        }

        public const int ClothDyeModel = 229, LeatherDyeModel = 494, EnamelModel = 495;

        public static bool IsDye(DbItemTemplate t) => t != null && t.Object_Type == 0 && t.Item_Type == 40 &&
            t.Model is ClothDyeModel or LeatherDyeModel or EnamelModel && t.Color > 0;

        /// <summary>Which dye goes on an item: cloth dye on cloth, leather dye on leather and studded / reinforced, enamel on
        /// metal armour and weapons.</summary>
        public static int DyeModelFor(DbItemTemplate t)
        {
            if (IsWeapon(t) || t.Object_Type == (int) eObjectType.Shield)
                return EnamelModel;
            return (eObjectType) t.Object_Type switch
            {
                eObjectType.Cloth => ClothDyeModel,
                eObjectType.Leather or eObjectType.Studded or eObjectType.Reinforced => LeatherDyeModel,
                _ => t.Item_Type == Slot.CLOAK ? ClothDyeModel : EnamelModel,
            };
        }

        /// <summary>A colour the drop could have been dyed with: the cheaper colours at low level, the richer ones higher up.</summary>
        public static int DyeColorFor(DbItemTemplate t, int level)
        {
            DbItemTemplate d = PickDye(DyeModelFor(t), level);
            return d?.Color ?? 0;
        }

        public static DbItemTemplate PickDye(int model, int level)
        {
            long cap = level < 15 ? 1_375 : level < 30 ? 6_875 : level < 40 ? 33_000 : long.MaxValue;
            var pool = Dyes().Where(d => (model == 0 || d.Model == model) && d.Price <= cap).ToList();
            if (pool.Count == 0)
                pool = Dyes().Where(d => model == 0 || d.Model == model).ToList();
            return pool.Count == 0 ? null : pool[Util.Random(0, pool.Count - 1)];
        }

        // ---------------------------------------------------------------- extras on a kill

        /// <summary>What a kill drops besides its loot table: a dye now and then (humanoids more often), a novelty potion,
        /// a monster trophy, rarely a treasure map. Nothing from a grey monster.</summary>
        public static List<DbItemTemplate> ForKill(GameNPC mob, GameObject killer)
        {
            var out_ = new List<DbItemTemplate>();
            try
            {
                if (mob == null || mob.Realm != eRealm.None)
                    return out_;
                GameLiving owner = killer as GameLiving;
                if (owner is GameNPC npc && npc.Brain is DOL.AI.Brain.IControlledBrain cb && cb.GetPlayerOwner() is GamePlayer po)
                    owner = po;
                if (owner is not GamePlayer player)
                    return out_;
                if (LevelScaling.LootCon(player, mob) <= -3)
                    return out_;
                int level = Math.Clamp((int) mob.Level, 1, 50);
                bool humanoid = mob.BodyType == (ushort) NpcTemplateMgr.eBodyType.Humanoid;
                if (Util.Random(0, humanoid ? 89 : 149) == 0 && PickDye(0, level) is DbItemTemplate dye)
                    out_.Add(dye);
                if (Util.Random(0, humanoid ? 89 : 149) == 0 && NoveltyPotions.RandomDrop() is DbItemTemplate potion)
                    out_.Add(potion);
                bool named = LootUses.IsNamed(mob);
                if ((named || Util.Chance(22)) && LootUses.Trophy(mob) is DbItemTemplate trophy)
                    out_.Add(trophy);
                if (Util.Random(0, 399) == 0 && LootUses.MapTemplate() is DbItemTemplate map)
                    out_.Add(map);
            }
            catch (Exception e)
            {
                log.Error($"LootOverhaul.ForKill {mob?.Name}", e);
            }
            return out_;
        }

        /// <summary>A good drop on the ground: its light column for the new client ("#BEAM|oid|tier": 3 Superior, 4 Legendary).</summary>
        public static void Beam(GameObject item, Tier tier, IEnumerable<GamePlayer> near)
        {
            if (item == null || tier < Tier.Superior)
                return;
            foreach (GamePlayer p in near)
                NewClient.Send(p, $"#BEAM|{item.ObjectID}|{(int) tier}");
        }
    }

    /// <summary>A Legendary drop's own name (owner: "randomly generated if you can make that work"): a hero of its realm
    /// and a word for its kind ("Brannoc's Reaver"), or its kind and a place of the realm ("Aegis of Connacht").</summary>
    public static class LegendaryNames
    {
        private static readonly Dictionary<eRealm, string[]> Heroes = new()
        {
            [eRealm.Albion] = ["Brannoc", "Gawain", "Elowen", "Tristram", "Morwenna", "Cador", "Isolde", "Bedwyr", "Rhosyn", "Aldric", "Gwenllian", "Percivale"],
            [eRealm.Midgard] = ["Ragnvald", "Sigrun", "Hakon", "Astrid", "Brynjar", "Thyra", "Ulfgar", "Solveig", "Eirik", "Gudrun", "Hrolf", "Ingrid"],
            [eRealm.Hibernia] = ["Fionnlagh", "Aoife", "Cathal", "Niamh", "Diarmuid", "Siobhan", "Ruadhan", "Eithne", "Conall", "Grainne", "Brannagh", "Oisin"],
        };
        private static readonly Dictionary<eRealm, string[]> Places = new()
        {
            [eRealm.Albion] = ["Camelot", "the Black Mountains", "Avalon", "Lyonesse", "Salisbury", "the Pennines", "Llyn Barfog"],
            [eRealm.Midgard] = ["Jordheim", "Myrkwood", "Vanern", "Uppland", "Muspelheim", "Raumarik", "Skona"],
            [eRealm.Hibernia] = ["Tir na Nog", "Connacht", "Lough Derg", "Bri Leith", "Cruachan", "Sheeroe", "Emain Macha"],
        };
        private static readonly string[] WeaponNouns = ["Reaver", "Edge", "Fang", "Thorn", "Bane", "Song", "Wrath", "Oath", "Fury", "Sorrow"];
        private static readonly string[] ArmorNouns = ["Aegis", "Mantle", "Guard", "Ward", "Embrace", "Bulwark", "Vigil"];
        private static readonly string[] JewelNouns = ["Charm", "Token", "Tear", "Promise", "Star", "Heart", "Whisper"];

        public static string Make(eRealm realm, DbItemTemplate t)
        {
            if (!Heroes.ContainsKey(realm))
                realm = eRealm.Albion;
            string[] nouns = LootOverhaul.IsWeapon(t) ? WeaponNouns : LootOverhaul.IsArmor(t) ? ArmorNouns : JewelNouns;
            string noun = nouns[Util.Random(0, nouns.Length - 1)];
            return Util.Chance(65)
                ? $"{Heroes[realm][Util.Random(0, Heroes[realm].Length - 1)]}'s {noun}"
                : $"{noun} of {Places[realm][Util.Random(0, Places[realm].Length - 1)]}";
        }
    }
}
