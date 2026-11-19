using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using DOL.AI.Brain;
using DOL.Events;
using DOL.GS.DynamicEvents;
using DOL.GS.Keeps;
using DOL.GS.ServerProperties;
using DOL.GS.Commands;

namespace DOL.GS
{
    /// <summary>
    /// Fixed con tiers and full scaling (owner 2026-11-18/19, "Purposeful PvE"): ESO-style "One Tamriel" - levels don't
    /// decide where you can go, what you meet there does. A monster's con colour is its tier, the same for everyone
    /// whatever their level: grey critters that flee and give nothing, green plain auto-attackers, blue a step up, yellow
    /// a real duel, orange a lieutenant, red a camp boss or roaming named, purple an epic encounter. "Let's consider a mid
    /// level player with average gear when it comes to the idea of how the colors would work."
    ///
    /// How: when a fight starts the monster takes the level that cons its tier to whoever started it (the highest level
    /// of their group nearby) - its fight base. Everything DAoC already does by level (hit, damage, armour, experience,
    /// drops) then plays out at that con. Group members below the fight base are lifted, those above scaled down, by
    /// the same curve LevelScaling used. Before a fight each viewer is shown the monster at the level that cons its tier
    /// to them. RvR regions, events, guards, merchants, pets and bots stay as they were.
    ///
    /// The tier itself comes, for now, from a first guess per zone (the type's level against the zone's spread, critters
    /// and named monsters picked out); the zone reviews replace it zone by zone with deliberate choices.
    /// </summary>
    public static class MonsterTiers
    {
        public static bool Enabled = true;
        public const sbyte Unset = sbyte.MinValue;
        public const sbyte None = sbyte.MaxValue;
        public const sbyte Grey = -3, Green = -2, Blue = -1, Yellow = 0, Orange = 1, Red = 2, Purple = 3;

        static volatile bool _ready;
        public static bool Ready => _ready;

        // ------------------------------------------------------------------ the tier

        /// <summary>This NPC's tier (-3 grey .. 3 purple), or None when it isn't tiered.</summary>
        public static sbyte Tier(GameNPC n)
        {
            if (!Enabled || !_ready || n == null)
                return None;
            sbyte t = n.MonsterTier;
            if (t != Unset)
                return t;
            t = Assign(n);
            n.MonsterTier = t;
            return t;
        }

        public static bool IsTiered(GameObject o) => o is GameNPC n && Tier(n) != None;

        /// <summary>Set a tier by hand (a zone file, a GM): it sticks until changed again.</summary>
        public static void SetTier(GameNPC n, sbyte tier)
        {
            if (n == null)
                return;
            if (n.MonsterTier == Unset || n.MonsterTier == None)
                Snapshot(n);
            n.MonsterTier = tier;
            n.TierFightBase = 0;
        }

        static bool Eligible(GameNPC n)
        {
            if (n is GameBot || n is EventNpc || n is GameGuard || n is GameKeepGuard || n is GameMerchant || n is GameTrainingDummy)
                return false;
            if (n.Realm != eRealm.None || n.Brain is IControlledBrain || n.Brain == null)
                return false;
            if ((n.Flags & (GameNPC.eFlags.PEACE | GameNPC.eFlags.CANTTARGET)) != 0)
                return false;
            if (n.Level <= 0 || string.IsNullOrEmpty(n.Name))
                return false;
            Region r = n.CurrentRegion;
            if (r == null || r.IsRvR)                      // (not IsFrontier: the three home regions carry that flag)
                return false;
            return true;
        }

        static void Snapshot(GameNPC n)
        {
            n.TierBaseLevel = n.Level;
            n.TierBaseStats = new short[] { n.Strength, n.Constitution, n.Dexterity, n.Quickness, n.Intelligence, n.Empathy, n.Piety, n.Charisma };
        }

        static sbyte Assign(GameNPC n)
        {
            if (!Eligible(n))
                return None;
            Snapshot(n);
            if (n is IGameEpicNpc)
                return Purple;
            ZoneTypes zs = Types(n.CurrentZone, n.CurrentRegion);
            zs.ByName.TryGetValue(n.Name, out TypeInfo ti);
            if (IsCritter(n, ti))
                return Grey;
            double s = (ti != null && ti.Rank >= 0 ? ti.Rank : zs.Percentile(n.Level)) + zs.Shift;
            if (char.IsUpper(n.Name[0]))
                return s >= 0.85 ? Red : Orange;            // a named monster: a lieutenant at least
            // the zone's types weakest first, by how many there are: the first 45% green, then blue to 80%, yellow to
            // 95%, the rest orange (owner's peaceful mix: 45 / 35 / 15 / 4 / 1) - older zones lean harder (Shift)
            return s < 0.45 ? Green : s < 0.80 ? Blue : s < 0.95 ? Yellow : Orange;
        }

