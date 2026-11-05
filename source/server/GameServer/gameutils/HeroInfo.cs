using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.Database;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.GS.Styles;

namespace DOL.GS
{
    /// <summary>
    /// What the new client's modern Hero panel needs from the server (owner 2026-11-03, "a GW2 inspired character
    /// panel"; docs/MODERN_UI.md):
    ///   - the spellbook as a roadmap: every ability, style and spell each of your specializations will teach, with the
    ///     level that teaches it and whether you have it now (the trainer window's own lists leave out the baseline
    ///     spell lines and stop at its packet size). "/book" answers in "#BOOK|" system lines:
    ///       #BOOK|begin|specPoints
    ///       #BOOK|spec|index|level|name           (index = the trainable spec's place, as PlayerTrainHandler counts)
    ///       #BOOK|sk|index|level|kind|icon|have|group|name   (kind a / s / p / g: ability, style, spell, song;
    ///                                                         level: the spec level - or for a baseline line your
    ///                                                         character level - that teaches it)
    ///       #BOOK|end
    ///   - the level you fight at (LevelScaling): "#ELV|level" when it changes - your level against your target when
    ///     you are scaled down to it, else your own. Checked once a second.
    /// </summary>
    public static class HeroInfo
    {
        public const string BookPrefix = "#BOOK|";
        public const string LevelPrefix = "#ELV|";
        private static readonly ConcurrentDictionary<string, int> _sentLevel = new();

