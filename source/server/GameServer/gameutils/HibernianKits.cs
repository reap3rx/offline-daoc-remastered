using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// The Warden and the Bard (agreed 20 Nov; owner: "Everything else seems good, let's build it"). Fewer buttons, more
    /// done by fighting well; every spell family one button that grows as it ranks (SpellFamilies). Built at start-up,
    /// never written to the database.
    ///
    /// Warden - heals by fighting, the least casting of the three:
    ///   Verdant Strike   every style that lands heals your group around you, more the closer they stand
    ///   Nature's Bulwark a timed block raises a bladeturn bubble: I (Nurture 2) you, II (10) you and your most hurt
    ///                    groupmate, III (18) your group - replaces the cast Nature's Ward / Fend / Shield
    ///   Verdant Mend     a timed parry pulses a small heal on those close to you
    ///   Wellspring I-V   (Regrowth 10-50) every heal you give 5% stronger a rank
    ///   Warden's Vigor   (Regrowth 2-41) the old endurance / fatigue buffs as a passive
    ///   Rallying Cry     (Regrowth 15/30/45) an instant shout: a chain heal over 3/4/5 groupmates, 30 s reuse
    ///   Renewal          the one cast heal (the baseline's); the other heals, the cures and the resist buffs go -
    ///                    Purify cures all, one resist chant (Warden's Resolve) for all six magic resists
    ///   Challenge        (no Battle Cry) - TauntShouts
    /// Bard - crowd control, support, the least healing:
    ///   Music evades     an evade may answer: mesmerize the attacker, stun it, Discord (it turns on its own kind), a
    ///                    mesmerize around it, Enthrall (turned for longer - never bots, bosses or named), Inspire (your
    ///                    group recovers a little); about a third as often at Music 1 as at 50
    ///   Anthem of Mending (Regrowth 5+) an instant burst of healing over time on the group, 20 s reuse - no direct heals
    ///   Dirge            (Music 12+) a song: enemies around you attack slower and resist magic less
    ///   Hymn of Warding  (Music 25/46) a song: all six magic resists for the group (10, then 20)
    ///   Crescendo        Blades / Blunt styles that land build up to 5; your next song pulse spends them as a burst of
    ///                    health, endurance and power for the group
    ///   Song Wheel       (level 5) an ability: tap it for the song that fits now, hold it for a wheel of your songs
    ///   mez down to one single (Mesmerizing Melody) and the Lullaby Wave cone; Lullaby (area), Discordant, Confusion stay
    /// Druid - the purest healer, no styles:
    ///   Bramble Shield   (Nurture 5-45) the mana shield; a perfect ward roots the attacker, then poisons it as the root ends
    ///   the nature spirit one summon (its best rank), a form picked on the pet window - bear, wolf or wisp - always on your
    ///                    target; your blows may call its special (5% at Nature 1 to 25% at 50): Maul (stun, holds anger),
    ///                    Rend (bleed, snare), Mending Light (heals the most hurt)
    ///   Rejuvenation     (Regrowth 13+) a heal over time stacking to 3; cast on 3 it Blooms
    ///   Nature's Sanction stays, its rank at 45 (Nature's Communion) the whole group (in place of Bith's); Purify; the smart
    ///                    heals' lines and Verdant Pulse stay; the Confluxes, the Spirits and the Major heals go
    ///   Gift of the Wild (Nurture 2) every buff on the group in one cast (the single buffs leave the book); Nature's Mantle
    ///                    for the three resist buffs; one single root and one area root
    /// Spell ids 97100-97199.
    /// </summary>
    public static class HibernianKits
    {
        public const int Warden = 46, Druid = 47, Bard = 48;
        public const string KitLine = "Hibernian Kit Effects";

        // hidden effects
        const int BulwarkSelf = 97100, BulwarkAlly = 97101, BulwarkGroup = 97102, MezProc = 97103, DiscordProc = 97104,
            EnthrallProc = 97105, AoeMezProc = 97106, DazeProc = 97107, StunProc = 97108;
        // learned spells (families: one button each)
        const int Resolve = 97110, Purify = 97115, PurifyBard = 97116, Anthem = 97120, Dirge = 97130, HymnWarding = 97135;

        public const int BulwarkCooldownMs = 8000, MendCooldownMs = 1500, MendRadius = 400, StrikeRadius = 600;
        public const int RallyReuseMs = 30000, RallyRange = 1500, RallyJump = 800, AnthemReuse = 20;
        public const int CrescendoMax = 5, CrescendoTickMs = 5000, CrescendoForgetMs = 30000;
        public static readonly int[] BulwarkAt = { 2, 10, 18 }, WellspringAt = { 10, 20, 30, 40, 50 },
            VigorAt = { 2, 12, 22, 32, 41 }, RallyAt = { 15, 30, 45 };
        public const string BulwarkKey = "Nature's Bulwark", MendKey = "Verdant Mend", WellspringKey = "Wellspring",
            VigorKey = "Warden's Vigor", RallyKey = "Rallying Cry", WheelKey = "Song Wheel", MusicEvadeKey = "Music of Evasion";

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[HibernianKits] " + ex);
            }
        }

        public static void Register()
        {
            // ---- the hidden effects
            Hidden(Db(BulwarkSelf, "Nature's Bulwark", "Bladeturn", "Self", duration: 30, effect: 5121, icon: 5121,
                msg1: "Bark closes over you like a shield."));
            Hidden(Db(BulwarkAlly, "Nature's Bulwark", "Bladeturn", "Realm", range: 1500, duration: 30, effect: 5122, icon: 5122,
                msg1: "Bark closes over you like a shield."));
            Hidden(Db(BulwarkGroup, "Nature's Bulwark", "Bladeturn", "Group", radius: 1500, duration: 30, effect: 5123, icon: 5123,
                msg1: "Bark closes over you like a shield."));
            Hidden(Db(MezProc, "Mesmerized", "Mesmerize", "Enemy", duration: 6, effect: 5311, icon: 5311, msg1: "The music holds you still!"));
            Hidden(Db(AoeMezProc, "Lulled", "Mesmerize", "Enemy", radius: 350, duration: 5, effect: 5371, icon: 5371,
                msg1: "The music holds you still!"));
            Hidden(Db(DiscordProc, "Discord", "Confusion", "Enemy", value: -100, duration: 5, effect: 5351, icon: 5351));
            Hidden(Db(EnthrallProc, "Enthralled", "Confusion", "Enemy", value: -100, duration: 15, effect: 5354, icon: 5354));
            Hidden(Db(DazeProc, "Dazed", "CombatSpeedDebuff", "Enemy", value: 15, duration: 8, effect: 5421, icon: 5421,
                msg1: "The music dulls your blows!"));
            Hidden(Db(StunProc, "Stunned", "StyleStun", "Enemy", duration: 2, effect: 2132, icon: 2132));

            int trimmed = WardenBook() + BardBook() + DruidBook();
            Abilities();
            Console.WriteLine($"[HibernianKits] Warden, Bard and Druid: {trimmed} spells trimmed, {_added} added");
        }

        // ------------------------------------------------------------------ the spellbooks

        static int _added;

        static int WardenBook()
        {
            int n = 0;
            // Regrowth: the baseline keeps Renewal and the resurrection; the spec line keeps the Solar regeneration
            n += ClassBaseline(Specs.Regrowth, "Regrowth", Warden, "Regrowth Warden Base", s => s.Group is 4821 or 4831);
            n += SkillBase.RemoveLineSpells("Regrowth Warden Spec", s => s.Group is 4851 or 4871 or 4931 or 4932 || s.ID is 14382 or 14383);
            Add("Regrowth Warden Spec", 20, Db(Purify, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 4869,
                icon: 4869, group: Purify, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            // Nurture: the cast bladeturns (Nature's Bulwark now) and the three resist buffs (one chant) go
            n += SkillBase.RemoveLineSpells("Nurture Warden Spec", s => s.Group is 5121 or 5122 or 5123 or 5141 or 5144 or 5147);
            Spell chant = SkillBase.GetSpellByID(5131);       // (Guardian's Encouragement: a chant's pulse)
            int[] lv = { 22, 33, 43 }, val = { 8, 16, 24 };
            string[] names = { "Warden's Resolve", "Warden's Fortitude", "Warden's Bastion" };
            for (int i = 0; i < 3; i++)
            {
                DbSpell d = Db(Resolve + i, names[i], "AllMagicResistsBuff", "Group", value: val[i], radius: 1500, power: 0, cast: 3,
                    effect: 5141, icon: 5141, group: Resolve, desc: $"A chant: your group resists heat, cold, matter, body, spirit and energy {val[i]}% better.");
                Chant(d, chant);
                Add("Nurture Warden Spec", lv[i], d);
            }
            return n;
        }

        static int BardBook()
        {
            int n = 0;
            // Regrowth: no direct heals at all - the baseline keeps the resurrection; the spec line keeps Chant of Healing
            n += ClassBaseline(Specs.Regrowth, "Regrowth", Bard, "Regrowth Bard Base", s => s.Group == 4831);
            n += SkillBase.RemoveLineSpells("Regrowth Bard Spec", s => s.Group is 4851 or 4961 or 4869 or 4983 or 4981);
            Add("Regrowth Bard Spec", 7, Db(PurifyBard, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 4869,
                icon: 4869, group: Purify, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            int[] alv = { 5, 15, 26, 33, 42 }, tick = { 8, 18, 30, 42, 55 };
            string[] an = { "Anthem of Mending", "Anthem of Renewal", "Anthem of Restoration", "Anthem of Renascence", "Anthem of Apotheosis" };
            for (int i = 0; i < alv.Length; i++)
                Add("Regrowth Bard Spec", alv[i], Db(Anthem + i, an[i], "HealOverTime", "Group", value: tick[i], radius: 1500,
                    duration: 10, frequency: 20, power: 6 + i * 4, recast: AnthemReuse, effect: 4971, icon: 4971, group: Anthem,
                    desc: $"Instant: your group heals {tick[i]} every 2 seconds for 10 seconds."));
            // Music: one single mesmerize, the cone, Lullaby (area), Discordant, Confusion; the shouts, the targeted area
            // mesmerizes, the harmonies and the twelve resist hymns go
            n += SkillBase.RemoveLineSpells("Bard Music", s => s.Group == 5301);
            n += SkillBase.RemoveLineSpells("Bard Music Spec", s => s.Group is 5361 or 5371 or 5393 or 5394 || s.Group >= 5381 && s.Group <= 5392);
            Spell song = SkillBase.GetSpellByID(4971);        // (Chant of Healing: a song's pulse and instrument)
            int[] dlv = { 12, 34, 44 }, dval = { 10, 15, 20 };
            string[] dn = { "Dirge", "Mournful Dirge", "Dirge of the Fallen" };
            for (int i = 0; i < 3; i++)
            {
                DbSpell d = Db(Dirge + i, dn[i], "Dirge", "Enemy", value: dval[i], radius: 500, duration: 6, effect: 5421, icon: 5421,
                    group: Dirge, desc: $"A song: enemies within 500 of you attack {dval[i]}% slower and resist magic {dval[i]}% less.");
                Chant(d, song);
                d.Range = 0;
                Add("Bard Music Spec", dlv[i], d);
            }
            int[] hlv = { 25, 46 }, hval = { 10, 20 };
            string[] hn = { "Hymn of Warding", "Hymn of Sanctuary" };
            for (int i = 0; i < 2; i++)
            {
                DbSpell d = Db(HymnWarding + i, hn[i], "AllMagicResistsBuff", "Group", value: hval[i], radius: 1500, effect: 5381,
                    icon: 5381, group: HymnWarding, desc: $"A song: your group resists heat, cold, matter, body, spirit and energy {hval[i]}% better.");
                Chant(d, song);
                Add("Bard Music Spec", hlv[i], d);
            }
            return n;
        }

        /// <summary>A class of its own baseline in a shared specialization (Warden / Druid / Bard all have Regrowth): a copy
        /// of the shared line holding only the spells kept, hinted to the class (Specialization picks it over the shared).
        /// How many spells it leaves out.</summary>
        static int ClassBaseline(string spec, string fromLine, int cls, string key, Func<Spell, bool> keep)
        {
            SpellLine src = SkillBase.GetSpellLine(fromLine, false);
            if (src == null)
                return 0;
            var line = new SpellLine(key, src.Name, 9000 + cls, src.Spec, true);
            SkillBase.RegisterSpellLine(line);
            int dropped = 0;
            foreach (Spell s in SkillBase.GetSpellList(fromLine))
            {
                if (keep(s))
                    SkillBase.AddSpellToSpellLine(key, s.ID, s.Level);
                else
                    dropped++;
            }
            SkillBase.AddSpecSpellLine(spec, line, cls);
            return dropped;
        }

        /// <summary>The pulse of a chant / song taken from one of the class's own (its frequency, duration, instrument).</summary>
        static void Chant(DbSpell d, Spell from)
        {
            d.Pulse = 1;
            d.Frequency = from != null ? from.Frequency / 100 : 50;
            d.Duration = Math.Max(d.Duration, from != null ? from.Duration / 1000 : 6);
            d.InstrumentRequirement = from?.InstrumentRequirement ?? 0;
            d.CastTime = from != null ? from.CastTime / 1000.0 : 3;
        }

        static void Add(string line, int level, DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[HibernianKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(line, new Spell(d, level));
            _added++;
        }

        static void Hidden(DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[HibernianKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(KitLine, new Spell(d, 1));
        }

        static DbSpell Db(int id, string name, string type, string target, double value = 0, int range = 0, int radius = 0,
            int duration = 0, int frequency = 0, int power = 0, double cast = 0, int recast = 0, int effect = 0, int icon = 0,
            int group = 0, string msg1 = "", string desc = "") =>
            new DbSpell
            {
                SpellID = id, Name = name, Type = type, Target = target, Value = value, Range = range, Radius = radius,
                Duration = duration, Frequency = frequency, Power = power, CastTime = cast, RecastDelay = recast,
                ClientEffect = effect, Icon = icon != 0 ? icon : effect, SpellGroup = group, Message1 = msg1,
                Description = desc != "" ? desc : name,
            };

        // ------------------------------------------------------------------ the abilities

        static void Abilities()
        {
            var bulwark = new DbAbility
            {
                KeyName = BulwarkKey, Name = BulwarkKey, IconID = 5121, InternalID = 3910, AbilityID = 3910,
                Description = "A timed block raises a bark bubble that turns aside the next blow (30 seconds): rank I on you, rank II " +
                    "on you and your most hurt groupmate, rank III on your whole group. Once every 8 seconds.",
            };
            for (int i = 0; i < BulwarkAt.Length; i++)
                SkillBase.AddScriptedAbility(bulwark, Specs.Nurture, BulwarkAt[i], Warden, i + 1);
            var mend = new DbAbility
            {
                KeyName = MendKey, Name = MendKey, IconID = 4801, InternalID = 3911, AbilityID = 3911,
                Description = $"A timed parry pulses a small heal on you and your groupmates within {MendRadius} (more the closer they stand).",
            };
            SkillBase.AddScriptedAbility(mend, Specs.Parry, 1, Warden);
            var well = new DbAbility
            {
                KeyName = WellspringKey, Name = WellspringKey, IconID = 4851, InternalID = 3912, AbilityID = 3912,
                Implementation = typeof(SkillHandler.WellspringAbility).FullName,
                Description = "Every heal you give is 5% stronger for each rank (Regrowth 10, 20, 30, 40 and 50).",
            };
            for (int i = 0; i < WellspringAt.Length; i++)
                SkillBase.AddScriptedAbility(well, Specs.Regrowth, WellspringAt[i], Warden, i + 1);
            var vigor = new DbAbility
            {
                KeyName = VigorKey, Name = VigorKey, IconID = 4931, InternalID = 3913, AbilityID = 3913,
                Implementation = typeof(SkillHandler.WardenVigorAbility).FullName,
                Description = "Your styles cost 6% less endurance for each rank; from rank III you also recover endurance faster, in combat too.",
            };
            for (int i = 0; i < VigorAt.Length; i++)
                SkillBase.AddScriptedAbility(vigor, Specs.Regrowth, VigorAt[i], Warden, i + 1);
            var rally = new DbAbility
            {
                KeyName = RallyKey, Name = RallyKey, IconID = 974, InternalID = 3914, AbilityID = 3914,
                Description = "An instant shout: a heal that leaps from your most hurt groupmate to the next (3 at rank I, 4 at II, 5 at III), " +
                    "a little less each leap. 30 second reuse.",
            };
            for (int i = 0; i < RallyAt.Length; i++)
                SkillBase.AddScriptedAbility(rally, Specs.Regrowth, RallyAt[i], Warden, i + 1);
            var wheel = new DbAbility
            {
                KeyName = WheelKey, Name = WheelKey, IconID = 0, InternalID = 3915, AbilityID = 3915,
                Description = "Put it on your bar. Tap it: the song that fits the moment (healing when your group is hurt, the Dirge in a " +
                    "fight, power, endurance or speed otherwise). Hold it: a wheel of your songs - point at one and let go.",
            };
            SkillBase.AddScriptedAbility(wheel, "BardCareer", 5);
            var evade = new DbAbility
            {
                KeyName = MusicEvadeKey, Name = MusicEvadeKey, IconID = 5311, InternalID = 3916, AbilityID = 3916,
                Description = "When you evade, your music may answer: mesmerize the attacker (15%), stun it (8%), Discord - it turns on " +
                    "its own kind for 5 seconds (6%), a mesmerize around it (4%), Enthrall - turned for 15 seconds (1%, never bots, bosses " +
                    "or named), or Inspire - your group recovers a little health, endurance and power (5%). Those are at Music 50; at " +
                    "Music 1 about a third as often.",
            };
            SkillBase.AddScriptedAbility(evade, Specs.Music, 1, Bard);
        }

        // ------------------------------------------------------------------ helpers

        public static int ClassOf(GameLiving l) => l switch
        {
            GamePlayer p => p.CharacterClass?.ID ?? 0,
            GameBot b => b.CharacterClass?.ID ?? 0,
            _ => 0
        };

        static SpellLine EffectLine => SkillBase.GetSpellLine(GlobalSpellsLines.Combat_Styles_Effect);

        static void Cast(GameLiving caster, int spellId, GameLiving target)
        {
            if (SkillBase.GetSpellByID(spellId) is Spell sp)
                ScriptMgr.CreateSpellHandler(caster, sp, EffectLine)?.StartSpell(target);
        }

        public static double HealFactor(GameLiving healer) => 1.0 + healer.GetModified(eProperty.HealingEffectiveness) * 0.01;

        /// <summary>Your group (yourself included, or only you) alive within range.</summary>
        public static List<GameLiving> Mates(GameLiving who, int range)
        {
            var list = new List<GameLiving>();
            if (who.Group != null)
            {
                foreach (GameLiving m in who.Group.GetMembersInTheGroup())
                    if (m != null && m.IsAlive && m.ObjectState == GameObject.eObjectState.Active && m.CurrentRegion == who.CurrentRegion &&
                        who.IsWithinRadius(m, range))
                        list.Add(m);
            }
            if (!list.Contains(who))
                list.Add(who);
            return list;
        }

        /// <summary>A heal from a fighting healer: what it gave.</summary>
        public static int Heal(GameLiving healer, GameLiving t, int amount, ushort fx, string what)
        {
            if (t == null || !t.IsAlive || amount <= 0 || t.Health >= t.MaxHealth)
                return 0;
            int got = t.ChangeHealth(healer, eHealthChangeType.Spell, amount);
            if (got <= 0)
                return 0;
            foreach (GamePlayer v in t.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(healer, t, fx, 0, false, 1);
            if (healer is GamePlayer hp)
                hp.Out.SendMessage(t == healer ? $"Your {what} heals you for {got} hit points." : $"Your {what} heals {t.GetName(0, false)} for {got} hit points.",
                    eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            if (t is GamePlayer tp && t != healer)
                tp.Out.SendMessage($"{healer.GetName(0, true)}'s {what} heals you for {got} hit points.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            return got;
        }

        /// <summary>Near is worth all of it, StrikeRadius away (or the range given) a third.</summary>
        static double Falloff(GameLiving a, GameLiving b, int radius)
        {
            double d = a == b ? 0 : a.GetDistanceTo(b);
            return d <= 150 ? 1.0 : Math.Max(0.33, 1.0 - 0.67 * (d - 150) / Math.Max(1, radius - 150));
        }

        sealed class KitState
        {
            public long BulwarkReady, MendReady, CrescendoAt;
            public int Crescendo;
            public bool CrescendoTicking;
        }

        static readonly ConditionalWeakTable<GameLiving, KitState> _state = new();
        static KitState State(GameLiving l) => _state.GetValue(l, _ => new KitState());

        // ------------------------------------------------------------------ the Warden: fighting heals

        /// <summary>StyleRework.AfterStyle: a Warden's style landed - Verdant Strike; a Bard's - a Crescendo stack.</summary>
        public static void AfterStyle(GameLiving owner, AttackData ad)
        {
            int cls = ClassOf(owner);
            if (cls == Warden)
                VerdantStrike(owner, ad);
            else if (cls == Bard && ad.Style != null && (ad.Style.Spec == Specs.Blades || ad.Style.Spec == Specs.Blunt))
                AddCrescendo(owner);
        }

        public static void VerdantStrike(GameLiving w, AttackData ad)
        {
            int dealt = ad.Damage + ad.CriticalDamage;
            int baseHeal = (int) (Math.Max(dealt * 0.35, w.Level * 1.0) * HealFactor(w));
            foreach (GameLiving m in Mates(w, StrikeRadius))
                Heal(w, m, (int) (baseHeal * Falloff(w, m, StrikeRadius)), 4801, "Verdant Strike");
        }

        public static void VerdantMend(GameLiving w)
        {
            KitState s = State(w);
            long now = GameLoop.GameLoopTime;
            if (now < s.MendReady)
                return;
            s.MendReady = now + MendCooldownMs;
            int baseHeal = (int) ((8 + w.Level * 1.6) * HealFactor(w));
            foreach (GameLiving m in Mates(w, MendRadius))
                Heal(w, m, (int) (baseHeal * Falloff(w, m, MendRadius)), 4802, "Verdant Mend");
        }

        public static int BulwarkRank(GameLiving w)
        {
            int nurture = w.GetModifiedSpecLevel(Specs.Nurture);
            return nurture >= BulwarkAt[2] ? 3 : nurture >= BulwarkAt[1] ? 2 : nurture >= BulwarkAt[0] ? 1 : 0;
        }

        public static void Bulwark(GameLiving w)
        {
            int rank = BulwarkRank(w);
            KitState s = State(w);
            long now = GameLoop.GameLoopTime;
            if (rank == 0 || now < s.BulwarkReady)
                return;
            s.BulwarkReady = now + BulwarkCooldownMs;
            if (rank >= 3 && w.Group != null)
            {
                Cast(w, BulwarkGroup, w);
                return;
            }
            Cast(w, BulwarkSelf, w);
            if (rank >= 2 && Mates(w, 1500).Where(m => m != w && m.Health < m.MaxHealth).OrderBy(m => m.HealthPercent).FirstOrDefault() is GameLiving hurt)
                Cast(w, BulwarkAlly, hurt);
        }

        /// <summary>Rallying Cry: a heal leaping over the most hurt; how many it healed.</summary>
        public static int RallyingCry(GameLiving w, int rank)
        {
            int jumps = 2 + Math.Clamp(rank, 1, 3);
            int heal = (int) ((30 + w.Level * 3 + w.GetModifiedSpecLevel(Specs.Regrowth) * 3) * HealFactor(w));
            var pool = Mates(w, RallyRange).Where(m => m.Health < m.MaxHealth).ToList();
            GameLiving at = w;
            int n = 0;
            foreach (GamePlayer v in w.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(w, eEmote.LetsGo);
            while (n < jumps && pool.Count > 0)
            {
                GameLiving next = pool.Where(m => n == 0 || at.IsWithinRadius(m, RallyJump)).OrderBy(m => m.HealthPercent).FirstOrDefault();
                if (next == null)
                    break;
                pool.Remove(next);
                Heal(w, next, heal, 4841, "Rallying Cry");
                heal = heal * 9 / 10;
                at = next;
                n++;
            }
            return n;
        }

        // ------------------------------------------------------------------ the Bard: music answers an evade

        public static void MusicEvade(GameLiving bard, GameLiving attacker)
        {
            if (attacker == null || !attacker.IsAlive)
                return;
            int music = Math.Clamp(bard.GetModifiedSpecLevel(Specs.Music), 1, 50);
            double f = 1.0 / 3.0 + 2.0 / 3.0 * (music - 1) / 49.0;
            double r = Util.RandomDouble() * 100.0;
            double at = 0;
            bool Hit(double pct) => r < (at += pct * f);
            string said = null;
            if (Hit(15))
            {
                Cast(bard, MezProc, attacker);
                said = "Your music mesmerizes {0}!";
            }
            else if (Hit(8))
            {
                Cast(bard, StunProc, attacker);
                said = "A sharp note stuns {0}!";
            }
            else if (Hit(6))
            {
                Cast(bard, DiscordProc, attacker);
                said = "Discord! {0} turns on its own kind!";
            }
            else if (Hit(4))
            {
                Cast(bard, AoeMezProc, attacker);
                said = "Your music lulls everything around {0}!";
            }
            else if (Hit(1))
            {
                if (attacker is GameNPC n && n is not GameBot && n is not IGameEpicNpc && !LootUses.IsNamed(n))
                {
                    Cast(bard, EnthrallProc, attacker);
                    said = "Your music enthralls {0}!";
                }
            }
            else if (Hit(5))
            {
                foreach (GameLiving m in Mates(bard, 1500))
                {
                    m.ChangeHealth(bard, eHealthChangeType.Spell, Math.Max(1, m.MaxHealth * 3 / 100));
                    m.ChangeEndurance(bard, eEnduranceChangeType.Spell, Math.Max(1, m.MaxEndurance * 3 / 100));
                    if (m.MaxMana > 0)
                        m.ChangeMana(bard, eManaChangeType.Spell, Math.Max(1, m.MaxMana * 3 / 100));
                    foreach (GamePlayer v in m.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                        v.Out.SendSpellEffectAnimation(bard, m, 4971, 0, false, 1);
                }
                said = "Your music inspires your group!";
            }
            if (said != null && bard is GamePlayer p)
                p.Out.SendMessage(string.Format(said, attacker.GetName(0, false)), eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
        }

        // ------------------------------------------------------------------ the Bard: Crescendo

        public static void AddCrescendo(GameLiving bard)
        {
            KitState s = State(bard);
            s.Crescendo = Math.Min(CrescendoMax, s.Crescendo + 1);
            s.CrescendoAt = GameLoop.GameLoopTime;
            if (bard is GamePlayer p)
                p.Out.SendMessage($"Crescendo {s.Crescendo}/{CrescendoMax}.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            if (s.CrescendoTicking)
                return;
            s.CrescendoTicking = true;
            new ECSGameTimer(bard, _ =>
            {
                long now = GameLoop.GameLoopTime;
                if (s.Crescendo <= 0 || !bard.IsAlive || now - s.CrescendoAt > CrescendoForgetMs)
                {
                    s.Crescendo = 0;
                    s.CrescendoTicking = false;
                    return 0;
                }
                if (!PlayingSong(bard))
                    return CrescendoTickMs;
                int stacks = s.Crescendo;
                s.Crescendo = 0;
                s.CrescendoTicking = false;
                foreach (GameLiving m in Mates(bard, 1500))
                {
                    m.ChangeHealth(bard, eHealthChangeType.Spell, (int) (Math.Max(1, m.MaxHealth * 2 * stacks / 100) * HealFactor(bard)));
                    m.ChangeEndurance(bard, eEnduranceChangeType.Spell, Math.Max(1, m.MaxEndurance * 2 * stacks / 100));
                    if (m.MaxMana > 0)
                        m.ChangeMana(bard, eManaChangeType.Spell, Math.Max(1, m.MaxMana * 2 * stacks / 100));
                    foreach (GamePlayer v in m.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                        v.Out.SendSpellEffectAnimation(bard, m, 4972, 0, false, 1);
                }
                if (bard is GamePlayer bp)
                    bp.Out.SendMessage($"Crescendo! Your song swells - your group recovers {2 * stacks}% of health, endurance and power.",
                        eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                return 0;
            }, 1000);
        }

        public static bool PlayingSong(GameLiving l) =>
            l.effectListComponent.GetPulseEffects().Any(e => e.SpellHandler?.Spell?.NeedInstrument == true);

        // ------------------------------------------------------------------ AttackComponent: a blow turned aside

        /// <summary>After a blow is worked out (AttackComponent): a Warden's block / parry, a Bard's evade. An action-combat
        /// player's timed defense only (not a chained or held one); anyone else's dice blocks / parries some of the time.</summary>
        public static void AfterDefense(AttackData ad)
        {
            if (ad?.Target is not GameLiving d || ad.Attacker is not GameLiving a || !d.IsAlive)
                return;
            int cls = ClassOf(d);
            if (cls != Warden && cls != Bard)
                return;
            try
            {
                bool action = d is GamePlayer p && ActionCombat.IsActive(p) && ad.ActionDefense is not eActionDefense.None;
                bool timed = action && !ad.ActionAuto;
                bool dice = !action && Util.Chance(35);
                bool blocked = action ? ad.ActionDefense is eActionDefense.Block : ad.AttackResult is eAttackResult.Blocked;
                bool parried = action ? ad.ActionDefense is eActionDefense.Parry : ad.AttackResult is eAttackResult.Parried;
                bool evaded = action ? ad.ActionDefense is eActionDefense.Dodge : ad.AttackResult is eAttackResult.Evaded;
                if (cls == Warden && blocked && (timed || dice))
                    Bulwark(d);
                else if (cls == Warden && parried && (timed || dice))
                    VerdantMend(d);
                else if (cls == Bard && evaded)
                    MusicEvade(d, a);
            }
            catch (Exception e)
            {
                Console.WriteLine("[HibernianKits] after defense: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ the Song Wheel

        /// <summary>The songs you know (the best rank of each), in book order.</summary>
        public static List<(Spell Spell, SpellLine Line)> Songs(GamePlayer p)
        {
            var out_ = new List<(Spell, SpellLine)>();
            var seen = new HashSet<int>();
            foreach (var (line, skills) in p.GetAllUsableListSpells())
                foreach (Skill sk in SpellFamilies.BestOnly(skills))
                    if (sk is Spell sp && sp.NeedInstrument && sp.IsPulsing && seen.Add(sp.ID))
                        out_.Add((sp, line));
            foreach (var (sk, parent) in p.GetAllUsableSkills())    // (a hybrid's songs: its songs page)
                if (sk is Spell sp && sp.NeedInstrument && sp.IsPulsing && parent is SpellLine line && seen.Add(sp.ID))
                    out_.Add((sp, line));
            return out_;
        }

        /// <summary>/songwheel list: "#SNG|name;name;..." for the client's wheel.</summary>
        public static void SendSongs(GamePlayer p) =>
            NewClient.Send(p, "#SNG|" + string.Join(";", Songs(p).Select(s => s.Spell.Name.Replace(";", ","))));

        /// <summary>The tap: the song that fits now. Null when none is known.</summary>
        public static (Spell Spell, SpellLine Line)? SmartSong(GamePlayer p)
        {
            var songs = Songs(p);
            if (songs.Count == 0)
                return null;
            (Spell, SpellLine)? Of(eSpellType t) => songs.Where(s => s.Spell.SpellType == t).Select(s => ((Spell, SpellLine)?) s).FirstOrDefault();
            var group = Mates(p, 1500);
            double hurt = group.Min(m => m.HealthPercent);
            double tired = group.Min(m => m.MaxEndurance > 0 ? m.Endurance * 100.0 / m.MaxEndurance : 100);
            double drained = group.Where(m => m.MaxMana > 0).Select(m => (double) m.ManaPercent).DefaultIfEmpty(100.0).Min();
            bool fight = p.InCombat || group.Any(m => m.InCombat);
            bool foes = p.GetNPCsInRadius(500).Any(n => n.IsAlive && n.InCombat && GameServer.ServerRules.IsAllowedToAttack(p, n, true));
            var order = new List<eSpellType>();
            if (fight)
            {
                if (hurt < 70) order.Add(eSpellType.HealthRegenBuff);
                if (foes) order.Add(eSpellType.Dirge);
                if (tired < 40) order.Add(eSpellType.EnduranceRegenBuff);
                order.AddRange(new[] { eSpellType.HealthRegenBuff, eSpellType.EnduranceRegenBuff, eSpellType.AllMagicResistsBuff });
            }
            else
            {
                if (hurt < 90) order.Add(eSpellType.HealthRegenBuff);
                if (drained < 80) order.Add(eSpellType.PowerRegenBuff);
                if (tired < 80) order.Add(eSpellType.EnduranceRegenBuff);
                order.AddRange(new[] { eSpellType.SpeedEnhancement, eSpellType.PowerRegenBuff, eSpellType.HealthRegenBuff });
            }
            foreach (eSpellType t in order)
                if (Of(t) is (Spell, SpellLine) pick)
                    return pick;
            return songs[0];
        }

        public static void UseWheel(GamePlayer p)
        {
            if (SmartSong(p) is not (Spell sp, SpellLine line))
            {
                p.Out.SendMessage("You don't know a song yet.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            if (EffectListService.GetPulseEffectOnTarget(p, sp) != null)
            {
                p.Out.SendMessage($"You are already playing {sp.Name}.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            p.CastSpell(sp, line);
        }

        // ------------------------------------------------------------------ the Druid (agreed 20 Nov): the purest healer

        const int PurifyDruid = 97117, Rejuv = 97140, Communion = 97145, Gift = 97150, Mantle = 97151,
            BrambleRoot = 97160, BramblePoison = 97165, Maul = 97170, RendBleed = 97171, RendSnare = 97172;
        public static readonly int[] BrambleAt = { 5, 15, 25, 35, 45 };
        public const string BrambleKey = "Bramble Shield", FormKey = "druidform";
        public const int RejuvTickMs = 3000, RejuvTicks = 5, RejuvMax = 3;

        /// <summary>The Druid's Nature Spirit ranks: one summon (SpellFamilies keeps the best).</summary>
        public static readonly HashSet<int> NatureSpirits = new() { 5251, 5252, 5253, 5254, 5255 };

        // what Gift of the Wild casts: the buffs that left the book (baseline by your level, the spec's by Nurture)
        static readonly List<Spell> _giftBase = new(), _giftSpec = new();

        static int DruidBook()
        {
            int n = 0;
            Hidden(Db(Maul, "Mauled", "StyleStun", "Enemy", duration: 2, effect: 2132, icon: 2132, msg1: "You are mauled and stunned!"));
            var bleed = Db(RendBleed, "Rent", "StyleBleeding", "Enemy", duration: 12, frequency: 30, effect: 2130, icon: 2130);
            bleed.Damage = 10;
            bleed.DamageType = (int) eDamageType.Slash;
            Hidden(bleed);
            Hidden(Db(RendSnare, "Hamstrung", "StyleSpeedDecrease", "Enemy", value: 35, duration: 8, effect: 2135, icon: 2135));
            for (int r = 1; r <= 5; r++)
            {
                Hidden(Db(BrambleRoot + r - 1, "Bramble Snare", "SpeedDecrease", "Enemy", value: 99, duration: 2 + r, effect: 5281,
                    icon: 5281, msg1: "Brambles burst up and hold you!"));
                var poison = Db(BramblePoison + r - 1, "Bramble Poison", "DamageOverTime", "Enemy", duration: 3 + 2 * r, frequency: 20,
                    effect: 5261, icon: 5261, msg1: "The thorns' poison burns in you!");
                poison.Damage = 6 + 8 * r;
                poison.DamageType = (int) eDamageType.Body;
                Hidden(poison);
            }

            // Regrowth: the smart heals' lines stay (Greater heals, the baseline); Rejuvenation; Verdant Pulse; Nature's
            // Sanction (and its group rank at 45 in place of Bith's); Purify; the resurrection
            n += SkillBase.RemoveLineSpells("Regrowth Druid Spec", s => s.Group is 4851 or 4983 or 4869 or 4888 or 4885 or 4892 or 4871 ||
                s.ID is 14382 or 14383);
            Add("Regrowth Druid Spec", 6, Db(PurifyDruid, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 4869,
                icon: 4869, group: Purify, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            int[] rlv = { 13, 22, 34, 44 }, rval = { 15, 28, 45, 62 };
            string[] rn = { "Rejuvenation", "Greater Rejuvenation", "Superior Rejuvenation", "Wild Rejuvenation" };
            for (int i = 0; i < rlv.Length; i++)
                Add("Regrowth Druid Spec", rlv[i], Db(Rejuv + i, rn[i], "Rejuvenation", "Realm", value: rval[i], range: 2000,
                    power: 6 + i * 4, cast: 1.5, effect: 4851, icon: 4892, group: Rejuv,
                    desc: $"A friend heals {rval[i]} every 3 seconds for 15 seconds; it stacks three times (more each stack). Cast on " +
                        "three stacks, it Blooms: what was left to heal comes at once, and half again."));
            if (SkillBase.GetSpellByID(4884) is Spell sanction)
            {
                DbSpell d = CloneDb(sanction, Communion);
                d.Name = "Nature's Communion";
                d.Target = "Group";
                d.Radius = 1500;
                d.Range = 0;
                d.Description = "Instant: every one of your group is healed in full.";
                Add("Regrowth Druid Spec", 45, d);
            }

            // Nurture: the buffs leave the book for Gift of the Wild (one cast, all of them on your group); the three resist
            // buffs become Nature's Mantle
            foreach (Spell s in SkillBase.GetSpellList("Nurture"))
                _giftBase.Add(s);
            n += ClassBaseline(Specs.Nurture, "Nurture", Druid, "Nurture Druid Base", _ => false);
            foreach (Spell s in SkillBase.GetSpellList("Druid Nurture Spec"))
                if (s.SpellType is eSpellType.StrengthConstitutionBuff or eSpellType.DexterityQuicknessBuff or eSpellType.AcuityBuff or eSpellType.CombatSpeedBuff)
                    _giftSpec.Add(s);
            n += SkillBase.RemoveLineSpells("Druid Nurture Spec", s => s.SpellType is eSpellType.StrengthConstitutionBuff or
                eSpellType.DexterityQuicknessBuff or eSpellType.AcuityBuff or eSpellType.CombatSpeedBuff || s.Group is 5081 or 5084 or 5087);
            Add("Druid Nurture Spec", 2, Db(Gift, "Gift of the Wild", "GiftOfTheWild", "Group", radius: 1500, power: 10, cast: 3,
                effect: 5061, icon: 5061, group: Gift,
                desc: "Every buff you know - armor, strength, constitution, dexterity, quickness, acuity, haste - on your whole group at once."));
            int[] mlv = { 23, 32, 43 }, mval = { 8, 16, 24 };
            string[] mn = { "Nature's Mantle", "Nature's Cloak", "Nature's Aegis" };
            for (int i = 0; i < 3; i++)
                Add("Druid Nurture Spec", mlv[i], Db(Mantle + i, mn[i], "AllMagicResistsBuff", "Group", value: mval[i], radius: 1500,
                    duration: 1200, power: 19 + i * 9, cast: 3, effect: 5081, icon: 5081, group: Mantle,
                    desc: $"Your group resists heat, cold, matter, body, spirit and energy {mval[i]}% better for 20 minutes."));

            // Nature: one single root (Grasping Vines - hold it to charge) and one area root (Patch of Ivy); the instant
            // undergrowths go; Contamination, Bear's Hide and the thorns stay
            n += SkillBase.RemoveLineSpells("Druid Nature Spec", s => s.Group is 5291 or 5292);

            var bramble = new DbAbility
            {
                KeyName = BrambleKey, Name = BrambleKey, IconID = 5271, InternalID = 3917, AbilityID = 3917,
                Description = "Your mana shield (hold right click / LT) is a wall of brambles. Raised just before a blow lands - a perfect " +
                    "ward - the brambles root the attacker (3 to 7 seconds by rank), and when the root ends their thorns poison it " +
                    "(5 to 13 seconds). Ranks at Nurture 5, 15, 25, 35 and 45.",
            };
            for (int i = 0; i < BrambleAt.Length; i++)
                SkillBase.AddScriptedAbility(bramble, Specs.Nurture, BrambleAt[i], Druid, i + 1);
            var spirit = new DbAbility
            {
                KeyName = "Spirit of the Wild", Name = "Spirit of the Wild", IconID = 5251, InternalID = 3918, AbilityID = 3918,
                Description = "Your nature spirit takes the form you pick on the pet window (FORM): bear, wolf or wisp. It always goes for " +
                    "your target. Your own blows may call its special (5% at Nature 1, 25% at 50): the bear Mauls (a 2 second stun, and " +
                    "it holds the foe's anger), the wolf Rends (a bleed and a snare), the wisp's Mending Light heals your most hurt groupmate.",
            };
            SkillBase.AddScriptedAbility(spirit, Specs.Nature, 1, Druid);
            return n;
        }

        static DbSpell CloneDb(Spell s, int id) => new DbSpell
        {
            SpellID = id, Name = s.Name, Type = s.SpellType.ToString(), Target = s.Target.ToString(), Range = s.Range, Radius = s.Radius,
            Value = s.Value, Damage = s.Damage, DamageType = (int) s.DamageType, Duration = s.Duration / 1000, Frequency = s.Frequency / 100,
            Pulse = s.Pulse, PulsePower = s.PulsePower, Power = s.Power, CastTime = s.CastTime / 1000.0, RecastDelay = s.RecastDelay / 1000,
            ClientEffect = s.ClientEffect, Icon = s.Icon, SpellGroup = s.Group, EffectGroup = s.EffectGroup, Message1 = s.Message1,
            Message2 = s.Message2, Message3 = s.Message3, Message4 = s.Message4, Description = s.Description,
            InstrumentRequirement = s.InstrumentRequirement, Concentration = s.Concentration, SubSpellID = s.SubSpellID,
            SharedTimerGroup = s.SharedTimerGroup, MoveCast = s.MoveCast, Uninterruptible = s.Uninterruptible,
        };

        /// <summary>Gift of the Wild on one friend: the best rank of every buff the Druid knows.</summary>
        public static int GiveGift(GameLiving druid, GameLiving t)
        {
            SpellLine line = SkillBase.GetSpellLine(Specs.Nurture);
            int nurture = druid.GetModifiedSpecLevel(Specs.Nurture);
            int given = 0;
            foreach (var g in _giftBase.Where(s => s.Level <= druid.Level).Concat(_giftSpec.Where(s => s.Level <= nurture))
                .GroupBy(s => (s.Group, s.SpellType)))
            {
                Spell best = g.OrderBy(s => s.Level).Last();
                ScriptMgr.CreateSpellHandler(druid, best, line)?.StartSpell(t);
                given++;
            }
            return given;
        }

        // ---- Rejuvenation: a stacking heal over time that Blooms

        sealed class Rejuvenating
        {
            public GameLiving Healer;
            public int Stacks, PerTick, TicksLeft;
            public bool Ticking;
        }

        static readonly ConditionalWeakTable<GameLiving, Rejuvenating> _rejuv = new();

        public static void Rejuvenate(GameLiving healer, GameLiving t, Spell spell)
        {
            if (t == null || !t.IsAlive)
                return;
            Rejuvenating r = _rejuv.GetValue(t, _ => new Rejuvenating());
            int per = (int) (spell.Value * HealFactor(healer));
            if (r.Stacks >= RejuvMax && r.TicksLeft > 0)
            {
                // Bloom: what was left, at once, and half again
                int bloom = r.PerTick * r.Stacks * r.TicksLeft * 3 / 2;
                r.Stacks = 0;
                r.TicksLeft = 0;
                Heal(healer, t, bloom, 4867, "Bloom");
                return;
            }
            r.Healer = healer;
            r.Stacks = Math.Min(RejuvMax, r.Stacks + 1);
            r.PerTick = Math.Max(r.PerTick, per);
            r.TicksLeft = RejuvTicks;
            foreach (GamePlayer v in t.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(healer, t, spell.ClientEffect, 0, false, 1);
            if (healer is GamePlayer hp)
                hp.Out.SendMessage($"{spell.Name} on {(t == healer ? "you" : t.GetName(0, false))}: {r.Stacks}/{RejuvMax}" +
                    (r.Stacks == RejuvMax ? " - cast it again to Bloom!" : "."), eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            if (r.Ticking)
                return;
            r.Ticking = true;
            new ECSGameTimer(t, _ =>
            {
                if (!t.IsAlive || r.TicksLeft <= 0 || r.Stacks <= 0)
                {
                    r.Ticking = false;
                    r.Stacks = 0;
                    r.PerTick = 0;
                    return 0;
                }
                r.TicksLeft--;
                Heal(r.Healer, t, r.PerTick * r.Stacks, 4892, "Rejuvenation");
                return RejuvTickMs;
            }, RejuvTickMs);
        }

        // ---- the Bramble Shield (ManaShield: a Druid's perfect ward)

        public static int BrambleRank(GameLiving d)
        {
            int nurture = d.GetModifiedSpecLevel(Specs.Nurture);
            int rank = 0;
            foreach (int at in BrambleAt)
                if (nurture >= at)
                    rank++;
            return rank;
        }

        public static void Bramble(GamePlayer druid, GameLiving attacker)
        {
            if (ClassOf(druid) != Druid || attacker == null || !attacker.IsAlive)
                return;
            int rank = BrambleRank(druid);
            if (rank == 0)
                return;
            Cast(druid, BrambleRoot + rank - 1, attacker);
            druid.Out.SendMessage($"Brambles burst up and hold {attacker.GetName(0, false)}!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            new ECSGameTimer(druid, _ =>
            {
                if (attacker.IsAlive && druid.IsAlive)
                    Cast(druid, BramblePoison + rank - 1, attacker);
                return 0;
            }, (2 + rank) * 1000);
        }

        // ---- the nature spirit: forms, its special, always on your target

        public enum Form { Bear, Wolf, Wisp }
        const string FormParam = "druidform";
        static readonly string[] TierWords = { "cub", "youth", "adolescent", "adult", "patriarch" };
        static readonly string[] WispWords = { "minor", "lesser", "", "major", "greater" };

        public static Form FormOf(GameLiving druid)
        {
            if (druid is not GamePlayer p)
                return druid is GameBot b && b.Group != null && b.Group.GetMembersInTheGroup().Count(m => m != b) > 0 ? Form.Wisp : Form.Bear;
            var rec = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId)
                .And(DB.Column("KeyName").IsEqualTo(FormParam)));
            return Enum.TryParse(rec?.Value, true, out Form f) ? f : Form.Bear;
        }

        public static void SetForm(GamePlayer p, Form f)
        {
            var rec = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId)
                .And(DB.Column("KeyName").IsEqualTo(FormParam)));
            if (rec == null)
                GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(p.ObjectId, FormParam, f.ToString()));
            else
            {
                rec.Value = f.ToString();
                GameServer.Database.SaveObject(rec);
            }
            if (p.ControlledBrain?.Body is GameNPC pet && IsNatureSpirit(pet))
                ApplyForm(p, pet, f);
            p.Out.SendMessage($"Your nature spirit takes the form of a {f.ToString().ToLower()}.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
        }

        static readonly ConditionalWeakTable<GameNPC, StrongBox<int>> _spirits = new();

        static bool IsNatureSpirit(GameNPC pet) => _spirits.TryGetValue(pet, out _);

        /// <summary>SummonDruidPet: the spirit just summoned takes its form.</summary>
        public static void OnSummoned(GameLiving druid, GameNPC pet, Spell spell)
        {
            if (druid == null || pet == null || ClassOf(druid) != Druid)
                return;
            int tier = Math.Clamp(spell.ID - 5251, 0, 4);
            _spirits.AddOrUpdate(pet, new StrongBox<int>(tier));
            ApplyForm(druid, pet, FormOf(druid));
        }

        static void ApplyForm(GameLiving druid, GameNPC pet, Form f)
        {
            int tier = _spirits.TryGetValue(pet, out StrongBox<int> b) ? b.Value : 2;
            pet.Model = f switch { Form.Bear => (ushort) 101, Form.Wolf => (ushort) 102, _ => (ushort) 966 };
            pet.Name = f switch
            {
                Form.Bear => "bear " + TierWords[tier],
                Form.Wolf => "wolf " + TierWords[tier],
                _ => (WispWords[tier] + " wisp").Trim(),
            };
            foreach (GamePlayer v in pet.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendNPCCreate(pet);
            (pet.Brain as AI.Brain.ControlledMobBrain)?.UpdatePetWindow();   // (the pet window's name)
        }

        /// <summary>GameLiving.OnAttackEnemy: a Druid's spirit goes for what the Druid attacks; the Druid's own blows may call
        /// its special.</summary>
        public static void OnAttackEnemy(GameLiving druid, AttackData ad)
        {
            if (ad?.Target is not GameLiving t || ad.Attacker != druid || ClassOf(druid) != Druid)
                return;
            if (druid.ControlledBrain is not IControlledBrain brain || brain.Body is not GameNPC pet || !pet.IsAlive || !IsNatureSpirit(pet))
                return;
            try
            {
                if (t.IsAlive && pet.TargetObject != t)
                    brain.Attack(t);
                if (!ad.IsMeleeAttack || !ad.IsHit || !t.IsAlive)
                    return;
                int nature = Math.Clamp(druid.GetModifiedSpecLevel(Specs.Nature), 1, 50);
                double chance = 5 + 20.0 * (nature - 1) / 49.0;
                if (!Util.Chance((int) Math.Round(chance)))
                    return;
                Form f = FormOf(druid);
                string said;
                switch (f)
                {
                    case Form.Bear:
                        Cast(pet, Maul, t);
                        if (t is GameNPC tn && tn.Brain is StandardMobBrain mb)
                            mb.AddToAggroList(pet, 200 + druid.Level * 20);
                        said = $"Your bear mauls {t.GetName(0, false)}!";
                        break;
                    case Form.Wolf:
                        Cast(pet, RendBleed, t);
                        Cast(pet, RendSnare, t);
                        said = $"Your wolf rends {t.GetName(0, false)}!";
                        break;
                    default:
                        GameLiving hurt = Mates(druid, 1500).OrderBy(m => m.HealthPercent).First();
                        Heal(druid, hurt, (int) ((20 + druid.Level * 4) * HealFactor(druid)), 4851, "wisp's Mending Light");
                        said = null;
                        break;
                }
                if (said != null && druid is GamePlayer dp)
                    dp.Out.SendMessage(said, eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            }
            catch (Exception e)
            {
                Console.WriteLine("[HibernianKits] spirit: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ bots

        sealed class BotTimes
        {
            public long Next, RallyReady;
        }

        static readonly ConditionalWeakTable<GameBot, BotTimes> _bots = new();

        /// <summary>BotBrain.Think: a Warden bot shouts Rallying Cry when two of its group are hurt (or one badly).</summary>
        public static void BotThink(GameBot bot)
        {
            if (bot == null || !bot.IsAlive || ClassOf(bot) != Warden || bot.IsIncapacitated)
                return;
            int regrowth = bot.GetModifiedSpecLevel(Specs.Regrowth);
            if (regrowth < RallyAt[0])
                return;
            long now = GameLoop.GameLoopTime;
            BotTimes t = _bots.GetValue(bot, _ => new BotTimes());
            if (now < t.Next || now < t.RallyReady)
                return;
            t.Next = now + 1000;
            var hurt = Mates(bot, RallyRange).Where(m => m.HealthPercent < 75).ToList();
            if (hurt.Count >= 2 || hurt.Any(m => m.HealthPercent < 45))
            {
                RallyingCry(bot, regrowth >= RallyAt[2] ? 3 : regrowth >= RallyAt[1] ? 2 : 1);
                t.RallyReady = now + RallyReuseMs;
            }
        }
    }
}

namespace DOL.GS.SkillHandler
{
    using DOL.GS.PacketHandler;

    /// <summary>Wellspring: every heal 5% stronger a rank.</summary>
    public class WellspringAbility : PropertyChangingAbility
    {
        public WellspringAbility(DbAbility dba, int level) : base(dba, level, eProperty.HealingEffectiveness) { }
        public override int GetAmountForLevel(int level) => 5 * Math.Max(0, level);
    }

    /// <summary>Warden's Vigor: less fatigue a rank; endurance back faster from rank III.</summary>
    public class WardenVigorAbility : PropertyChangingAbility
    {
        public WardenVigorAbility(DbAbility dba, int level) : base(dba, level, new[] { eProperty.FatigueConsumption, eProperty.EnduranceRegenerationAmount }) { }

        public override void Activate(GameLiving living, bool sendUpdates)
        {
            if (m_activeLiving != null)
                return;
            m_activeLiving = living;
            int lvl = living.CalculateSkillLevel(this);
            living.AbilityBonus[eProperty.FatigueConsumption] += 6 * lvl;
            living.AbilityBonus[eProperty.EnduranceRegenerationAmount] += lvl >= 3 ? 1 : 0;
        }

        public override void Deactivate(GameLiving living, bool sendUpdates)
        {
            if (m_activeLiving == null)
                return;
            int lvl = living.CalculateSkillLevel(this);
            living.AbilityBonus[eProperty.FatigueConsumption] -= 6 * lvl;
            living.AbilityBonus[eProperty.EnduranceRegenerationAmount] -= lvl >= 3 ? 1 : 0;
            m_activeLiving = null;
        }
    }

    [SkillHandler(HibernianKits.RallyKey)]
    public class RallyingCryAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            int n = HibernianKits.RallyingCry(player, ab.Level);
            if (n == 0)
                player.Out.SendMessage("Your rallying cry rings out, but no one near needs healing.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            player.DisableSkill(ab, HibernianKits.RallyReuseMs);
        }
    }

    [SkillHandler(HibernianKits.WheelKey)]
    public class SongWheelAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player != null && player.IsAlive)
                HibernianKits.UseWheel(player);
        }
    }
}
