using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using DOL.Database;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// Your companion's character sheet (owner 2026-11-19: "Also need a way to be able to see their stats, spec, and
    /// spells available to them"): /companion sheet (its interact menu: Character Sheet) sends "#CSHEET|{json}" - its
    /// name, class, role and competence, health / power / endurance, the eight stats as they are now (items and buffs in),
    /// armour factor, weapon skill and resists, every specialization with its level, and the styles, abilities and spells
    /// it can use now. The client's companion sheet window shows it.
    /// </summary>
    public static partial class PersonalCompanions
    {
        static readonly (eProperty Prop, string Label)[] SheetStats =
        {
            (eProperty.Strength, "STR"), (eProperty.Constitution, "CON"), (eProperty.Dexterity, "DEX"), (eProperty.Quickness, "QUI"),
            (eProperty.Intelligence, "INT"), (eProperty.Piety, "PIE"), (eProperty.Empathy, "EMP"), (eProperty.Charisma, "CHA"),
        };

        static readonly (eProperty Prop, string Label)[] SheetResists =
        {
            (eProperty.Resist_Crush, "CRUSH"), (eProperty.Resist_Slash, "SLASH"), (eProperty.Resist_Thrust, "THRUST"),
            (eProperty.Resist_Heat, "HEAT"), (eProperty.Resist_Cold, "COLD"), (eProperty.Resist_Matter, "MATTER"),
            (eProperty.Resist_Body, "BODY"), (eProperty.Resist_Spirit, "SPIRIT"), (eProperty.Resist_Energy, "ENERGY"),
        };

        public static string Sheet(GamePlayer p)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            GameBot bot = Of(p);
            if (bot == null)
                return $"{r.Name} isn't with you - call them first.";
            try
            {
                var styles = new List<object>();
                var abilities = new List<string>();
                foreach (var (skill, _) in bot.GetAllUsableSkills())
                {
                    if (skill is Style st)
                        styles.Add(new { name = st.Name, spec = st.Spec, level = st.SpecLevelRequirement, icon = st.Icon,
                            opening = st.OpeningRequirementType.ToString(), end = st.EnduranceCost });
                    else if (skill is Ability ab)
                        abilities.Add(ab.Name);
                }
                var spells = new List<object>();
                foreach (var (line, list) in bot.GetAllUsableListSpells())
                    foreach (Skill s in list)
                        if (s is Spell sp)
                            spells.Add(new { line = line.Name, name = sp.Name, level = sp.Level, icon = sp.Icon, type = sp.SpellType.ToString(),
                                power = sp.Power, cast = sp.CastTime / 1000.0 });
                DbInventoryItem weapon = bot.ActiveWeapon;
                var sheet = new
                {
                    name = bot.Name,
                    cls = bot.CharacterClass?.Name ?? r.Class.ToString(),
                    race = r.Race.ToString(),
                    level = (int) bot.Level,
                    role = RoleName(r),
                    competence = CompetenceTitle(r.Competence),
                    alive = bot.IsAlive,
                    hp = new[] { bot.Health, bot.MaxHealth },
                    power = new[] { bot.Mana, bot.MaxMana },
                    endurance = new[] { bot.Endurance, bot.MaxEndurance },
                    stats = SheetStats.Select(s => new { k = s.Label, v = bot.GetModified(s.Prop) }).ToList(),
                    resists = SheetResists.Select(s => new { k = s.Label, v = bot.GetModified(s.Prop) }).ToList(),
                    af = bot.GetModified(eProperty.ArmorFactor),
                    weapon = weapon?.Name ?? "",
                    ws = weapon != null ? (int) bot.GetWeaponSkill(weapon) : 0,
                    specs = bot.GetSpecList().Where(s => s.Trainable || s.Level > 1)
                        .Select(s => new { name = s.Name, level = s.Level }).ToList(),
                    gear = GearSlots.Select(g => (g.Label, Item: bot.Inventory?.GetItem(g.Slot))).Where(g => g.Item != null)
                        .Select(g => new { slot = g.Label, name = g.Item.Name, level = g.Item.Level, id = g.Item.Id_nb }).ToList(),
                    abilities,
                    styles,
                    spells,
                };
                // in pieces (a system line holds well under 2 KB): "#CSHEETP|..." then the last as "#CSHEET|..."
                string json = JsonSerializer.Serialize(sheet);
                const int piece = 900;
                for (int i = 0; i < json.Length; i += piece)
                    NewClient.Send(p, (i + piece >= json.Length ? "#CSHEET|" : "#CSHEETP|") + json.Substring(i, Math.Min(piece, json.Length - i)));
                return null;
            }
            catch (Exception ex)
            {
                log.Error($"Companion sheet for {bot.Name}", ex);
                return $"{bot.Name}'s sheet couldn't be made: {ex.Message}";
            }
        }
    }
}