        static readonly string[] CritterWords = { "ambient", "larva", " cub", "grass spirit", "rabbit", "hare", "squirrel", "butterfly", "fawn", "piglet", "chick" };

        /// <summary>Critters: little things that leave you alone and are worth nothing (owner: "prey animals, water beetle
        /// larvae, etc. ... distributed around for flavor").</summary>
        static bool IsCritter(GameNPC n, TypeInfo ti)
        {
            string lower = n.Name.ToLowerInvariant();
            foreach (string w in CritterWords)
                if (lower.Contains(w))
                    return true;
            int max = ti?.MaxLevel ?? n.Level;
            bool neutral = ti != null ? ti.Neutral : (n.Brain is StandardMobBrain b && b.AggroLevel == 0);
            return max <= 2 && neutral;
        }

        // ------------------------------------------------------------------ a zone's monster types

        sealed class TypeInfo
        {
            public int Count, MaxLevel, NeutralCount;
            public double LevelSum;
            public double Rank = -1;           // where the type sits among the zone's monsters, weakest first (0..1)
            public double MeanLevel => LevelSum / Math.Max(1, Count);
            public bool Neutral => NeutralCount * 2 > Count;
        }

        sealed class ZoneTypes
        {
            public readonly Dictionary<string, TypeInfo> ByName = new();
            public int[] Levels = Array.Empty<int>();
            public double Shift;

            public double Percentile(double level)
            {
                if (Levels.Length == 0)
                    return 0.5;
                int below = 0, equal = 0;
                foreach (int l in Levels)
                {
                    if (l < level - 0.01) below++;
                    else if (Math.Abs(l - level) <= 0.5) equal++;
                }
                return (below + equal * 0.5) / Levels.Length;
            }
        }

        static readonly ConcurrentDictionary<int, ZoneTypes> _zones = new();

        static ZoneTypes Types(Zone zone, Region region)
        {
            if (zone == null || region == null)
                return new ZoneTypes();
            return _zones.GetOrAdd(zone.ID, _ => Build(zone, region));
        }

        static ZoneTypes Build(Zone zone, Region region)
        {
            var zt = new ZoneTypes();
            var levels = new List<int>();
            GameObject[] all = region.Objects;
            if (all != null)
                foreach (GameObject o in all)
                {
                    if (o is not GameNPC n || n.CurrentZone != zone || !Eligible(n))
                        continue;
                    int lv = n.MonsterTier is not Unset and not None ? n.TierBaseLevel : n.Level;
                    if (!zt.ByName.TryGetValue(n.Name, out TypeInfo ti))
                        zt.ByName[n.Name] = ti = new TypeInfo();
                    ti.Count++;
                    ti.LevelSum += lv;
                    ti.MaxLevel = Math.Max(ti.MaxLevel, lv);
                    if (n.Brain is StandardMobBrain b && b.AggroLevel == 0)
                        ti.NeutralCount++;
                    if (char.IsLower(n.Name[0]))
                        levels.Add(lv);
                }
            levels.Sort();
            zt.Levels = levels.ToArray();
            // each ordinary type's place among the zone's monsters, weakest first, weighted by how many there are
            var order = new List<KeyValuePair<string, TypeInfo>>();
            int total = 0;
            foreach (var kv in zt.ByName)
                if (char.IsLower(kv.Key[0]))
                {
                    order.Add(kv);
                    total += kv.Value.Count;
                }
            order.Sort((a, b) => a.Value.MeanLevel != b.Value.MeanLevel ? a.Value.MeanLevel.CompareTo(b.Value.MeanLevel)
                : string.CompareOrdinal(a.Key, b.Key));
            int seen = 0;
            foreach (var kv in order)
            {
                kv.Value.Rank = (seen + kv.Value.Count * 0.5) / Math.Max(1, total);
                seen += kv.Value.Count;
            }
            double median = levels.Count > 0 ? levels[levels.Count / 2] : 10;
            zt.Shift = Math.Clamp((median - 15) / 200.0, 0, 0.15);  // older, harder zones lean a little more dangerous
            return zt;
        }

