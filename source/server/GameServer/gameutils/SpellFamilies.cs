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
            // pets are not ranks of each other (owner 2026-11-19: "New pets shouldn't replace older pets, because the pets
            // have different utility (like Underhill Ally is a healer, Underhill Compatriot is a tank)"): each its own
            if (HibernianKits.NatureSpirits.Contains(s.ID))
                return ("pet", 5251);                    // (the Druid's nature spirit: one summon, its forms on the pet window)
            // Albion's pets that are one creature in ranks (owner 2026-11-24: "make sure the spell book isn't filled with
            // weaker versions of the same spell once you learn one"): a Theurgist's elementals (one kind a line) and a
            // Cabalist's simulacra - only the best; a Necromancer's three zombie servants are one. His other servants stay
            // each their own, as in vanilla (an Abomination is not a Greater Necroservant).
            if (s.SpellType is eSpellType.SummonTheurgistPet or eSpellType.SummonSimulacrum)
                return ("pet", s.SpellType);
            if (s.ID is >= 9401 and <= 9403)
                return ("pet", 9401);
            // Midgard's (owner 2026-11-24: lower commanders "can go away as soon as you learn the newest one"): a Bonedancer's
            // commander and each of its six minion kinds (two a line, alternating ids: id / 10 is the kind) - only the best of
            // each; a Spiritmaster's spirit fighter and a Hunter's companion are one pet in ranks
            if (s.SpellType is eSpellType.SummonCommander or eSpellType.SummonMinion)
                return ("pet", s.ID / 10);
            if (s.SpellType is eSpellType.SummonSpiritFighter or eSpellType.SummonHunterPet)
                return ("pet", s.SpellType);
            if (IsPet(s))
                return ("pet", s.ID);
            // ranks the old data gave groups of their own (a Cleric's Gift / Boon / Blessing of the Host, its Refiner's
            // Strength / Purifying Strength / Mercybringer): one job each
            if (s.SpellType is eSpellType.SpreadHeal or eSpellType.MeleeDamageBuff)
                return (s.SpellType, s.Target);
            if (s.Group != 0)
                return (s.Group, s.SpellType);
            return (s.SpellType, s.Target, s.Radius > 0, s.Range == 0 && s.Radius > 0, s.CastTime <= 0, s.DamageType,
                s.Frequency > 0, s.Pulse > 0, s.NeedInstrument);
        }

        public static bool IsPet(Spell s) => s.SpellType.ToString().StartsWith("Summon") || s.SpellType == eSpellType.AstralPetSummon;

        /// <summary>The rank before this one in its line (the spell it replaced), or null - its tooltip: "A more powerful
        /// version of ...".</summary>
        public static Spell PreviousRank(Spell spell, IEnumerable<Spell> lineSpells)
        {
            if (spell == null || lineSpells == null)
                return null;
            object k = Key(spell);
            return lineSpells.Where(s => s.ID != spell.ID && (s.Level < spell.Level || s.Level == spell.Level && s.ID < spell.ID) && Equals(Key(s), k))
                .OrderBy(s => s.Level).ThenBy(s => s.ID).LastOrDefault();
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
