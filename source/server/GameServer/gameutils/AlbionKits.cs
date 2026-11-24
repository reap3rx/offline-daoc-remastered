using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// Albion's classes (owner 2026-11-24, "Albion Class Rework - the plan" and his answers: "Go ahead and knock out all
    /// Albion classes"). Each has a Hibernian counterpart, the same power and its own twist; built at start-up, never written
    /// to the database. The weapon lines' class versions are in StyleRework.Albion.
    ///
    /// Casters (as ClassKits': one keeps them off, one signature):
    ///   Wizard     Rune of Embers (Pyromancy 15)   a rune at your feet bursts on the first enemy to step on it
    ///              Ice Shell (Liquifaction 18)      3 s frozen: nothing hurts you, you can't act; 60 s reuse
    ///   Theurgist  Gust Ward (Vapormancy 10)       whatever strikes you may be blown back, its swing broken
    ///              Wall of Ice (Refrigeration 14)  a wall at the ground target chills what crosses it (slower attacks)
    ///              its pets are set down where it aims (ChannelCasting.IsPlaced - SummonTheurgistPet)
    ///   Sorcerer   Disrupting Thought (Domination 8/22/38/48) an instant ranged interrupt, castable behind the mana shield
    ///              Thrall's Sacrifice (Domination 17/40) your charmed pet takes half of each blow on you, to a limit
    ///   Cabalist   Leeching Ward (Vivification 9)  whatever strikes you may lose a little health to you
    ///              Simulacrum Swap (Matter Manipulation 14) you and your simulacrum trade places; what was on you turns on it
    ///   Necromancer as vanilla (owner: "keep them as close to vanilla DAoC Necros as possible") - the charging and the one
    ///              spell per job are the realm-wide systems'
    /// Healers and support:
    ///   Friar      Sermon of the Staff (every Staff style heals the group around you), Blessed Guard (a timed parry: a
    ///              bladeturn bubble - you, your most hurt, your group, at Enhancement 2/10/18), Light Feet (a timed evade
    ///              pulses a small heal), Call to Prayer (Rejuvenation 15/30/45: a chain heal shout); the book: one cast
    ///              heal, Purify, the Encouragements, Habit of the Order (every Enhancement buff in one cast)
    ///   Cleric     Holy Aegis (the mana shield: a perfect ward smites and blinds), Judgement (its smites mark the
    ///              target: groupmates' blows on it heal them), Benediction (a stacking heal over time that blooms into
    ///              Absolution), Blessing of Avalon (every Enhancement buff in one cast), Sanctuary (a circle of light heals)
    ///   Minstrel   Song Wheel, Tempo (styles build to 5: the next mesmerize or stun instant and sure), Sharp Note (an
    ///              instant ranged interrupt), Thunderous Chord (a cone stun, 4 s), Unseen Song (the speed song plays on
    ///              in stealth)
    /// Fighters (their lines in StyleRework.Albion):
    ///   Paladin    its positional and reactive styles surge its chants (both pulse at once); Zeal (level 20): 10 s of
    ///              surges on every style and 50% stronger healing
    ///   Armsman    Hold the Line (level 20): 10 s - monsters in front of you can't get past to your group
    ///   Mercenary  Opportunist (level 20): 15 s - every evade and parry answers with a free off-hand strike
    ///   Reaver     Soul Tether (every Flexible style: 10 s, a tenth of your damage back as health, snared if it runs);
    ///              Riposte of Souls (a perfect parry: your next style casts your life drain)
    /// Stealthers:
    ///   Infiltrator Ambush, Slip Away (a dodge may stealth you: 1% a point of Stealth), Marked (positionals: an opener
    ///              always crits), Lingering Venom (positionals feed your poison: +15% and 4 s, up to 3), Garrote breaks
    ///              spells
    ///   Scout      Pinning Shot (critical / overdrawn shots root 3-5 s), Hidden Nest (a still shot from stealth from
    ///              1000+ doesn't reveal you, 30 s), Shield and Bow (blows don't break your draw - endurance pays), Fall Back
    /// Spell ids 97300-97399; ability ids 3940-3959.
    /// </summary>
    public static class AlbionKits
    {
        public const int Paladin = 1, Armsman = 2, Scout = 3, Minstrel = 4, Theurgist = 5, Cleric = 6, Wizard = 7, Sorcerer = 8,
            Infiltrator = 9, Friar = 10, Mercenary = 11, Necromancer = 12, Cabalist = 13, Reaver = 19;
        public const string KitLine = "Albion Kit Effects";

        // learned spells
        public const int RuneOfEmbers = 97300, IceShell = 97301, GustWard = 97302, WallOfIce = 97303, Disrupt = 97304,
            Thrall = 97308, LeechWard = 97310, SimSwap = 97311, SharpNote = 97312, ThunderChord = 97316, PurifyFriar = 97320,
            PurifyCleric = 97321, Habit = 97322, Benediction = 97325, Avalon = 97330, Sanctuary = 97331;
        // hidden effects
        public const int GustStagger = 97350, IceChill = 97351, LeechDrain = 97352, RuneBlast = 97353, RuneStagger = 97354,
            AegisBlind = 97355, AegisSmite = 97356, GuardSelf = 97361, GuardAlly = 97362, GuardGroup = 97363, PinRoot = 97364,
            TetherSnare = 97367, HoldRoot = 97368;

        public const int IceShellMs = 3000, GuardCooldownMs = 8000, FeetCooldownMs = 1500, FeetRadius = 400, SermonRadius = 600;
        public const int PrayerReuseMs = 30000, PrayerRange = 1500, PrayerJump = 800;
        public const int TempoMax = 5, TempoForgetMs = 30000, SurgeCooldownMs = 1500;
        public const int ZealMs = 10000, ZealReuseMs = 90000, HoldMs = 10000, HoldReuseMs = 45000, HoldReach = 450,
            OpportunistMs = 15000, OpportunistReuseMs = 120000;
        public const int TetherMs = 10000, TetherSnareRange = 450, JudgeMs = 10000, JudgeHealCooldownMs = 2000;
        public const double TetherShare = 0.10, VenomStep = 0.15;
        public const int VenomMax = 3, VenomExtendMs = 4000, RiposteWindowMs = 8000;
        public const int NestReuseMs = 30000, NestMinRange = 1000, SteadyDrawCostPercent = 5;
        public const int ThunderChordSeconds = 4;      // (owner: "no longer than 4 seconds for such a powerful AoE")
        public static readonly int[] GuardAt = { 2, 10, 18 }, PrayerAt = { 15, 30, 45 }, AegisAt = { 5, 15, 25, 35, 45 };
        public const string GuardKey = "Blessed Guard", FeetKey = "Light Feet", SermonKey = "Sermon of the Staff", PrayerKey = "Call to Prayer",
            AegisKey = "Holy Aegis", JudgementKey = "Judgement", TempoKey = "Tempo", UnseenKey = "Unseen Song", ZealKey = "Zeal",
            HoldKey = "Hold the Line", OpportunistKey = "Opportunist", TetherKey = "Soul Tether", RiposteKey = "Riposte of Souls",
            SlipKey = "Slip Away", VenomKey = "Lingering Venom", PinKey = "Pinning Shot", NestKey = "Hidden Nest", SteadyKey = "Shield and Bow";

        public static readonly HashSet<int> Interrupts = new();

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[AlbionKits] " + ex);
            }
        }

        static int _added;

        public static void Register()
        {
            _added = 0;
            // ---- the hidden effects
            Hidden(Db(GustStagger, "Buffeted", "StyleStun", "Enemy", duration: 1, effect: 2132, icon: 2132, msg1: "A gust throws you back a step!"));
            Hidden(Db(IceChill, "Chilled", "CombatSpeedDebuff", "Enemy", value: 20, duration: 3, effect: 274, icon: 274, msg1: "The ice chills your blows!"));
            var leech = Db(LeechDrain, "Leeching Ward", "Lifedrain", "Enemy", value: -100, effect: 4401, icon: 4401, msg1: "Your life is drawn away!");
            leech.Damage = 25;
            leech.DamageType = (int) eDamageType.Spirit;
            leech.LifeDrainReturn = 100;
            Hidden(leech);
            var blast = Db(RuneBlast, "Rune of Embers", "DirectDamage", "Enemy", effect: 360, icon: 360, msg1: "The rune bursts into flame under you!");
            blast.Damage = 90;
            blast.DamageType = (int) eDamageType.Heat;
            Hidden(blast);
            Hidden(Db(RuneStagger, "Staggered", "StyleStun", "Enemy", duration: 1, effect: 2132, icon: 2132));
            Hidden(Db(AegisBlind, "Blinded by Light", "ToHitDebuff", "Enemy", value: 25, duration: 5, effect: 1611, icon: 1611, msg1: "Holy light blinds you!"));
            for (int r = 1; r <= 5; r++)
            {
                var smite = Db(AegisSmite + r - 1, "Holy Aegis", "DirectDamage", "Enemy", effect: 1601, icon: 1601, msg1: "Holy light smites you!");
                smite.Damage = 15 + 20 * r;
                smite.DamageType = (int) eDamageType.Spirit;
                Hidden(smite);
            }
            Hidden(Db(GuardSelf, "Blessed Guard", "Bladeturn", "Self", duration: 30, effect: 1501, icon: 1501, msg1: "A blessed guard closes over you."));
            Hidden(Db(GuardAlly, "Blessed Guard", "Bladeturn", "Realm", range: 1500, duration: 30, effect: 1501, icon: 1501, msg1: "A blessed guard closes over you."));
            Hidden(Db(GuardGroup, "Blessed Guard", "Bladeturn", "Group", radius: 1500, duration: 30, effect: 1501, icon: 1501, msg1: "A blessed guard closes over you."));
            for (int r = 0; r < 3; r++)
                Hidden(Db(PinRoot + r, "Pinned", "SpeedDecrease", "Enemy", value: 99, duration: 3 + r, effect: 11310, icon: 11361, msg1: "An arrow pins you where you stand!"));
            Hidden(Db(TetherSnare, "Soul Tether", "StyleSpeedDecrease", "Enemy", value: 40, duration: 3, effect: 9611, icon: 9611, msg1: "The tether drags at your soul!"));
            Hidden(Db(HoldRoot, "Held", "SpeedDecrease", "Enemy", value: 99, duration: 2, effect: 11310, icon: 11361, msg1: "A wall of steel bars your way!"));

            Casters();
            int trimmed = FriarBook() + ClericBook() + MinstrelBook();
            Abilities();
            foreach (int id in Interrupts)
                ManaShield.AllowedIds.Add(id);
            Console.WriteLine($"[AlbionKits] {_added} spells added, {trimmed} trimmed");
        }

        // ------------------------------------------------------------------ the casters

        static void Casters()
        {
            // ---- Wizard
            Add("Pyromancy", 15, Db(RuneOfEmbers, "Rune of Embers", "RuneOfEmbers", "Self", radius: 150, duration: 30, power: -8, recast: 20,
                effect: 360, icon: 360, group: RuneOfEmbers, sub: RuneBlast,
                desc: "A rune of embers at your feet: the first enemy to step on it is burned and its swing broken. It lasts 30 seconds."));
            Add("Liquifaction", 18, Db(IceShell, "Ice Shell", "IceShell", "Self", duration: 3, power: -6, recast: 60, effect: 177, icon: 177,
                group: IceShell, desc: "Instant: you freeze in a shell of ice for 3 seconds - nothing hurts you, and you can't act. 60 second reuse."));
            // ---- Theurgist
            Add("Vapormancy", 10, Db(GustWard, "Gust Ward", "DefensiveProc", "Self", value: GustStagger, frequency: 25, duration: 600,
                power: -8, cast: 3, effect: 4561, icon: 4561, group: GustWard, msg1: "The wind wheels about you.", msg2: "The wind wheels about {0}.",
                desc: "The wind guards you: whatever strikes you may be blown back a step, its swing broken."));
            Add("Refrigeration", 14, Db(WallOfIce, "Wall of Ice", "IceWall", "Area", radius: 120, range: 1500, duration: 10, sub: IceChill,
                power: -8, cast: 1, recast: 25, effect: 274, icon: 274, group: WallOfIce,
                desc: "A wall of ice at your ground target: whatever crosses it is chilled and attacks slower."));
            // ---- Sorcerer
            Rank("Domination", new[] { 8, 22, 38, 48 }, new[] { "Disrupting Thought", "Disrupting Will", "Disrupting Mind", "Disrupting Soul" },
                (i, n) => Db(Disrupt, n, "DirectDamage", "Enemy", damage: new[] { 25, 60, 95, 130 }[i], damageType: (int) eDamageType.Spirit,
                    range: 1500, power: -4, recast: 12, effect: 2611, icon: 2611, group: Disrupt,
                    desc: "An instant jolt of thought that interrupts the target's casting."), true);
            Rank("Domination", new[] { 17, 40 }, new[] { "Thrall's Sacrifice", "Thrall's Devotion" },
                (i, n) => Db(Thrall, n, "ThrallsSacrifice", "Self", value: new[] { 200, 450 }[i], duration: 15, power: -8, recast: 30,
                    effect: 2619, icon: 2619, group: Thrall,
                    desc: "Your charmed pet throws itself in the way: for 15 seconds half of each blow on you goes to it instead, to a limit, while it's near."), false);
            // ---- Cabalist
            Add("Vivification", 9, Db(LeechWard, "Leeching Ward", "DefensiveProc", "Self", value: LeechDrain, frequency: 30, duration: 600,
                power: -8, cast: 3, effect: 4401, icon: 4401, group: LeechWard, msg1: "A hungry ward settles over you.", msg2: "A hungry ward settles over {0}.",
                desc: "A hungry ward guards you: whatever strikes you may lose a little health to you."));
            Add("Matter Manipulation", 14, Db(SimSwap, "Simulacrum Swap", "SimulacrumSwap", "Self", power: -6, recast: 30, effect: 4221, icon: 4221,
                group: SimSwap, desc: "Instant: you and your simulacrum trade places, and whatever was on you turns on it."));
        }

        // ------------------------------------------------------------------ the Friar's and the Cleric's books

        static readonly List<Spell> _habitBase = new(), _habitSelf = new(), _avalonBase = new(), _avalonSpec = new();

        static int FriarBook()
        {
            int n = 0;
            // Rejuvenation: the one cast heal (the regular heals) and the resurrection; the minors and the group heals go
            n += HibernianKits.ClassBaseline(Specs.Rejuvenation, "Rejuvenation", Friar, "Rejuvenation Friar Base", s => s.Group is 1331 or 1315);
            // Rebirth: the Major heals and the cures go (Purify); the Encouragements and the resurrection stay
            n += SkillBase.RemoveLineSpells("Rebirth", s => s.Group is 1020 or 110 or 100 || s.ID is 14382 or 14383);
            Add("Rebirth", 10, Db(PurifyFriar, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 1371, icon: 1371,
                group: PurifyFriar, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            // Enhancement: every buff in one cast - Habit of the Order (the base buffs on the group, your own on you)
            foreach (Spell s in SkillBase.GetSpellList("Enhancement"))
                _habitBase.Add(s);
            n += HibernianKits.ClassBaseline(Specs.Enhancement, "Enhancement", Friar, "Enhancement Friar Base", _ => false);
            foreach (Spell s in SkillBase.GetSpellList("Friar Enhancement Spec"))
                if (HabitKeeps(s))
                    _habitSelf.Add(s);
            n += SkillBase.RemoveLineSpells("Friar Enhancement Spec", s => HabitKeeps(s) || s.SpellType is eSpellType.Taunt);
            Add("Friar Enhancement Spec", 4, Db(Habit, "Habit of the Order", "AlbionBlessing", "Group", radius: 1500, power: 10, cast: 3,
                effect: 1701, icon: 1701, group: Habit,
                desc: "Every buff you know in one cast: the order's blessings on your group, and your own shields, readiness and stamina on you."));
            return n;
        }

        static bool HabitKeeps(Spell s) => s.SpellType is eSpellType.SpecArmorFactorBuff or eSpellType.DexterityQuicknessBuff or
            eSpellType.FatigueConsumptionBuff or eSpellType.ArmorAbsorptionBuff or eSpellType.HeatResistBuff or eSpellType.ColdResistBuff or
            eSpellType.MatterResistBuff;

        static int ClericBook()
        {
            int n = 0;
            // Rejuvenation: the regular and group heals and the resurrection; the minors go
            n += HibernianKits.ClassBaseline(Specs.Rejuvenation, "Rejuvenation", Cleric, "Rejuvenation Cleric Base", s => s.Group is 1331 or 1321 or 1315);
            // Rebirth (Cleric): the Major heals (the Greater do the job) and the cures go (Purify); the rest stays
            n += SkillBase.RemoveLineSpells("Rebirth (Cleric)", s => s.Group is 1020 or 110 or 100 || s.ID is 14382 or 14383);
            Add("Rebirth (Cleric)", 9, Db(PurifyCleric, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 1371, icon: 1371,
                group: PurifyCleric, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            int[] blv = { 12, 22, 34, 44 }, bval = { 15, 28, 45, 62 };
            string[] bn = { "Benediction", "Greater Benediction", "Holy Benediction", "Divine Benediction" };
            for (int i = 0; i < blv.Length; i++)
                Add("Rebirth (Cleric)", blv[i], Db(Benediction + i, bn[i], "Rejuvenation", "Realm", value: bval[i], range: 2000, power: 6 + i * 4,
                    cast: 1.5, effect: 1340, icon: 1340, group: Benediction,
                    desc: $"A friend heals {bval[i]} every 3 seconds for 15 seconds; it stacks three times (more each stack). Cast on three stacks, " +
                        "it becomes Absolution: what was left to heal comes at once, and half again."));
            Add("Rebirth (Cleric)", 16, Db(Sanctuary, "Sanctuary", "Sanctuary", "Self", value: 60, radius: 350, duration: 12, power: -10, cast: 2,
                recast: 30, effect: 1421, icon: 1421, group: Sanctuary,
                desc: "A circle of holy light at your feet heals your side within it every 2 seconds."));
            // Enhancement: every buff in one cast - Blessing of Avalon
            foreach (Spell s in SkillBase.GetSpellList("Enhancement"))
                _avalonBase.Add(s);
            n += HibernianKits.ClassBaseline(Specs.Enhancement, "Enhancement", Cleric, "Enhancement Cleric Base", _ => false);
            foreach (Spell s in SkillBase.GetSpellList("Guardian Angel"))
                if (AvalonTakes(s))
                    _avalonSpec.Add(s);
            n += SkillBase.RemoveLineSpells("Guardian Angel", AvalonTakes);
            Add("Guardian Angel", 2, Db(Avalon, "Blessing of Avalon", "AlbionBlessing", "Group", radius: 1500, power: 10, cast: 3,
                effect: 1511, icon: 1511, group: Avalon,
                desc: "Every blessing you know - armor, strength, constitution, dexterity, quickness, acuity, regeneration and the three wards - on your whole group at once."));
            return n;
        }

        static bool AvalonTakes(Spell s) => s.SpellType is eSpellType.StrengthConstitutionBuff or eSpellType.DexterityQuicknessBuff or
            eSpellType.AcuityBuff or eSpellType.SpecArmorFactorBuff or eSpellType.HealthRegenBuff or eSpellType.BodyResistBuff or
            eSpellType.SpiritResistBuff or eSpellType.EnergyResistBuff;

        static int MinstrelBook()
        {
            Rank("Instruments", new[] { 6, 16, 32, 48 }, new[] { "Sharp Note", "Sharp Chord", "Sharp Refrain", "Sharp Crescendo" },
                (i, n) => Db(SharpNote, n, "DirectDamage", "Enemy", damage: new[] { 20, 50, 85, 120 }[i], damageType: (int) eDamageType.Energy,
                    range: 1500, power: -4, recast: 12, effect: 1131, icon: 1131, group: SharpNote,
                    desc: "An instant sharp note that interrupts the target's casting."), true);
            Add("Instruments", 22, Db(ThunderChord, "Thunderous Chord", "Stun", "Cone", range: 600, radius: 60, duration: ThunderChordSeconds, power: -10, cast: 0,
                recast: 30, effect: 1161, icon: 1161, group: ThunderChord, desc: $"A thunderous chord that stuns what stands in front of you for {ThunderChordSeconds} seconds."));
            return 0;
        }

        /// <summary>Habit of the Order / Blessing of Avalon on one friend: the best rank of every buff the healer knows.</summary>
        public static int Bless(GameLiving healer, GameLiving t, Spell spell)
        {
            if (spell.Group is MidgardKits.Aesir or MidgardKits.Deep)
                return MidgardKits.Bless(healer, t, spell);     // (a Healer's Gift of the Aesir, a Shaman's Gift of the Deep)
            bool friar = spell.Group == Habit;
            int spec = healer.GetModifiedSpecLevel(Specs.Enhancement);
            IEnumerable<Spell> onAll = friar ? _habitBase.Where(s => s.Level <= healer.Level) :
                _avalonBase.Where(s => s.Level <= healer.Level).Concat(_avalonSpec.Where(s => s.Level <= spec && s.Target is not eSpellTarget.GROUP));
            IEnumerable<Spell> once = friar ? _habitSelf.Where(s => s.Level <= spec) : _avalonSpec.Where(s => s.Level <= spec && s.Target is eSpellTarget.GROUP);
            SpellLine line = SkillBase.GetSpellLine(Specs.Enhancement) ?? SkillBase.GetSpellLine(GlobalSpellsLines.Item_Effects);
            int given = 0;
            foreach (var g in onAll.GroupBy(s => (s.Group, s.SpellType)))
            {
                ScriptMgr.CreateSpellHandler(healer, g.OrderBy(s => s.Level).Last(), line)?.StartSpell(t);
                given++;
            }
            if (t == healer)
                foreach (var g in once.GroupBy(s => (s.Group, s.SpellType)))
                {
                    ScriptMgr.CreateSpellHandler(healer, g.OrderBy(s => s.Level).Last(), line)?.StartSpell(healer);
                    given++;
                }
            return given;
        }

        // ------------------------------------------------------------------ the abilities

        static void Abilities()
        {
            Ability(AegisKey, 3940, 1601, "Your mana shield (hold right click / LT) is holy light. Raised just before a blow lands - a perfect ward - it " +
                "smites the attacker and blinds it for 5 seconds (it misses more). Ranks at Smite 5, 15, 25, 35 and 45 (more damage).",
                Specs.Smite, AegisAt, Cleric);
            Ability(JudgementKey, 3941, 1608, $"Your smites mark their target for {JudgeMs / 1000} seconds: your groupmates' blows on a marked foe heal them a little.",
                Specs.Smite, new[] { 1 }, Cleric);
            Ability(SermonKey, 3942, 1321, $"Every Staff style that lands heals your group within {SermonRadius} (more the closer they stand).",
                Specs.Staff, new[] { 1 }, Friar);
            Ability(GuardKey, 3943, 1501, "A timed parry puts a blessed bladeturn on you (turns aside the next blow, 30 seconds): rank II also on your most " +
                "hurt groupmate, rank III on your whole group. Once every 8 seconds. Ranks at Enhancement 2, 10 and 18.",
                Specs.Enhancement, GuardAt, Friar);
            Ability(FeetKey, 3944, 1531, $"A timed evade pulses a small heal on you and your groupmates within {FeetRadius} (more the closer they stand).",
                "FriarCareer", new[] { 1 }, Friar);
            Ability(PrayerKey, 3945, 1321, "An instant shout: a heal that leaps from your most hurt groupmate to the next (3 at rank I, 4 at II, 5 at III), " +
                "a little less each leap. 30 second reuse.", Specs.Rejuvenation, PrayerAt, Friar);
            var wheel = new DbAbility
            {
                KeyName = HibernianKits.WheelKey, Name = HibernianKits.WheelKey, IconID = 228, InternalID = 3915, AbilityID = 3915,
                Description = "Put it on your bar. Tap it: the song that fits the moment (healing when your group is hurt, power or endurance " +
                    "otherwise, speed on the road). Hold it: a wheel of your songs - point at one and let go.",
            };
            SkillBase.AddScriptedAbility(wheel, "MinstrelCareer", 5);
            Ability(TempoKey, 3947, 1171, $"Every Slash or Thrust style that lands builds Tempo (up to {TempoMax}). At {TempoMax}, your next mesmerize or stun is " +
                "instant and can't be resisted.", Specs.Instruments, new[] { 1 }, Minstrel);
            Ability(UnseenKey, 3948, 1101, "Your speed song plays on when you stealth, and starting it doesn't bring you out of stealth.",
                Specs.Stealth, new[] { 1 }, Minstrel);
            Ability(ZealKey, 3949, 1021, $"For {ZealMs / 1000} seconds every style that lands surges your chants, and your healing is 50% stronger. " +
                $"{ZealReuseMs / 1000} second reuse. (Your positional and reactive styles always surge your chants: both pulse at once.)",
                "PaladinCareer", new[] { 20 }, Paladin);
            Ability(HoldKey, 3950, 1031, $"For {HoldMs / 1000} seconds no monster in front of you gets past you to your group: what tries is held fast. " +
                $"{HoldReuseMs / 1000} second reuse.", "ArmsmanCareer", new[] { 20 }, Armsman);
            Ability(OpportunistKey, 3951, 413, $"For {OpportunistMs / 1000} seconds every blow you evade or parry is answered by a free off-hand strike. " +
                $"{OpportunistReuseMs / 1000} second reuse.", "MercenaryCareer", new[] { 20 }, Mercenary);
            Ability(TetherKey, 3952, 9611, $"Every Flexible style that lands tethers its target for {TetherMs / 1000} seconds: a tenth of all the damage you " +
                "deal comes back to you as health, and the tethered foe is snared if it runs from you.", Specs.Flexible, new[] { 1 }, Reaver);
            Ability(RiposteKey, 3953, 9614, "A perfect parry: your next style also casts your life drain on its target - the rank before your best. " +
                $"({RiposteWindowMs / 1000} seconds to use it.)", "ReaverCareer", new[] { 2 }, Reaver);
            Ability(SlipKey, 3954, 0, "When you dodge a blow you may slip away in a puff of smoke: 1% for each point of Stealth. You are hidden, the " +
                "monsters lose you, and nothing can find you for 5 seconds - open on it again.", Specs.Stealth, new[] { 1 }, Infiltrator);
            Ability(VenomKey, 3955, 0, $"Each positional style that lands on a foe with your poison on it feeds the venom: it hits {VenomStep * 100:0}% harder " +
                $"and lasts {VenomExtendMs / 1000} seconds longer, up to {VenomMax} times.", Specs.Envenom, new[] { 1 }, Infiltrator);
            var ambush = new DbAbility
            {
                KeyName = HibernianHybrids.AmbushKey, Name = HibernianHybrids.AmbushKey, IconID = 0, InternalID = 3930, AbilityID = 3930,
                Description = "Your first blow from stealth can't be parried, blocked or dodged by a monster.",
            };
            SkillBase.AddScriptedAbility(ambush, "InfiltratorCareer", 1);
            Ability(PinKey, 3957, 0, "Your critical and overdrawn shots pin their target: rooted for 3 seconds, 4 at Longbows 20, 5 at 40 (damage frees it).",
                Specs.Longbow, new[] { 1 }, Scout);
            Ability(NestKey, 3958, 0, $"A shot from stealth, standing still, from {NestMinRange} or more away doesn't give you away: the monster searches where " +
                $"the arrow came from. Once every {NestReuseMs / 1000} seconds.", Specs.Stealth, new[] { 1 }, Scout);
            Ability(SteadyKey, 3959, 0, $"Blows don't break your draw: you hold it, and each one costs you {SteadyDrawCostPercent}% of your endurance instead.",
                Specs.Shields, new[] { 1 }, Scout);
        }

        static void Ability(string key, int id, int icon, string desc, string spec, int[] at, int cls)
        {
            var a = new DbAbility { KeyName = key, Name = key, IconID = icon, InternalID = id, AbilityID = id, Description = desc };
            for (int i = 0; i < at.Length; i++)
                SkillBase.AddScriptedAbility(a, spec, at[i], spec.EndsWith("Career") ? 0 : cls, i + 1);
        }

        // ------------------------------------------------------------------ helpers

        static void Rank(string line, int[] levels, string[] names, Func<int, string, DbSpell> make, bool interrupt)
        {
            for (int i = 0; i < levels.Length; i++)
            {
                DbSpell d = make(i, names[i]);
                d.SpellID = d.SpellGroup + i;
                Add(line, levels[i], d);
                if (interrupt)
                    Interrupts.Add(d.SpellID);
            }
        }

        static void Add(string line, int level, DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[AlbionKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(line, new Spell(d, level));
            _added++;
        }

        static void Hidden(DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[AlbionKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(KitLine, new Spell(d, 1));
        }

        static DbSpell Db(int id, string name, string type, string target, double value = 0, double damage = 0, int damageType = 0,
            int range = 0, int radius = 0, int duration = 0, int frequency = 0, int sub = 0, int power = 0, double cast = 0,
            int recast = 0, int effect = 0, int icon = 0, int group = 0, string msg1 = "", string msg2 = "", string desc = "") =>
            new DbSpell
            {
                SpellID = id, Name = name, Type = type, Target = target, Value = value, Damage = damage, DamageType = damageType,
                Range = range, Radius = radius, Duration = duration, Frequency = frequency, SubSpellID = sub, Power = power,
                CastTime = cast, RecastDelay = recast, ClientEffect = effect, Icon = icon != 0 ? icon : effect, SpellGroup = group,
                Message1 = msg1, Message2 = msg2, Description = desc != "" ? desc : name,
            };

        public static int ClassOf(GameLiving l) => HibernianKits.ClassOf(l);
        static long Now => GameLoop.GameLoopTime;

        static void Cast(GameLiving caster, int spellId, GameLiving target)
        {
            if (SkillBase.GetSpellByID(spellId) is Spell sp && target != null)
                ScriptMgr.CreateSpellHandler(caster, sp, SkillBase.GetSpellLine(GlobalSpellsLines.Combat_Styles_Effect))?.StartSpell(target);
        }

        static void Say(GameLiving l, string text, eChatType type = eChatType.CT_Spell)
        {
            if (l is GamePlayer p)
                p.Out.SendMessage(text, type, eChatLoc.CL_SystemWindow);
        }

        static void Fx(GameLiving from, GameLiving to, ushort fx)
        {
            foreach (GamePlayer v in to.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(from, to, fx, 0, false, 1);
        }

        static double Falloff(GameLiving a, GameLiving b, int radius)
        {
            double d = a == b ? 0 : a.GetDistanceTo(b);
            return d <= 150 ? 1.0 : Math.Max(0.33, 1.0 - 0.67 * (d - 150) / Math.Max(1, radius - 150));
        }

        sealed class Kit
        {
            public long ShellUntil, GuardReady, FeetReady, SurgeReady, ZealUntil, HoldUntil, OpportunistUntil, RiposteUntil,
                NestReady, NestHiddenUntil, TempoAt, JudgedUntil, JudgeHealReady, ThrallUntil, SteadyReady;
            public int Tempo, ThrallLeft;
            public GameLiving JudgedBy;
            public readonly Dictionary<GameLiving, long> Tethers = new();
        }

        static readonly ConditionalWeakTable<GameLiving, Kit> _kits = new();
        static Kit Of(GameLiving l) => _kits.GetValue(l, _ => new Kit());
        static bool Has(GameLiving l, out Kit k) => _kits.TryGetValue(l, out k);

        // ------------------------------------------------------------------ a style landed (StyleRework.AfterStyle)

        public static void AfterStyle(GameLiving owner, AttackData ad)
        {
            Style st = ad?.Style;
            if (st == null || ad.Target is not GameLiving t || owner == null)
                return;
            int cls = ClassOf(owner);
            try
            {
                switch (cls)
                {
                    case Friar when st.Spec == Specs.Staff:
                        Sermon(owner, ad);
                        break;
                    case Minstrel when st.Spec == Specs.Slash || st.Spec == Specs.Thrust:
                        AddTempo(owner);
                        break;
                    case Paladin:
                        bool zeal = Has(owner, out Kit pk) && pk.ZealUntil > Now;
                        if (zeal || st.Db.OpeningRequirementType is 1 or 2)
                            Surge(owner, zeal);
                        break;
                    case Reaver:
                        if (st.Spec == Specs.Flexible)
                            Tether(owner, t);
                        if (Has(owner, out Kit rk) && rk.RiposteUntil > Now)
                        {
                            rk.RiposteUntil = 0;
                            RiposteOfSouls(owner, t);
                        }
                        break;
                    case Infiltrator:
                        if (Array.IndexOf(StyleRework.InfiltratorMarks, st.ID) >= 0)
                        {
                            HibernianHybrids.Expose(t);
                            Say(owner, $"{t.GetName(0, true)} is marked - your next opener on it will find its mark.");
                        }
                        if (st.ID is StyleRework.SlashDetaunt or StyleRework.ThrustDetaunt or StyleRework.DualDetaunt)
                            HibernianHybrids.DropThreat(owner, t, 25);
                        if (st.Spec == Specs.Critical_Strike && st.ID == HibernianHybrids.Garrote)
                            HibernianHybrids.BreakSpell(owner, t, "Your garrote");
                        if (st.Db.OpeningRequirementType == 2)
                            FeedVenom(owner, t);
                        break;
                    case Scout when st.ID == StyleRework.ThrustDetaunt && st.Spec == Specs.Thrust:
                        HibernianHybrids.DropThreat(owner, t, 50);
                        break;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"[AlbionKits] after {st.Name}: {e.Message}");
            }
        }

        // ------------------------------------------------------------------ a blow turned aside (AttackComponent)

        public static void AfterDefense(AttackData ad)
        {
            if (ad?.Target is not GameLiving d || ad.Attacker is not GameLiving a || !d.IsAlive)
                return;
            int cls = ClassOf(d);
            if (cls is not (Friar or Reaver or Infiltrator or Mercenary))
                return;
            try
            {
                bool action = d is GamePlayer p && ActionCombat.IsActive(p) && ad.ActionDefense is not eActionDefense.None;
                bool timed = action && !ad.ActionAuto;
                bool dice = !action && Util.Chance(35);
                bool parried = action ? ad.ActionDefense is eActionDefense.Parry : ad.AttackResult is eAttackResult.Parried;
                bool evaded = action ? ad.ActionDefense is eActionDefense.Dodge : ad.AttackResult is eAttackResult.Evaded;
                switch (cls)
                {
                    case Friar when parried && (timed || dice):
                        BlessedGuard(d);
                        break;
                    case Friar when evaded && (timed || dice):
                        LightFeet(d);
                        break;
                    case Reaver when parried && (timed || dice):
                        Of(d).RiposteUntil = Now + RiposteWindowMs;
                        Say(d, "Riposte of Souls! Your next style drains life.");
                        break;
                    case Infiltrator when evaded && !d.IsStealthed && Util.Chance((int) Math.Round(HibernianHybrids.VoidstepPercent(d.GetModifiedSpecLevel(Specs.Stealth)))):
                        new ECSGameTimer(d, _ =>
                        {
                            HibernianHybrids.Voidstep(d, "Slip Away! A puff of smoke, and you're gone - nothing can find you for a few seconds.");
                            return 0;
                        }, HibernianHybrids.VoidstepDelayMs);
                        break;
                    case Mercenary when (evaded || parried) && Has(d, out Kit mk) && mk.OpportunistUntil > Now:
                        OpportunistStrike(d, a);
                        break;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[AlbionKits] after defense: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ the Friar

        public static void Sermon(GameLiving f, AttackData ad)
        {
            int dealt = ad.Damage + ad.CriticalDamage;
            int baseHeal = (int) (Math.Max(dealt * 0.35, f.Level * 1.0) * HibernianKits.HealFactor(f));
            foreach (GameLiving m in HibernianKits.Mates(f, SermonRadius))
                HibernianKits.Heal(f, m, (int) (baseHeal * Falloff(f, m, SermonRadius)), 1321, "Sermon of the Staff");
        }

        public static int GuardRank(GameLiving f)
        {
            int spec = f.GetModifiedSpecLevel(Specs.Enhancement);
            return spec >= GuardAt[2] ? 3 : spec >= GuardAt[1] ? 2 : spec >= GuardAt[0] ? 1 : 0;
        }

        public static void BlessedGuard(GameLiving f)
        {
            int rank = GuardRank(f);
            Kit k = Of(f);
            if (rank == 0 || Now < k.GuardReady)
                return;
            k.GuardReady = Now + GuardCooldownMs;
            if (rank >= 3 && f.Group != null)
            {
                Cast(f, GuardGroup, f);
                return;
            }
            Cast(f, GuardSelf, f);
            if (rank >= 2 && HibernianKits.Mates(f, 1500).Where(m => m != f && m.Health < m.MaxHealth).OrderBy(m => m.HealthPercent).FirstOrDefault() is GameLiving hurt)
                Cast(f, GuardAlly, hurt);
        }

        public static void LightFeet(GameLiving f)
        {
            Kit k = Of(f);
            if (Now < k.FeetReady)
                return;
            k.FeetReady = Now + FeetCooldownMs;
            int baseHeal = (int) ((8 + f.Level * 1.6) * HibernianKits.HealFactor(f));
            foreach (GameLiving m in HibernianKits.Mates(f, FeetRadius))
                HibernianKits.Heal(f, m, (int) (baseHeal * Falloff(f, m, FeetRadius)), 1531, "Light Feet");
        }

        /// <summary>Call to Prayer: a heal leaping over the most hurt; how many it healed.</summary>
        public static int CallToPrayer(GameLiving f, int rank)
        {
            int jumps = 2 + Math.Clamp(rank, 1, 3);
            int heal = (int) ((30 + f.Level * 3 + f.GetModifiedSpecLevel(Specs.Rejuvenation) * 3) * HibernianKits.HealFactor(f));
            var pool = HibernianKits.Mates(f, PrayerRange).Where(m => m.Health < m.MaxHealth).ToList();
            GameLiving at = f;
            int n = 0;
            foreach (GamePlayer v in f.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(f, eEmote.Pray);
            while (n < jumps && pool.Count > 0)
            {
                GameLiving next = pool.Where(m => n == 0 || at.IsWithinRadius(m, PrayerJump)).OrderBy(m => m.HealthPercent).FirstOrDefault();
                if (next == null)
                    break;
                pool.Remove(next);
                HibernianKits.Heal(f, next, heal, 1321, "Call to Prayer");
                heal = heal * 9 / 10;
                at = next;
                n++;
            }
            return n;
        }

        // ------------------------------------------------------------------ the Cleric

        public static int AegisRank(GameLiving c)
        {
            int spec = c.GetModifiedSpecLevel(Specs.Smite), rank = 0;
            foreach (int at in AegisAt)
                if (spec >= at)
                    rank++;
            return rank;
        }

        /// <summary>ManaShield.Pay: a Cleric's perfect ward smites the attacker and blinds it.</summary>
        public static void HolyAegis(GamePlayer c, GameLiving attacker)
        {
            if (ClassOf(c) != Cleric || attacker == null || !attacker.IsAlive)
                return;
            int rank = AegisRank(c);
            if (rank == 0)
                return;
            Cast(c, AegisSmite + rank - 1, attacker);
            Cast(c, AegisBlind, attacker);
            c.Out.SendMessage($"Holy light bursts from your ward and smites {attacker.GetName(0, false)}!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
        }

        static bool IsSmite(ISpellHandler h) => h?.SpellLine?.KeyName is "Smiting" or "Terrible Hammer" && h.Spell?.SpellType is eSpellType.DirectDamage;

        /// <summary>GameLiving.OnAttackEnemy: a Cleric's smite marks its target (Judgement); a groupmate's blow on a marked foe
        /// heals that groupmate.</summary>
        public static void OnAttackEnemy(GameLiving attacker, AttackData ad)
        {
            if (ad?.Target is not GameLiving t || attacker == null)
                return;
            try
            {
                if (ClassOf(attacker) == Cleric && ad.AttackType == AttackData.eAttackType.Spell && IsSmite(ad.SpellHandler) && t.IsAlive)
                {
                    Kit tk = Of(t);
                    tk.JudgedBy = attacker;
                    tk.JudgedUntil = Now + JudgeMs;
                    return;
                }
                if (!ad.IsMeleeAttack || !ad.IsHit || !Has(t, out Kit k) || k.JudgedUntil <= Now || k.JudgedBy is not GameLiving cleric)
                    return;
                if (attacker != cleric && (attacker.Group == null || attacker.Group != cleric.Group))
                    return;
                Kit ak = Of(attacker);
                if (Now < ak.JudgeHealReady)
                    return;
                ak.JudgeHealReady = Now + JudgeHealCooldownMs;
                int heal = (int) ((10 + cleric.Level * 1.2 + cleric.GetModifiedSpecLevel(Specs.Smite) * 0.8) * HibernianKits.HealFactor(cleric));
                HibernianKits.Heal(cleric, attacker, heal, 1608, "Judgement");
            }
            catch (Exception e)
            {
                Console.WriteLine("[AlbionKits] judgement: " + e.Message);
            }
        }

        public static bool IsJudged(GameLiving t) => t != null && Has(t, out Kit k) && k.JudgedUntil > Now;

        // ------------------------------------------------------------------ the Minstrel

        public static void AddTempo(GameLiving m)
        {
            Kit k = Of(m);
            if (Now - k.TempoAt > TempoForgetMs)
                k.Tempo = 0;
            k.TempoAt = Now;
            if (k.Tempo >= TempoMax)
                return;
            k.Tempo++;
            Say(m, k.Tempo >= TempoMax ? $"Tempo {TempoMax}/{TempoMax}: your next mesmerize or stun is instant and sure!" : $"Tempo {k.Tempo}/{TempoMax}.");
        }

        public static int TempoOf(GameLiving m) => Has(m, out Kit k) && Now - k.TempoAt <= TempoForgetMs ? k.Tempo : 0;

        static bool TempoSpell(Spell s) => s != null && s.SpellType is eSpellType.Mesmerize or eSpellType.Stun;

        /// <summary>SpellHandler.CalculateCastingTime: a Minstrel's mesmerize or stun at full Tempo is instant.</summary>
        public static bool TempoInstant(GameLiving caster, Spell spell) =>
            caster != null && ClassOf(caster) == Minstrel && TempoSpell(spell) && TempoOf(caster) >= TempoMax;

        static readonly ConditionalWeakTable<ISpellHandler, object> _sure = new();

        /// <summary>CCSpellHandler: a mesmerize or stun spent at full Tempo can't be resisted (all its targets).</summary>
        public static bool TempoSure(ISpellHandler h)
        {
            if (h == null)
                return false;
            if (_sure.TryGetValue(h, out _))
                return true;
            if (!TempoInstant(h.Caster, h.Spell))
                return false;
            Of(h.Caster).Tempo = 0;
            _sure.Add(h, new object());
            Say(h.Caster, "Tempo! Your music can't be denied.");
            return true;
        }

        public static bool IsSpeedSong(Spell s) => s != null && s.SpellType is eSpellType.SpeedEnhancement && s.NeedInstrument;

        /// <summary>SpellHandler: a Minstrel starting its speed song keeps its stealth (Unseen Song).</summary>
        public static bool QuietSpell(GameLiving caster, Spell spell) => ClassOf(caster) == Minstrel && IsSpeedSong(spell);

        /// <summary>StealthECSEffect: a Minstrel's speed song plays on in stealth.</summary>
        public static bool KeepsSongInStealth(GameLiving m, ECSGameEffect e) =>
            ClassOf(m) == Minstrel && e is ECSGameSpellEffect se && IsSpeedSong(se.SpellHandler?.Spell);

        // ------------------------------------------------------------------ the Paladin

        /// <summary>The Paladin's chants pulse at once.</summary>
        public static int Surge(GameLiving p, bool zeal = false)
        {
            Kit k = Of(p);
            if (!zeal && Now < k.SurgeReady)
                return 0;
            k.SurgeReady = Now + SurgeCooldownMs;
            int n = 0;
            foreach (ECSPulseEffect e in p.effectListComponent.GetPulseEffects())
                if (e.SpellHandler?.SpellLine?.KeyName == Specs.Chants && e.IsActive)
                {
                    e.NextTick = Now;
                    n++;
                }
            if (n > 0)
                Say(p, n == 1 ? "Your chant surges!" : "Your chants surge!");
            return n;
        }

        public static bool Zeal(GameLiving p)
        {
            Kit k = Of(p);
            if (k.ZealUntil > Now)
                return false;
            k.ZealUntil = Now + ZealMs;
            p.AbilityBonus[eProperty.HealingEffectiveness] += 50;
            Fx(p, p, 1021);
            Say(p, $"Zeal! For {ZealMs / 1000} seconds every blow surges your chants.", eChatType.CT_Important);
            new ECSGameTimer(p, _ =>
            {
                p.AbilityBonus[eProperty.HealingEffectiveness] -= 50;
                return 0;
            }, ZealMs);
            return true;
        }

        // ------------------------------------------------------------------ the Armsman

        public static bool HoldTheLine(GameLiving a)
        {
            Kit k = Of(a);
            if (k.HoldUntil > Now)
                return false;
            k.HoldUntil = Now + HoldMs;
            foreach (GamePlayer v in a.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(a, eEmote.Military);
            Say(a, "You plant your feet: none shall pass!", eChatType.CT_Important);
            var held = new Dictionary<GameNPC, long>();
            new ECSGameTimer(a, _ =>
            {
                if (!a.IsAlive || Now > k.HoldUntil)
                    return 0;
                foreach (GameNPC n in a.GetNPCsInRadius(HoldReach))
                {
                    if (!n.IsAlive || n.TargetObject == a || n.TargetObject is not GameLiving victim || !a.IsObjectInFront(n, 150) ||
                        !GameServer.ServerRules.IsAllowedToAttack(a, n, true))
                        continue;
                    if (victim.Group == null || victim.Group != a.Group)
                        continue;
                    if (held.TryGetValue(n, out long at) && Now - at < 1800)
                        continue;
                    held[n] = Now;
                    Cast(a, HoldRoot, n);
                    if (n.Brain is StandardMobBrain b)
                        b.AddToAggroList(a, 50 + a.Level * 5);
                }
                return 500;
            }, 100);
            return true;
        }

        // ------------------------------------------------------------------ the Mercenary

        public static bool Opportunist(GameLiving m)
        {
            Kit k = Of(m);
            if (k.OpportunistUntil > Now)
                return false;
            k.OpportunistUntil = Now + OpportunistMs;
            Fx(m, m, 413);
            Say(m, $"Opportunist! For {OpportunistMs / 1000} seconds every blow you turn aside gets an answer.", eChatType.CT_Important);
            return true;
        }

        static void OpportunistStrike(GameLiving m, GameLiving foe)
        {
            if (!foe.IsAlive || !m.IsWithinRadius(foe, 400))
                return;
            int dmg = (int) ((10 + m.Level * 2.4) * (1.0 + m.GetModifiedSpecLevel(Specs.Dual_Wield) / 100.0));
            var ad = new AttackData
            {
                Attacker = m, Target = foe, Damage = dmg, DamageType = eDamageType.Slash, AttackType = AttackData.eAttackType.MeleeDualWield,
                AttackResult = eAttackResult.HitUnstyled, CausesCombat = true,
            };
            foe.OnAttackedByEnemy(ad);
            m.DealDamage(ad);
            foreach (GamePlayer v in m.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            {
                v.Out.SendCombatAnimation(m, foe, 0, 0, 0, 0, 0x0A, foe.HealthPercent);
                v.Out.SendSpellEffectAnimation(m, foe, StyleRework.SweepHitFx, 0, false, 1);
            }
            Say(m, $"Opportunist: your off-hand answers {foe.GetName(0, false)} for {dmg} damage!", eChatType.CT_YouHit);
        }

        // ------------------------------------------------------------------ the Reaver

        public static void Tether(GameLiving r, GameLiving t)
        {
            if (!t.IsAlive)
                return;
            Kit k = Of(r);
            bool fresh = !k.Tethers.TryGetValue(t, out long until) || until <= Now;
            k.Tethers[t] = Now + TetherMs;
            if (!fresh)
                return;
            Fx(r, t, 9611);
            Say(r, $"Soul Tether: {t.GetName(0, false)} is bound to you.");
            new ECSGameTimer(r, _ =>
            {
                if (!k.Tethers.TryGetValue(t, out long u) || u <= Now || !t.IsAlive || !r.IsAlive)
                {
                    k.Tethers.Remove(t);
                    return 0;
                }
                if (t.IsMoving && !r.IsWithinRadius(t, TetherSnareRange))
                    Cast(r, TetherSnare, t);
                return 1000;
            }, 1000);
        }

        public static bool IsTethered(GameLiving r, GameLiving t) => Has(r, out Kit k) && k.Tethers.TryGetValue(t, out long u) && u > Now;

        /// <summary>GameLiving.DealDamage: a Reaver with a tether out gets a tenth of the damage it deals back as health.</summary>
        public static void AfterDeal(GameLiving attacker, AttackData ad)
        {
            if (attacker == null || ad == null || !Has(attacker, out Kit k) || k.Tethers.Count == 0 || ClassOf(attacker) != Reaver)
                return;
            if (!k.Tethers.Values.Any(u => u > Now))
                return;
            int heal = (int) ((ad.Damage + ad.CriticalDamage) * TetherShare);
            if (heal > 0 && attacker.IsAlive && attacker.Health < attacker.MaxHealth)
                attacker.ChangeHealth(attacker, eHealthChangeType.Spell, heal);
        }

        static Spell DrainFor(GameLiving r)
        {
            List<Spell> list = SkillBase.GetSpellList(Specs.Soulrending);
            int spec = r.GetModifiedSpecLevel(Specs.Soulrending);
            var drains = list.Where(s => s.SpellType is eSpellType.Lifedrain && s.Level <= Math.Max(1, spec)).OrderBy(s => s.Level).ToList();
            if (drains.Count == 0)
                return null;
            return drains.Count >= 2 ? drains[^2] : drains[^1];
        }

        static void RiposteOfSouls(GameLiving r, GameLiving t)
        {
            Spell sp = DrainFor(r);
            SpellLine line = SkillBase.GetSpellLine(Specs.Soulrending);
            if (sp == null || line == null || !t.IsAlive)
                return;
            ScriptMgr.CreateSpellHandler(r, sp, line)?.StartSpell(t);
            Say(r, $"Riposte of Souls: {sp.Name} drains {t.GetName(0, false)}!");
        }

        // ------------------------------------------------------------------ the Infiltrator: Lingering Venom

        static readonly ConditionalWeakTable<ECSGameEffect, StrongBox<int>> _venom = new();

        static ECSGameSpellEffect PoisonOn(GameLiving caster, GameLiving t) =>
            t?.effectListComponent.GetSpellEffects(eEffect.DamageOverTime)?
                .FirstOrDefault(e => e.IsActive && e.SpellHandler?.Caster == caster && e.SpellHandler.SpellLine?.KeyName == GlobalSpellsLines.Mundane_Poisons);

        internal static void FeedVenom(GameLiving i, GameLiving t)
        {
            ECSGameSpellEffect e = PoisonOn(i, t);
            if (e == null)
                return;
            StrongBox<int> box = _venom.GetValue(e, _ => new StrongBox<int>(0));
            if (box.Value >= VenomMax)
                return;
            box.Value++;
            if (e.Duration > 0)
                e.ExpireTick += VenomExtendMs;
            Say(i, $"Lingering Venom {box.Value}/{VenomMax}: your poison in {t.GetName(0, false)} runs deeper.");
        }

        public static double VenomFactor(int stacks) => 1.0 + VenomStep * Math.Clamp(stacks, 0, VenomMax);

        /// <summary>DoTSpellHandler: an Infiltrator's fed poison hits harder.</summary>
        public static double DotFactor(GameLiving caster, GameLiving t, ISpellHandler h)
        {
            if (h?.SpellLine?.KeyName != GlobalSpellsLines.Mundane_Poisons || ClassOf(caster) is not (Infiltrator or MidgardKits.Shadowblade))
                return 1.0;
            ECSGameSpellEffect e = PoisonOn(caster, t);
            return e != null && _venom.TryGetValue(e, out StrongBox<int> box) ? VenomFactor(box.Value) : 1.0;
        }

        // ------------------------------------------------------------------ the Scout

        public static int PinSeconds(int longbows) => longbows >= 40 ? 5 : longbows >= 20 ? 4 : 3;

        /// <summary>ActionCombat.Loose: a critical or overdrawn shot pins its target as it lands.</summary>
        public static void PinningShot(GamePlayer p, GameLiving target, int flightMs)
        {
            if (p == null || target == null || ClassOf(p) != Scout)
                return;
            int secs = PinSeconds(p.GetModifiedSpecLevel(Specs.Longbow));
            new ECSGameTimer(p, _ =>
            {
                if (target.IsAlive && p.IsAlive)
                {
                    Cast(p, PinRoot + secs - 3, target);
                    Say(p, $"Your arrow pins {target.GetName(0, false)} where it stands!");
                }
                return 0;
            }, Math.Max(1, flightMs + 120));
        }

        /// <summary>ActionCombat.Loose: a Scout's still shot from stealth from far off keeps it hidden (Hidden Nest).</summary>
        public static bool HiddenNestShot(GamePlayer p, GameLiving target, int flightMs)
        {
            if (p == null || target == null || !p.IsStealthed || ClassOf(p) != Scout || p.IsMoving)
                return false;
            Kit k = Of(p);
            if (Now < k.NestReady || p.GetDistanceTo(target) < NestMinRange)
                return false;
            k.NestReady = Now + NestReuseMs;
            k.NestHiddenUntil = Now + flightMs + 600;
            var from = new Point3D(p.X, p.Y, p.Z);
            new ECSGameTimer(p, _ =>
            {
                if (target is GameNPC n && n.IsAlive && n.Brain is IOldAggressiveBrain brain && n.Brain is not IControlledBrain)
                {
                    brain.RemoveFromAggroList(p);
                    if (n.TargetObject == p)
                    {
                        n.TargetObject = null;
                        n.attackComponent.StopAttack();
                    }
                    n.WalkTo(from, (short) Math.Max((int) n.MaxSpeed, 150));
                    Say(p, $"Your arrow flies from your hidden nest - {n.GetName(0, false)} searches for you.");
                }
                return 0;
            }, Math.Max(1, flightMs + 80));
            return true;
        }

        public static bool KeepsHidden(GamePlayer p) => p != null && Has(p, out Kit k) && k.NestHiddenUntil > Now;

        /// <summary>ActionCombat's draw: a Scout's draw holds through a blow, its endurance paying (Shield and Bow).</summary>
        public static bool SteadyDraw(GamePlayer p)
        {
            if (p == null || ClassOf(p) != Scout || p.GetModifiedSpecLevel(Specs.Shields) < 1)
                return false;
            Kit k = Of(p);
            if (Now < k.SteadyReady)
                return true;                                  // (the same flurry of blows pays once)
            int cost = Math.Max(1, p.MaxEndurance * SteadyDrawCostPercent / 100);
            if (p.Endurance < cost)
                return false;
            p.ChangeEndurance(p, eEnduranceChangeType.Spell, -cost);
            k.SteadyReady = Now + 1000;
            return true;
        }

        // ------------------------------------------------------------------ the casters' spells (spells/AlbionKitSpells.cs)

        public static bool Shelled(GameLiving l) => l != null && Has(l, out Kit k) && k.ShellUntil > Now;

        public static void Shell(GameLiving w, int ms, ushort fx)
        {
            Kit k = Of(w);
            k.ShellUntil = Now + ms;
            w.attackComponent.StopAttack();
            if (w.IsCasting)
                w.StopCurrentSpellcast();
            bool wasStunned = w.IsStunned;
            w.IsStunned = true;
            (w as GamePlayer)?.Out.SendUpdateMaxSpeed();
            Fx(w, w, fx);
            new ECSGameTimer(w, _ =>
            {
                if (Now < k.ShellUntil && w.IsAlive)
                {
                    Fx(w, w, fx);
                    return 1000;
                }
                if (!wasStunned && !w.effectListComponent.ContainsEffectForEffectType(eEffect.Stun))
                    w.IsStunned = false;
                (w as GamePlayer)?.Out.SendUpdateMaxSpeed();
                Say(w, "The ice shell cracks and falls away.");
                return 0;
            }, 1000);
        }

        public static void StartThrall(GameLiving s, int limit, int ms)
        {
            Kit k = Of(s);
            k.ThrallLeft = limit;
            k.ThrallUntil = Now + ms;
        }

        /// <summary>GameLiving.TakeDamage: a Sorcerer's charmed pet takes half of each blow, to a limit, while it's near. What
        /// is left for the Sorcerer.</summary>
        public static int ThrallTakes(GameLiving s, GameObject source, eDamageType type, int amount)
        {
            if (amount <= 0 || s == null || !Has(s, out Kit k) || k.ThrallUntil <= Now || k.ThrallLeft <= 0)
                return amount;
            if (s.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive || !s.IsWithinRadius(pet, 1000))
                return amount;
            int share = Math.Min(amount / 2, k.ThrallLeft);
            if (share <= 0)
                return amount;
            k.ThrallLeft -= share;
            pet.TakeDamage(source, type, share, 0);
            if (k.ThrallLeft <= 0)
                Say(s, "Your thrall can take no more for you.");
            return amount - share;
        }

        // ------------------------------------------------------------------ bots

        sealed class BotTimes
        {
            public long Next, PrayerReady, ZealReady, HoldReady, OppReady;
        }

        static readonly ConditionalWeakTable<GameBot, BotTimes> _bots = new();

        /// <summary>BotBrain.Think: a Friar bot's Call to Prayer, a Paladin's Zeal, an Armsman's Hold the Line, a
        /// Mercenary's Opportunist.</summary>
        public static void BotThink(GameBot bot)
        {
            if (bot == null || !bot.IsAlive || bot.IsIncapacitated)
                return;
            int cls = ClassOf(bot);
            if (cls is not (Friar or Paladin or Armsman or Mercenary))
                return;
            long now = Now;
            BotTimes t = _bots.GetValue(bot, _ => new BotTimes());
            if (now < t.Next)
                return;
            t.Next = now + 1000;
            switch (cls)
            {
                case Friar:
                    int rej = bot.GetModifiedSpecLevel(Specs.Rejuvenation);
                    if (rej < PrayerAt[0] || now < t.PrayerReady)
                        return;
                    var hurt = HibernianKits.Mates(bot, PrayerRange).Where(m => m.HealthPercent < 75).ToList();
                    if (hurt.Count >= 2 || hurt.Any(m => m.HealthPercent < 45))
                    {
                        CallToPrayer(bot, rej >= PrayerAt[2] ? 3 : rej >= PrayerAt[1] ? 2 : 1);
                        t.PrayerReady = now + PrayerReuseMs;
                    }
                    break;
                case Paladin when bot.Level >= 20 && bot.InCombat && now >= t.ZealReady:
                    if (HibernianKits.Mates(bot, 1500).Count(m => m.HealthPercent < 70) >= 2 && Zeal(bot))
                        t.ZealReady = now + ZealReuseMs;
                    break;
                case Armsman when bot.Level >= 20 && bot.InCombat && now >= t.HoldReady && bot.Group != null:
                    if (bot.GetNPCsInRadius(HoldReach).Cast<GameNPC>().Count(n => n.IsAlive && n.TargetObject is GameLiving v && v != bot && v.Group == bot.Group) >= 2 &&
                        HoldTheLine(bot))
                        t.HoldReady = now + HoldReuseMs;
                    break;
                case Mercenary when bot.Level >= 20 && bot.InCombat && now >= t.OppReady:
                    if (bot.GetNPCsInRadius(400).Cast<GameNPC>().Any(n => n.IsAlive && n.TargetObject == bot) && Opportunist(bot))
                        t.OppReady = now + OpportunistReuseMs;
                    break;
            }
        }
    }
}

namespace DOL.GS.SkillHandler
{
    using DOL.GS.PacketHandler;

    [SkillHandler(AlbionKits.PrayerKey)]
    public class CallToPrayerAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (AlbionKits.CallToPrayer(player, ab.Level) == 0)
                player.Out.SendMessage("Your prayer rings out, but no one near needs healing.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            player.DisableSkill(ab, AlbionKits.PrayerReuseMs);
        }
    }

    [SkillHandler(AlbionKits.ZealKey)]
    public class ZealAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (AlbionKits.Zeal(player))
                player.DisableSkill(ab, AlbionKits.ZealReuseMs);
        }
    }

    [SkillHandler(AlbionKits.HoldKey)]
    public class HoldTheLineAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (AlbionKits.HoldTheLine(player))
                player.DisableSkill(ab, AlbionKits.HoldReuseMs);
        }
    }

    [SkillHandler(AlbionKits.OpportunistKey)]
    public class OpportunistAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (AlbionKits.Opportunist(player))
                player.DisableSkill(ab, AlbionKits.OpportunistReuseMs);
        }
    }
}
