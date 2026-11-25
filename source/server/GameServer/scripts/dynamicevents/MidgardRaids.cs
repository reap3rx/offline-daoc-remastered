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
    /// Midgard's two raids (claude 2026-11-25, "Midgard - the plan", round 4), made like Morgana's (MorganaRaid.cs): the raid is a
    /// chain (its boss stage), and this gives the boss phases, champions that shield it, and spells:
    ///   - Hati at his howe (zone108 rk_hatis_howe, the King's March): I Hati (to 66%): Moon-Bite on whoever he's looking at, now and
    ///     then a Frost-Fetter that roots them; II Skoll (from 66%): his brother, the wolf that hunts the sun, comes out of the
    ///     north with Fenrir's soldiers, and while Skoll stands Hati cannot be brought below 60% - the Howl (cold, everyone near);
    ///     III the Fimbulwinter (from 33%): he calls the endless winter down, and the Wretch of Winter walks in it with its wraiths;
    ///     while it stands, not below 28% - the Fimbulwinter (cold, everyone near).
    ///   - the Drakulv Hierophant at the Wyrm-Temple (zone116 mh_wyrm_temple, the Dragon-Oath): I the Hierophant: Wyrm-Fire, now
    ///     and then a Scale-Bind; II the Wyrm-Guard (from 66%): the temple's champion, and while it stands not below 60% - Scale-Rot
    ///     (a disease: curers); III the Brood-Elder (from 33%): he speaks his half of the dragon's name and one of her eldest brood
    ///     comes up out of the temple; while it lives, not below 28% - the Dragon's Breath (heat, everyone near).
    /// </summary>
    public sealed class PhasedRaid
    {
        public const double SecondAt = 0.66, ThirdAt = 0.33;
        public const double SecondFloor = 0.60, ThirdFloor = 0.28;

        public string ChainId;
        public int Zone;
        public string[] Names;                      // [0] phase 1 .. [2] phase 3
        public string[] Calls;                      // [0] phase 2's words, [1] phase 3's
        public string[] CallTitles;
        public (int Template, string Name, string Guild, int Size, double Hp)[] Champions;      // [0] phase 2, [1] phase 3
        public (int Template, string Name, string Guild, int Size)[] Adds;                      // [0] phase 2, [1] phase 3
        public Spell Bolt, Root, Aoe2, Aoe3;

        /// <summary>The phase by health (pure: tested): 1, 2 the first champion called, 3 the second.</summary>
        public static int PhaseAt(double healthPct) => healthPct <= ThirdAt ? 3 : healthPct <= SecondAt ? 2 : 1;

        /// <summary>How low the boss can be brought while its champion stands (pure: tested).</summary>
        public static double Floor(int phase, bool championAlive) => !championAlive ? 0 : phase == 3 ? ThirdFloor : phase == 2 ? SecondFloor : 0;

        public string NameFor(int phase) => Names[Math.Clamp(phase, 1, 3) - 1];

        sealed class Fight
        {
            public int Phase = 1;
            public long NextCast, NextAoe, NextRoot;
            public EventNpc Champion;
        }

        readonly ConditionalWeakTable<GameNPC, Fight> _fights = new();

        public static readonly PhasedRaid[] All = { MidgardRaids.Hati, MidgardRaids.Hierophant };

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
                    foreach (PhasedRaid r in All)
                        if (c.Zone?.ID == r.Zone && c.Def.Id == r.ChainId && c.Stage?.Boss is EventNpc q && q.IsAlive)
                            r.Fighting(c, q, now);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[PhasedRaid] " + ex.Message);
            }
        }

        void Fighting(ChainRuntime c, EventNpc q, long now)
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
                foreach (GamePlayer p in c.PlayersInZone())
                {
                    p.Out.SendMessage(CallTitles[phase - 2], eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                    p.Out.SendMessage(Calls[phase - 2], eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                }
                if (phase == 3)
                    f.NextAoe = now + 5000;
            }
            bool championAlive = f.Champion != null && f.Champion.IsAlive && f.Champion.ObjectState == GameObject.eObjectState.Active;
            double floor = Floor(f.Phase, championAlive);
            if (floor > 0 && pct < floor)
                q.Health = (int) Math.Ceiling(q.MaxHealth * floor);
            if (!q.InCombat || q.IsCasting || q.TargetObject is not GameLiving t || !t.IsAlive)
                return;
            if (now >= f.NextAoe && f.Phase >= 2)
            {
                f.NextAoe = now + (f.Phase == 3 ? 16_000 : 20_000);
                Cast(q, f.Phase == 3 ? Aoe3 : Aoe2);
                return;
            }
            if (now >= f.NextRoot)
            {
                f.NextRoot = now + 22_000;
                if (!t.effectListComponent.ContainsEffectForEffectType(eEffect.MovementSpeedDebuff))
                {
                    Cast(q, Root);
                    return;
                }
            }
            if (now >= f.NextCast)
            {
                f.NextCast = now + (f.Phase == 3 ? 6500 : 8500);
                Cast(q, Bolt);
            }
        }

        EventNpc Call(ChainRuntime c, EventNpc q, int phase)
        {
            StageRuntime st = c.Stage;
            if (st == null)
                return null;
            var at = new System.Numerics.Vector3(q.X, q.Y, q.Z);
            var ch = Champions[phase - 2];
            EventNpc champ = c.Make(ch.Template, ch.Name, 62, 0, (byte) ch.Size, null, ch.Guild, c.Around(at, 450), EventRole.Hostile, st);
            if (champ != null)
            {
                champ.HealthMult = ch.Hp;
                champ.Health = champ.MaxHealth;
                st.Spawned.Add(champ);
            }
            var ad = Adds[phase - 2];
            for (int i = 0; i < 3; i++)
            {
                EventNpc add = c.Make(ad.Template, ad.Name, 55, 0, (byte) ad.Size, null, ad.Guild, c.Around(at, 550), EventRole.Hostile, st);
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

        public static Spell Make(int id, string name, int effect, eSpellType type, eDamageType dmg, double damage, int range, int radius,
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
    }

    public static class MidgardRaids
    {
        public const string HatiChain = "rk_hatis_howe", HierophantChain = "mh_wyrm_temple";

        public static readonly PhasedRaid Hati = new()
        {
            ChainId = HatiChain, Zone = 108,
            Names = new[] { "Hati, Who Hunts the Moon", "Hati, Brother of Skoll", "Hati, Bringer of the Fimbulwinter" },
            CallTitles = new[] { "Skoll comes", "The Fimbulwinter" },
            Calls = new[]
            {
                "Hati throws back his head and howls, and out of the north something answers - a wolf as great as he is, its fur the colour of a setting sun: Skoll, who hunts the sun as Hati hunts the moon. While Skoll stands, Hati is beyond your reach.",
                "Hati howls at the moon, and the moon flinches. Snow comes down out of a clear sky - thick, then blinding - and in it walks the Wretch of Winter with the wraiths behind it. The Fimbulwinter. While the Wretch stands, Hati is beyond your reach."
            },
            Champions = new[]
            {
                (60165623, "Skoll, Who Hunts the Sun", "Brother of Hati", 95, 7.0),
                (60161108, "the Wretch of Winter", "Herald of the Fimbulwinter", 80, 9.0)
            },
            Adds = new[]
            {
                (60160797, "fenrir soldier", "Hati's Host", 55),
                (60167978, "windswept wraith", "of the endless winter", 55)
            },
            Bolt = PhasedRaid.Make(9108101, "Moon-Bite", 4568, eSpellType.DirectDamageNoVariance, eDamageType.Cold, 440, 1500, 0, 3),
            Root = PhasedRaid.Make(9108102, "Frost-Fetter", 4125, eSpellType.SpeedDecrease, eDamageType.Cold, 0, 1500, 0, 2, 10, 0, 99),
            Aoe2 = PhasedRaid.Make(9108103, "The Howl of Skoll", 13533, eSpellType.DirectDamageNoVariance, eDamageType.Cold, 380, 0, 650, 3),
            Aoe3 = PhasedRaid.Make(9108104, "The Fimbulwinter", 13533, eSpellType.DirectDamageNoVariance, eDamageType.Cold, 500, 0, 700, 3),
        };

        public static readonly PhasedRaid Hierophant = new()
        {
            ChainId = HierophantChain, Zone = 116,
            Names = new[] { "the Drakulv Hierophant", "the Hierophant, Keeper of the Rite", "the Hierophant, Speaker of the Name" },
            CallTitles = new[] { "The Wyrm-Guard", "The Brood-Elder rises" },
            Calls = new[]
            {
                "The Hierophant strikes his staff on the temple floor, and the Wyrm-Guard comes down the steps - a drakulv in a dragon's whole scale, sworn to die before its master. While it stands, the Hierophant is beyond your reach.",
                "The Hierophant speaks - half a name, and the temple shakes with it. Out of the pit behind the altar climbs one of Gjalpinulva's eldest brood, smoke pouring from its jaws. While it lives, the Hierophant is beyond your reach."
            },
            Champions = new[]
            {
                (60160116, "the Wyrm-Guard", "Sworn to the Hierophant", 80, 7.0),
                (60159218, "the Brood-Elder", "Eldest of Gjalpinulva's Brood", 100, 9.0)
            },
            Adds = new[]
            {
                (60160112, "drakulv axehand", "Gjalpinulva's Drakulv", 55),
                (60160111, "drakulv attendant", "the Hierophant's Disciples", 55)
            },
            Bolt = PhasedRaid.Make(9116101, "Wyrm-Fire", 4159, eSpellType.DirectDamageNoVariance, eDamageType.Heat, 440, 1500, 0, 3),
            Root = PhasedRaid.Make(9116102, "Scale-Bind", 4125, eSpellType.SpeedDecrease, eDamageType.Spirit, 0, 1500, 0, 2, 10, 0, 99),
            Aoe2 = PhasedRaid.Make(9116103, "Scale-Rot", 13559, eSpellType.Disease, eDamageType.Body, 0, 0, 650, 2, 40, 0, 50),
            Aoe3 = PhasedRaid.Make(9116104, "The Dragon's Breath", 4159, eSpellType.DirectDamageNoVariance, eDamageType.Heat, 500, 0, 700, 3),
        };
    }
}