        public static void SendBook(GamePlayer p)
        {
            if (p?.Out == null)
                return;
            p.Out.SendMessage($"{BookPrefix}begin|{p.SkillSpecialtyPoints}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            var specs = p.GetSpecList().Where(s => s.Trainable).ToList();
            for (int i = 0; i < specs.Count; i++)
            {
                Specialization spec = specs[i];
                int lv = spec.GetSpecLevelForLiving(p);
                p.Out.SendMessage($"{BookPrefix}spec|{i}|{lv}|{Clean(spec.Name)}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                var rows = new List<(int level, string kind, int icon, bool have, string group, string name)>();
                try
                {
                    foreach (Ability ab in spec.PretendAbilitiesForLiving(p, GamePlayer.MAX_LEVEL))
                        rows.Add((ab.SpecLevelRequirement, "a", ab.Icon, ab.SpecLevelRequirement <= lv, "ABILITIES", ab.Name));
                    foreach (Style st in spec.PretendStylesForLiving(p, GamePlayer.MAX_LEVEL))
                        rows.Add((st.SpecLevelRequirement, "s", st.Icon, st.SpecLevelRequirement <= lv, "STYLES", st.Name));
                    // the spell lines as you have them now (baseline lines go by your level, spec lines by the spec's):
                    // every spell in each, learned up to the line's level
                    foreach (SpellLine line in spec.GetSpellLinesForLiving(p))
                    {
                        int have = line.Level;
                        foreach (Spell sp in SkillBase.GetSpellList(line.KeyName).OrderBy(s => s.Level).ThenBy(s => s.ID))
                        {
                            string kind = sp is Song || sp.NeedInstrument ? "g" : "p";
                            rows.Add((sp.Level, kind, sp.Icon, sp.Level <= have, line.Name + (line.IsBaseLine ? " (BASE)" : ""), sp.Name));
                        }
                    }
                }
                catch (Exception)
                {
                    // a spec that can't list itself just shows what it could
                }
                foreach (var r in rows.OrderBy(r => r.group == "ABILITIES" ? 0 : r.group == "STYLES" ? 1 : 2).ThenBy(r => r.group).ThenBy(r => r.level))
                    p.Out.SendMessage($"{BookPrefix}sk|{i}|{r.level}|{r.kind}|{r.icon}|{(r.have ? 1 : 0)}|{Clean(r.group)}|{Clean(r.name)}",
                        eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            p.Out.SendMessage($"{BookPrefix}end", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        private static string Clean(string s) => (s ?? "").Replace("|", "/");

        /// <summary>The level you fight your target at (your own when you aren't scaled to it).</summary>
        public static int FightingLevel(GamePlayer p)
        {
            if (p.TargetObject is GameLiving t && t.IsAlive)
            {
                int gap = LevelScaling.Gap(p, t);
                if (gap > 0)
                    return p.Level - gap;
            }
            return p.Level;
        }

        private static void Tick(GamePlayer p)
        {
            PetTick(p);
            int lv = FightingLevel(p);
            if (_sentLevel.TryGetValue(p.ObjectId, out int was) && was == lv)
                return;
            _sentLevel[p.ObjectId] = lv;
            p.Out?.SendMessage($"{LevelPrefix}{lv}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        /// <summary>The modern pet window's retinue (owner 2026-11-04): a commander's sub-pets - a King's retainers, a
        /// Bonedancer's minions - as "#PET|oid,role,health %,name|..." ("#PET|" for none) when it changes. Role: melee,
        /// healer, caster, debuffer, archer, buffer; health -1 while it lies dead.</summary>
        public const string PetPrefix = "#PET|";
        private static readonly ConcurrentDictionary<string, string> _sentPets = new();

        private static void PetTick(GamePlayer p)
        {
            var sb = new System.Text.StringBuilder();
            try
            {
                GameNPC cmd = p.ControlledBrain?.Body;
                if (cmd?.ControlledNpcList != null)
                {
                    foreach (var b in cmd.ControlledNpcList)
                    {
                        if (b?.Body is not GameNPC sub || sub.ObjectState != GameObject.eObjectState.Active)
                            continue;
                        string role = b switch
                        {
                            DOL.AI.Brain.BdHealerBrain => "healer",
                            DOL.AI.Brain.BdCasterBrain => "caster",
                            DOL.AI.Brain.BdDebufferBrain => "debuffer",
                            DOL.AI.Brain.BdArcherBrain => "archer",
                            DOL.AI.Brain.BdBufferBrain => "buffer",
                            _ => "melee",
                        };
                        sb.Append('|').Append(sub.ObjectID).Append(',').Append(role).Append(',')
                          .Append(sub.IsAlive ? sub.HealthPercent : -1).Append(',').Append(Clean(sub.Name));
                    }
                }
            }
            catch (Exception)
            {
                return;                                             // (a list changing under us: next second)
            }
            string line = PetPrefix + (sb.Length > 0 ? sb.ToString(1, sb.Length - 1) : "");
            if (_sentPets.TryGetValue(p.ObjectId, out string was) && was == line)
                return;
            _sentPets[p.ObjectId] = line;
            p.Out?.SendMessage(line, eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(PlayerEntered));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler(PlayerQuit));
        }

        [GameServerStoppedEvent]
        public static void OnServerStopped(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.RemoveHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(PlayerEntered));
            GameEventMgr.RemoveHandler(GamePlayerEvent.Quit, new DOLEventHandler(PlayerQuit));
        }

        // ---------------------------------------------------------------- the client's per-character settings
        // (owner 2026-11-03: the action camera "as portable as possible, so probably server side"): small strings the
        // new client keeps on the character - "/clientcfg set key value" stores one (DOLCharactersXCustomParam
        // "cfg:key"), and each comes back at login as "#CFG|key|value". The client owns what they mean.
        public const string CfgPrefix = "#CFG|";
        private const string CfgKey = "cfg:";

        public static bool ValidKey(string k) => !string.IsNullOrEmpty(k) && k.Length <= 24 && k.All(c => char.IsLetterOrDigit(c) || c == '_');

        public static void StoreConfig(GamePlayer p, string key, string value)
        {
            if (p == null || !ValidKey(key) || value == null || value.Length > 400)
                return;
            try
            {
                var rec = DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
                    DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId).And(DB.Column("KeyName").IsEqualTo(CfgKey + key)));
                if (rec == null)
                    GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(p.ObjectId, CfgKey + key, value));
                else if (rec.Value != value)
                {
                    rec.Value = value;
                    GameServer.Database.SaveObject(rec);
                }
            }
            catch (Exception)
            {
                // best effort: the client keeps its own copy too
            }
        }

        public static void SendConfigs(GamePlayer p)
        {
            try
            {
                var recs = DOLDB<DbCoreCharacterXCustomParam>.SelectObjects(DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId));
                foreach (var r in recs.Where(r => r.KeyName != null && r.KeyName.StartsWith(CfgKey)))
                    p.Out.SendMessage($"{CfgPrefix}{r.KeyName.Substring(CfgKey.Length)}|{r.Value}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
            }
            catch (Exception)
            {
            }
        }

        private static void PlayerEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            SendConfigs(p);
            _sentLevel.TryRemove(p.ObjectId, out _);
            _sentPets.TryRemove(p.ObjectId, out _);
            new ECSGameTimer(p, _ =>
            {
                if (p.ObjectState == GameObject.eObjectState.Deleted || p.Client == null || p.Client.Player != p)
                    return 0;
                Tick(p);
                return 1000;
            }, 1000);
        }

        private static void PlayerQuit(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is GamePlayer p)
            {
                _sentLevel.TryRemove(p.ObjectId, out _);
                _sentPets.TryRemove(p.ObjectId, out _);
            }
        }
    }
}

namespace DOL.GS.Commands
{
    [Cmd("&book", ePrivLevel.Player, "Your spellbook: everything your specializations teach, and when", "/book")]
    public class BookCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            HeroInfo.SendBook(client?.Player);
        }
    }
}

namespace DOL.GS.Commands
{
    [Cmd("&clientcfg", ePrivLevel.Player, "The new client's settings kept on your character", "/clientcfg set <key> <value>")]
    public class ClientCfgCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null || args.Length < 4 || args[1] != "set")
                return;
            HeroInfo.StoreConfig(p, args[2], string.Join(" ", args.Skip(3)));
        }
    }
}
