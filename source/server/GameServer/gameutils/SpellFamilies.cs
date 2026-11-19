using System.Collections.Generic;
using System.Linq;

namespace DOL.GS
{
    /// <summary>
    /// One spell per job (owner 2026-11-19: "we're fixing their spells so upgrades replace the older spell, and the
    /// spell book is cleaned up to work well with controllers and our new combat system"): a spell line's ranks of the
    /// same spell - Gleam Ray, Moon Ray, Sun Ray, Aurora Blast - are one family, and a player only has its best rank
    /// learned; the next rank takes its place (the client's hotbars put the upgrade where the old one sat). The family
    /// is DAoC's own spell group with the spell's type (the database groups ranks for buff stacking); a spell without a
    /// group goes by what it does - type, target, area, instant, damage type, over time, pulsing, instrument.
    /// </summary>
    public static class SpellFamilies
    {
        public static object Key(Spell s)
        {
            if (s.Group != 0)
                return (s.Group, s.SpellType);
            return (s.SpellType, s.Target, s.Radius > 0, s.Range == 0 && s.Radius > 0, s.CastTime <= 0, s.DamageType,
                s.Frequency > 0, s.Pulse > 0, s.NeedInstrument);
        }

        /// <summary>Only the best learned rank of each family, in the line's order (by level).</summary>
        public static List<Skill> BestOnly(IEnumerable<Skill> spells)
        {
            var best = new Dictionary<object, Spell>();
            var order = new List<object>();
            var others = new List<Skill>();
            foreach (Skill sk in spells)
            {
                if (sk is not Spell sp)
                {
                    others.Add(sk);
                    continue;
                }
                object k = Key(sp);
                if (!best.TryGetValue(k, out Spell had))
                {
                    best[k] = sp;
                    order.Add(k);
                }
                else if (sp.Level > had.Level || sp.Level == had.Level && sp.ID > had.ID)
                    best[k] = sp;
            }
            return order.Select(k => (Skill) best[k]).OrderBy(s => s.Level).ThenBy(s => s.ID).Concat(others).ToList();
        }

        /// <summary>The spellbook roadmap's rows for a line: one a family - the rank you have (or the first, not yet), and
        /// the next rank and its level.</summary>
        public static IEnumerable<(Spell shown, bool have, Spell next)> Roadmap(IEnumerable<Spell> lineSpells, int lineLevel)
        {
            foreach (var g in lineSpells.OrderBy(s => s.Level).ThenBy(s => s.ID).GroupBy(Key))
            {
                var ranks = g.ToList();
                Spell had = ranks.LastOrDefault(s => s.Level <= lineLevel);
                Spell next = ranks.FirstOrDefault(s => s.Level > lineLevel);
                yield return (had ?? ranks[0], had != null, had == null ? ranks.Skip(1).FirstOrDefault() : next);
            }
        }
    }
}
