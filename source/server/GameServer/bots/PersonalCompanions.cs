using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.Keeps;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;

namespace DOL.GS
{
    /// <summary>
    /// Your companion (owner 2026-11-11: "a real bot that feels like a roleplaying player"). One a character: at level 7
    /// a quest sends you to someone in your starting town (companion.json), where you choose its sex, class and race; it
    /// gets a name of its realm, and from then on it is at your side at your level - a member of your group in full (it
    /// takes its share of a kill's experience), with its own death rules (GameBot.IsPersonalCompanion: it releases at
    /// once when nobody in the group can raise it, after a minute when someone could but doesn't, and walks back from its
    /// bind stone) and its own small talk (chatty, normal or quiet).
    ///   Call Companion (/companion call): brings it to you at once, alive - from anywhere, from death, from home.
    ///   Send Companion Home (/companion home): it leaves until you call it; it stays home across log-ins.
    ///   /companion talk chatty|normal|quiet, /companion rename &lt;name&gt; (at a Name Registrar).
    /// What it is lives in DOLCharactersXCustomParam "companion": "class|race|gender|name|talk|home".
    /// </summary>
    public static class PersonalCompanions
    {
        static readonly Logging.Logger log = Logging.LoggerManager.Create(typeof(PersonalCompanions));
        public const string ParamKey = "companion";
        public const int QuestLevel = 7;
        const long CALL_REUSE_MS = 10_000;

        public sealed class Record
        {
            public eCharacterClass Class;
            public eRace Race;
            public eGender Gender;
            public string Name = "";
            public string Talk = "normal";
            public bool Home;

            public string Format() => $"{(int) Class}|{(int) Race}|{(int) Gender}|{Name}|{Talk}|{(Home ? 1 : 0)}";

            public static Record Parse(string v)
            {
                string[] p = (v ?? "").Split('|');
                if (p.Length < 4 || !int.TryParse(p[0], out int c) || !int.TryParse(p[1], out int r) || !int.TryParse(p[2], out int g) ||
                    string.IsNullOrWhiteSpace(p[3]))
                    return null;
                return new Record
                {
                    Class = (eCharacterClass) c, Race = (eRace) r, Gender = (eGender) g, Name = p[3],
                    Talk = p.Length > 4 && p[4] is "chatty" or "normal" or "quiet" ? p[4] : "normal",
                    Home = p.Length > 5 && p[5] == "1",
                };
            }
        }

        static readonly ConcurrentDictionary<GamePlayer, GameBot> _active = new();
        static readonly ConcurrentDictionary<string, Record> _records = new();      // character id -> (cached)
        static readonly ConcurrentDictionary<GamePlayer, long> _calledAt = new();
        static readonly ConcurrentDictionary<GamePlayer, long> _spokeAt = new();

        public static string QuestId(eRealm realm) => realm switch
        {
            eRealm.Albion => "companion_alb", eRealm.Midgard => "companion_mid", eRealm.Hibernia => "companion_hib", _ => null,
        };

