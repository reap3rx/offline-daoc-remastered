using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// Queen Cliodna's fight at the Queen's Seat (owner 2026-11-24: "a 3 phase fight. One as a normal female Elf (her base
    /// form) then transforming into a larger Hag, then finally a large Bainshee. Her fight should be nearly the equivalent of
    /// a Dragon raid, requiring multiple groups ... A long fight, very high HP, requires healers and disease/poison curers").
    /// The raid is a chain (zone208 cf_queens_seat, its boss stage); this gives its boss her phases and her spells:
    ///   I   the Queen (an elf, her own face): Dark Blast (cold) and a stun on whoever she's looking at;
    ///   II  the Hag (from 66%): bigger, and rotten - Hag's Rot (a disease over everyone near: curers) and Bog-Venom (poison
    ///       on her target: curers again);
    ///   III the Bainshee (from 33%): bigger still, and keening - the Keen (heavy spirit damage on everyone near) and a
    ///       Screech that slows; she calls bainshees out of the trees.
    /// And the forest's own bainshees (the zone build's, the events'): normal-sized, wailing - Wailing Pain on their target,
    /// now and then a Screech round them. Their look and sounds are the client's Bainshee class's (model 1885; the
    /// spells' client effects carry the SpellBanshee sounds).
    /// </summary>
    public static class CliodnaRaid
    {
        public const string ChainId = "cf_queens_seat";
        public const ushort ElfModel = 347, HagModel = 445, BainsheeModel = 1885;
        public const double HagAt = 0.66, BainsheeAt = 0.33;

        /// <summary>Her phase by her health (pure: tested): 1 the Queen, 2 the Hag, 3 the Bainshee.</summary>
        public static int PhaseAt(double healthPct) => healthPct <= BainsheeAt ? 3 : healthPct <= HagAt ? 2 : 1;

        public static (string name, ushort model, byte size) Look(int phase) => phase switch
        {
            3 => ("Cliodna, the Bainshee Queen", BainsheeModel, 110),
            2 => ("Cliodna the Hag", HagModel, 90),
            _ => ("Queen Cliodna", ElfModel, 62)
        };

        sealed class Fight
        {
            public int Phase = 1;
            public long NextCast, NextAoe, NextRot;
        }

        static readonly ConditionalWeakTable<GameNPC, Fight> _fights = new();
        static readonly ConditionalWeakTable<GameNPC, Fight> _wailers = new();

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
                {
                    if (c.Zone?.ID != LugCampaign.ForestZone || c.Stage == null)
                        continue;
                    if (c.Def.Id == ChainId && c.Stage.Boss is EventNpc q && q.IsAlive)
                        Queen(c, q, now);
                    foreach (EventNpc n in c.Stage.Spawned.Where(n => n.IsAlive && n.IsEnemy && n.Model == BainsheeModel && n != c.Stage.Boss).ToList())
                        Wail(n, now);
                }
                if (now >= _nextScan)
                {
                    _nextScan = now + 20_000;
                    _built = ZoneBuilds.SiteIds(LugCampaign.ForestZone).SelectMany(s => ZoneBuilds.SiteNpcs(LugCampaign.ForestZone, s))
                        .Where(n => n.Model == BainsheeModel).ToList();
                }
                foreach (GameNPC n in _built)
                    if (n.IsAlive && n.InCombat && n.ObjectState == GameObject.eObjectState.Active)
                        Wail(n, now);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[CliodnaRaid] " + ex.Message);
            }
        }

        static long _nextScan;
        static List<GameNPC> _built = new();

        static void Queen(ChainRuntime c, EventNpc q, long now)
        {
            Fight f = _fights.GetValue(q, _ => new Fight { NextCast = now + 6000, NextAoe = now + 20_000, NextRot = now + 15_000 });
            double pct = q.Health / (double) Math.Max(1, q.MaxHealth);
            int phase = PhaseAt(pct);
            if (phase > f.Phase)
            {
                f.Phase = phase;
                var (name, model, size) = Look(phase);
                q.Name = name;
                q.Model = model;
                q.Size = size;
                q.BroadcastLivingEquipmentUpdate();
                string words = phase == 2
                    ? "Cliodna's beauty sloughs away like wet bark. What stands up is old, and bent, and rotten: 'You wanted to see the Queen? THIS is the Queen.'"
                    : "The Hag screams - and keeps screaming, and the scream becomes a shape, pale and tall in green scale: the Bainshee Queen. Every bainshee in the forest answers her.";
                foreach (GamePlayer p in c.PlayersInZone())
                {
                    p.Out.SendMessage(name, eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
                    p.Out.SendMessage(words, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                }
                if (phase == 3)
                    f.NextAoe = now + 4000;
            }
            if (!q.InCombat || q.IsCasting || q.TargetObject is not GameLiving t || !t.IsAlive)
                return;
            if (now >= f.NextAoe && f.Phase == 3)
            {
                f.NextAoe = now + 18_000;
                Cast(q, Util.Chance(60) ? Keen : Screech);
                return;
            }
            if (now >= f.NextRot && f.Phase == 2)
            {
                f.NextRot = now + 16_000;
                Cast(q, Util.Chance(50) ? Rot : Venom);
                return;
            }
            if (now >= f.NextCast)
            {
                f.NextCast = now + (f.Phase == 3 ? 7000 : 9000);
                if (f.Phase == 1)
                    Cast(q, !t.effectListComponent.ContainsEffectForEffectType(eEffect.Stun) && !t.effectListComponent.ContainsEffectForEffectType(eEffect.StunImmunity) && Util.Chance(40) ? Stun : DarkBlast);
                else if (f.Phase == 2)
                    Cast(q, Util.Chance(50) ? Venom : DarkBlast);
                else
                    Cast(q, WailingPain);
            }
        }

        /// <summary>A forest bainshee in a fight: Wailing Pain on its target every so often, sometimes a Screech round it.</summary>
        static void Wail(GameNPC n, long now)
        {
            if (n.IsCasting || n.TargetObject is not GameLiving t || !t.IsAlive)
                return;
            Fight f = _wailers.GetValue(n, _ => new Fight { NextCast = now + 3000 + Util.Random(0, 4000), NextAoe = now + 15_000 + Util.Random(0, 10_000) });
            if (now >= f.NextAoe && n.IsWithinRadius(t, 300))
            {
                f.NextAoe = now + 25_000 + Util.Random(0, 10_000);
                Cast(n, Screech);
                return;
            }
            if (now >= f.NextCast)
            {
                f.NextCast = now + 10_000 + Util.Random(0, 4000);
                Cast(n, WailingPain);
            }
        }

        static void Cast(GameNPC who, Spell s)
        {
            try { who.CastSpell(s, SkillBase.GetSpellLine(GlobalSpellsLines.Mob_Spells), false); }
            catch (Exception) { }
        }

        // ------------------------------------------------------------------ the spells (client effects: the Bainshee
        // class's own for the wails - 13532 Wailing Pain, 13540 Prohibiting Screech, 13559 Bawler's Infliction)

        static Spell Make(int id, string name, int effect, eSpellType type, eDamageType dmg, double damage, int range, int radius,
                          int castS, int duration = 0, int frequency = 0, double value = 0)
        {
            var d = new DbSpell
            {
                AllowAdd = false, SpellID = id, Name = name, ClientEffect = effect, Icon = effect, CastTime = castS, RecastDelay = 0,
                Damage = damage, DamageType = (int) dmg, Range = range, Radius = radius, Duration = duration, Frequency = frequency,
                Value = value, Target = eSpellTarget.ENEMY.ToString(), Type = type.ToString(), Uninterruptible = true, MoveCast = true
            };
            return new Spell(d, 60);
        }

        public static readonly Spell DarkBlast = Make(9208101, "Dark Blast", 4159, eSpellType.DirectDamageNoVariance, eDamageType.Cold, 420, 1500, 0, 3);
        public static readonly Spell Stun = Make(9208102, "Stun", 4125, eSpellType.Stun, eDamageType.Energy, 0, 1500, 0, 3, 6);
        public static readonly Spell Rot = Make(9208103, "Hag's Rot", 13559, eSpellType.Disease, eDamageType.Body, 0, 0, 600, 2, 40, 0, 50);
        public static readonly Spell Venom = Make(9208104, "Bog-Venom", 13558, eSpellType.DamageOverTime, eDamageType.Body, 90, 1500, 0, 2, 30, 3000);
        public static readonly Spell Keen = Make(9208105, "The Keen", 13533, eSpellType.DirectDamageNoVariance, eDamageType.Spirit, 520, 0, 700, 3);
        public static readonly Spell Screech = Make(9208106, "Prohibiting Screech", 13540, eSpellType.SpeedDecrease, eDamageType.Spirit, 0, 0, 450, 2, 12, 0, 50);
        public static readonly Spell WailingPain = Make(9208107, "Wailing Pain", 13532, eSpellType.DirectDamageNoVariance, eDamageType.Spirit, 260, 1500, 0, 2);
    }
}
