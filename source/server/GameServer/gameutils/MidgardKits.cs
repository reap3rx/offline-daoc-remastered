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
    /// Midgard's classes (owner 2026-11-24, "Midgard Class Rework - the plan" and his answers: "Go ahead with the build of
    /// Midgard's classes"). Each has a Hibernian and an Albion counterpart, the same power and its own Norse twist; built at
    /// start-up, never written to the database. The weapon lines' class versions are in StyleRework.Midgard. The Valkyrie is
    /// left out (owner: "It's a catacombs class").
    ///
    /// The grip (every Midgard melee class; Sword, Axe, Hammer and Spear styles) - risk against reward (owner: "Maybe they
    /// get more offense but take a bit more damage ... make sure it's balanced"):
    ///   two-handed      the style hits 10% harder, and you take 10% more damage for 5 seconds
    ///   weapon and board no extra damage, and you take 10% less damage for 5 seconds
    ///   off hand empty  a third of the style's endurance comes back
    /// Casters (two spells each: one keeps them off, one signature):
    ///   Runemaster   Raven Ward (Runes of Suppression 10)   Runic Detonation (passive, Runecarving)
    ///   Spiritmaster Ward of the Einherjar (Spirit Suppression 10)   Valhalla's Charge (Summoning 15)
    ///   Bonedancer   Grasping Bones (Bone Army 14)   March of the Dead (Bone Army 25)
    /// Healers and support:
    ///   Healer   Eir's Aegis (the mana shield: a perfect ward mesmerizes), Stillness (+20% heals near what you hold),
    ///            Eir's Blessing (a stacking heal over time that blooms), Gift of the Aesir, Purify; the glances go
    ///   Shaman   Blight Feast (your rot heals your most hurt), Spore Ward (a perfect ward diseases), Mycelial Ring, Gift of
    ///            the Deep, Purify
    ///   Skald    Song Wheel, Saga (styles build to 5: the next shout hits a cone and rallies the group), War Howl breaks
    ///            spells, Battle Roar a dazing cone, Song of the Aesir (one resist song)
    /// Fighters: Warrior Iron Stand, Thane Thunderstruck, Berserker Blood Rage (and rage below half health), Savage
    ///   Kelgor's Howl (and the blood price).
    /// Stealthers: Shadowblade Ambush, Hel's Mist, Marked, Twin Ambush, Lingering Venom, Garrote; Hunter Mark the Prey,
    ///   Leap Away.
    /// Spell ids 97400-97499; ability ids 3960-3999.
    /// </summary>
    public static class MidgardKits
    {
        public const int Thane = 21, Warrior = 22, Shadowblade = 23, Skald = 24, Hunter = 25, Healer = 26, Spiritmaster = 27,
            Shaman = 28, Runemaster = 29, Bonedancer = 30, Berserker = 31, Savage = 32;
        public const string KitLine = "Midgard Kit Effects";

        // learned spells
        public const int RavenWard = 97400, ValhallaCharge = 97401, EinherjarWard = 97402, GraspingBones = 97403, MarchOfTheDead = 97404,
            PurifyHealer = 97405, PurifyShaman = 97406, Aesir = 97407, Deep = 97408, EirsBlessing = 97410, MycelialRing = 97415,
            SongOfAesir = 97420;
        // hidden effects
        public const int RavenBlind = 97450, EinherjarCall = 97451, ChargeStun = 97452, BonesSnare = 97453, AegisMez = 97454,
            SporeDisease = 97455, RingSnare = 97456, MidStagger = 97457, RoarDaze = 97458;

        public const int GripMs = 5000, RageReuseMs = 90000, RageMs = 15000, RageMax = 5, IronMs = 10000, IronReuseMs = 60000,
            ThunderMs = 10000, ThunderReuseMs = 90000, HowlReuseMs = 60000, SagaMax = 5, SagaForgetMs = 30000,
            DetonateMs = 6000, MarchMs = 10000, PreyMs = 10000, HowlBreakMs = 12000, StillnessRange = 1500, FeastCooldownMs = 1000;
        public const double GripBonus = 0.10, GripRisk = 1.10, GripGuard = 0.90, RageLow = 0.15, RageStep = 0.05, PreyFactor = 1.20,
            StillnessFactor = 1.20, BloodPricePercent = 2, DetonateShare = 0.30, TwinShare = 0.25, ArcShare = 1.0;
        public const string GripKey = "Grip", RunicKey = "Runic Detonation", AegisKey = "Eir's Aegis", StillnessKey = "Stillness",
            FeastKey = "Blight Feast", SporeKey = "Spore Ward", SagaKey = "Saga", IronKey = "Iron Stand", ThunderKey = "Thunderstruck",
            RageKey = "Blood Rage", HowlKey = "Kelgor's Howl", MistKey = "Hel's Mist", TwinKey = "Twin Ambush", PreyKey = "Mark the Prey",
            FuryKey = "Fury";

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[MidgardKits] " + ex);
            }
        }

        static int _added;

        public static void Register()
        {
            _added = 0;
            // ---- the hidden effects
            Hidden(Db(RavenBlind, "Huginn's Wings", "ToHitDebuff", "Enemy", value: 20, duration: 4, effect: 2610, icon: 2610, msg1: "Black wings beat about your eyes!"));
            Hidden(Db(EinherjarCall, "Call of the Einherjar", "EinherjarCall", "Enemy", effect: 2801, icon: 2801));
            Hidden(Db(ChargeStun, "Valhalla's Charge", "Stun", "Enemy", duration: 2, effect: 2132, icon: 2132, msg1: "A spirit warrior crashes into you!"));
            Hidden(Db(BonesSnare, "Grasping Bones", "SpeedDecrease", "Enemy", value: 50, duration: 8, effect: 10031, icon: 10031, msg1: "Bony hands clutch at your legs!"));
            Hidden(Db(AegisMez, "Eir's Aegis", "Mesmerize", "Enemy", duration: 3, effect: 3301, icon: 3301, msg1: "Eir's calm falls over you."));
            Hidden(Db(SporeDisease, "Spore Ward", "Disease", "Enemy", value: 15, duration: 15, effect: 3421, icon: 3421, msg1: "Spores choke you!"));
            Hidden(Db(RingSnare, "Mycelial Ring", "SpeedDecrease", "Enemy", value: 35, duration: 3, effect: 3431, icon: 3431, msg1: "Threads of fungus cling to you!"));
            Hidden(Db(MidStagger, "Staggered", "StyleStun", "Enemy", duration: 2, effect: 2132, icon: 2132));
            Hidden(Db(RoarDaze, "Dazed", "CombatSpeedDebuff", "Enemy", value: 15, duration: 4, effect: 3627, icon: 3627, msg1: "The roar leaves your head ringing!"));

            Casters();
            int trimmed = HealerBook() + ShamanBook() + SkaldBook();
            Abilities();
            Console.WriteLine($"[MidgardKits] {_added} spells added, {trimmed} trimmed");
        }

        // ------------------------------------------------------------------ the casters

        static void Casters()
        {
            // ---- Runemaster
            Add("Runes of Suppression", 10, Db(RavenWard, "Raven Ward", "DefensiveProc", "Self", value: RavenBlind, frequency: 25, duration: 600,
                power: -8, cast: 3, effect: 2610, icon: 2610, group: RavenWard, msg1: "Huginn's wings beat about you.", msg2: "Ravens wheel about {0}.",
                desc: "Odin's ravens guard you: whatever strikes you may be blinded by their wings and miss more for 4 seconds."));
            // ---- Spiritmaster
            Add("Spirit Suppression", 10, Db(EinherjarWard, "Ward of the Einherjar", "DefensiveProc", "Self", value: EinherjarCall, frequency: 30,
                duration: 600, power: -8, cast: 3, effect: 2801, icon: 2801, group: EinherjarWard, msg1: "The einherjar stand guard over you.",
                msg2: "Spirits stand guard over {0}.",
                desc: "Whatever strikes you may draw your spirit warrior's fury: your pet turns on it, and it turns on your pet."));
            Add("Summoning", 15, Db(ValhallaCharge, "Valhalla's Charge", "ValhallaCharge", "Enemy", range: 1500, power: -8, recast: 30,
                sub: ChargeStun, effect: 2801, icon: 2801, group: ValhallaCharge,
                desc: "Your spirit warrior leaps to your target, stuns it for 2 seconds and holds its anger. 30 second reuse."));
            // ---- Bonedancer
            Add("Bone Army", 14, Db(GraspingBones, "Grasping Bones", "GraspingBones", "Area", radius: 120, range: 1500, duration: 10, sub: BonesSnare,
                power: -8, cast: 1, recast: 25, effect: 10031, icon: 10031, group: GraspingBones,
                desc: "Skeletal hands claw up at your ground target: enemies in them are slowed 50% for 8 seconds."));
            Add("Bone Army", 25, Db(MarchOfTheDead, "March of the Dead", "MarchOfTheDead", "Enemy", range: 2000, duration: MarchMs / 1000,
                power: -10, recast: 60, effect: 10101, icon: 10101, group: MarchOfTheDead,
                desc: $"Your commander and every minion turn on your target and attack 25% faster for {MarchMs / 1000} seconds. 60 second reuse."));
        }

        // ------------------------------------------------------------------ the Healer's, the Shaman's and the Skald's books

        static readonly List<Spell> _aesirBase = new(), _aesirSpec = new(), _deepSpec = new();

        static int HealerBook()
        {
            int n = 0;
            // Mending: the minor heals go
            n += HibernianKits.ClassBaseline(Specs.Mending, "Mending", Healer, "Mending Healer Base", s => s.Group != 130);
            // the cures become Purify
            n += SkillBase.RemoveLineSpells("Healer Mending Spec", s => s.Group is 100 or 110 || s.ID is 14382 or 14383);
            Add("Healer Mending Spec", 6, Db(PurifyHealer, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 3071, icon: 3071,
                group: PurifyHealer, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            int[] blv = { 12, 22, 34, 44 }, bval = { 15, 28, 45, 62 };
            string[] bn = { "Eir's Blessing", "Eir's Grace", "Eir's Favor", "Eir's Benevolence" };
            for (int i = 0; i < blv.Length; i++)
                Add("Healer Mending Spec", blv[i], Db(EirsBlessing + i, bn[i], "Rejuvenation", "Realm", value: bval[i], range: 2000, power: 6 + i * 4,
                    cast: 1.5, effect: 3081, icon: 3081, group: EirsBlessing,
                    desc: $"A friend heals {bval[i]} every 3 seconds for 15 seconds; it stacks three times (more each stack). Cast on three stacks, " +
                        "it becomes Eir's Mercy: what was left to heal comes at once, and half again."));
            // Pacification: the glances fold into the glares and gazes
            n += SkillBase.RemoveLineSpells("Pacification Spec", s => s.Group is 3030 or 3000);
            // Augmentation: every buff in one cast - Gift of the Aesir
            foreach (Spell s in SkillBase.GetSpellList("Augmentation"))
                _aesirBase.Add(s);
            n += HibernianKits.ClassBaseline(Specs.Augmentation, "Augmentation", Healer, "Augmentation Healer Base", _ => false);
            foreach (Spell s in SkillBase.GetSpellList("Healer Augmentation Spec"))
                if (AesirTakes(s))
                    _aesirSpec.Add(s);
            n += SkillBase.RemoveLineSpells("Healer Augmentation Spec", AesirTakes);
            Add("Healer Augmentation Spec", 2, Db(Aesir, "Gift of the Aesir", "AlbionBlessing", "Group", radius: 1500, power: 10, cast: 3,
                effect: 3161, icon: 3161, group: Aesir,
                desc: "Every blessing you know - armor, strength, constitution, dexterity and quickness of attack - on your whole group at once."));
            return n;
        }

        static bool AesirTakes(Spell s) => s.SpellType is eSpellType.CombatSpeedBuff && s.Target is eSpellTarget.REALM;

        static int ShamanBook()
        {
            int n = 0;
            // Mending: one heal - the minor and the group heals go (the group heals over time stay)
            n += HibernianKits.ClassBaseline(Specs.Mending, "Mending", Shaman, "Mending Shaman Base", s => s.Group is not (130 or 120));
            n += SkillBase.RemoveLineSpells("Shaman Mend Spec", s => s.Group is 100 or 110 || s.ID is 14382 or 14383 ||
                s.SpellType is eSpellType.HealthRegenBuff && s.Target is eSpellTarget.REALM);
            Add("Shaman Mend Spec", 6, Db(PurifyShaman, "Purify", "CureAll", "Realm", range: 2000, power: 8, cast: 2, effect: 3071, icon: 3071,
                group: PurifyShaman, desc: "Cleanses a friend of poison, disease, bleeding, nearsight and silence."));
            Add("Subterranean Spec", 16, Db(MycelialRing, "Mycelial Ring", "MycelialRing", "Self", value: 40, radius: 350, duration: 12, sub: RingSnare,
                power: -10, cast: 2, recast: 30, effect: 3451, icon: 3451, group: MycelialRing,
                desc: "A ring of fungus at your feet: your side heals within it every 2 seconds, and enemies in it are slowed."));
            // Augmentation: every buff in one cast - Gift of the Deep
            n += HibernianKits.ClassBaseline(Specs.Augmentation, "Augmentation", Shaman, "Augmentation Shaman Base", _ => false);
            foreach (Spell s in SkillBase.GetSpellList("Shaman Augmentation Spec"))
                if (DeepTakes(s))
                    _deepSpec.Add(s);
            n += SkillBase.RemoveLineSpells("Shaman Augmentation Spec", DeepTakes);
            Add("Shaman Augmentation Spec", 2, Db(Deep, "Gift of the Deep", "AlbionBlessing", "Group", radius: 1500, power: 10, cast: 3,
                effect: 3261, icon: 3261, group: Deep,
                desc: "Every blessing you know - armor, strength, constitution, dexterity, quickness, acuity, the deep's force and stamina - on your whole group at once."));
            return n;
        }

        static bool DeepTakes(Spell s) => s.Target is eSpellTarget.REALM && s.SpellType is eSpellType.StrengthConstitutionBuff or
            eSpellType.DexterityQuicknessBuff or eSpellType.AcuityBuff or eSpellType.DamageAdd or eSpellType.EnduranceRegenBuff;

        static int SkaldBook()
        {
            // the twelve resist chants and songs become one song
            int n = SkillBase.RemoveLineSpells(Specs.Battlesongs, s => s.Group is >= 3651 and <= 3662 or 3690);
            Spell chant = SkillBase.GetSpellByID(3607);       // (Chant of Blood: a chant's pulse)
            int[] lv = { 25, 44 }, val = { 10, 20 };
            string[] nm = { "Song of the Aesir", "Saga of the Aesir" };
            for (int i = 0; i < 2; i++)
            {
                DbSpell d = Db(SongOfAesir + i, nm[i], "AllMagicResistsBuff", "Group", value: val[i], radius: 1500, effect: 3651, icon: 3651,
                    group: SongOfAesir, desc: $"A chant: your group resists heat, cold, matter, body, spirit and energy {val[i]}% better.");
                HibernianKits.Chant(d, chant);
                Add(Specs.Battlesongs, lv[i], d);
            }
            return n;
        }

        /// <summary>Gift of the Aesir / of the Deep on one friend: the best rank of every buff the healer knows.</summary>
        public static int Bless(GameLiving healer, GameLiving t, Spell spell)
        {
            bool shaman = spell.Group == Deep;
            int spec = healer.GetModifiedSpecLevel(Specs.Augmentation);
            IEnumerable<Spell> all = _aesirBase.Where(s => s.Level <= healer.Level)
                .Concat((shaman ? _deepSpec : _aesirSpec).Where(s => s.Level <= spec));
            SpellLine line = SkillBase.GetSpellLine(Specs.Augmentation) ?? SkillBase.GetSpellLine(GlobalSpellsLines.Item_Effects);
            int given = 0;
            foreach (var g in all.GroupBy(s => s.SpellType))
            {
                ScriptMgr.CreateSpellHandler(healer, g.OrderBy(s => s.Level).Last(), line)?.StartSpell(t);
                given++;
            }
            return given;
        }

        // ------------------------------------------------------------------ the abilities

        static void Abilities()
        {
            string grip = $"Midgard's weapons go in one hand or two. Sword, Axe, Hammer and Spear styles: with a two-handed weapon they hit " +
                $"{GripBonus * 100:0}% harder but leave you open (you take {(GripRisk - 1) * 100:0}% more damage for {GripMs / 1000} seconds); with " +
                $"weapon and shield you take {(1 - GripGuard) * 100:0}% less damage for {GripMs / 1000} seconds; with the off hand empty a third of " +
                "the style's endurance comes back.";
            Ability(GripKey, 3960, 0, grip, "VikingCareer", new[] { 1 }, 0);
            Ability(GripKey, 3960, 0, grip, "MidgardRogueCareer", new[] { 1 }, 0);
            Ability(RunicKey, 3961, 2611, $"Your Runecarving bolts leave a rune on their target: your next direct-damage spell on it within {DetonateMs / 1000} " +
                $"seconds sets it off - {DetonateShare * 100:0}% more damage and a 2 second stagger.", Specs.Runecarving, new[] { 1 }, Runemaster);
            Ability(AegisKey, 3962, 3301, "Your mana shield (hold right click / LT) is Eir's calm. Raised just before a blow lands - a perfect ward - it " +
                "mesmerizes the attacker for 3 seconds.", Specs.Mending, new[] { 1 }, Healer);
            Ability(StillnessKey, 3963, 3366, $"While a monster you mesmerized or stunned is held, your heals on groupmates near it are " +
                $"{(StillnessFactor - 1) * 100:0}% stronger.", Specs.Pacification, new[] { 1 }, Healer);
            Ability(FeastKey, 3964, 3471, "Every tick of your damage over time heals your most hurt groupmate a little (once a second).",
                Specs.Subterranean, new[] { 1 }, Shaman);
            Ability(SporeKey, 3965, 3421, "Your mana shield (hold right click / LT) is a cloud of spores. Raised just before a blow lands - a perfect ward - " +
                "it diseases the attacker (slower, weaker, healed less).", Specs.Mending, new[] { 1 }, Shaman);
            var wheel = new DbAbility
            {
                KeyName = HibernianKits.WheelKey, Name = HibernianKits.WheelKey, IconID = 228, InternalID = 3915, AbilityID = 3915,
                Description = "Put it on your bar. Tap it: the chant that fits the moment (rest when your group is hurt, blood in a fight, travel on " +
                    "the road). Hold it: a wheel of your chants - point at one and let go.",
            };
            SkillBase.AddScriptedAbility(wheel, "SkaldCareer", 5);
            Ability(SagaKey, 3966, 3627, $"Every Sword, Axe or Hammer style that lands builds your Saga (up to {SagaMax}). At {SagaMax}, your next shout " +
                "also hits every enemy in front of you and rallies your group (a burst of endurance). Your War Howl breaks a monster's spell " +
                $"(once every {HowlBreakMs / 1000} seconds); your Battle Roar dazes and hits everything in front of you.", Specs.Battlesongs, new[] { 1 }, Skald);
            Ability(IronKey, 3967, 0, $"For {IronMs / 1000} seconds every blow you block or parry staggers the attacker. {IronReuseMs / 1000} second reuse.",
                "WarriorCareer", new[] { 20 }, Warrior);
            Ability(ThunderKey, 3968, 3508, $"For {ThunderMs / 1000} seconds every style that lands calls lightning down on its target. " +
                $"{ThunderReuseMs / 1000} second reuse.", "ThaneCareer", new[] { 20 }, Thane);
            Ability(RageKey, 3969, 0, $"For {RageMs / 1000} seconds every style that lands adds a stack of rage: +{RageStep * 100:0}% damage, up to {RageMax}. " +
                $"{RageReuseMs / 1000} second reuse.", "BerserkerCareer", new[] { 20 }, Berserker);
            Ability(FuryKey, 3970, 0, $"Below half health your styles hit {RageLow * 100:0}% harder.", "BerserkerCareer", new[] { 1 }, Berserker);
            Ability(HowlKey, 3971, 0, $"A howl that renews every Savagery buff on you, free. {HowlReuseMs / 1000} second reuse. (Blood price: a Hand to Hand " +
                $"style that lands while a Savagery buff is up wins back {BloodPricePercent}% of your health.)", "SavageCareer", new[] { 20 }, Savage);
            var ambush = new DbAbility
            {
                KeyName = HibernianHybrids.AmbushKey, Name = HibernianHybrids.AmbushKey, IconID = 0, InternalID = 3930, AbilityID = 3930,
                Description = "Your first blow from stealth can't be parried, blocked or dodged by a monster.",
            };
            SkillBase.AddScriptedAbility(ambush, "ShadowbladeCareer", 1);
            Ability(MistKey, 3972, 0, "When you dodge a blow you may vanish into Hel's mist: 1% for each point of Stealth. You are hidden, the monsters " +
                "lose you, and nothing can find you for 5 seconds - open on it again.", Specs.Stealth, new[] { 1 }, Shadowblade);
            Ability(TwinKey, 3973, 0, $"Your stealth opener with a left axe in hand: your off hand strikes too. With a two-handed sword or axe: it hits " +
                $"{TwinShare * 100:0}% harder. (Your positionals leave it Marked: a stealth opener on it always crits.)", "ShadowbladeCareer", new[] { 1 }, Shadowblade);
            Ability(AlbionKits.VenomKey, 3955, 0, $"Each positional style that lands on a foe with your poison on it feeds the venom: it hits " +
                $"{AlbionKits.VenomStep * 100:0}% harder and lasts {AlbionKits.VenomExtendMs / 1000} seconds longer, up to {AlbionKits.VenomMax} times.",
                Specs.Envenom, new[] { 1 }, Shadowblade);
            Ability(PreyKey, 3974, 0, $"Your critical and overdrawn shots mark their target for {PreyMs / 1000} seconds: your pet goes for it at once and " +
                $"hits it {(PreyFactor - 1) * 100:0}% harder.", Specs.CompositeBow, new[] { 1 }, Hunter);
        }

        static void Ability(string key, int id, int icon, string desc, string spec, int[] at, int cls)
        {
            var a = new DbAbility { KeyName = key, Name = key, IconID = icon, InternalID = id, AbilityID = id, Description = desc };
            for (int i = 0; i < at.Length; i++)
                SkillBase.AddScriptedAbility(a, spec, at[i], spec.EndsWith("Career") ? 0 : cls, i + 1);
        }

        // ------------------------------------------------------------------ helpers

        static void Add(string line, int level, DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[MidgardKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
                return;
            }
            SkillBase.AddScriptedSpell(line, new Spell(d, level));
            _added++;
        }

        static void Hidden(DbSpell d)
        {
            if (SkillBase.GetSpellByID(d.SpellID) is Spell taken)
            {
                Console.WriteLine($"[MidgardKits] spell id {d.SpellID} is already {taken.Name} - {d.Name} not added");
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

        public static bool IsMidgardMelee(int cls) => cls is Thane or Warrior or Shadowblade or Skald or Hunter or Berserker or Savage;

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

        /// <summary>A share of a blow (or spell) dealt again, as a hit of its own: the grip, rage, Twin Ambush, a detonated rune.</summary>
        static int Extra(GameLiving owner, GameLiving t, int dmg, eDamageType type, AttackData.eAttackType kind, DbInventoryItem weapon, ushort fx)
        {
            if (t == null || !t.IsAlive || dmg <= 0)
                return 0;
            var ad = new AttackData
            {
                Attacker = owner, Target = t, Damage = dmg, DamageType = type, AttackType = kind,
                AttackResult = eAttackResult.HitUnstyled, Weapon = weapon, CausesCombat = true,
            };
            t.OnAttackedByEnemy(ad);
            owner.DealDamage(ad);
            if (fx != 0)
                Fx(owner, t, fx);
            return dmg;
        }

        static IEnumerable<GameLiving> FoesInFront(GameLiving owner, int reach, int arc, GameLiving except)
        {
            foreach (GameNPC n in owner.GetNPCsInRadius((ushort) reach))
                if (n != except && n.IsAlive && n.ObjectState == GameObject.eObjectState.Active && owner.IsObjectInFront(n, arc) &&
                    GameServer.ServerRules.IsAllowedToAttack(owner, n, true) && MonsterTiers.Combatant(n) == null)
                    yield return n;
        }

        sealed class Kit
        {
            public long RiskUntil, GuardUntil, IronUntil, ThunderUntil, RageUntil, SagaAt, HowlBreakReady, FeastReady, RuneUntil, PreyUntil;
            public int Rage, Saga;
            public GameLiving RunedBy, PreyOf;
        }

        static readonly ConditionalWeakTable<GameLiving, Kit> _kits = new();
        static Kit Of(GameLiving l) => _kits.GetValue(l, _ => new Kit());
        static bool Has(GameLiving l, out Kit k) => _kits.TryGetValue(l, out k);

        // ------------------------------------------------------------------ the grip

        public enum Grip { None, TwoHanded, Shield, Empty, Dual }

        public static Grip GripOf(GameLiving l)
        {
            if (l == null)
                return Grip.None;
            if (l.ActiveWeaponSlot == eActiveWeaponSlot.TwoHanded)
                return Grip.TwoHanded;
            DbInventoryItem left = l.ActiveLeftWeapon;
            if (left == null)
                return Grip.Empty;
            return left.Object_Type == (int) eObjectType.Shield ? Grip.Shield : Grip.Dual;
        }

        static bool GripLine(Style st) => st.Spec is Specs.Sword or Specs.Axe or Specs.Hammer or Specs.Spear;

        /// <summary>GameLiving.TakeDamage: a two-hander's opening (more), a shield's cover (less), a Hunter's marked prey
        /// under its pet's teeth (more).</summary>
        public static double TakenFactor(GameLiving victim, GameObject source)
        {
            double f = 1.0;
            if (victim != null && Has(victim, out Kit k))
            {
                if (k.RiskUntil > Now)
                    f *= GripRisk;
                if (k.GuardUntil > Now)
                    f *= GripGuard;
                if (k.PreyUntil > Now && source is GameNPC pet && pet.Brain is IControlledBrain cb && cb.GetPlayerOwner() is GamePlayer o &&
                    o == k.PreyOf)
                    f *= PreyFactor;
            }
            return f;
        }

        static void ApplyGrip(GameLiving owner, AttackData ad, Style st, Kit k)
        {
            switch (GripOf(owner))
            {
                case Grip.TwoHanded:
                    Extra(owner, ad.Target, (int) ((ad.Damage + ad.CriticalDamage) * GripBonus), ad.DamageType, ad.AttackType, ad.Weapon, 0);
                    k.RiskUntil = Now + GripMs;
                    k.GuardUntil = 0;
                    break;
                case Grip.Shield:
                    k.GuardUntil = Now + GripMs;
                    k.RiskUntil = 0;
                    break;
                case Grip.Empty:
                    int cost = StyleProcessor.CalculateEnduranceCost(owner, st, ad.Weapon?.SPD_ABS ?? 30, false);
                    if (cost >= 3)
                        owner.ChangeEndurance(owner, eEnduranceChangeType.Regenerate, cost / 3);
                    break;
            }
        }

        // ------------------------------------------------------------------ a style landed (StyleRework.AfterStyle)

        public static void AfterStyle(GameLiving owner, AttackData ad)
        {
            Style st = ad?.Style;
            if (st == null || ad.Target is not GameLiving t || owner == null)
                return;
            int cls = ClassOf(owner);
            if (!IsMidgardMelee(cls))
                return;
            try
            {
                Kit k = Of(owner);
                int dealt = ad.Damage + ad.CriticalDamage;
                if (GripLine(st))
                    ApplyGrip(owner, ad, st, k);
                switch (cls)
                {
                    case Thane:
                        if (k.ThunderUntil > Now && Array.IndexOf(StyleRework.ThaneBolts, st.ID) < 0)
                            Cast(owner, StyleRework.ThorBolt, t);
                        if (Array.IndexOf(StyleRework.ThaneBolts, st.ID) >= 0 && GripOf(owner) == Grip.TwoHanded &&
                            t.GetNPCsInRadius(300).Cast<GameNPC>().FirstOrDefault(n => n != t && n.IsAlive && GameServer.ServerRules.IsAllowedToAttack(owner, n, true)) is GameNPC arc)
                        {
                            Cast(owner, st.Procs.Any(p => p.Spell.ID == StyleRework.ThorBoltBig) ? StyleRework.ThorBoltBig : StyleRework.ThorBolt, arc);
                            Say(owner, $"The lightning arcs to {arc.GetName(0, false)}!");
                        }
                        break;
                    case Berserker:
                        double rage = owner.HealthPercent < 50 ? RageLow : 0;
                        if (k.RageUntil > Now)
                        {
                            rage += RageStep * k.Rage;
                            if (k.Rage < RageMax)
                            {
                                k.Rage++;
                                Say(owner, $"Blood Rage {k.Rage}/{RageMax}!");
                            }
                        }
                        if (rage > 0)
                            Extra(owner, t, (int) (dealt * rage), ad.DamageType, ad.AttackType, ad.Weapon, 0);
                        break;
                    case Savage when st.Spec == Specs.HandToHand:
                        if (SavageryBuffs(owner).Any() && owner.Health < owner.MaxHealth)
                        {
                            int heal = Math.Max(1, (int) (owner.MaxHealth * BloodPricePercent / 100));
                            owner.ChangeHealth(owner, eHealthChangeType.Spell, heal);
                        }
                        break;
                    case Skald when st.Spec is Specs.Sword or Specs.Axe or Specs.Hammer:
                        AddSaga(owner, k);
                        break;
                    case Shadowblade:
                        if (Array.IndexOf(StyleRework.ShadowbladeMarks, st.ID) >= 0)
                        {
                            HibernianHybrids.Expose(t);
                            Say(owner, $"{t.GetName(0, true)} is marked - your next opener on it will find its mark.");
                        }
                        if (st.ID == StyleRework.LeftRavager && st.Spec == Specs.Left_Axe)
                            HibernianHybrids.DropThreat(owner, t, 25);
                        if (st.Spec == Specs.Critical_Strike && st.ID == HibernianHybrids.Garrote)
                            HibernianHybrids.BreakSpell(owner, t, "Your garrote");
                        if (st.Db.OpeningRequirementType == 2)
                            AlbionKits.FeedVenom(owner, t);
                        if (st.StealthRequirement)
                            TwinAmbush(owner, ad);
                        break;
                    case Hunter when st.ID == StyleRework.SpearDetaunt && st.Spec == Specs.Spear:
                        HibernianHybrids.DropThreat(owner, t, 50);
                        break;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine($"[MidgardKits] after {st.Name}: {e.Message}");
            }
        }

        static void TwinAmbush(GameLiving owner, AttackData ad)
        {
            switch (GripOf(owner))
            {
                case Grip.Dual when owner.ActiveLeftWeapon?.Object_Type == (int) eObjectType.LeftAxe:
                    StyleRework.OffhandStrike(owner, ad, StyleRework.OffhandShare);
                    break;
                case Grip.TwoHanded:
                    int extra = Extra(owner, ad.Target, (int) ((ad.Damage + ad.CriticalDamage) * TwinShare), ad.DamageType, ad.AttackType, ad.Weapon,
                        StyleRework.SweepHitFx);
                    Say(owner, $"Twin Ambush: your great blade bites deeper for {extra} more!", eChatType.CT_YouHit);
                    break;
            }
        }

        // ------------------------------------------------------------------ a blow turned aside (AttackComponent)

        public static void AfterDefense(AttackData ad)
        {
            if (ad?.Target is not GameLiving d || ad.Attacker is not GameLiving a || !d.IsAlive)
                return;
            int cls = ClassOf(d);
            if (cls is not (Warrior or Shadowblade))
                return;
            try
            {
                bool action = d is GamePlayer p && ActionCombat.IsActive(p) && ad.ActionDefense is not eActionDefense.None;
                bool parried = action ? ad.ActionDefense is eActionDefense.Parry : ad.AttackResult is eAttackResult.Parried;
                bool evaded = action ? ad.ActionDefense is eActionDefense.Dodge : ad.AttackResult is eAttackResult.Evaded;
                bool blocked = action ? ad.ActionDefense is eActionDefense.Block : ad.AttackResult is eAttackResult.Blocked;
                switch (cls)
                {
                    case Warrior when (parried || blocked) && Has(d, out Kit wk) && wk.IronUntil > Now:
                        Cast(d, MidStagger, a);
                        Say(d, $"Iron Stand: {a.GetName(0, true)} reels from your guard!");
                        break;
                    case Shadowblade when evaded && !d.IsStealthed && Util.Chance((int) Math.Round(HibernianHybrids.VoidstepPercent(d.GetModifiedSpecLevel(Specs.Stealth)))):
                        new ECSGameTimer(d, _ =>
                        {
                            HibernianHybrids.Voidstep(d, "Hel's Mist! The mist takes you - nothing can find you for a few seconds.");
                            return 0;
                        }, HibernianHybrids.VoidstepDelayMs);
                        break;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("[MidgardKits] after defense: " + e.Message);
            }
        }

        // ------------------------------------------------------------------ the fighters' abilities

        public static bool IronStand(GameLiving w)
        {
            Kit k = Of(w);
            if (k.IronUntil > Now)
                return false;
            k.IronUntil = Now + IronMs;
            foreach (GamePlayer v in w.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(w, eEmote.Military);
            Say(w, $"Iron Stand! For {IronMs / 1000} seconds every blow you turn aside staggers its striker.", eChatType.CT_Important);
            return true;
        }

        public static bool Thunderstruck(GameLiving t)
        {
            Kit k = Of(t);
            if (k.ThunderUntil > Now)
                return false;
            k.ThunderUntil = Now + ThunderMs;
            Fx(t, t, 3527);
            Say(t, $"Thunderstruck! For {ThunderMs / 1000} seconds Thor answers every blow.", eChatType.CT_Important);
            return true;
        }

        public static bool BloodRage(GameLiving b)
        {
            Kit k = Of(b);
            if (k.RageUntil > Now)
                return false;
            k.RageUntil = Now + RageMs;
            k.Rage = 0;
            foreach (GamePlayer v in b.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(b, eEmote.Rude);
            Say(b, $"Blood Rage! For {RageMs / 1000} seconds every blow feeds your fury.", eChatType.CT_Important);
            return true;
        }

        public static int RageOf(GameLiving b) => Has(b, out Kit k) && k.RageUntil > Now ? k.Rage : 0;

        static IEnumerable<ECSGameSpellEffect> SavageryBuffs(GameLiving s) =>
            s.effectListComponent.GetSpellEffects().Where(e => e.IsActive && e.SpellHandler?.SpellLine?.KeyName == Specs.Savagery &&
                e.SpellHandler.Caster == s && e.Duration > 0);

        /// <summary>Kelgor's Howl: every Savagery buff on you renewed, free. How many.</summary>
        public static int KelgorsHowl(GameLiving s)
        {
            int n = 0;
            foreach (ECSGameSpellEffect e in SavageryBuffs(s).ToList())
            {
                e.ExpireTick = Now + e.Duration;
                n++;
            }
            foreach (GamePlayer v in s.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(s, eEmote.Roar);
            Say(s, n == 0 ? "You howl, but no Savagery burns in you." : $"Kelgor's Howl! {n} of your savage gifts burn anew.", eChatType.CT_Important);
            return n;
        }

        // ------------------------------------------------------------------ the Skald

        static void AddSaga(GameLiving s, Kit k)
        {
            if (Now - k.SagaAt > SagaForgetMs)
                k.Saga = 0;
            k.SagaAt = Now;
            if (k.Saga >= SagaMax)
                return;
            k.Saga++;
            Say(s, k.Saga >= SagaMax ? $"Saga {SagaMax}/{SagaMax}: your next shout rings out over the whole field!" : $"Saga {k.Saga}/{SagaMax}.");
        }

        public static int SagaOf(GameLiving s) => Has(s, out Kit k) && Now - k.SagaAt <= SagaForgetMs ? k.Saga : 0;

        static bool IsShout(Spell sp) => sp != null && sp.SpellType is eSpellType.DirectDamage && sp.Group is 3620 or 3625;

        static void Shout(GameLiving s, GameLiving t, AttackData ad)
        {
            Spell sp = ad.SpellHandler.Spell;
            Kit k = Of(s);
            int dmg = Math.Max(1, ad.Damage + ad.CriticalDamage);
            if (sp.Group == 3620 && Now >= k.HowlBreakReady && t.IsCasting)
            {
                k.HowlBreakReady = Now + HowlBreakMs;
                HibernianHybrids.BreakSpell(s, t, "Your war howl");
            }
            if (sp.Group == 3625)
            {
                Cast(s, RoarDaze, t);
                foreach (GameLiving f in FoesInFront(s, 600, 90, t).Take(4).ToList())
                {
                    Extra(s, f, dmg, ad.DamageType, AttackData.eAttackType.Unknown, null, (ushort) sp.ClientEffect);
                    Cast(s, RoarDaze, f);
                }
            }
            if (SagaOf(s) >= SagaMax)
            {
                k.Saga = 0;
                int hit = 0;
                if (sp.Group != 3625)
                    foreach (GameLiving f in FoesInFront(s, 700, 120, t).Take(5).ToList())
                    {
                        Extra(s, f, dmg, ad.DamageType, AttackData.eAttackType.Unknown, null, (ushort) sp.ClientEffect);
                        hit++;
                    }
                foreach (GameLiving m in HibernianKits.Mates(s, 1500))
                    if (m.MaxEndurance > 0)
                        m.ChangeEndurance(s, eEnduranceChangeType.Spell, m.MaxEndurance * 15 / 100);
                foreach (GamePlayer v in s.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendEmoteAnimation(s, eEmote.Victory);
                Say(s, $"Your saga rings out{(hit > 0 ? $" over {hit} more foes" : "")} - your group finds its second wind!", eChatType.CT_Important);
            }
        }

        // ------------------------------------------------------------------ spells landing (GameLiving.OnAttackEnemy)

        /// <summary>A Skald's shouts, a Runemaster's runes.</summary>
        public static void OnAttackEnemy(GameLiving attacker, AttackData ad)
        {
            if (ad?.Target is not GameLiving t || attacker == null || ad.AttackType != AttackData.eAttackType.Spell || ad.SpellHandler?.Spell is not Spell sp)
                return;
            if (ad.Damage + ad.CriticalDamage <= 0 || !t.IsAlive)
                return;
            int cls = ClassOf(attacker);
            try
            {
                if (cls == Skald && IsShout(sp))
                    Shout(attacker, t, ad);
                else if (cls == Runemaster && attacker.HasAbility(RunicKey))
                    Rune(attacker, t, ad, sp);
            }
            catch (Exception e)
            {
                Console.WriteLine("[MidgardKits] on attack: " + e.Message);
            }
        }

        static void Rune(GameLiving r, GameLiving t, AttackData ad, Spell sp)
        {
            Kit tk = Of(t);
            if (sp.SpellType is eSpellType.Bolt && ad.SpellHandler.SpellLine?.KeyName is "Runes of Destruction" or "Runecarving")
            {
                tk.RunedBy = r;
                tk.RuneUntil = Now + DetonateMs;
                Say(r, $"A rune burns on {t.GetName(0, false)}.");
                return;
            }
            if (sp.SpellType is eSpellType.DirectDamage && tk.RunedBy == r && tk.RuneUntil > Now)
            {
                tk.RuneUntil = 0;
                int extra = Extra(r, t, (int) ((ad.Damage + ad.CriticalDamage) * DetonateShare), ad.DamageType, AttackData.eAttackType.Unknown, null, 2611);
                Cast(r, MidStagger, t);
                Say(r, $"Runic Detonation! The rune on {t.GetName(0, false)} bursts for {extra} more.", eChatType.CT_YouHit);
            }
        }

        // ------------------------------------------------------------------ the Healer and the Shaman

        /// <summary>ManaShield.Pay: a Healer's perfect ward mesmerizes (Eir's Aegis), a Shaman's diseases (Spore Ward).</summary>
        public static void PerfectWard(GamePlayer p, GameLiving attacker)
        {
            if (p == null || attacker == null || !attacker.IsAlive)
                return;
            switch (ClassOf(p))
            {
                case Healer:
                    Cast(p, AegisMez, attacker);
                    p.Out.SendMessage($"Eir's calm flows from your ward - {attacker.GetName(0, false)} stands still!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                    break;
                case Shaman:
                    Cast(p, SporeDisease, attacker);
                    p.Out.SendMessage($"Spores burst from your ward and choke {attacker.GetName(0, false)}!", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
                    break;
            }
        }

        static bool HeldBy(GameLiving n, GameLiving healer) =>
            n.IsAlive && (n.IsMezzed || n.IsStunned) && n.effectListComponent.GetSpellEffects()
                .Any(e => e.IsActive && e.SpellHandler?.Caster == healer && e.EffectType is eEffect.Mez or eEffect.Stun);

        /// <summary>HealSpellHandler: a Healer's heals near a monster it holds are stronger (Stillness).</summary>
        public static double HealFactor(GameLiving healer, GameLiving target)
        {
            if (healer == null || target == null || ClassOf(healer) != Healer)
                return 1.0;
            foreach (GameNPC n in target.GetNPCsInRadius(StillnessRange))
                if (HeldBy(n, healer))
                    return StillnessFactor;
            return 1.0;
        }

        /// <summary>DoTSpellHandler: a Shaman's rot heals its most hurt groupmate (Blight Feast).</summary>
        public static void BlightFeast(GameLiving caster, int dmg)
        {
            if (caster == null || dmg <= 0 || ClassOf(caster) != Shaman || !caster.IsAlive)
                return;
            Kit k = Of(caster);
            if (Now < k.FeastReady)
                return;
            k.FeastReady = Now + FeastCooldownMs;
            GameLiving hurt = HibernianKits.Mates(caster, 1500).Where(m => m.Health < m.MaxHealth).OrderBy(m => m.HealthPercent).FirstOrDefault();
            if (hurt == null)
                return;
            int heal = (int) (Math.Max(dmg * 0.5, 4 + caster.Level * 0.4) * HibernianKits.HealFactor(caster));
            HibernianKits.Heal(caster, hurt, heal, 3471, "Blight Feast");
        }

        // ------------------------------------------------------------------ the Hunter

        /// <summary>ActionCombat.Loose: a Hunter's critical or overdrawn shot marks its target; the pet goes for it.</summary>
        public static void MarkThePrey(GamePlayer p, GameLiving target, int flightMs)
        {
            if (p == null || target == null || ClassOf(p) != Hunter)
                return;
            new ECSGameTimer(p, _ =>
            {
                if (!target.IsAlive || !p.IsAlive)
                    return 0;
                Kit tk = Of(target);
                tk.PreyOf = p;
                tk.PreyUntil = Now + PreyMs;
                if (p.ControlledBrain is IControlledBrain pet && pet.Body is GameNPC body && body.IsAlive)
                {
                    pet.Attack(target);
                    Say(p, $"You mark {target.GetName(0, false)} as prey - your pet goes for it!");
                }
                else
                    Say(p, $"You mark {target.GetName(0, false)} as prey.");
                return 0;
            }, Math.Max(1, flightMs + 120));
        }

        // ------------------------------------------------------------------ the casters' spells (spells/MidgardKitSpells.cs)

        public static void March(GameLiving bd, GameLiving target, int ms)
        {
            if (bd?.ControlledBrain?.Body is not GameNPC commander || !commander.IsAlive)
                return;
            var army = new List<GameNPC> { commander };
            if (commander.ControlledNpcList != null)
                foreach (IControlledBrain b in commander.ControlledNpcList)
                    if (b?.Body is GameNPC m && m.IsAlive)
                        army.Add(m);
            bd.ControlledBrain.Attack(target);
            foreach (GameNPC m in army)
            {
                if (m != commander && m.Brain is IControlledBrain mb)
                    mb.Attack(target);
                m.AbilityBonus[eProperty.MeleeSpeed] += 25;
                Fx(bd, m, 10101);
            }
            new ECSGameTimer(bd, _ =>
            {
                foreach (GameNPC m in army)
                    m.AbilityBonus[eProperty.MeleeSpeed] -= 25;
                return 0;
            }, ms);
        }

        // ------------------------------------------------------------------ bots

        sealed class BotTimes
        {
            public long Next, Ready;
        }

        static readonly ConditionalWeakTable<GameBot, BotTimes> _bots = new();

        /// <summary>BotBrain.Think: a Warrior's Iron Stand, a Thane's Thunderstruck, a Berserker's Blood Rage, a Savage's
        /// Kelgor's Howl.</summary>
        public static void BotThink(GameBot bot)
        {
            if (bot == null || !bot.IsAlive || bot.IsIncapacitated || bot.Level < 20 || !bot.InCombat)
                return;
            int cls = ClassOf(bot);
            if (cls is not (Warrior or Thane or Berserker or Savage))
                return;
            long now = Now;
            BotTimes t = _bots.GetValue(bot, _ => new BotTimes());
            if (now < t.Next || now < t.Ready)
                return;
            t.Next = now + 1000;
            bool foes = bot.GetNPCsInRadius(400).Cast<GameNPC>().Any(n => n.IsAlive && n.TargetObject == bot);
            switch (cls)
            {
                case Warrior when foes && IronStand(bot):
                    t.Ready = now + IronReuseMs;
                    break;
                case Thane when Thunderstruck(bot):
                    t.Ready = now + ThunderReuseMs;
                    break;
                case Berserker when BloodRage(bot):
                    t.Ready = now + RageReuseMs;
                    break;
                case Savage when SavageryBuffs(bot).Any(e => e.ExpireTick - now < 10000):
                    KelgorsHowl(bot);
                    t.Ready = now + HowlReuseMs;
                    break;
            }
        }
    }
}

namespace DOL.GS.SkillHandler
{
    using DOL.GS.PacketHandler;

    [SkillHandler(MidgardKits.IronKey)]
    public class IronStandAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (MidgardKits.IronStand(player))
                player.DisableSkill(ab, MidgardKits.IronReuseMs);
        }
    }

    [SkillHandler(MidgardKits.ThunderKey)]
    public class ThunderstruckAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (MidgardKits.Thunderstruck(player))
                player.DisableSkill(ab, MidgardKits.ThunderReuseMs);
        }
    }

    [SkillHandler(MidgardKits.RageKey)]
    public class BloodRageAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            if (MidgardKits.BloodRage(player))
                player.DisableSkill(ab, MidgardKits.RageReuseMs);
        }
    }

    [SkillHandler(MidgardKits.HowlKey)]
    public class KelgorsHowlAbilityHandler : IAbilityActionHandler
    {
        public void Execute(Ability ab, GamePlayer player)
        {
            if (player == null || !player.IsAlive || player.IsIncapacitated)
                return;
            MidgardKits.KelgorsHowl(player);
            player.DisableSkill(ab, MidgardKits.HowlReuseMs);
        }
    }
}
