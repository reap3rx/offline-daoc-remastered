using System.Collections.Generic;
using DOL.AI.Brain;

namespace DOL.GS.Commands
{
    /// <summary>
    /// The interact menu (owner 2026-11-11: "hold the interact button ... it will bring up a small menu that has ways you
    /// can interact with that person"): what you can do with your target - a bot or player, your pet, or yourself. The
    /// client asks with the object's id when you hold Interact on it; the answer is one line, #SMENU|title|label=action|...
    /// where an action is a slash command, "@pet:order" (your pet's window) or "@whisper:Name" (the chat line).
    ///   /socialmenu [objectId]
    /// </summary>
    [CmdAttribute("&socialmenu", ePrivLevel.Player, "What you can do with your target (the controller's hold-Interact menu)", "/socialmenu [objectId]")]
    public class SocialMenuCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer me = client?.Player;
            if (me == null)
                return;
            GameObject target = me.TargetObject;
            if (args.Length > 1 && ushort.TryParse(args[1], out ushort oid) && oid != 0)
            {
                GameObject picked = WorldMgr.GetObjectByIDFromRegion(me.CurrentRegionID, oid);
                if (picked != null && me.IsWithinRadius(picked, 2500))
                {
                    target = picked;
                    if (me.TargetObject != picked)
                    {
                        me.TargetObject = picked;
                        client.Out.SendChangeTarget(picked);
                    }
                }
            }
            target ??= me;
            List<(string Label, string Action)> entries = Entries(me, target, out string title);
            if (entries.Count == 0)
            {
                ChatUtil.SendSystemMessage(me, $"There is nothing to do with {target.GetName(0, false)}.");
                return;
            }
            var line = new System.Text.StringBuilder("#SMENU|").Append(Clean(title));
            foreach (var (label, action) in entries)
                line.Append('|').Append(Clean(label)).Append('=').Append(Clean(action));
            NewClient.Send(me, line.ToString());
        }

        private static string Clean(string s) => s.Replace("|", "/").Replace("=", "-");

        public static List<(string, string)> Entries(GamePlayer me, GameObject target, out string title)
        {
            var list = new List<(string, string)>();
            title = target.Name;
            Group group = me.Group;
            bool leader = group != null && group.Leader == me;

            if (target == me)
            {
                title = "Yourself";
                list.Add(("Buff Yourself", "/buff"));
                if (group != null)
                    list.Add(("Leave Group", "/disband"));
                return list;
            }

            if (target is not GameBot && target is GameNPC npc && npc.Brain is IControlledBrain brain && brain.GetPlayerOwner() == me)
            {
                title = $"{npc.Name} (your pet)";
                list.Add(("Attack My Target", "@pet:attack"));
                list.Add(("Follow Me", "@pet:follow"));
                list.Add(("Stay Here", "@pet:stay"));
                list.Add(("Aggressive", "@pet:aggressive"));
                list.Add(("Defensive", "@pet:defensive"));
                list.Add(("Passive", "@pet:passive"));
                list.Add(("Buff", "/buff"));
                list.Add(("Dismiss", "@pet:release"));
                return list;
            }

            // a bot (a GameNPC that plays) or a player of your realm; monsters, merchants, the other realms: nothing here
            if (target is not (GameBot or GamePlayer) || target is not GameLiving other || other.Realm != me.Realm)
                return list;

            bool sameGroup = group != null && other.Group == group;
            if (!sameGroup && (group == null || leader))
                list.Add(("Invite to Group", "/invite " + other.Name));
            if (sameGroup && leader)
            {
                list.Add(("Kick from Group", "/disband " + other.Name));
                list.Add(("Make Leader", "/makeleader " + other.Name));
            }
            if (sameGroup && !leader)
                list.Add(("Leave Group", "/disband"));
            list.Add(("Buff", "/buff"));
            list.Add(("Follow", "/follow"));
            list.Add(("Assist", "/assist"));
            list.Add(("Whisper", "@whisper:" + other.Name));
            if (other is GamePlayer real && real.Client != null && real.Client != me.Client)
                list.Add(("Trade", "/tradewith"));
            return list;
        }
    }

    /// <summary>Open a trade window with your target (a real player - the bots don't trade).</summary>
    [CmdAttribute("&tradewith", ePrivLevel.Player, "Open a trade with your target", "/tradewith")]
    public class TradeWithCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer me = client?.Player;
            if (me?.TargetObject is not GamePlayer other || other == me || other.Client == null)
            {
                if (me != null)
                    ChatUtil.SendSystemMessage(me, "You can only trade with another player.");
                return;
            }
            if (!me.IsWithinRadius(other, 512))
            {
                ChatUtil.SendSystemMessage(me, $"{other.Name} is too far away to trade.");
                return;
            }
            if (!me.OpenTrade(other))
                ChatUtil.SendSystemMessage(me, $"{other.Name} is busy trading.");
        }
    }
}