        // ------------------------------------------------------------------ levels

        /// <summary>The level that cons <paramref name="tier"/> to someone of level <paramref name="b"/>.</summary>
        public static int LevelFor(int b, sbyte tier, int baseLevel)
        {
            b = Math.Clamp(b, 1, 100);
            if (tier == None)
                return baseLevel;
            var span = new List<int>();
            for (int l = 0; l <= Math.Min(127, b + 40); l++)
                if (ConLevels.GetConLevel(b, l) == tier)
                    span.Add(l);
            int lvl;
            if (span.Count == 0)
                lvl = tier < 0 ? Math.Max(0, b + tier) : b + tier;
            else if (tier == Grey)
                lvl = Math.Max(0, span[^1] - 1);
            else if (tier == Purple)
                lvl = Math.Max(baseLevel, span[0] + 2);
            else if (tier == Yellow)
                lvl = b;
            else
                lvl = span[span.Count / 2];
            return Math.Clamp(lvl, 0, 127);
        }

        /// <summary>The level a monster fights at against a side of level <paramref name="b"/>: the same level, whatever its
        /// tier (owner 2026-11-19: everyone on one footing, "their level is what gives them access to their tools") -
        /// how strong it is comes from its tier (TierStrength), not from DAoC's level gaps. Critters stay low; a purple
        /// never drops below where it was placed.</summary>
        public static int FightLevelFor(int b, sbyte tier, int baseLevel)
        {
            b = Math.Clamp(b, 1, 100);
            if (tier == Grey)
                return LevelFor(b, Grey, baseLevel);
            if (tier == Purple)
                return Math.Max(baseLevel, b);
            return b;
        }

        // ------------------------------------------------------------------ the power curve

        /// <summary>A tier's strength, a yellow being 1 (an even fight for a player whose own power is 1).</summary>
        public static readonly double[] TierStrength = { 0.25, 0.55, 0.75, 1.0, 1.35, 1.8, 3.0 };   // grey .. purple

        /// <summary>Everyone's footing against monsters (tunable live with /tier tune): overall multipliers on how hard a
        /// monster is to bring down and how hard it hits (1 = the fitted curve as it is).</summary>
        public static double Toughness = 1.0, Bite = 1.0;

        // The curve (owner 2026-11-19: "much too difficult now due to the damage numbers ... have them fight mobs of
        // every con. maybe at level 5, 15, 25, 35, 45, and 50 just to see how it feels, and then adjust the curve that
        // way"), fitted from the stand-in bench (TierCalibration): a monster level with you hits for InCurve(level) times
        // DAoC's own damage and takes OutCurve(level) times yours, then each con above your band (PowerTier) multiplies
        // its hits by InStep and divides yours by OutStep (and the other way for each below). The aim, in plain gear and
        // plain auto-attacks: an even con takes about 25 s to bring down and would take about 50 s to bring you down.
        public static double InStep = 1.6, OutStep = 1.55;
        public static readonly int[] CurveLevels = { 1, 5, 15, 25, 35, 45, 50 };
        // (bench run 1, 19 Nov: the stand-in Celt Hero in plain reinforced armour, a rowdy and a lough wolf at every con:
        // InCurve so an even con would take ~60 s to bring it down; OutCurve's shape from how fast it brought them down,
        // pinned at level 17 to what Fiona's fights felt right with - styles, gear and a companion make up the rest)
        public static readonly double[] InCurve = { 0.80, 0.80, 0.87, 0.86, 0.69, 0.55, 0.45 };
        public static readonly double[] OutCurve = { 0.35, 0.35, 0.72, 0.92, 1.25, 1.52, 1.81 };

        static double CurveAt(double[] curve, int level)
        {
            level = Math.Clamp(level, 1, 50);
            for (int i = 1; i < CurveLevels.Length; i++)
                if (level <= CurveLevels[i])
                {
                    double t = (level - CurveLevels[i - 1]) / (double) (CurveLevels[i] - CurveLevels[i - 1]);
                    return curve[i - 1] * Math.Pow(curve[i] / curve[i - 1], t);   // (geometric between the points)
                }
            return curve[^1];
        }

        /// <summary>How many cons a tier stands above a fighter of this level (negative: below).</summary>
        public static double ConGap(sbyte tier, int level) => Math.Clamp(tier, Grey, Purple) - PowerTier(level);

