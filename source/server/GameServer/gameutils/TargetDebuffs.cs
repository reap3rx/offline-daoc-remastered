using System;
using System.Collections.Generic;
using System.Text;

namespace DOL.GS
{
    /// <summary>
    /// Debuffs you can see (owner 2026-11-20: "For debuffs, can we show them on the target nameplate, the icon? Also, there
    /// are some bleeds or debuffs ... that don't give a debuff icon in my buff list"):
    ///   An icon for every lasting harmful effect: DAoC's database leaves some without one (every style bleed - the
    ///     monsters' bite bleeds among them - a few snares, slows and DoTs), so they never showed in your effect list or
    ///     anywhere else. FallbackIcon gives those their kind's icon (ECSGameSpellEffect.Icon).
    ///   A monster's harmful effects, sent to the players near it whenever its list changes (EffectListComponent):
    ///     "#DBF|oid|icon:seconds;..." (seconds left, 0 = none shown) - the client draws them over its plate.
    /// </summary>
    public static class TargetDebuffs
    {
        public const ushort BleedIcon = 2130, StunIcon = 2132, SnareIcon = 2135, SlowIcon = 2140;

        /// <summary>The icon a harmful spell's effect shows when its own is 0 (0: still none).</summary>
        public static ushort FallbackIcon(Spell s)
        {
            if (s == null || s.Duration <= 0 && s.Frequency <= 0)
                return 0;
            return s.SpellType switch
            {
                eSpellType.StyleBleeding => BleedIcon,
                eSpellType.StyleStun or eSpellType.Stun => StunIcon,
                eSpellType.StyleSpeedDecrease or eSpellType.SpeedDecrease or eSpellType.UnbreakableSpeedDecrease => SnareIcon,
                eSpellType.StyleCombatSpeedDebuff or eSpellType.CombatSpeedDebuff => SlowIcon,
                eSpellType.StrengthDebuff => 4083,
                eSpellType.DamageOverTime => 511,
                eSpellType.Disease => 4089,
                _ => 0
            };
        }

        /// <summary>EffectListComponent: a living's effects changed - a monster's harmful ones go to the players near it.</summary>
        public static void Changed(GameLiving owner)
        {
            try
            {
                if (owner is not GameNPC n || n is GameBot || n.ObjectState != GameObject.eObjectState.Active)
                    return;
                string line = Line(n);
                foreach (GamePlayer p in n.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    NewClient.Send(p, line);
            }
            catch (Exception e)
            {
                Console.WriteLine("[TargetDebuffs] " + e.Message);
            }
        }

        /// <summary>A monster's harmful effects as the client reads them.</summary>
        public static string Line(GameNPC n)
        {
            var sb = new StringBuilder("#DBF|").Append(n.ObjectID).Append('|');
            var seen = new HashSet<ushort>();
            List<ECSGameSpellEffect> list = n.effectListComponent?.GetSpellEffects();
            if (list != null)
                foreach (ECSGameSpellEffect e in list)
                {
                    if (e == null || e.IsDisabled || e.HasPositiveEffect || e is ECSImmunityEffect)
                        continue;
                    ushort icon = e.Icon;
                    if (icon == 0 || !seen.Add(icon))
                        continue;
                    long left = e.GetRemainingTimeForClient();
                    sb.Append(icon).Append(':').Append(left > 0 ? (left + 999) / 1000 : 0).Append(';');
                }
            return sb.ToString();
        }
    }
}