        // ---------------------------------------------------------------- start-up and the player's comings and goings

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(OnEntered));
            GameEventMgr.AddHandler(GamePlayerEvent.LevelUp, new DOLEventHandler(OnLevelUp));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler(OnQuit));
            StoryQuestManager.ChoiceMade += OnChoice;
            StoryQuestManager.Finished += OnQuestFinished;
            _ = new ECSGameTimer(null, Tick, 5000);
        }

        static void OnEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            _records.TryRemove(p.ObjectId, out _);
            // a moment for the world to settle around them (story people, the group)
            new ECSGameTimer(p, _ =>
            {
                if (p.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                Record r = Load(p);
                SendState(p, r);
                if (r == null)
                    OfferQuest(p);
                else if (!r.Home)
                    Spawn(p, r, false);
                return 0;
            }, 4000);
        }

        static void OnLevelUp(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            if (Load(p) == null)
                OfferQuest(p);
            else if (Of(p) is GameBot bot && bot.IsAlive)
                bot.Say(Pick(LevelLines, p, bot).Replace("{level}", p.Level.ToString()));
            // (its own level follows in the tick, out of a fight)
        }

        static void OnQuit(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            _active.TryRemove(p, out _);              // (a helper leaves with its owner: GameBot.OnOwnerQuit)
            _calledAt.TryRemove(p, out _);
            _spokeAt.TryRemove(p, out _);
            _records.TryRemove(p.ObjectId, out _);
        }

        /// <summary>Level 7 and no companion: the quest to find one starts (and the map shows where).</summary>
        static void OfferQuest(GamePlayer p)
        {
            if (p.Level < QuestLevel || QuestId(p.Realm) is not string id || StoryQuestManager.Doing(p, id) != null ||
                StoryQuestManager.Done(p, id))
                return;
            if (StoryQuestManager.StartFor(p, id) != null)
                p.Out.SendMessage("You have heard that someone in town is looking for a companion for you.",
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        // ---------------------------------------------------------------- the record

        public static Record Load(GamePlayer p)
        {
            if (p == null)
                return null;
            if (_records.TryGetValue(p.ObjectId, out Record cached))
                return cached;
            DbCoreCharacterXCustomParam row = Row(p);
            Record r = row == null ? null : Record.Parse(row.Value);
            if (r != null)
                _records[p.ObjectId] = r;
            return r;
        }

        static DbCoreCharacterXCustomParam Row(GamePlayer p) => DOLDB<DbCoreCharacterXCustomParam>.SelectObject(
            DB.Column("DOLCharactersObjectId").IsEqualTo(p.ObjectId).And(DB.Column("KeyName").IsEqualTo(ParamKey)));

        public static void Save(GamePlayer p, Record r)
        {
            _records[p.ObjectId] = r;
            DbCoreCharacterXCustomParam row = Row(p);
            if (row == null)
                GameServer.Database.AddObject(new DbCoreCharacterXCustomParam(p.ObjectId, ParamKey, r.Format()));
            else
            {
                row.Value = r.Format();
                GameServer.Database.SaveObject(row);
            }
        }

        /// <summary>The client's companion abilities (Call / Send Home) show while you have one: "#COMPANION|name".</summary>
        static void SendState(GamePlayer p, Record r) => NewClient.Send(p, "#COMPANION|" + (r?.Name ?? ""));

        public static GameBot Of(GamePlayer p) =>
            p != null && _active.TryGetValue(p, out GameBot b) && b.ObjectState == GameObject.eObjectState.Active ? b : null;

        public static bool IsCompanionOf(GamePlayer p, GameObject o) => o != null && Of(p) == o;

        // ---------------------------------------------------------------- the quest's answers

        static void OnChoice(GamePlayer p, StoryQuest s, StepDef st, OptionDef o)
        {
            if (!s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase) || string.Equals(o.Keyword, "back", StringComparison.OrdinalIgnoreCase))
                return;
            if (st.Id == "sex")
                s.SetCustomProperty("c_sex", o.Keyword.Equals("woman", StringComparison.OrdinalIgnoreCase) ? "2" : "1");
            else if (st.Id == "class" && Enum.TryParse(o.Keyword, true, out eCharacterClass c))
                s.SetCustomProperty("c_class", ((int) c).ToString());
            else if (st.Id.StartsWith("race_") && Enum.TryParse(o.Keyword, true, out eRace r))
                s.SetCustomProperty("c_race", ((int) r).ToString());
            s.SaveIntoDatabase();
        }

        static void OnQuestFinished(GamePlayer p, StoryQuest s, string ending)
        {
            if (!s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase))
                return;
            if (!int.TryParse(s.GetCustomProperty("c_class"), out int c) || !int.TryParse(s.GetCustomProperty("c_race"), out int r))
            {
                log.Warn($"Companion: {p.Name} finished {s.QuestId} without a class and race");
                return;
            }
            eGender g = s.GetCustomProperty("c_sex") == "2" ? eGender.Female : eGender.Male;
            Make(p, (eCharacterClass) c, (eRace) r, g);
        }

        /// <summary>A new companion: its name, the record, and at your side.</summary>
        public static GameBot Make(GamePlayer p, eCharacterClass c, eRace r, eGender g)
        {
            if (!AutonomousBotIdentityGenerator.IsClassAvailable(c) ||
                !AutonomousBotIdentityGenerator.GetEligibleRaces(c).Contains(r))
            {
                p.Out.SendMessage($"A {r} {c} can't be your companion.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return null;
            }
            var taken = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { p.Name };
            string name = null;
            for (int i = 0; i < 20 && name == null; i++)
            {
                string n = AutonomousBotIdentityGenerator.GenerateForClass(p.Realm, g, c, taken).Name;
                if (!NameInUse(n))
                    name = n;
            }
            name ??= AutonomousBotIdentityGenerator.GenerateForClass(p.Realm, g, c, taken).Name;
            var rec = new Record { Class = c, Race = r, Gender = g, Name = name };
            Save(p, rec);
            SendState(p, rec);
            GameBot bot = Spawn(p, rec, false);
            if (bot != null)
            {
                bot.TurnTo(p);
                bot.Say(Pick(HelloLines, p, bot));
                p.Out.SendMessage($"{name} is your companion now. Call Companion brings {(g == eGender.Female ? "her" : "him")} to you; " +
                    "Send Companion Home sends them off until you call. (/companion for the rest.)",
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
            return bot;
        }

        static bool NameInUse(string name) =>
            DOLDB<DbCoreCharacter>.SelectObject(DB.Column("Name").IsEqualTo(name)) != null ||
            ClientService.Instance.GetPlayers().Any(x => string.Equals(x.Name, name, StringComparison.OrdinalIgnoreCase)) ||
            _active.Values.Any(b => string.Equals(b.Name, name, StringComparison.OrdinalIgnoreCase));

        // ---------------------------------------------------------------- at your side

        /// <summary>The companion beside you (a fresh one at your level); null when it can't come (a full group ...).</summary>
        static GameBot Spawn(GamePlayer p, Record r, bool loud)
        {
            if (Of(p) is GameBot old)
            {
                _active.TryRemove(p, out _);
                old.Delete();
            }
            if (p.Group != null && p.Group.MemberCount >= p.Group.MaximumMemberCount)
            {
                p.Out.SendMessage($"Your group is full - {r.Name} can't join it.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return null;
            }
            if (p.CurrentRegion == null || p.CurrentZone == null)
                return null;
            GameBot bot;
            try
            {
                bot = new GameBot(p, (byte) r.Class, r.Name, (byte) r.Race, (byte) r.Gender, temporaryGroupHelper: true,
                    equipmentLevel: p.Level, botLevel: p.Level) { IsPersonalCompanion = true };
            }
            catch (Exception ex)
            {
                log.Error($"Companion: {p.Name}'s {r.Class} {r.Name}", ex);
                p.Out.SendMessage($"{r.Name} couldn't come: {ex.Message}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return null;
            }
            Vector3 at = Beside(p);
            bot.X = (int) Math.Round(at.X);
            bot.Y = (int) Math.Round(at.Y);
            bot.Z = (int) Math.Round(at.Z);
            bot.Heading = p.Heading;
            bot.CurrentRegionID = p.CurrentRegionID;
            if (!bot.AddToWorld())
            {
                bot.Delete();
                return null;
            }
            if (p.Group == null)
            {
                var group = new Group(p);
                GroupMgr.AddGroup(group);
                group.AddMember(p);
            }
            if (!p.Group.AddMember(bot))
            {
                bot.Delete();
                p.Out.SendMessage($"{r.Name} couldn't join your group.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return null;
            }
            bot.EnterPlayerLedGroup(p);
            bot.Follow(p, BotManager.FOLLOW_DISTANCE, BotManager.MAX_FOLLOW_DISTANCE);
            if (bot.Brain is BotBrain brain)
                brain.FSM.SetCurrentState(eFSMStateType.FOLLOW);
            _active[p] = bot;
            if (r.Home)
            {
                r.Home = false;
                Save(p, r);
            }
            if (loud)
                bot.Say(Pick(CalledLines, p, bot));
            return bot;
        }

        static Vector3 Beside(GamePlayer p)
        {
            double angle = p.Heading * Math.PI * 2 / 4096 + Math.PI * (Random.Shared.Next(2) == 0 ? 0.6 : -0.6);
            Vector3 current = new(p.X, p.Y, p.Z);
            Vector3 desired = new(p.X - (float) (Math.Sin(angle) * 140), p.Y + (float) (Math.Cos(angle) * 140), p.Z);
            return PathfindingProvider.Instance.GetMoveAlongSurface(p.CurrentZone, current, desired,
                PathfindingProvider.Instance.DefaultFilters) ?? current;
        }

        /// <summary>Call Companion: at your side now - alive, rested, from wherever it was (or home, or dead); not in combat.</summary>
        public static string Call(GamePlayer p)
        {
            Record r = Load(p);
            if (r == null)
                return p.Level < QuestLevel ? $"You have no companion yet (at level {QuestLevel} someone in town can help)." : "You have no companion yet - see the companion quest in your journal.";
            if (!p.IsAlive)
                return "You can't call anyone while you're dead.";
            // (owner 2026-11-12: calling back a dead companion mid-fight would be a free resurrection - not in combat)
            if (p.InCombat)
                return "You can't call your companion while you're in combat.";
            long now = GameLoop.GameLoopTime;
            if (_calledAt.TryGetValue(p, out long at) && now - at < CALL_REUSE_MS)
                return $"You must wait {(CALL_REUSE_MS - (now - at)) / 1000 + 1} seconds to call again.";
            _calledAt[p] = now;
            if (Of(p) is GameBot bot && bot.IsAlive && bot.CurrentRegionID == p.CurrentRegionID && bot.Group == p.Group && p.Group != null)
            {
                Vector3 to = Beside(p);
                bot.StopCurrentSpellcast();
                bot.StopMoving();
                bot.MoveTo(p.CurrentRegionID, (int) to.X, (int) to.Y, (int) to.Z, p.Heading);
                bot.EnterPlayerLedGroup(p);
                bot.Follow(p, BotManager.FOLLOW_DISTANCE, BotManager.MAX_FOLLOW_DISTANCE);
                if (bot.Brain is BotBrain brain)
                    brain.FSM.SetCurrentState(eFSMStateType.FOLLOW);
                bot.Say(Pick(CalledLines, p, bot));
                return null;
            }
            return Spawn(p, r, true) != null ? null : $"{r.Name} couldn't come.";
        }

        /// <summary>Send Companion Home: gone until called (and stays gone across log-ins).</summary>
        public static string Home(GamePlayer p)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            GameBot bot = Of(p);
            if (bot == null && r.Home)
                return $"{r.Name} is already at home.";
            if (bot != null)
            {
                if (bot.IsAlive)
                    bot.Say(Pick(HomeLines, p, bot));
                _active.TryRemove(p, out _);
                bot.Delete();
            }
            r.Home = true;
            Save(p, r);
            return $"{r.Name} heads home. Call Companion brings {(r.Gender == eGender.Female ? "her" : "him")} back.";
        }

        // ---------------------------------------------------------------- every few seconds: its level, its talk

        static int Tick(ECSGameTimer timer)
        {
            try
            {
                long now = GameLoop.GameLoopTime;
                foreach (var (p, bot) in _active.ToArray())
                {
                    if (p.ObjectState != GameObject.eObjectState.Active || bot.ObjectState != GameObject.eObjectState.Active)
                    {
                        _active.TryRemove(p, out _);      // (kicked, the group disbanded, logged out)
                        continue;
                    }
                    Record r = Load(p);
                    if (r == null)
                        continue;
                    // your level, out of a fight: a fresh one where it stands
                    if (bot.Level != p.Level && bot.IsAlive && !bot.InCombat && !p.InCombat && !bot.IsReturningAfterRelease &&
                        bot.CurrentRegionID == p.CurrentRegionID)
                    {
                        Spawn(p, r, false);
                        continue;
                    }
                    Chatter(p, bot, r, now);
                }
            }
            catch (Exception ex)
            {
                log.Error("Companion: tick", ex);
            }
            return 5000;
        }

        static void Chatter(GamePlayer p, GameBot bot, Record r, long now)
        {
            if (r.Talk == "quiet" || !bot.IsAlive || bot.InCombat || p.InCombat || bot.IsCasting || !bot.IsWithinRadius(p, 1500))
                return;
            long every = r.Talk == "chatty" ? 90_000 : 240_000;
            long last = _spokeAt.GetOrAdd(p, now);
            if (now - last < every / 3 || Random.Shared.NextDouble() > 5000.0 / every)
                return;
            string line = Remark(p, bot);
            if (string.IsNullOrEmpty(line))
                return;
            _spokeAt[p] = now;
            bot.Say(line);
        }

        static string Remark(GamePlayer p, GameBot bot)
        {
            var kinds = new List<Func<string>> { () => Pick(ZoneLines, p, bot), () => Pick(IdleLines, p, bot) };
            GameNPC mob = bot.GetNPCsInRadius(2000).OfType<GameNPC>()
                .FirstOrDefault(n => n.IsAlive && n.Realm == eRealm.None && n is not GameBot && (n.Flags & GameNPC.eFlags.PEACE) == 0 && !string.IsNullOrEmpty(n.Name));
            if (mob != null)
                kinds.Add(() => Pick(MobLines, p, bot).Replace("{mob}", mob.Name));
            StoryQuest q = StoryQuestManager.Active(p).FirstOrDefault(s => !s.QuestId.StartsWith("companion_"));
            if (q != null)
                kinds.Add(() => Pick(QuestLines, p, bot).Replace("{quest}", q.Def.Title));
            if (RvrNews(p.Realm) is string news)
                kinds.Add(() => news);
            return kinds[Random.Shared.Next(kinds.Count)]();
        }

        /// <summary>The frontier's word: who holds which keep (a keep of another realm's).</summary>
        static string RvrNews(eRealm mine)
        {
            try
            {
                var keeps = GameServer.KeepManager?.GetFrontierKeeps()?.Where(k => k != null && k.Realm != eRealm.None).ToList();
                if (keeps == null || keeps.Count == 0)
                    return null;
                int ours = keeps.Count(k => k.Realm == mine);
                var lost = keeps.Where(k => k.Realm != mine && k.OriginalRealm == mine).ToList();
                if (lost.Count > 0 && Random.Shared.Next(2) == 0)
                {
                    AbstractGameKeep k = lost[Random.Shared.Next(lost.Count)];
                    return Random.Shared.Next(2) == 0
                        ? $"Word from the frontier: {k.Name} flies {GlobalConstants.RealmToName(k.Realm)}'s banner now. Someone ought to do something about that."
                        : $"They say {GlobalConstants.RealmToName(k.Realm)} took {k.Name}. I'd like to be there when we take it back.";
                }
                return ours >= keeps.Count / 3
                    ? $"The frontier news is good - {GlobalConstants.RealmToName(mine)} holds {ours} keeps out there."
                    : $"Only {ours} keeps on the frontier are ours just now. The realm could use us out there, one day.";
            }
            catch
            {
                return null;
            }
        }

        static string Pick(string[] lines, GamePlayer p, GameBot bot) =>
            lines[Random.Shared.Next(lines.Length)].Replace("{player}", p.Name).Replace("{zone}", bot.CurrentZone?.Description ?? "these lands")
                .Replace("{me}", bot.Name);

        static readonly string[] HelloLines =
        [
            "{me}. Well met, {player} - lead on, and I'll be right behind you.",
            "So you're {player}. {me}, at your service. I've been waiting for someone worth following.",
            "{me}, and glad of the company. Where are we headed first, {player}?",
        ];
        static readonly string[] CalledLines =
        [
            "Here, {player}. What do you need?",
            "I came as fast as I could. What did I miss?",
            "Right beside you. Let's go.",
            "You called? Good - I was getting bored.",
        ];
        static readonly string[] HomeLines =
        [
            "Home it is. Call when you need me, {player}.",
            "I'll be at home with my boots off. Don't forget about me.",
            "Fair enough. Mind yourself out here without me.",
        ];
        static readonly string[] LevelLines =
        [
            "Level {level}! I can feel it too - we're getting stronger together.",
            "Look at you, {player}. Level {level}. The bards will hear of this yet.",
            "{level} seasons' worth of lessons, and every one of them earned. Well done.",
        ];
        static readonly string[] ZoneLines =
        [
            "{zone}. I never get tired of the light here.",
            "Keep an eye on the treeline - {zone} has a way of hiding things.",
            "I passed through {zone} as a child once. It looked bigger then.",
            "Smell that? Rain's coming to {zone}, mark my words.",
            "If I ever settle down, it'll be somewhere like {zone}. Quieter, maybe.",
            "Every road in {zone} seems to lead somewhere worth seeing.",
        ];
        static readonly string[] MobLines =
        [
            "That {mob} over there has been watching us. Say the word and it's dealt with.",
            "Mind the {mob}. They don't look like much until they're on you.",
            "Another {mob}. This land is crawling with them.",
            "I fought a {mob} once, before we met. I still have the scar.",
        ];
        static readonly string[] QuestLines =
        [
            "I keep thinking about {quest}. We should see it through.",
            "{quest} - do you think we'll get there in time?",
            "Whatever comes of {quest}, I'm glad I'm in it with you.",
        ];
        static readonly string[] IdleLines =
        [
            "Let's take a breather when this is done. My feet are killing me.",
            "Do you ever wonder what the bards will sing about us, {player}?",
            "I sharpened everything I own last night. Twice.",
            "Remind me to buy a better pair of boots next time we're in town.",
            "I'm glad it was you who came looking, {player}.",
        ];

        // ---------------------------------------------------------------- talk, rename

        /// <summary>GM testing: no companion, no record, the quest forgotten (it starts again at the next log-in).</summary>
        public static string Forget(GamePlayer p)
        {
            if (Of(p) is GameBot bot)
            {
                _active.TryRemove(p, out _);
                bot.Delete();
            }
            if (Row(p) is DbCoreCharacterXCustomParam row)
                GameServer.Database.DeleteObject(row);
            _records.TryRemove(p.ObjectId, out _);
            SendState(p, null);
            StoryQuestManager.Command(p, new[] { "storyquest", "reset", QuestId(p.Realm) ?? "" });
            return "Companion forgotten.";
        }

        public static string SetTalk(GamePlayer p, string how)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            how = (how ?? "").ToLowerInvariant();
            if (how is not ("chatty" or "normal" or "quiet"))
                return $"{r.Name} is {r.Talk}. /companion talk chatty | normal | quiet";
            r.Talk = how;
            Save(p, r);
            if (Of(p) is GameBot bot && bot.IsAlive)
                bot.Say(how switch
                {
                    "chatty" => "Oh, I've got plenty to say. You'll see.",
                    "quiet" => "I'll keep my thoughts to myself, then.",
                    _ => "As you like.",
                });
            return null;
        }

        public static string Rename(GamePlayer p, string name)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            if (p.TargetObject is not NameRegistrar reg || !p.IsWithinRadius(reg, 500))
                return "A Name Registrar in your capital records a companion's new name: target one and /companion rename <name>.";
            name = (name ?? "").Trim();
            if (name.Length < 3 || name.Length > 12 || !name.All(char.IsLetter))
                return "A name is 3 to 12 letters.";
            name = char.ToUpperInvariant(name[0]) + name[1..].ToLowerInvariant();
            if (string.Equals(name, r.Name, StringComparison.OrdinalIgnoreCase))
                return $"Your companion is already {name}.";
            if (NameInUse(name))
                return $"Someone is already called {name}.";
            string was = r.Name;
            r.Name = name;
            Save(p, r);
            SendState(p, r);
            if (Of(p) is GameBot bot)
                Spawn(p, r, false)?.Say($"{name}. I like the sound of that.");
            reg.SayTo(p, eChatLoc.CL_SystemWindow, $"It is written: {was} is known from this day as {name}.");
            return null;
        }
    }

    /// <summary>/companion: your companion - call, home, talk, rename (the client's abilities use the first two).</summary>
    [CmdAttribute("&companion", ePrivLevel.Player, "Your companion: call, send home, how much they talk, a new name",
        "/companion [call | home | talk chatty|normal|quiet | rename <name>]")]
    public class CompanionCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null)
                return;
            string what = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            string said = what switch
            {
                "call" => PersonalCompanions.Call(p),
                "home" => PersonalCompanions.Home(p),
                "talk" => PersonalCompanions.SetTalk(p, args.Length > 2 ? args[2] : ""),
                "rename" => PersonalCompanions.Rename(p, args.Length > 2 ? args[2] : ""),
                "forget" when client.Account.PrivLevel > (uint) ePrivLevel.Player => PersonalCompanions.Forget(p),
                _ => Status(p),
            };
            if (!string.IsNullOrEmpty(said))
                ChatUtil.SendSystemMessage(p, said);
        }

        static string Status(GamePlayer p)
        {
            PersonalCompanions.Record r = PersonalCompanions.Load(p);
            if (r == null)
                return p.Level < PersonalCompanions.QuestLevel
                    ? $"At level {PersonalCompanions.QuestLevel} someone in your starting town can find you a companion."
                    : "You have no companion yet - see the companion quest in your journal.";
            string where = PersonalCompanions.Of(p) is GameBot b ? (b.IsAlive ? "with you" : "dead") : r.Home ? "at home" : "away";
            return $"{r.Name}, {r.Race} {r.Class} ({where}; talks: {r.Talk}). /companion call | home | talk chatty|normal|quiet | rename <name> (at a Name Registrar)";
        }
    }
}
