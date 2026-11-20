using System;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// Taunts are shouts (owner 2026-11-19: "drop the taunt and detaunt styles ... all fighter based classes (Hero,
    /// Champion, Blademaster, Paladin, Armsman, etc..) [get] a ranged single target shout, and then eventually an AoE taunt
    /// shout. Stealthers and Minstrels do not apply"; "Taunts ... need to be really powerful and not have big
    /// cooldowns. I know on my champion, using the LW taunt style, I had to hit the mob multiple times"):
    ///   Challenge (level 5): the target's threat on you becomes its highest plus half again and a margin, and it turns
    ///     on you at once - 1500 range, instant, 8 s.
    ///   Battle Cry (level 20): the same on every monster within 600 of you - instant, 20 s.
    /// The fighters' blows also make half again the threat (ThreatFactor), so a tank keeps what it takes between shouts.
    /// A spell line, "Battle Cries" (a baseline line - your level teaches it), given each fighter class through its
    /// Blades / Two Handed / Sword specialization. Bots that fight use them when a monster is on someone softer.
    /// </summary>
    public static class TauntShouts
    {
        public const string LineKey = "Battle Cries";
        public const int ChallengeId = 64190, BattleCryId = 64191;
        public const double FighterThreat = 1.5;

        /// <summary>Fighter classes and the specialization each one's shouts come through (one every one of them has).</summary>
        public static readonly Dictionary<eCharacterClass, string> Fighters = new()
        {
            [eCharacterClass.Hero] = "Blades", [eCharacterClass.Champion] = "Blades", [eCharacterClass.Blademaster] = "Blades",
            [eCharacterClass.Armsman] = "Slash", [eCharacterClass.Paladin] = "Slash", [eCharacterClass.Mercenary] = "Slash",
            [eCharacterClass.Warrior] = "Sword", [eCharacterClass.Thane] = "Sword", [eCharacterClass.Berserker] = "Sword",
            [eCharacterClass.Savage] = "Hand to Hand", [eCharacterClass.Valkyrie] = "Sword",
        };

        public static bool IsFighter(GameLiving l)
        {
            int id = l switch
            {
                GamePlayer p => p.CharacterClass?.ID ?? 0,
                GameBot b => b.CharacterClass?.ID ?? 0,
                _ => 0
            };
            return id != 0 && Fighters.ContainsKey((eCharacterClass) id);
        }

        /// <summary>StandardMobBrain: a fighter's melee makes half again the threat.</summary>
        public static double ThreatFactor(GameLiving attacker, AttackData ad) =>
            ad != null && ad.IsMeleeAttack && IsFighter(attacker) ? FighterThreat : 1.0;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Register();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[TauntShouts] " + ex);
            }
        }

        public static void Register()
        {
            SkillBase.AddScriptedSpell(LineKey, new Spell(Db(ChallengeId, "Challenge", range: 1500, radius: 0, recast: 8, emote: "Taunt",
                desc: "Shout a challenge: the target turns on you at once, and you hold more of its anger than anyone else."), 5));
            SkillBase.AddScriptedSpell(LineKey, new Spell(Db(BattleCryId, "Battle Cry", range: 0, radius: 600, recast: 20, emote: "Roar",
                desc: "A roar that turns every enemy around you on you at once."), 20));
            int n = 0;
            foreach (var (cls, spec) in Fighters)
            {
                var classLine = new SpellLine(LineKey, LineKey, spec, true);
                SkillBase.AddSpecSpellLine(spec, classLine, (int) cls);
                n++;
            }
            Console.WriteLine($"[TauntShouts] Challenge and Battle Cry for {n} fighter classes");
        }

        static DbSpell Db(int id, string name, int range, int radius, int recast, string emote, string desc) => new DbSpell
        {
            SpellID = id, Name = name, Type = "TauntShout", Target = "Enemy", Range = range, Radius = radius, RecastDelay = recast,
            CastTime = 0, Power = 0, ClientEffect = 7353, Icon = 7353, SpellGroup = id, Description = desc, Message1 = emote,
        };

        /// <summary>One monster turned on the shouter: its threat on them its highest plus half again and a margin.</summary>
        public static void Taunt(GameLiving shouter, GameNPC n)
        {
            if (n?.Brain is not StandardMobBrain brain || !n.IsAlive)
                return;
            MonsterTiers.Touch(shouter, n);
            long top = brain.TopAggro;
            long have = brain.AggroOf(shouter);
            long want = (long) (top * 1.5) + 50 + shouter.Level * 10;
            if (want > have)
                brain.AddToAggroList(shouter, want - have);
            if (n.TargetObject != shouter && n.IsWithinRadius(shouter, 3000))
                n.StartAttack(shouter);
        }

        // ------------------------------------------------------------------ bots

        static readonly System.Runtime.CompilerServices.ConditionalWeakTable<GameBot, System.Runtime.CompilerServices.StrongBox<long>> _botNext = new();

        /// <summary>BotBrain.Think: a fighting fighter bot shouts when a monster is on someone softer (not a fighter): Battle
        /// Cry for two or more near it, Challenge for one.</summary>
        public static void BotThink(GameBot bot)
        {
            if (bot == null || !bot.IsAlive || !bot.InCombat || !IsFighter(bot) || bot.IsCasting || bot.IsIncapacitated)
                return;
            long now = GameLoop.GameLoopTime;
            var box = _botNext.GetValue(bot, _ => new System.Runtime.CompilerServices.StrongBox<long>(0));
            if (now < box.Value)
                return;
            box.Value = now + 1000;
            var side = new HashSet<GameLiving>();
            if (bot.Group != null)
                foreach (GameLiving m in bot.Group.GetMembersInTheGroup())
                    side.Add(m);
            if (MonsterTiers.Combatant(bot) is GameLiving lead)
                side.Add(lead);
            var onSoft = new List<GameNPC>();
            foreach (GameNPC n in bot.GetNPCsInRadius(1500))
            {
                if (!n.IsAlive || n.Brain is not StandardMobBrain || n.TargetObject is not GameLiving t || t == bot)
                    continue;
                if (side.Contains(t) && !IsFighter(t))
                    onSoft.Add(n);
            }
            if (onSoft.Count == 0)
                return;
            int near = onSoft.Count(n => n.IsWithinRadius(bot, 600));
            Spell cry = SkillBase.GetSpellByID(BattleCryId), chal = SkillBase.GetSpellByID(ChallengeId);
            SpellLine line = SkillBase.GetSpellLine(LineKey);
            if (line == null)
                return;
            if (near >= 2 && cry != null && bot.Level >= 20 && bot.GetSkillDisabledDuration(cry) <= 0)
                bot.CastSpell(cry, line);
            else if (chal != null && bot.Level >= 5 && bot.GetSkillDisabledDuration(chal) <= 0)
            {
                GameNPC pick = onSoft.OrderBy(n => n.GetDistanceTo(bot)).First();
                GameObject was = bot.TargetObject;
                bot.TargetObject = pick;
                bot.CastSpell(chal, line);
                bot.TargetObject = was;
            }
        }
    }
}

namespace DOL.GS.Spells
{
    /// <summary>A taunt shout (TauntShouts): every enemy it reaches turns on the shouter.</summary>
    [SpellHandler(eSpellType.TauntShout)]
    public class TauntShoutSpellHandler : SpellHandler
    {
        public TauntShoutSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription => Spell.Radius > 0
            ? "Every enemy around you turns on you."
            : "The target turns on you, and you hold more of its anger than anyone else.";

        public override bool StartSpell(GameLiving target)
        {
            // the shout itself: its emote for everyone near (Message1 carries which)
            eEmote emote = Spell.Message1 == "Roar" ? eEmote.Roar : eEmote.Taunt;
            foreach (GamePlayer v in Caster.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendEmoteAnimation(Caster, emote);
            return base.StartSpell(target);
        }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override void OnDirectEffect(GameLiving target)
        {
            if (target is not GameNPC n || !n.IsAlive)
                return;
            TauntShouts.Taunt(Caster, n);
            SendEffectAnimation(n, 0, false, 1);
            MessageToCaster($"{n.GetName(0, true)} turns on you!", eChatType.CT_Spell);
        }

        public override double CalculateSpellResistChance(GameLiving target) => 0;
    }
}
