using System;
using System.Linq;
using DOL.GS.PacketHandler;
using DOL.GS.Reputation;

namespace DOL.GS.Commands
{
    [Cmd("&rep", new[] { "&reputation" }, ePrivLevel.Player,
        "Your reputation with each faction and your realm, and your titles",
        "/rep - your standing (and the Reputation window)",
        "/rep title <number|auto> - wear one of your titles everywhere, or by where you are",
        "GM: /rep add <faction|realm> <points> [bot name] - /rep set <faction|realm> <points> - /rep reset - /rep near [points] - /rep qm [faction] - /rep bot <name>")]
    public class ReputationCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            bool gm = client.Account.PrivLevel > (uint) ePrivLevel.Player;
            switch (sub)
            {
                case "":
                    Summary(p, p);
                    ReputationService.SendWindow(p);
                    return;
                case "window":
                    ReputationService.SendWindow(p);
                    return;
                case "title":
                    Say(p, ReputationService.LockTitle(p, args.Length > 2 ? string.Join(" ", args.Skip(2)) : "auto"));
                    ReputationService.SendWindow(p);
                    return;
                case "add" or "set" when gm && args.Length > 3 && double.TryParse(args[3], out double pts):
                {
                    GameLiving who = args.Length > 4 && AutonomousBotRegistry.TryGetByName(string.Join(" ", args.Skip(4)), out GameBot bot) ? bot : p;
                    var s = ReputationService.Of(who);
                    if (s == null)
                        return;
                    string key = args[2];
                    if (key == "realm")
                    {
                        double have = s.Rvr;
                        ReputationService.GainRealm(who, sub == "set" ? Math.Max(0, pts - have) : pts, "GM", rated: false);
                    }
                    else if (RepDefs.Faction(key) is RepFactionDef f)
                    {
                        if (sub == "set")
                        {
                            lock (s.Sync)
                            {
                                s.Points[f.Key] = 0;
                                s.Dirty = true;
                            }
                        }
                        ReputationService.Gain(who, f, pts, "GM", quiet: false, rated: false);   // (a GM's number is the number)
                    }
                    else
                    {
                        Say(p, "No faction " + key + ". Factions: " + string.Join(", ", RepDefs.Zones.SelectMany(z => z.Factions).Select(f => f.Key)) + ", realm");
                        return;
                    }
                    Summary(p, who);
                    ReputationService.Push(p);
                    return;
                }
                case "reset" when gm:
                {
                    var s = ReputationService.Of(p);
                    lock (s.Sync)
                    {
                        s.Points.Clear();
                        s.Rvr = 0;
                        s.Lock = null;
                        s.Dirty = true;
                    }
                    ReputationService.Save(p);
                    ReputationService.Push(p);
                    Say(p, "Your reputation is reset.");
                    return;
                }
                case "near" when gm:
                {
                    // testing: the autonomous bots near you get standing (Honoured with this zone's first faction, or the
                    // points given) - their titles and their talk then show
                    RepZoneDef z = RepDefs.ForZone(p.CurrentZone);
                    if (z == null)
                    {
                        Say(p, "No factions in this zone.");
                        return;
                    }
                    double give = args.Length > 2 && double.TryParse(args[2], out double g) ? g : ReputationService.Thresholds[(int) Rank.Honoured];
                    var near = p.GetNPCsInRadius(2500).OfType<GameBot>().Where(b => b.IsAutonomousWorldBot && b.IsAlive && b.Realm == p.Realm).Take(4).ToList();
                    if (near.Count == 0)
                    {
                        // none here: go to the nearest bot of your realm in this region, and take the ones there
                        GameBot to = AutonomousBotRegistry.Snapshot()
                            .Where(b => b != null && b.IsAlive && b.Realm == p.Realm && b.CurrentRegionID == p.CurrentRegionID && b.ObjectState == GameObject.eObjectState.Active)
                            .OrderBy(b => p.GetDistanceTo(b)).FirstOrDefault();
                        if (to != null)
                        {
                            p.MoveTo(to.CurrentRegionID, to.X + 80, to.Y + 80, to.Z, p.Heading);
                            Say(p, $"Moved to {to.Name}.");
                            near = AutonomousBotRegistry.Snapshot()
                                .Where(b => b != null && b.IsAlive && b.Realm == p.Realm && b.CurrentRegionID == to.CurrentRegionID && to.GetDistanceTo(b) < 2500)
                                .Take(4).ToList();
                        }
                    }
                    foreach (GameBot nb in near)
                    {
                        var s = ReputationService.Of(nb);
                        double have = s.Get(z.Factions[0].Key);
                        ReputationService.Gain(nb, z.Factions[0], Math.Max(0, give - have), null, quiet: true, rated: false);
                    }
                    GameBot[] all = AutonomousBotRegistry.Snapshot();
                    Say(p, near.Count == 0 ? $"No bots near (online {all.Length}, your realm {all.Count(b => b?.Realm == p.Realm)}, this region {all.Count(b => b?.Realm == p.Realm && b.CurrentRegionID == p.CurrentRegionID)})." :"Given standing: " + string.Join(", ", near.Select(b => $"{b.Name} ({ReputationService.TitleFor(b)})")));
                    return;
                }
                case "qm" when gm:
                {
                    // testing: go to a faction's quartermaster (this zone's first faction, or the one named)
                    RepFactionDef f = args.Length > 2 ? RepDefs.Faction(args[2]) : RepDefs.ForZone(p.CurrentZone)?.Factions.FirstOrDefault();
                    GameNPC qm = f == null ? null : ReputationQuartermaster.Of(f);
                    if (qm == null)
                    {
                        Say(p, "That quartermaster isn't standing yet.");
                        return;
                    }
                    p.MoveTo(qm.CurrentRegionID, qm.X + 60, qm.Y + 60, qm.Z, p.Heading);
                    Say(p, $"Moved to {qm.Name}.");
                    return;
                }
                case "bot" when gm && args.Length > 2:
                    if (AutonomousBotRegistry.TryGetByName(string.Join(" ", args.Skip(2)), out GameBot b))
                        Summary(p, b);
                    else
                        Say(p, "No such bot online.");
                    return;
                default:
                    DisplaySyntax(client);
                    return;
            }
        }

        static void Say(GamePlayer p, string text) => p.Out.SendMessage(text, eChatType.CT_System, eChatLoc.CL_SystemWindow);

        static void Summary(GamePlayer to, GameLiving who)
        {
            var realm = RepDefs.Realm(who.Realm);
            double rp = ReputationService.RealmPoints(who);
            Rank rr = ReputationService.RealmRankOf(rp);
            Say(to, $"{(to == who ? "Your" : who.Name + "'s")} reputation - {realm?.Name ?? "Realm"}: {rr} ({rp:N0} / " +
                $"{ReputationService.RealmThresholds[Math.Min((int) rr + 1, 4)]:N0}).");
            foreach (RepZoneDef z in RepDefs.Zones.Where(z => z.Realm == (int) who.Realm))
                Say(to, $"  {z.Name}: " + string.Join(", ", z.Factions.Select(f =>
                {
                    double pts = ReputationService.Points(who, f);
                    Rank r = ReputationService.RankOf(pts);
                    return $"{f.Short} {r} ({pts:N0} / {ReputationService.Thresholds[Math.Min((int) r + 1, 4)]:N0})";
                })));
            var titles = ReputationService.TitlesEarned(who);
            if (titles.Count > 0)
                Say(to, "  Titles: " + string.Join(", ", titles.Select((t, i) => $"{i + 1}. {t.Title}")) +
                    $". Wearing: {ReputationService.TitleFor(who)}" + (to == who ? " (/rep title <number|auto>)" : ""));
        }
    }
}
