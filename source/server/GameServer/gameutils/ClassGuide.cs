using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using DOL.GS.PacketHandler;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// The class guide's data (owner 2026-11-20: "a document ... that goes over every class and their abilities, shared
    /// abilities (like Parry and Shield) and what they do. Detailed, like what level they're obtained, what they do ...
    /// a dev version that has all of that info but also things like their animation, spell effect"): every playable class's
    /// specializations as the server has them right now - its styles (with what each does, its opening, procs, icon and
    /// animation), its spell lines (each spell's level, numbers, icon and client effect) and its abilities (the spec or
    /// character level each comes at). /classguide writes it to class-guide.json in the server's folder; the docs are made
    /// from that file, so they can be made again after any change.
    /// </summary>
    public static class ClassGuide
    {
        public static string Write()
        {
            var classes = new List<object>();
            foreach (var (realm, list) in GlobalConstants.STARTING_CLASSES_DICT)
                foreach (eCharacterClass c in list)
                {
                    ICharacterClass cc = ScriptMgr.FindCharacterClass((int) c);
                    if (cc == null)
                        continue;
                    classes.Add(Class((int) c, cc, realm));
                }
            string path = Path.Combine(Directory.GetCurrentDirectory(), "class-guide.json");
            File.WriteAllText(path, JsonSerializer.Serialize(new { written = DateTime.Now.ToString("yyyy-MM-dd HH:mm"), classes },
                new JsonSerializerOptions { WriteIndented = true }));
            return path;
        }

        static object Class(int id, ICharacterClass cc, eRealm realm)
        {
            var specs = new List<object>();
            foreach (var (spec, level) in SkillBase.GetSpecializationCareer(id).OrderBy(kv => kv.Value))
                specs.Add(Spec(id, spec, level));
            return new
            {
                id, name = cc.Name, female = cc.FemaleName, realm = realm.ToString(), type = cc.ClassType.ToString(),
                races = cc.EligibleRaces?.Select(r => r.ID.ToString()).ToList(), primary = cc.PrimaryStat.ToString(),
                secondary = cc.SecondaryStat.ToString(), tertiary = cc.TertiaryStat.ToString(), mana = cc.ManaStat.ToString(),
                baseHp = cc.BaseHP, specPoints = cc.SpecPointsMultiplier, specs,
            };
        }

        static object Spec(int cls, Specialization spec, int levelRequired)
        {
            List<Style> styles = SkillBase.GetStyleList(spec.KeyName, cls);
            if (styles.Count == 0)
                styles = SkillBase.GetStyleList(spec.KeyName, 0);
            var byId = styles.ToDictionary(s => s.ID, s => s.Name);
            var lines = new List<object>();
            IList<Tuple<SpellLine, int>> all = SkillBase.GetSpecsSpellLines(spec.KeyName) ?? new List<Tuple<SpellLine, int>>();
            var mine = all.Where(t => t.Item2 == cls).ToList();
            foreach (bool baseline in new[] { true, false })
            {
                var pick = mine.Where(t => t.Item1.IsBaseLine == baseline).ToList();
                if (pick.Count == 0)
                    pick = all.Where(t => t.Item2 == 0 && t.Item1.IsBaseLine == baseline).ToList();
                foreach (var (line, _) in pick)
                    lines.Add(new
                    {
                        key = line.KeyName, name = line.Name, baseline,
                        spells = SkillBase.GetSpellList(line.KeyName).OrderBy(s => s.Level).ThenBy(s => s.ID).Select(Spell).ToList(),
                    });
            }
            return new
            {
                key = spec.KeyName, name = spec.Name, career = spec is CareerSpecialization, levelRequired,
                styles = styles.OrderBy(s => s.SpecLevelRequirement).Select(s => StyleOf(s, byId)).ToList(),
                lines,
                abilities = SkillBase.GetSpecAbilityList(spec.KeyName, cls).OrderBy(a => a.SpecLevelRequirement).Select(a => new
                {
                    key = a.KeyName, name = a.Name, rank = a.Level, at = a.SpecLevelRequirement, icon = a.Icon,
                    text = string.Join(" ", a.DelveInfo ?? new List<string>()),
                }).ToList(),
            };
        }

        static object StyleOf(Style s, Dictionary<int, string> byId)
        {
            var d = s.Db;
            string opening = d.OpeningRequirementType switch
            {
                0 when d.OpeningRequirementValue != 0 => "after " + (byId.TryGetValue(d.OpeningRequirementValue, out string n) ? n : "#" + d.OpeningRequirementValue),
                0 => "any",
                1 => d.AttackResultRequirement switch { 3 => "after you parry", 4 => "after you block", 5 => "after you evade", 2 => "after you miss", 7 => "after you hit", _ => "defensive (" + d.AttackResultRequirement + ")" },
                2 => d.OpeningRequirementValue switch { 0 => "from behind", 1 => "from the side", _ => "from the front" },
                _ => "?"
            };
            return new
            {
                id = s.ID, name = s.Name, at = s.SpecLevelRequirement, opening, about = StyleRework.Describe(s),
                weapon = d.WeaponTypeRequirement, endurance = d.EnduranceCost, growth = d.GrowthRate, toHit = d.BonusToHit,
                defense = d.BonusToDefense, icon = d.Icon, animation = d.TwoHandAnimation,
                procs = (s.Procs.Any(p => p.ClassId == s.ClassID) ? s.Procs.Where(p => p.ClassId == s.ClassID) : s.Procs.Where(p => p.ClassId == 0))
                    .Select(p => Spell(p.Spell)).ToList(),
            };
        }

        static object Spell(Spell s) => new
        {
            id = s.ID, name = s.Name, level = s.Level, type = s.SpellType.ToString(), target = s.Target.ToString(),
            range = s.Range, radius = s.Radius, castMs = s.CastTime, recastS = s.RecastDelay, durationS = s.Duration, frequency = s.Frequency,
            value = s.Value, damage = s.Damage, damageType = s.DamageType.ToString(), power = s.Power,
            concentration = s.Concentration, icon = s.Icon, effect = s.ClientEffect, text = s.Description,
            group = s.Group, harmful = s.IsHarmful,
        };
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&classguide", ePrivLevel.GM, "Write every playable class's specs, styles, spells and abilities to class-guide.json (ClassGuide)", "/classguide")]
    public class ClassGuideCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            try
            {
                client.Out.SendMessage("Class guide written: " + ClassGuide.Write(), eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            catch (Exception e)
            {
                client.Out.SendMessage("Class guide failed: " + e.Message, eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
        }
    }
}
