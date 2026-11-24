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

        // ------------------------------------------------------------------ named monsters: sturdier than their con

        /// <summary>Owner 2026-11-22: "Any boss or named mob ... should have more health than a regular mob of their
        /// con, probably at least 2x the health. Zone bosses more than that ... a yellow named mob should be more
        /// challenging than a yellow red wolfhound." A named monster (its name starts with a capital: Nock, Bertha, the
        /// Lady's own) takes half the damage of an ordinary one of its con - twice its health, in effect - unless set
        /// otherwise here. Event and story bosses get theirs as health (EventCons).</summary>
        public const double NamedSturdiness = 2.0;
        static readonly System.Runtime.CompilerServices.ConditionalWeakTable<GameNPC, object> _sturdy = new();

        public static void SetSturdiness(GameNPC n, double m)
        {
            if (n == null)
                return;
            _sturdy.Remove(n);
            _sturdy.Add(n, m);
        }

        public static double Sturdiness(GameNPC n)
        {
            if (n == null)
                return 1;
            if (_sturdy.TryGetValue(n, out object m))
                return (double) m;
            return n is not EventNpc && n.Realm == eRealm.None && IsNamed(n.Name) ? NamedSturdiness : 1;
        }

        public static bool IsNamed(string name) => !string.IsNullOrEmpty(name) && char.IsUpper(name[0]);

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

        /// <summary>The median level a zone's ordinary monsters were placed at (0: none) - ZoneRates' provisional rating.</summary>
        public static int ZoneMedianLevel(Zone zone, Region region)
        {
            int[] l = Types(zone, region).Levels;
            return l.Length == 0 ? 0 : l[l.Length / 2];
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
        /// how strong it is comes from its tier (BaseSwings, BaseLasts), not from DAoC's level gaps. Critters stay low;
        /// an epic encounter (a dragon, a raid boss) never drops below where it was placed.</summary>
        public static int FightLevelFor(int b, sbyte tier, int baseLevel, bool epic = false)
        {
            b = Math.Clamp(b, 1, 100);
            if (tier == Grey)
                return LevelFor(b, Grey, baseLevel);
            if (tier == Purple && epic)
                return Math.Max(baseLevel, b);
            return b;
        }

        // ------------------------------------------------------------------ one footing at every level

        // Owner 2026-11-22 (replacing the power bands of 2026-11-19, where levels 1-12 fought like a green and 50 like a
        // red): "I want a player who is wearing no armor, no weapons (or the same exact basic weapon relative to their
        // level) auto attacking a monster of the same con to do the same amount of relative damage to a monster of the
        // same con whether they're level 1 or level 50 ... The power for the level 50 will come with them having access
        // to better armor with better stats and stat bonuses on it, and their skills and abilities they've unlocked."
        //
        // So a con is the same fight at every level. OutCurve and InCurve only even out DAoC's own numbers from level to
        // level, fitted on the bench's baseline (TierCalibration, "/calib base": untrained, no armour, a plain
        // blue-conned weapon, the monster's moves off): OutCurve(level) is what a green takes BaseSwings[green] swings of
        // that baseline to bring down, InCurve(level) what takes a green BaseLasts[green] of its own swings to bring the
        // baseline down. Each con then has its own fixed numbers - the owner's targets: a green in 10-12 swings, won 80-90%
        // of the time; a blue an even trade; a yellow lost more often than not without gear and skills; then orange, red
        // and purple on the same climb. Training, gear and abilities are the power on top (nothing here sees them).
        // Fitted 22 Nov from the bench (tools: claude-work\fit, a race of swings with the bench's hit rates, damage spread
        // and swing times, pressing counted): a green 12 swings before pressing (about 10.7 with it) and won 85% of the
        // time, a blue 14 and 50%, a yellow 16 and 20%; an orange hits 1.35x as hard as a yellow, a red 1.8x, a purple 2.6x.
        public static readonly double[] BaseSwings = { 4, 12, 14, 16, 21, 30, 50 };        // grey .. purple: baseline swings to bring it down (before pressing)
        public static readonly double[] BaseLasts = { 37.06, 14.83, 12.15, 10.8, 8.0, 6.0, 4.15 };   // grey .. purple: its swings to bring the baseline down

        /// <summary>A purple's strength by its zone's rating (owner 2026-11-22: "I like having a power cap on purples for
        /// the peaceful or wild zones so that the dangerous and deadly zones still feel tougher even if you're fighting
        /// purple in both"): Peaceful, Wild, Dangerous, Deadly, Elite. Epic encounters (dragons, raid bosses) stand outside it.</summary>
        public static readonly double[] PurpleByRating = { 0.6, 0.75, 1.0, 1.25, 1.5 };

        /// <summary>Everyone's footing against monsters (tunable live with /tier tune): overall multipliers on how hard a
        /// monster is to bring down and how hard it hits (1 = the fitted curve as it is).</summary>
        public static double Toughness = 1.0, Bite = 1.0;

        // Each tier's own fine-tuning on top (the /tier tune window, owner 2026-11-21: "so I can tune all tiers of hits,
        // takes, and presses"), grey .. purple: TierHits times as hard it hits you, TierTakes times the damage it takes,
        // and TierPress added to each blow in a row you land on it (0: no pressing on that tier). All 1 = the targets.
        public static readonly double[] DefaultHits = { 1, 1, 1, 1, 1, 1, 1 };
        public static readonly double[] DefaultTakes = { 1, 1, 1, 1, 1, 1, 1 };
        public static readonly double[] DefaultPress = { 0, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10 };   // (every con but a critter: counted in the targets)
        public static readonly double[] TierHits = (double[]) DefaultHits.Clone();
        public static readonly double[] TierTakes = (double[]) DefaultTakes.Clone();
        public static readonly double[] TierPress = (double[]) DefaultPress.Clone();

        static int Ix(sbyte tier) => Math.Clamp(tier, Grey, Purple) + 3;

        public static double GreenTakes { get => TierTakes[1]; set => TierTakes[1] = value; }
        public static double GreenHits { get => TierHits[1]; set => TierHits[1] = value; }

        /// <summary>The bonus each blow in a row adds on this tier (0: pressing doesn't count there).</summary>
        public static double PressStepFor(sbyte tier) => tier == None ? 0 : TierPress[Ix(tier)];

        // Pressing the attack (owner 2026-11-21): each blow in a row a player (or bot) lands on a tier with a press step
        // (every con but grey since 2026-11-22 - the owner had raised it on every tier) adds that step to the next, up to
        // PressMax blows; a miss, a blow turned aside or PressWindowMs without one ends it.
        public const int PressMax = 5, PressWindowMs = 4000;

        public static void ResetTierTuning()
        {
            Array.Copy(DefaultHits, TierHits, 7);
            Array.Copy(DefaultTakes, TierTakes, 7);
            Array.Copy(DefaultPress, TierPress, 7);
        }

        // (no longer used for damage - kept so /tier tune instep|outstep still parse)
        public static double InStep = 1.0, OutStep = 1.0;
        public static readonly int[] CurveLevels = { 1, 5, 15, 25, 35, 45, 50 };
        // The baseline's level-to-level evening out (bench "/calib base", 22 Nov - see the calibration notes beside it):
        // a green's blows on the baseline against DAoC's own, and the baseline's blows on a green against DAoC's own.
        public static readonly double[] InCurve = { 0.2819, 0.3084, 0.3285, 0.3107, 0.2852, 0.2651, 0.2783 };
        public static readonly double[] OutCurve = { 0.5661, 1.1162, 1.7668, 2.9405, 4.0483, 4.8905, 5.9102 };
        // A caster's spells on top of OutCurve (bench "/calib spell"): the baseline caster's best untrained damage spell
        // brings a green down in SpellCasts casts at every level (casters stand in cloth and pay power for every cast, so a
        // little quicker than the baseline's swings). Training in the line raises it from there, as weapon training does
        // (owner 2026-11-22: "Training in Way of the Sun, for example will increase the damage of the spells that fall
        // under that line") - replacing the 2026-11-19 boost that had new mages destroying things.
        // (bench "/calib spell", 22 Nov: an untrained Eldritch's best damage spell - Nil Bolt at 1, then Way of the
        // Eclipse's Void spells by level - 12.9% of a monster's health a cast at level 1, 11% at 25, 7.4% at 50 before this)
        public static readonly double[] SpellCurve = { 1.369, 0.4316, 0.4365, 0.309, 0.2375, 0.2882, 0.2295 };
        public const double SpellCasts = 10;

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

        /// <summary>A tiered monster's hits on a fighter of this level, against DAoC's own damage.</summary>
        public static double InFactor(sbyte tier, int level) =>
            CurveAt(InCurve, level) * BaseLasts[1] / BaseLasts[Ix(tier)] * Bite * TierHits[Ix(tier)];

        /// <summary>A fighter of this level's hits on a tiered monster, against DAoC's own damage.</summary>
        public static double OutFactor(sbyte tier, int level) =>
            CurveAt(OutCurve, level) * BaseSwings[1] / BaseSwings[Ix(tier)] / Toughness * TierTakes[Ix(tier)];

        /// <summary>A purple's zone cap (PurpleByRating) for this monster, split evenly between how long it lasts and how hard
        /// it hits (so the fight as a whole is that much easier or harder); 1 for every other tier and for epics.</summary>
        public static double PurpleCap(GameNPC n)
        {
            if (n == null || n is IGameEpicNpc || Tier(n) != Purple || n.CurrentZone == null)
                return 1.0;
            return Math.Sqrt(PurpleByRating[(int) ZoneRates.RatingOf(n.CurrentZone)]);
        }

        sealed class Pressing
        {
            public GameLiving Target;
            public int Count;
            public long At;
        }

        static readonly System.Runtime.CompilerServices.ConditionalWeakTable<GameLiving, Pressing> _pressing = new();

        /// <summary>Blows in a row this attacker has landed on this monster (0 when the run has ended).</summary>
        public static int PressCount(GameLiving attacker, GameLiving target) =>
            _pressing.TryGetValue(attacker, out Pressing p) && p.Target == target && GameLoop.GameLoopTime - p.At <= PressWindowMs ? p.Count : 0;

        /// <summary>AttackComponent, after every blow: a player's or bot's run of hits on a green or blue goes on, or ends.</summary>
        public static void AfterBlow(AttackData ad)
        {
            if (ad?.Attacker is not (GamePlayer or GameBot) || ad.Target is not GameNPC n || n is GameBot)
                return;
            sbyte t = Tier(n);
            if (PressStepFor(t) <= 0)
                return;
            Pressing p = _pressing.GetValue(ad.Attacker, _ => new Pressing());
            long now = GameLoop.GameLoopTime;
            if (ad.IsHit)
            {
                p.Count = p.Target == n && now - p.At <= PressWindowMs ? Math.Min(PressMax, p.Count + 1) : 1;
                p.Target = n;
                p.At = now;
            }
            else if (ad.AttackResult is eAttackResult.Missed or eAttackResult.Evaded or eAttackResult.Parried or eAttackResult.Blocked or eAttackResult.Fumbled)
                p.Count = 0;
        }

        /// <summary>A player's (or bot's) spell on a tiered monster: SpellCurve at its level (1 for anything else).</summary>
        public static double SpellOut(GameLiving caster, GameLiving target)
        {
            if (target is not GameNPC tn || Tier(tn) == None || TierCalibration.Raw(tn))
                return 1.0;
            // an Animist's turrets and bombers are its spells too (owner 2026-11-21: turret spell power) - at its level
            if (caster is GameNPC pet && (pet.Brain is TurretBrain or BomberBrain) && Combatant(pet) is GameLiving owner && owner != pet)
                caster = owner;
            if (caster is not (GamePlayer or GameBot))
                return 1.0;
            return CurveAt(SpellCurve, caster.Level);
        }

        static string TuningFile => System.IO.Path.Combine(GameServer.Instance.Configuration.RootDirectory, "tier-tuning.txt");

        /// <summary>Keep /tier tune's numbers across restarts (runtime\server\tier-tuning.txt: toughness, bite, the seven
        /// strengths).</summary>
        public static void SaveTuning()
        {
            try
            {
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                System.IO.File.WriteAllText(TuningFile, "v4 " + string.Join(" ", new[] { Toughness, Bite }.Concat(InCurve).Concat(OutCurve).Concat(SpellCurve)
                    .Concat(TierHits).Concat(TierTakes).Concat(TierPress).Select(v => v.ToString(ci))));
            }
            catch (Exception) { }
        }

        /// <summary>Only a v4 file (2026-11-22, one footing at every level): the older ones were tuned against the power
        /// bands, which are gone - they're left alone and the fitted defaults stand.</summary>
        static void LoadTuning()
        {
            try
            {
                if (!System.IO.File.Exists(TuningFile))
                    return;
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                string[] parts = System.IO.File.ReadAllText(TuningFile).Split(' ', StringSplitOptions.RemoveEmptyEntries);
                if (parts.Length == 0 || parts[0] != "v4")
                    return;
                double[] v = parts.Skip(1).Select(x => double.Parse(x, ci)).ToArray();
                int n = CurveLevels.Length;
                if (v.Length < 2 + 3 * n + 21)
                    return;
                Toughness = v[0];
                Bite = v[1];
                Array.Copy(v, 2, InCurve, 0, n);
                Array.Copy(v, 2 + n, OutCurve, 0, n);
                Array.Copy(v, 2 + 2 * n, SpellCurve, 0, n);
                int at = 2 + 3 * n;
                Array.Copy(v, at, TierHits, 0, 7);
                Array.Copy(v, at + 7, TierTakes, 0, 7);
                Array.Copy(v, at + 14, TierPress, 0, 7);
            }
            catch (Exception) { }
        }

        /// <summary>How strong a bot of this level looks next to you, as a con (its plate's border, BotStrengthTo): 1-12 a
        /// green, 13-24 a blue, 25-36 a yellow, 37-49 an orange, 50 a red. (Until 2026-11-22 this was also everyone's
        /// footing against monsters - the power bands; now a con is the same fight at every level.)</summary>
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
            byte lvl = (byte) FightLevelFor(b, t, body.TierBaseLevel, body is IGameEpicNpc);
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
            if (target is GameNPC rt && TierCalibration.Raw(rt) || attacker is GameNPC ra && TierCalibration.Raw(ra))
                return true;                                        // (the bench's baseline: DAoC's own numbers)
            if (target is GameNPC tn && Tier(tn) != None)
            {
                GameLiving c = Combatant(attacker);
                if (c != null && tn.TierFightBase > 0)
                    f = Out(c.Level, tn.TierFightBase) * OutFactor(Tier(tn), c.Level) / PurpleCap(tn);
                f /= Sturdiness(tn);                                // (a named monster: twice the health of its con)
                f *= ZoneRates.TakesIn(tn.CurrentZone);             // (a harder zone's monsters take a little less)
                if (attacker is GamePlayer or GameBot)
                    f *= 1.0 + PressStepFor(Tier(tn)) * PressCount(attacker, tn);   // (pressing the attack)
                else if (c == null && attacker is GameNPC ally && ally.Realm != eRealm.None && ally.Level > tn.Level)
                    // (owner 2026-11-23, Bugs & Fixes: once a player engages, "the NPCs for the event then attack them,
                    // they do an extreme amount of damage") - the monster dropped to the player's fight level and the
                    // realm's people (an event's guards, the Host's soldiers) kept their own: as if they fought at its level
                    f *= Math.Max(0.05, Math.Pow(tn.Level / (double) ally.Level, 1.5));
                return true;
            }
            if (attacker is GameNPC an && Tier(an) != None)
            {
                GameLiving c = Combatant(target);
                if (c != null && an.TierFightBase > 0)
                    f = In(c.Level, an.TierFightBase) * InFactor(Tier(an), c.Level) * PurpleCap(an)
                        * ZoneRates.HitsIn(an.CurrentZone);         // (and hit a little harder)
                else if (c == null && target is GameNPC tgt && tgt.Realm != eRealm.None && an.Level > tgt.Level)
                    // an event's own people (the pedlar you're keeping alive) against a monster that took a high
                    // fighter's level: as if it fought at theirs
                    f = Math.Max(0.05, Math.Pow(tgt.Level / (double) an.Level, 1.5));
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
    [CmdAttribute("&tier", ePrivLevel.Player, "A monster's fixed con tier (MonsterTiers): show it, set it, or tune the tiers",
        "/tier tune  (the tuning window; anyone - test it out of GM mode, where monsters fight back)",
        "/tier tune tier <grey..purple> hits|takes|press <value>  ·  /tier tune reset",
        "/tier tune [toughness|bite|instep|outstep <value> | in|out|spell <level> <value> | in|out|spell v1,..,v7]  (the power curve, live)",
        "/tier  (your target, GM)", "/tier set <grey|green|blue|yellow|orange|red|purple>  (GM)", "/tier zone  (the tally around you, GM)")]
    public class TierCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        static readonly string[] Names = { "grey", "green", "blue", "yellow", "orange", "red", "purple" };

        /// <summary>The /tier tune window's numbers for the modern client: "#TUNE|{json}".</summary>
        public static string WindowJson(GamePlayer p)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            string N(double v) => v.ToString("0.###", ci);
            var sb = new StringBuilder("{\"level\":").Append(p.Level)
                .Append(",\"like\":0")
                .Append(",\"toughness\":").Append(N(MonsterTiers.Toughness))
                .Append(",\"bite\":").Append(N(MonsterTiers.Bite))
                .Append(",\"tiers\":[");
            for (int i = 0; i < 7; i++)
            {
                sbyte t = (sbyte) (i - 3);
                if (i > 0) sb.Append(',');
                sb.Append("{\"name\":\"").Append(Names[i]).Append("\",\"hits\":").Append(N(MonsterTiers.TierHits[i]))
                    .Append(",\"takes\":").Append(N(MonsterTiers.TierTakes[i]))
                    .Append(",\"press\":").Append(N(MonsterTiers.TierPress[i]))
                    .Append(",\"nowHits\":").Append(N(MonsterTiers.InFactor(t, p.Level)))
                    .Append(",\"nowTakes\":").Append(N(MonsterTiers.OutFactor(t, p.Level))).Append('}');
            }
            return sb.Append("]}").ToString();
        }

        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client.Player;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            if (sub == "tune")
            {
                var ci = System.Globalization.CultureInfo.InvariantCulture;
                bool window = args.Length > 2 && args[2].ToLowerInvariant() == "window";
                if (args.Length > 2 && args[2].ToLowerInvariant() == "reset")
                {
                    MonsterTiers.ResetTierTuning();
                    MonsterTiers.SaveTuning();
                    window = true;
                }
                else if (args.Length > 5 && args[2].ToLowerInvariant() == "tier")
                {
                    // /tier tune tier <name> hits|takes|press <v>
                    int i = Array.IndexOf(Names, args[3].ToLowerInvariant());
                    if (i >= 0 && double.TryParse(args[5], System.Globalization.NumberStyles.Float, ci, out double tv) && tv >= 0)
                    {
                        string what = args[4].ToLowerInvariant();
                        if (what == "hits" && tv > 0) MonsterTiers.TierHits[i] = Math.Min(tv, 20);
                        else if (what == "takes" && tv > 0) MonsterTiers.TierTakes[i] = Math.Min(tv, 20);
                        else if (what == "press") MonsterTiers.TierPress[i] = Math.Min(tv, 2);
                        MonsterTiers.SaveTuning();
                    }
                    window = true;
                }
                // /tier tune toughness|bite|instep|outstep <v>  ·  /tier tune in|out <level> <v>  ·  /tier tune in|out v1,v2,..
                else if (args.Length > 3)
                {
                    string what = args[2].ToLowerInvariant();
                    double[] curve = what == "in" ? MonsterTiers.InCurve : what == "out" ? MonsterTiers.OutCurve :
                        what == "spell" ? MonsterTiers.SpellCurve : null;
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
                    else if (double.TryParse(args[3], System.Globalization.NumberStyles.Float, ci, out double v) && v >= 0)
                    {
                        if (what == "toughness" && v > 0) MonsterTiers.Toughness = v;
                        else if (what == "bite" && v > 0) MonsterTiers.Bite = v;
                        else if (what == "instep" && v > 0) MonsterTiers.InStep = v;
                        else if (what == "outstep" && v > 0) MonsterTiers.OutStep = v;
                        else if (what == "greentakes" && v > 0) MonsterTiers.GreenTakes = v;
                        else if (what == "greenhits" && v > 0) MonsterTiers.GreenHits = v;
                        else if (what == "press") MonsterTiers.TierPress[1] = MonsterTiers.TierPress[2] = v;
                    }
                    MonsterTiers.SaveTuning();
                    window |= args.Length == 4 && (args[2].ToLowerInvariant() is "toughness" or "bite");
                }
                else if (args.Length == 2)
                    window = true;                              // (typed /tier tune: the window)
                if (window && NewClient.Is(p))
                {
                    NewClient.Send(p, "#TUNE|" + WindowJson(p));
                    return;
                }
                DisplayMessage(client, $"Toughness {MonsterTiers.Toughness:0.##}, bite {MonsterTiers.Bite:0.##}; " +
                    $"curve at levels {string.Join(",", MonsterTiers.CurveLevels)}: in {string.Join(",", MonsterTiers.InCurve.Select(x => x.ToString("0.###", ci)))}, " +
                    $"out {string.Join(",", MonsterTiers.OutCurve.Select(x => x.ToString("0.###", ci)))}, " +
                    $"spell {string.Join(",", MonsterTiers.SpellCurve.Select(x => x.ToString("0.###", ci)))} - " +
                    string.Join(", ", Names.Select((n, i) => $"{n} (hits x{MonsterTiers.TierHits[i]:0.##}, takes x{MonsterTiers.TierTakes[i]:0.##}, press +{MonsterTiers.TierPress[i] * 100:0}%) " +
                        $"now hits x{MonsterTiers.InFactor((sbyte) (i - 3), p.Level):0.##} takes x{MonsterTiers.OutFactor((sbyte) (i - 3), p.Level):0.##}")));
                return;
            }
            if (client.Account.PrivLevel < (uint) ePrivLevel.GM)
            {
                DisplayMessage(client, "Only /tier tune is open to everyone; the rest of /tier is for GMs.");
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