        /// <summary>A tiered monster's hits on a fighter of this level, against DAoC's own damage.</summary>
        public static double InFactor(sbyte tier, int level) => CurveAt(InCurve, level) * Math.Pow(InStep, ConGap(tier, level)) * Bite;

        /// <summary>A fighter of this level's hits on a tiered monster, against DAoC's own damage.</summary>
        public static double OutFactor(sbyte tier, int level) => CurveAt(OutCurve, level) / Math.Pow(OutStep, ConGap(tier, level)) / Toughness;

        static string TuningFile => System.IO.Path.Combine(GameServer.Instance.Configuration.RootDirectory, "tier-tuning.txt");

        /// <summary>Keep /tier tune's numbers across restarts (runtime\server\tier-tuning.txt: toughness, bite, the seven
        /// strengths).</summary>
        public static void SaveTuning()
        {
            try
            {
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                System.IO.File.WriteAllText(TuningFile, "v2 " + string.Join(" ", new[] { Toughness, Bite, InStep, OutStep }.Concat(InCurve).Concat(OutCurve)
                    .Select(v => v.ToString(ci))));
            }
            catch (Exception) { }
        }

        static void LoadTuning()
        {
            try
            {
                if (!System.IO.File.Exists(TuningFile))
                    return;
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                string[] parts = System.IO.File.ReadAllText(TuningFile).Split(' ', StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 0 || parts[0] != "v2")
                    return;                                      // (the first curve's numbers: they meant something else)
                double[] v = parts.Skip(1).Select(x => double.Parse(x, ci)).ToArray();
                int n = CurveLevels.Length;
                if (v.Length >= 4 + 2 * n)
                {
                    Toughness = v[0];
                    Bite = v[1];
                    InStep = v[2];
                    OutStep = v[3];
                    Array.Copy(v, 4, InCurve, 0, n);
                    Array.Copy(v, 4 + n, OutCurve, 0, n);
                }
            }
            catch (Exception) { }
        }

        /// <summary>The tier a player (or bot) of this level fights like in plain gear (owner 2026-11-19): 1-12 a green,
        /// 13-24 a blue, 25-36 a yellow, 37-49 an orange, 50 a red - smoothly in between.</summary>
        public static double PowerTier(int level)
        {
            level = Math.Clamp(level, 1, 50);
            if (level >= 50)
                return Red;
            // band centres: 6.5 -> green, 18.5 -> blue, 30.5 -> yellow, 43 -> orange, 50 -> red
            double[] at = { 1, 6.5, 18.5, 30.5, 43, 50 };
            double[] tier = { -2.4, -2, -1, 0, 1, 2 };
            for (int i = 1; i < at.Length; i++)
                if (level <= at[i])
                    return tier[i - 1] + (tier[i] - tier[i - 1]) * (level - at[i - 1]) / (at[i] - at[i - 1]);
            return Red;
        }

        /// <summary>The strength of a tier, or of a power between tiers.</summary>
        public static double Strength(double tier)
        {
            tier = Math.Clamp(tier, -3, 3);
            int lo = (int) Math.Floor(tier);
            if (lo >= 3)
                return TierStrength[6];
            double f = tier - lo;
            return TierStrength[lo + 3] + (TierStrength[lo + 4] - TierStrength[lo + 3]) * f;
        }

        public static double Power(int level) => Strength(PowerTier(level));

        /// <summary>The one whose level counts on the players' side: a player, a bot, or the owner of a pet of either.</summary>
        public static GameLiving Combatant(GameLiving l) => l switch
        {
            GamePlayer p => p,
            GameBot b => b,
            GameNPC { Brain: IControlledBrain cb } => cb.GetLivingOwner() is GameLiving o && (o is GamePlayer || o is GameBot) ? o : null,
            _ => null
        };

        /// <summary>The level a fight starts at: the highest of the group nearby (so no one carries a low friend
        /// through easy fights - the lower ones are lifted instead).</summary>
        public static int EngageLevel(GameLiving side)
        {
            int top = side.Level;
            if (side.Group != null)
                foreach (GameLiving m in side.Group.GetMembersInTheGroup())
                    if (m != null && m.IsAlive && m.CurrentRegion == side.CurrentRegion && m.IsWithinRadius(side, 4000))
                        top = Math.Max(top, m.Level);
            return top;
        }

