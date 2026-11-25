using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.Events;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// Morgana le Fay at the Gate of Annwn (claude 2026-11-24, "Albion - the plan", round 4: "Morgana's campaign and raid ... a
    /// three-phase raid with Morgana, the Wrath of Mordred and the Afanc"). The raid is a chain (zone007 lb_gate_of_annwn, its boss
    /// stage); this gives its boss her phases and her spells:
    ///   I   Morgana (to 66%): Fay-Fire on whoever she's looking at, now and then a Glamour that roots them;
    ///   II  the Wrath of Mordred (from 66%): she calls her nephew's ghost out of the gate - a champion with his own health - and
    ///       while he stands she cannot be brought below 60%. Camlann's Curse (a disease round her: curers) and Fay-Fire;
    ///   III the Afanc (from 33%): she sings the lake open and the Afanc that Arthur slew comes up out of it, with hounds of
    ///       Annwn behind; while it lives she cannot be brought below 28%. The Drowning (cold, everyone near) and Fay-Fire.
    /// Her look stays her own; her name says what she is doing.
    /// </summary>
    public static class MorganaRaid
    {
        public const string ChainId = "lb_gate_of_annwn";
        public const int Zone = 7;
        public const double WrathAt = 0.66, AfancAt = 0.33;
        public const double WrathFloor = 0.60, AfancFloor = 0.28;
        public const int WrathTemplate = 13039, AfancTemplate = 13019, HoundTemplate = 12999, KnightTemplate = 12016;

        /// <summary>Her phase by her health (pure: tested): 1 Morgana, 2 the Wrath of Mordred called, 3 the Afanc raised.</summary>
        public static int PhaseAt(double healthPct) => healthPct <= AfancAt ? 3 : healthPct <= WrathAt ? 2 : 1;

        /// <summary>How low she can be brought while her champion stands (pure: tested).</summary>
        public static double Floor(int phase, bool championAlive) => !championAlive ? 0 : phase == 3 ? AfancFloor : phase == 2 ? WrathFloor : 0;

        public static string NameFor(int phase) => phase switch
        {
            3 => "Morgana le Fay, Singer of the Lake",
            2 => "Morgana le Fay, Mistress of Camlann",
            _ => "Morgana le Fay"
        };

        sealed class Fight
        {
            public int Phase = 1;
            public long NextCast, NextAoe, NextRoot;
            public EventNpc Champion;
        }

        static readonly ConditionalWeakTable<GameNPC, Fight> _fights = new();

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            _ = new ECSGameTimer(null, _ => { Tick(); return 1000; }, 30_000);
        }

        static void Tick()
        {
            try
            {
                long now = Environment.TickCount64;
                foreach (ChainRuntime c in DynamicEventManager.Chains)
                    if (c.Zone?.ID == Zone && c.Def.Id == ChainId && c.Stage?.Boss is EventNpc q && q.IsAlive)
                        Morgana(c, q, now);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[MorganaRaid] " + ex.Message);
            }
        }

        static void Morgana(ChainRuntime c, EventNpc q, long now)
        {
            Fight f = _fights.GetValue(q, _ => new Fight { NextCast = now + 6000, NextAoe = now + 20_000, NextRoot = now + 14_000 });
            double pct = q.Health / (double) Math.Max(1, q.MaxHealth);
            int phase = PhaseAt(pct);
            if (phase > f.Phase)
            {
                f.Phase = phase;
                q.Name = NameFor(phase);
                q.BroadcastLivingEquipmentUpdate();
                f.Champion = Call(c, q, phase);
                string words = phase == 2
                    ? "Morgana opens her hand toward the Gate, and something in black mail walks out of it, still bleeding from Camlann: 'Nephew. Kill them for me.' The Wrath of Mordred is here - and while he stands, she is beyond your reach."
                    : "Morgana sings, and the lake answers. The water heaves - and the Afanc, the beast Arthur himself dragged out of Llyn Barfog, comes up the shore with the hounds of Annwn baying behind it. While it lives, she is beyond your reach.";
                foreach (GamePlayer p in c.PlayersInZone())
                {
                    p.Out.SendMessage(phase == 2 ? "The Wrath of Mordred" : "The Afanc rises", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                    p.Out.SendMessage(words, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                }
                if (phase == 3)
                    f.NextAoe = now + 5000;
            }
            // her champion shields her: she can't be brought below the floor while it stands
            bool championAlive = f.Champion != null && f.Champion.IsAlive && f.Champion.ObjectState == GameObject.eObjectState.Active;
            double floor = Floor(f.Phase, championAlive);
            if (floor > 0 && pct < floor)
                q.Health = (int) Math.Ceiling(q.MaxHealth * floor);
            if (!q.InCombat || q.IsCasting || q.TargetObject is not GameLiving t || !t.IsAlive)
                return;
            if (now >= f.NextAoe && f.Phase >= 2)
            {
                f.NextAoe = now + (f.Phase == 3 ? 16_000 : 20_000);
                Cast(q, f.Phase == 3 ? Drowning : Curse);
                return;
            }
            if (now >= f.NextRoot)
            {
                f.NextRoot = now + 22_000;
                if (!t.effectListComponent.ContainsEffectForEffectType(eEffect.MovementSpeedDebuff))
                {
                    Cast(q, Glamour);
                    return;
                }
            }
            if (now >= f.NextCast)
            {
                f.NextCast = now + (f.Phase == 3 ? 6500 : 8500);
                Cast(q, FayFire);
            }
        }

        /// <summary>Her champion for the phase, and its company: added to the stage's monsters, so they go when it ends.</summary>
        static EventNpc Call(ChainRuntime c, EventNpc q, int phase)
        {
            StageRuntime st = c.Stage;
            if (st == null)
                return null;
            var at = new System.Numerics.Vector3(q.X, q.Y, q.Z);
            EventNpc champ = phase == 2
                ? c.Make(WrathTemplate, "the Wrath of Mordred", 62, 0, 70, null, "Morgana's champion", c.Around(at, 400), EventRole.Hostile, st)
                : c.Make(AfancTemplate, "the Afanc", 62, 0, 90, null, "the Beast of the Lake", c.Around(at, 600), EventRole.Hostile, st);
            if (champ != null)
            {
                champ.HealthMult = phase == 2 ? 7 : 9;
                champ.Health = champ.MaxHealth;
                st.Spawned.Add(champ);
            }
            for (int i = 0; i < 3; i++)
            {
                EventNpc add = phase == 2
                    ? c.Make(KnightTemplate, "knight of Camlann", 55, 485, 55, null, "Mordred's host", c.Around(at, 500), EventRole.Hostile, st)
                    : c.Make(HoundTemplate, "hound of Annwn", 55, 0, 60, null, "the Hunt of Annwn", c.Around(at, 600), EventRole.Hostile, st);
                if (add != null)
                    st.Spawned.Add(add);
            }
            return champ;
        }

        static void Cast(GameNPC who, Spell s)
        {
            try { who.CastSpell(s, SkillBase.GetSpellLine(GlobalSpellsLines.Mob_Spells), false); }
            catch (Exception) { }
        }

        static Spell Make(int id, string name, int effect, eSpellType type, eDamageType dmg, double damage, int range, int radius,
                          int castS, int duration = 0, int frequency = 0, double value = 0)
        {
            var d = new DbSpell
            {
                AllowAdd = false, SpellID = id, Name = name, ClientEffect = effect, Icon = effect, CastTime = castS, RecastDelay = 0,
                Damage = damage, DamageType = (int) dmg, Range = range, Radius = radius, Duration = duration, Frequency = frequency,
                Value = value, Target = eSpellTarget.ENEMY.ToString(), Type = type.ToString(), Uninterruptible = true, MoveCast = true
            };
            return new Spell(d, 62);
        }

        public static readonly Spell FayFire = Make(9007101, "Fay-Fire", 4159, eSpellType.DirectDamageNoVariance, eDamageType.Heat, 440, 1500, 0, 3);
        public static readonly Spell Glamour = Make(9007102, "Glamour", 4125, eSpellType.SpeedDecrease, eDamageType.Spirit, 0, 1500, 0, 2, 10, 0, 99);
        public static readonly Spell Curse = Make(9007103, "Camlann's Curse", 13559, eSpellType.Disease, eDamageType.Body, 0, 0, 650, 2, 40, 0, 50);
        public static readonly Spell Drowning = Make(9007104, "The Drowning", 13533, eSpellType.DirectDamageNoVariance, eDamageType.Cold, 500, 0, 700, 3);
    }
}