        /// <summary>The level this viewer is shown the monster at: its fight level once a fight is on, otherwise the
        /// level that cons its tier to them.</summary>
        public static int DisplayLevel(GameNPC n, GamePlayer viewer)
        {
            sbyte t = Tier(n);
            if (t == None || viewer == null)
                return -1;
            if (n.TierFightBase > 0)
                return n.Level;
            return LevelFor(viewer.Level, t, n.TierBaseLevel);
        }

        /// <summary>The level a player fights this monster at (the modern HUD's), or -1 when it isn't tiered.</summary>
        public static int FightingLevel(GamePlayer p, GameLiving target)
        {
            if (target is not GameNPC n || Tier(n) == None)
                return -1;
            return n.TierFightBase > 0 ? n.TierFightBase : p.Level;
        }

        // ------------------------------------------------------------------ the fight

        /// <summary>Called as something lands on a monster's aggro list. Starts a fight at the right level; a critter
        /// runs instead (returns true: don't add it).</summary>
        public static bool OnAggro(GameNPC body, GameLiving attacker, bool hadAggro)
        {
            sbyte t = Tier(body);
            if (t == None || attacker == null)
                return false;
            GameLiving side = Combatant(attacker);
            if (side == null)
                return false;                                   // monster against monster: as it was
            if (t == Grey)
            {
                Flee(body, attacker);
                return true;
            }
            Engage(body, side, t, hadAggro);
            return false;
        }

        /// <summary>Called as a player, bot or pet starts an attack or a spell on something: a tiered monster takes the
        /// fight's level before the blow lands.</summary>
        public static void Touch(GameLiving attacker, GameLiving target)
        {
            if (target is not GameNPC n || attacker == null || attacker == target)
                return;
            sbyte t = Tier(n);
            if (t == None || t == Grey)
                return;
            GameLiving side = Combatant(attacker);
            if (side == null)
                return;
            Engage(n, side, t, n.Brain is StandardMobBrain b && b.HasAggro);
        }

        static void Engage(GameNPC body, GameLiving side, sbyte t, bool hadAggro)
        {
            if (!body.IsAlive)
                return;
            if (hadAggro && body.TierFightBase > 0)
                return;
            if (!hadAggro && body.TierFightBase > 0 && body.HealthPercent < 100)
                return;                                         // still hurt from the last fight: keep its level
            int b = EngageLevel(side);
            byte lvl = (byte) FightLevelFor(b, t, body.TierBaseLevel);
            if (body.TierFightBase == b && body.Level == lvl)
                return;
            body.TierFightBase = b;
            body.SetTierFightLevel(lvl);
        }

        static void Flee(GameNPC body, GameLiving from)
        {
            if (!body.IsAlive || body.IsIncapacitated)
                return;
            double dx = body.X - from.X, dy = body.Y - from.Y;
            double len = Math.Sqrt(dx * dx + dy * dy);
            if (len < 1)
            {
                double a = Util.RandomDouble() * Math.PI * 2;
                dx = Math.Cos(a); dy = Math.Sin(a); len = 1;
            }
            int x = (int) (body.X + dx / len * 900), y = (int) (body.Y + dy / len * 900);
            body.StopAttack();
            body.WalkTo(new Point3D(x, y, body.Z), (short) Math.Max((int) body.MaxSpeed, 200));
        }

        /// <summary>A stats snapshot moved to a new level, as auto-set stats grow per level.</summary>
        public static short[] StatsAt(GameNPC n, int level)
        {
            short[] s = n.TierBaseStats;
            if (s == null || s.Length < 8)
                return null;
            int d = level - n.TierBaseLevel;
            short Grow(short v, double perLevel) => (short) Math.Clamp(v + d * perLevel, 1, short.MaxValue);
            return new[]
            {
                Grow(s[0], Properties.MOB_AUTOSET_STR_MULTIPLIER), Grow(s[1], Properties.MOB_AUTOSET_CON_MULTIPLIER),
                Grow(s[2], Properties.MOB_AUTOSET_DEX_MULTIPLIER), Grow(s[3], Properties.MOB_AUTOSET_QUI_MULTIPLIER),
                Grow(s[4], Properties.MOB_AUTOSET_INT_MULTIPLIER), Grow(s[5], 1), Grow(s[6], 1), Grow(s[7], 1)
            };
        }

        const double OUT_DOWN = 2.0, IN_DOWN = 1.5, MIN_OUT = 0.1, MAX_IN = 4.0;   // as LevelScaling
        const double OUT_UP = 1.0, IN_UP = 1.0, MAX_OUT_UP = 3.0, MIN_IN_UP = 0.33;

        /// <summary>The damage factor of an attack with a tiered monster on either end (true), or false when neither
        /// is one (LevelScaling's own rules then).</summary>
        public static bool TryDamageFactor(GameLiving attacker, GameLiving target, out double f)
        {
            f = 1.0;
            if (target is GameNPC tn && Tier(tn) != None)
            {
                GameLiving c = Combatant(attacker);
                if (c != null && tn.TierFightBase > 0)
                    f = Out(c.Level, tn.TierFightBase) * OutFactor(Tier(tn), c.Level);
                return true;
            }
            if (attacker is GameNPC an && Tier(an) != None)
            {
                GameLiving c = Combatant(target);
                if (c != null && an.TierFightBase > 0)
                    f = In(c.Level, an.TierFightBase) * InFactor(Tier(an), c.Level);
                return true;
            }
            return false;
        }

        static double Out(int level, int b)
        {
            if (level == b || level <= 0 || b <= 0) return 1.0;
            return level > b ? Math.Max(MIN_OUT, Math.Pow(b / (double) level, OUT_DOWN))
                             : Math.Min(MAX_OUT_UP, Math.Pow(b / (double) level, OUT_UP));
        }

        static double In(int level, int b)
        {
            if (level == b || level <= 0 || b <= 0) return 1.0;
            return level > b ? Math.Min(MAX_IN, Math.Pow(level / (double) b, IN_DOWN))
                             : Math.Max(MIN_IN_UP, Math.Pow(level / (double) b, IN_UP));
        }

        /// <summary>A tiered monster's spells were written for its old level: their damage follows its fight level.</summary>
        public static double SpellFactor(GameLiving caster)
        {
            if (caster is not GameNPC n || Tier(n) == None || n.TierBaseLevel <= 0)
                return 1.0;
            return Math.Clamp((n.Level + 3) / (double) (n.TierBaseLevel + 3), 0.25, 8.0);
        }

        /// <summary>The con between two objects when a tiered monster is one of them (true): its tier, for everyone.</summary>
        public static bool TryCon(GameObject viewer, GameObject seen, out int con)
        {
            con = 0;
            if (!_ready)
                return false;
            sbyte ts = seen is GameNPC sn ? Tier(sn) : None;
            sbyte tv = viewer is GameNPC vn ? Tier(vn) : None;
            if (ts != None && tv == None)
            {
                con = ts;
                return true;
            }
            if (tv != None && ts == None)
            {
                con = Math.Clamp(-tv, -3, 3);
                return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ the client

        static readonly ConcurrentDictionary<string, Dictionary<ushort, (GameNPC npc, sbyte tier)>> _sent = new();
        static readonly ConcurrentDictionary<string, ushort> _region = new();

        /// <summary>Tell the modern client the tiers of the monsters around: "#TIER|oid:tier;..." (new or changed ones).</summary>
        /// <summary>How far an aggressive monster notices you, by its con (owner 2026-11-19: "lower con should have the lowest
        /// ranges, higher con with higher ranges. None at ridiculous levels" - so the weaker ones can be picked off
        /// first). Wolves and hounds are aggressive whatever their record says ("mobs like wolves should be set to
        /// aggressive"). Applied as monsters come into a player's view (PushTiers), so a respawn gets it again.</summary>
        public static int AggroRangeFor(sbyte tier) => tier switch
        {
            Green => 250, Blue => 350, Yellow => 450, Orange => 550, Red => 650, Purple => 750, _ => 200
        };

        static readonly string[] Hunters = { "wolf", "hound", "jackal", "wild dog", "warg" };

        public static void ApplyAggro(GameNPC n, sbyte tier)
        {
            if (n?.Brain is not StandardMobBrain b || tier == None || tier <= Grey)
                return;
            if (b.AggroLevel <= 0)
            {
                string name = (n.Name ?? "").ToLowerInvariant();
                foreach (string h in Hunters)
                    if (name.Contains(h))
                    {
                        b.AggroLevel = 100;
                        break;
                    }
            }
            if (b.AggroLevel > 0)
                b.AggroRange = AggroRangeFor(tier);
        }

        public static void PushTiers(GamePlayer p)
        {
            if (!_ready || p?.Client == null)
                return;
            var sent = _sent.GetOrAdd(p.ObjectId, _ => new());
            var sb = new StringBuilder();
            var bots = new StringBuilder();
            int n = 0;
            lock (sent)
            {
                if (!_region.TryGetValue(p.ObjectId, out ushort reg) || reg != p.CurrentRegionID)
                {
                    sent.Clear();                               // a new region: the client starts over
                    _region[p.ObjectId] = p.CurrentRegionID;
                }
                foreach (GameNPC npc in p.GetNPCsInRadius(WorldMgr.VISIBILITY_DISTANCE))
                {
                    if (npc is GameBot bot)
                    {
                        // a bot's plate border: how strong it is next to you (owner 2026-11-19: "a level 50 bot ... a
                        // purple colored border to like a level 10 player"), its level never shown
                        sbyte bt = (sbyte) (BotStrengthTo(bot, p) + 10);   // (+10 keeps it apart from monster tiers)
                        if (sent.TryGetValue(npc.ObjectID, out var bw) && bw.npc == npc && bw.tier == bt)
                            continue;
                        sent[npc.ObjectID] = (npc, bt);
                        bots.Append(npc.ObjectID).Append(':').Append(bt - 10).Append(';');
                        continue;
                    }
                    sbyte t = Tier(npc);
                    if (t == None)
                        continue;
                    ApplyAggro(npc, t);
                    if (sent.TryGetValue(npc.ObjectID, out var was) && was.npc == npc && was.tier == t)
                        continue;
                    sent[npc.ObjectID] = (npc, t);
                    sb.Append(npc.ObjectID).Append(':').Append(t).Append(';');
                    if (++n >= 80)
                    {
                        NewClient.Send(p, "#TIER|" + sb);
                        sb.Clear();
                        n = 0;
                    }
                }
            }
            if (sb.Length > 0)
                NewClient.Send(p, "#TIER|" + sb);
            if (bots.Length > 0)
                NewClient.Send(p, "#BTIER|" + bots);
            if (_logged.TryAdd(p.ObjectId + ":" + p.CurrentRegionID, 0))
                Console.WriteLine($"[MonsterTiers] {p.Name}: {sent.Count} tiers sent in region {p.CurrentRegionID} (new client {NewClient.Is(p)})");
        }

        static readonly ConcurrentDictionary<string, byte> _logged = new();

        /// <summary>How strong a bot is next to a player, as a con (-3 .. 3): its level's power, plus a companion's
        /// competence, against the player's.</summary>
        public static int BotStrengthTo(GameBot bot, GamePlayer p)
        {
            double mine = PowerTier(bot.Level);
            int rank = PersonalCompanions.RankOf(bot);
            if (rank >= 0)
                mine += (rank - 5) * 0.08;                      // a raw companion a little below its level, a legend above
            return (int) Math.Clamp(Math.Round(mine - PowerTier(p.Level)), -3, 3);
        }

        public static void Forget(GamePlayer p)
        {
            if (p == null)
                return;
            _sent.TryRemove(p.ObjectId, out _);
            _region.TryRemove(p.ObjectId, out _);
        }

        // ------------------------------------------------------------------ start

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            _zones.Clear();
            LoadTuning();
            _ready = true;
            int count = 0;
            var tally = new int[7];
            var purple = new List<string>();
            foreach (Region r in WorldMgr.GetAllRegions())
            {
                GameObject[] all = r.Objects;
                if (all == null)
                    continue;
                foreach (GameObject o in all)
                    if (o is GameNPC n)
                    {
                        sbyte t = Tier(n);
                        if (t != None && t >= -3 && t <= 3)
                        {
                            count++;
                            tally[t + 3]++;
                            if (t == Purple && purple.Count < 12 && !purple.Contains(n.Name))
                                purple.Add(n.Name);
                        }
                    }
            }
            Console.WriteLine($"[MonsterTiers] {count} monsters tiered: grey {tally[0]}, green {tally[1]}, blue {tally[2]}, yellow {tally[3]}, orange {tally[4]}, red {tally[5]}, purple {tally[6]} (e.g. {string.Join(", ", purple)})");
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&tier", ePrivLevel.GM, "A monster's fixed con tier (MonsterTiers): show it, or set it",
        "/tier  (your target)", "/tier set <grey|green|blue|yellow|orange|red|purple>", "/tier zone  (the tally around you)",
        "/tier tune [toughness|bite|instep|outstep <value> | in|out <level> <value> | in|out v1,..,v7]  (the power curve, live)")]
    public class TierCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        static readonly string[] Names = { "grey", "green", "blue", "yellow", "orange", "red", "purple" };

        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            if (sub == "tune")
            {
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                // /tier tune toughness|bite|instep|outstep <v>  ·  /tier tune in|out <level> <v>  ·  /tier tune in|out v1,v2,..
                if (args.Length > 3)
                {
                    string what = args[2].ToLowerInvariant();
                    double[] curve = what == "in" ? MonsterTiers.InCurve : what == "out" ? MonsterTiers.OutCurve : null;
                    if (curve != null && args.Length > 4 && int.TryParse(args[3], out int lv) &&
                        double.TryParse(args[4], System.Globalization.NumberStyles.Float, ci, out double cv) && cv > 0)
                    {
                        int at = Array.IndexOf(MonsterTiers.CurveLevels, lv);
                        if (at >= 0)
                            curve[at] = cv;
                    }
                    else if (curve != null)
                    {
                        double[] all = args[3].Split(',').Select(x => double.TryParse(x, System.Globalization.NumberStyles.Float, ci, out double y) ? y : -1).ToArray();
                        if (all.Length == curve.Length && all.All(x => x > 0))
                            Array.Copy(all, curve, curve.Length);
                    }
                    else if (double.TryParse(args[3], System.Globalization.NumberStyles.Float, ci, out double v) && v > 0)
                    {
                        if (what == "toughness") MonsterTiers.Toughness = v;
                        else if (what == "bite") MonsterTiers.Bite = v;
                        else if (what == "instep") MonsterTiers.InStep = v;
                        else if (what == "outstep") MonsterTiers.OutStep = v;
                    }
                    MonsterTiers.SaveTuning();
                }
                DisplayMessage(client, $"Toughness {MonsterTiers.Toughness:0.##}, bite {MonsterTiers.Bite:0.##}, steps in {MonsterTiers.InStep:0.##} out {MonsterTiers.OutStep:0.##}; " +
                    $"curve at levels {string.Join(",", MonsterTiers.CurveLevels)}: in {string.Join(",", MonsterTiers.InCurve.Select(x => x.ToString("0.###", ci)))}, " +
                    $"out {string.Join(",", MonsterTiers.OutCurve.Select(x => x.ToString("0.###", ci)))}; you fight like {MonsterTiers.PowerTier(p.Level):0.0} - " +
                    string.Join(", ", Names.Select((n, i) => $"{n} hits x{MonsterTiers.InFactor((sbyte) (i - 3), p.Level):0.##} takes x{MonsterTiers.OutFactor((sbyte) (i - 3), p.Level):0.##}")));
                return;
            }
            if (sub == "zone")
            {
                var tally = new int[7];
                int none = 0;
                foreach (GameNPC n in p.GetNPCsInRadius(8000))
                {
                    sbyte t = MonsterTiers.Tier(n);
                    if (t == MonsterTiers.None) none++;
                    else tally[t + 3]++;
                }
                DisplayMessage(client, $"Within 8000: grey {tally[0]}, green {tally[1]}, blue {tally[2]}, yellow {tally[3]}, " +
                    $"orange {tally[4]}, red {tally[5]}, purple {tally[6]}; not tiered {none}");
                return;
            }
            if (p.TargetObject is not GameNPC npc)
            {
                DisplayMessage(client, "Target a monster.");
                return;
            }
            if (sub == "set" && args.Length > 2)
            {
                int i = Array.IndexOf(Names, args[2].ToLowerInvariant());
                if (i < 0)
                {
                    DisplayMessage(client, "Tiers: " + string.Join(", ", Names));
                    return;
                }
                MonsterTiers.SetTier(npc, (sbyte) (i - 3));
                MonsterTiers.Forget(p);                        // resend the tiers around you
            }
            sbyte tier = MonsterTiers.Tier(npc);
            DisplayMessage(client, tier == MonsterTiers.None
                ? $"{npc.Name}: not tiered (level {npc.Level})."
                : $"{npc.Name}: {Names[tier + 3]} - placed at level {npc.TierBaseLevel}, now level {npc.Level}" +
                  (npc.TierFightBase > 0 ? $" (a fight set for level {npc.TierFightBase})" : "") +
                  $"; stamina {(int) MonsterMoves.Stamina(npc)}, " + (MonsterMoves.Humanoid(npc) ? "humanoid" : "beast") +
                  (MonsterMoves.Shield(npc) ? " with a shield" : "") + (MonsterMoves.Guarding(npc) ? ", guarding" : ""));
        }
    }
}
