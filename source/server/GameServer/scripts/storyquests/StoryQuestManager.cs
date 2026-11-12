using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Reflection;
using System.Text;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.Commands;
using DOL.GS.DynamicEvents;
using DOL.GS.PacketHandler;
using Newtonsoft.Json;

namespace DOL.GS.StoryQuests
{
    /// <summary>
    /// Story quests: the files, their people, and every player's progress (README.md). Once a second it looks at each
    /// player with a story quest: a place reached, monsters to spawn for a kill step, an encounter to start (a dynamic-event
    /// chain of their own, ChainRuntime with Allow = them and their group), the map marker of the step. Their people are
    /// StoryNpcs: a click talks (the step's words, or the quest's offer), a [keyword] answers.
    /// </summary>
    public static class StoryQuestManager
    {
        static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);
        public const uint MarkerBase = 0xFFFF0000;

        static readonly Dictionary<string, StoryQuestDef> _quests = new(StringComparer.OrdinalIgnoreCase);
        static readonly Dictionary<string, StoryNpcDef> _npcDefs = new(StringComparer.OrdinalIgnoreCase);
        static readonly ConcurrentDictionary<string, StoryNpc> _npcs = new(StringComparer.OrdinalIgnoreCase);
        static readonly ConcurrentDictionary<string, long> _npcWanted = new(StringComparer.OrdinalIgnoreCase);   // a During npc: last wanted at
        static readonly ConcurrentDictionary<string, List<StoryMob>> _mobs = new();     // "<player>|<quest>|<step>" -> its monsters
        static readonly ConcurrentDictionary<string, ChainRuntime> _encounters = new(); // the same key -> its chain
        static readonly ConcurrentDictionary<string, long> _encounterRetry = new();
        static readonly ConcurrentDictionary<GamePlayer, string> _markers = new();
        static readonly object _lock = new();

        public static IEnumerable<StoryQuestDef> Quests => _quests.Values;
        /// <summary>An answer picked on a choice step (before the quest moves on): the companion quest records them.</summary>
        public static event Action<GamePlayer, StoryQuest, StepDef, OptionDef> ChoiceMade;
        /// <summary>A quest finished (its ending's id) - after its rewards.</summary>
        public static event Action<GamePlayer, StoryQuest, string> Finished;
        public static StoryQuestDef Quest(string id) => id != null && _quests.TryGetValue(id, out var q) ? q : null;
        static long Now => Environment.TickCount64;   // (the dynamic events' clock: encounters share it)

        // ---------------------------------------------------------------- start-up

        [GameServerStartedEvent]
        public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
        {
            Load();
            GameEventMgr.AddHandler(GameLivingEvent.Dying, new DOLEventHandler(OnDying));
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler(OnQuit));
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, new DOLEventHandler(OnEntered));
            _ = new ECSGameTimer(null, Tick, 5000);
        }

        public static void Load()
        {
            var files = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            Assembly asm = typeof(StoryQuestManager).Assembly;
            foreach (string res in asm.GetManifestResourceNames().Where(n => n.StartsWith("StoryQuests.") && n.EndsWith(".json")))
            {
                using var s = new StreamReader(asm.GetManifestResourceStream(res)!, Encoding.UTF8);
                files[res["StoryQuests.".Length..]] = s.ReadToEnd();
            }
            string dir = Path.Combine(GameServer.Instance.Configuration.RootDirectory, "story-quests");
            if (Directory.Exists(dir))
                foreach (string f in Directory.GetFiles(dir, "*.json"))
                    files[Path.GetFileName(f)] = File.ReadAllText(f, Encoding.UTF8);
            _quests.Clear();
            _npcDefs.Clear();
            foreach (var (name, json) in files.OrderBy(kv => kv.Key))
            {
                try
                {
                    var file = JsonConvert.DeserializeObject<StoryFileDef>(json);
                    if (file == null)
                        continue;
                    file.Name ??= name;
                    foreach (StoryNpcDef n in file.Npcs)
                        _npcDefs[n.Id] = n;
                    foreach (StoryQuestDef q in file.Quests)
                    {
                        q.File = file;
                        if (q.MinLevel <= 0)
                            q.MinLevel = Math.Max(1, q.Level - 3);
                        _quests[q.Id] = q;
                    }
                }
                catch (Exception ex)
                {
                    log.Error($"Story quests: can't read {name}", ex);
                }
            }
            log.Info($"Story quests: {_quests.Count} quests, {_npcDefs.Count} people in {files.Count} files");
            foreach (StoryNpcDef d in _npcDefs.Values.Where(d => d.During.Count == 0))
                Spawn(d);
        }

        // ---------------------------------------------------------------- people

        static Zone ZoneOf(int zone) => WorldMgr.GetZone((ushort) zone);

        /// <summary>Zone metres to region units (z from the place, else the zone's ground).</summary>
        public static Vector3 ToWorld(int zoneId, double[] p)
        {
            Zone z = ZoneOf(zoneId);
            if (z == null || p == null || p.Length < 2)
                return Vector3.Zero;
            var v = new Vector3((float) (z.XOffset + p[0] * 40), (float) (z.YOffset + p[1] * 40), p.Length > 2 ? (float) (p[2] * 40) : 0f);
            var nav = PathfindingProvider.Instance;
            if (nav != null && nav.IsAvailable && nav.HasNavmesh(z))
            {
                Vector3? floor = nav.GetClosestPoint(z, v, 96, 96, 2048, nav.DefaultFilters);
                if (floor.HasValue)
                    return floor.Value;
            }
            return v;
        }

        static StoryNpc Spawn(StoryNpcDef d)
        {
            Zone z = ZoneOf(d.Zone);
            if (z == null || d.Pos == null)
            {
                log.Warn($"Story quests: {d.Id} has no place (zone {d.Zone})");
                return null;
            }
            Vector3 at = ToWorld(d.Zone, d.Pos);
            var npc = new StoryNpc { Def = d };
            if (d.Template > 0 && NpcTemplateMgr.GetTemplate(d.Template) is NpcTemplate tpl)
                npc.LoadTemplate(tpl);
            npc.Name = d.Name ?? npc.Name;
            npc.GuildName = d.Guild ?? "";
            npc.Level = (byte) Math.Clamp(d.Level > 0 ? d.Level : 20, 1, 255);
            if (d.Model > 0) npc.Model = d.Model;
            if (d.Size > 0) npc.Size = d.Size;
            if (!string.IsNullOrEmpty(d.Equipment))
                npc.LoadEquipmentTemplateFromDatabase(d.Equipment);
            npc.X = (int) at.X;
            npc.Y = (int) at.Y;
            npc.Z = (int) at.Z;
            npc.Heading = d.Pos.Length > 3 ? (ushort) d.Pos[3] : (ushort) 0;
            npc.CurrentRegion = z.ZoneRegion;
            npc.RespawnInterval = -1;
            npc.RoamingRange = 0;
            npc.LoadedFromScript = true;
            if (d.Hostile)
            {
                npc.Realm = eRealm.None;
                npc.SetOwnBrain(new StandardMobBrain { AggroLevel = 100, AggroRange = 500 });
            }
            else
            {
                npc.Realm = d.Realm is >= 1 and <= 3 ? (eRealm) d.Realm : RealmOf(z.ZoneRegion.ID);
                npc.Flags |= GameNPC.eFlags.PEACE;
                npc.SetOwnBrain(new BlankBrain());
            }
            if (!npc.AddToWorld())
                return null;
            npc.Health = npc.MaxHealth;
            _npcs[d.Id] = npc;
            return npc;
        }

        static eRealm RealmOf(ushort region) =>
            region >= 200 && region < 300 ? eRealm.Hibernia : region >= 100 && region < 200 ? eRealm.Midgard : eRealm.Albion;

        public static StoryNpc Npc(string id) => id != null && _npcs.TryGetValue(id, out var n) && n.ObjectState == GameObject.eObjectState.Active ? n : null;

        // ---------------------------------------------------------------- who can take what

        public static bool CanTake(GamePlayer p, StoryQuestDef q)
        {
            if (p == null || q == null || p.Level < q.MinLevel)
                return false;
            if (q.Classes.Count > 0 && !q.Classes.Contains(p.CharacterClass.ID))
                return false;
            StoryNpcDef giver = q.Giver != null && _npcDefs.TryGetValue(q.Giver, out var g) ? g : null;
            int realm = q.Realm > 0 ? q.Realm : giver?.Realm > 0 ? giver.Realm : giver != null && ZoneOf(giver.Zone) is Zone z ? (int) RealmOf(z.ZoneRegion.ID) : 0;
            if (realm > 0 && (int) p.Realm != realm)
                return false;
            if (!string.IsNullOrEmpty(q.Requires) && !Done(p, q.Requires))
                return false;
            return !Done(p, q.Id) && Doing(p, q.Id) == null;
        }

        public static bool Done(GamePlayer p, string id) =>
            p.GetFinishedQuests().OfType<StoryQuest>().Any(s => string.Equals(s.QuestId, id, StringComparison.OrdinalIgnoreCase));

        public static StoryQuest Doing(GamePlayer p, string id) =>
            p.QuestList.Keys.OfType<StoryQuest>().FirstOrDefault(s => string.Equals(s.QuestId, id, StringComparison.OrdinalIgnoreCase) && s.Step > 0);

        public static IEnumerable<StoryQuest> Active(GamePlayer p) => p.QuestList.Keys.OfType<StoryQuest>().Where(s => s.Step > 0 && s.Def != null);

        public static eQuestIndicator Indicator(GamePlayer p, StoryNpc npc)
        {
            if (p == null || npc?.Def == null)
                return eQuestIndicator.None;
            foreach (StoryQuest s in Active(p))
                if (s.Step_ is StepDef st && st.Type is "talk" or "choice" && Same(st.Npc, npc.Def.Id))
                    return eQuestIndicator.Finish;
            if (_quests.Values.Any(q => Same(q.Giver, npc.Def.Id) && CanTake(p, q)))
                return eQuestIndicator.Available;
            if (Active(p).Any(s => Same(s.Def.Giver, npc.Def.Id)))
                return eQuestIndicator.Pending;
            return eQuestIndicator.None;
        }

        static bool Same(string a, string b) => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);

        static void RefreshIndicators(GamePlayer p)
        {
            foreach (StoryNpc n in _npcs.Values)
                if (n.ObjectState == GameObject.eObjectState.Active && n.CurrentRegion == p.CurrentRegion && n.IsWithinRadius(p, 6000))
                    p.Out.SendNPCsQuestEffect(n, n.GetQuestIndicator(p));
        }

        // ---------------------------------------------------------------- talking

        public static void OnInteract(GamePlayer p, StoryNpc npc)
        {
            // a step here: its words (a talk step without a keyword is done by the click)
            foreach (StoryQuest s in Active(p).ToList())
            {
                if (!string.IsNullOrEmpty(s.Choosing) && Same(s.Step_?.Npc, npc.Def.Id))
                {
                    OfferChoice(p, npc, s, s.Choosing);
                    return;
                }
                StepDef st = s.Step_;
                if (st == null || st.Type is not ("talk" or "choice") || !Same(st.Npc, npc.Def.Id))
                    continue;
                StoryDialog.Say(p, npc, Words(st.Say, p), st.Type == "choice" ? "choice" : "talk", null, s);
                if (st.Type == "talk" && string.IsNullOrEmpty(st.Keyword))
                    StepDone(p, s);
                return;
            }
            // a quest to give
            StoryQuestDef offer = _quests.Values.FirstOrDefault(q => Same(q.Giver, npc.Def.Id) && CanTake(p, q));
            if (offer != null)
            {
                StoryDialog.Say(p, npc, Words(offer.Offer, p) + (offer.Group ? "\n\n(This is a task for a group - you may want help with it.)" : ""),
                    "offer", offer);
                return;
            }
            // one under way that they gave
            StoryQuest mine = Active(p).FirstOrDefault(s => Same(s.Def.Giver, npc.Def.Id));
            if (mine?.Step_ != null)
            {
                StoryDialog.Say(p, npc, $"{mine.Step_.Goal}. I'm counting on you.", "talk", null, mine);
                return;
            }
            if (!string.IsNullOrEmpty(npc.Def.Idle))
                StoryDialog.Say(p, npc, Words(npc.Def.Idle, p), "idle");
        }

        public static void OnWhisper(GamePlayer p, StoryNpc npc, string text)
        {
            text = (text ?? "").Trim();
            foreach (StoryQuest s in Active(p).ToList())
            {
                StepDef st = s.Step_;
                if (st == null || !Same(st.Npc, npc.Def.Id))
                    continue;
                if (!string.IsNullOrEmpty(s.Choosing))
                {
                    string pick = Choices(s, s.Choosing).FirstOrDefault(t => Same(t.Name, text))?.Id_nb;
                    if (pick != null)
                        s.Complete(s.Choosing, pick);
                    else
                        OfferChoice(p, npc, s, s.Choosing);
                    RefreshIndicators(p);
                    return;
                }
                if (st.Type == "talk" && Same(st.Keyword, text))
                {
                    StepDone(p, s);
                    return;
                }
                if (st.Type == "choice")
                {
                    OptionDef o = st.Options.FirstOrDefault(x => Same(x.Keyword, text));
                    if (o == null)
                        continue;
                    try { ChoiceMade?.Invoke(p, s, st, o); }
                    catch (Exception ex) { log.Error($"Story quests: {s.QuestId} choice {o.Keyword}", ex); }
                    if (!string.IsNullOrEmpty(o.Say))
                        StoryDialog.Say(p, npc, Words(o.Say, p), "talk", null, s);
                    Advance(p, s, o.Next, o.Ending);
                    return;
                }
            }
            foreach (StoryQuestDef q in _quests.Values.Where(q => Same(q.Giver, npc.Def.Id) && CanTake(p, q)))
            {
                if (Same(q.Accept, text))
                {
                    var sq = new StoryQuest(p, q);
                    if (!p.AddQuest(sq))
                        return;
                    sq.QuestGiver = npc;
                    sq.RebuildGoals();
                    p.Out.SendQuestUpdate(sq);
                    StoryDialog.Log(p, sq);
                    RefreshIndicators(p);
                    StepEntered(p, sq);
                    return;
                }
                if (q.Topics.FirstOrDefault(kv => Same(kv.Key, text)) is var t && t.Value != null)
                {
                    StoryDialog.Say(p, npc, Words(t.Value, p), "topic", q);
                    return;
                }
            }
        }

        static string Words(string s, GamePlayer p) =>
            (s ?? "").Replace("{name}", p.Name).Replace("{class}", p.CharacterClass.Name).Replace("{race}", p.RaceName);

        // ---------------------------------------------------------------- steps

        static void StepDone(GamePlayer p, StoryQuest s)
        {
            StepDef st = s.Step_;
            if (st == null)
                return;
            if (!string.IsNullOrEmpty(st.Text) && st.Type is not ("talk" or "choice"))
                p.Out.SendMessage(Words(st.Text, p), eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            Advance(p, s, st.Next, st.Ending);
        }

        static void Advance(GamePlayer p, StoryQuest s, string next, string ending)
        {
            StepDef st = s.Step_;
            if (st?.Give != null)
            {
                if (!string.IsNullOrEmpty(st.Give.Id) && GameServer.Database.FindObjectByKey<DbItemTemplate>(st.Give.Id) is DbItemTemplate tpl)
                {
                    if (!p.Inventory.AddTemplate(GameInventoryItem.Create(tpl), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                        p.CreateItemOnTheGround(GameInventoryItem.Create(tpl));
                }
                else if (!string.IsNullOrEmpty(st.Give.Name))
                    s.GiveStoryItem(st.Give.Name);
                p.Out.SendMessage($"You receive {st.Give.Name}.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
            }
            if (!string.IsNullOrEmpty(st?.Take))
                s.TakeStoryItem(st.Take);
            ClearStepWorld(p, s);
            if (!string.IsNullOrEmpty(ending))
            {
                Finish(p, s, ending);
                return;
            }
            if (string.IsNullOrEmpty(next))
            {
                int i = s.Def.Steps.FindIndex(x => x.Id == s.StepId);
                next = i >= 0 && i + 1 < s.Def.Steps.Count ? s.Def.Steps[i + 1].Id : null;
            }
            if (next == null)
            {
                Finish(p, s, "default");
                return;
            }
            s.SetStep(next);
            p.Out.SendMessage($"{s.Name}: {s.Step_?.Goal}", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            StoryDialog.Log(p, s);
            RefreshIndicators(p);
            StepEntered(p, s);
        }

        /// <summary>A step begun: a talk step whose npc isn't there yet comes; the marker moves.</summary>
        static void StepEntered(GamePlayer p, StoryQuest s)
        {
            _markers.TryRemove(p, out _);
            Look(p, s);
        }

        static void Finish(GamePlayer p, StoryQuest s, string ending)
        {
            EndingDef e = ending != null && s.Def.Endings.TryGetValue(ending, out var ed) ? ed : null;
            RewardsDef r = e?.Rewards ?? s.Def.Rewards;
            if (r != null && r.Choice.Count > 1 && Npc(s.Step_?.Npc) is StoryNpc npc)
            {
                s.SetChoosing(ending);
                s.RebuildGoals();
                p.Out.SendQuestUpdate(s);
                OfferChoice(p, npc, s, ending, Words(e?.Text, p));
                return;
            }
            if (!string.IsNullOrEmpty(e?.Text))
            {
                if (Npc(s.Step_?.Npc) is StoryNpc by)
                    StoryDialog.Say(p, by, Words(e.Text, p), "end", null, s, ending);
                else
                    p.Out.SendMessage(Words(e.Text, p), eChatType.CT_Important, eChatLoc.CL_SystemWindow);
            }
            s.Complete(ending, null);
            RefreshIndicators(p);
            ClearMarker(p);
            try { Finished?.Invoke(p, s, ending); }
            catch (Exception ex) { log.Error($"Story quests: {s.QuestId} finished", ex); }
        }

        /// <summary>Hand a quest to someone without its giver's offer (the companion quest at level 7): its first step
        /// begins and the map points the way. Null when they can't take it.</summary>
        public static StoryQuest StartFor(GamePlayer p, string id)
        {
            if (Quest(id) is not StoryQuestDef q || !CanTake(p, q))
                return null;
            var sq = new StoryQuest(p, q);
            if (!p.AddQuest(sq))
                return null;
            sq.QuestGiver = Npc(q.Giver);
            sq.RebuildGoals();
            p.Out.SendQuestUpdate(sq);
            StoryDialog.Log(p, sq);
            RefreshIndicators(p);
            StepEntered(p, sq);
            return sq;
        }

        static List<DbItemTemplate> Choices(StoryQuest s, string ending)
        {
            EndingDef e = ending != null && s.Def.Endings.TryGetValue(ending, out var ed) ? ed : null;
            RewardsDef r = e?.Rewards ?? s.Def.Rewards;
            var l = new List<DbItemTemplate>();
            foreach (string id in r?.Choice ?? new List<string>())
                if (StageRuntime.ItemAtLevel(id, s.QuestPlayer.Level) is DbItemTemplate t)
                    l.Add(t);
            return l;
        }

        static void OfferChoice(GamePlayer p, StoryNpc npc, StoryQuest s, string ending, string said = null)
        {
            var names = Choices(s, ending).Select(t => $"[{t.Name}]");
            string pick = "Take what will serve you best: " + string.Join(", ", names) + ".";
            StoryDialog.Say(p, npc, string.IsNullOrEmpty(said) ? pick : said + "\n\n" + pick, "reward", null, s, ending);
        }

        // ---------------------------------------------------------------- rewards

        public static void Reward(GamePlayer p, StoryQuest s, string ending, string chosen)
        {
            EndingDef e = ending != null && s.Def?.Endings != null && s.Def.Endings.TryGetValue(ending, out var ed) ? ed : null;
            RewardsDef r = e?.Rewards ?? s.Def?.Rewards;
            p.Out.SendMessage($"{s.Name} - {(e?.Tragic == true ? "a sad end" : "complete")}.", eChatType.CT_ScreenCenter, eChatLoc.CL_SystemWindow);
            if (r == null)
                return;
            int lvl = p.Level;
            // a share of a level at the quest's level (yours while you're below it): well past it, a tenth
            int at = Math.Min(lvl, (s.Def?.Level ?? lvl) + 2);
            long levelXp = at < 50 ? GamePlayer.GetExperienceAmountForLevel(at) - GamePlayer.GetExperienceAmountForLevel(at - 1) : 0;
            int over = lvl - (s.Def?.Level ?? lvl);
            double past = over <= 2 ? 1.0 : Math.Max(0.1, 1.0 - 0.15 * (over - 2));   // well past it: down to a tenth
            long xp = (long) (Math.Max(0, levelXp) * r.XpPct / 100.0 * past);
            if (xp > 0 && lvl < 50)
                p.GainExperience(eXPSource.Quest, xp, false);
            long copper = (long) r.CopperPerLevel * lvl;
            if (copper > 0)
            {
                p.AddMoney(copper, "You are rewarded {0}.");
                LootFeed.Money(p, copper);
            }
            if (r.Marks > 0 && GameServer.Database.FindObjectByKey<DbItemTemplate>(EventTokenMerchant.MarkId) is DbItemTemplate mark &&
                p.Inventory.AddTemplate(GameInventoryItem.Create(mark), r.Marks, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
            {
                p.Out.SendMessage($"You receive {r.Marks} {mark.Name}{(r.Marks > 1 ? "s" : "")}.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                LootFeed.Item(p, mark, r.Marks);
            }
            var give = r.Items.ToList();
            if (!string.IsNullOrEmpty(chosen))
                give.Add(chosen);
            else if (r.Choice.Count == 1)
                give.Add(r.Choice[0]);                      // (one to choose from is no choice)
            foreach (string id in give)
            {
                if (StageRuntime.ItemAtLevel(id, lvl) is not DbItemTemplate tpl)
                {
                    log.Warn($"Story quests: {s.QuestId} reward {id} doesn't exist");
                    continue;
                }
                tpl = SpecialLoot.Enrich(tpl, p, s.Def?.Title ?? "a story");
                DbInventoryItem item = GameInventoryItem.Create(tpl);
                if (!p.Inventory.AddTemplate(item, 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                    p.CreateItemOnTheGround(item);
                p.Out.SendMessage($"You receive {tpl.Name}!", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                LootFeed.Item(p, tpl, 1);
            }
        }

        // ---------------------------------------------------------------- once a second

        static int Tick(ECSGameTimer timer)
        {
            try
            {
                long now = Now;
                var wanted = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                {
                    if (p.ObjectState != GameObject.eObjectState.Active || p.CurrentRegion == null)
                        continue;
                    Barks(p, now);
                    foreach (StoryQuest s in Active(p).ToList())
                    {
                        string here = s.QuestId + "/" + s.StepId;
                        foreach (StoryNpcDef d in _npcDefs.Values.Where(d => d.During.Any(x => Same(x, here))))
                            wanted.Add(d.Id);
                        Look(p, s);
                    }
                }
                // the people who are there only for a step: come, and go a while after nobody needs them
                foreach (string id in wanted)
                {
                    _npcWanted[id] = now;
                    if (Npc(id) == null && _npcDefs.TryGetValue(id, out var d))
                        Spawn(d);
                }
                foreach (var (id, npc) in _npcs.ToArray())
                    if (npc.Def.During.Count > 0 && (!_npcWanted.TryGetValue(id, out long at) || now - at > 120_000))
                    {
                        if (npc.ObjectState == GameObject.eObjectState.Active && !npc.InCombat)
                            npc.RemoveFromWorld();
                        _npcs.TryRemove(id, out _);
                    }
                foreach (var (key, chain) in _encounters.ToArray())
                {
                    chain.Tick(now);
                    // its people all gone (logged out, far away): it ends quietly
                    if (!chain.PlayersInZone().Any())
                        chain.End("fail", now);
                }
            }
            catch (Exception ex)
            {
                log.Error("Story quests: tick", ex);
            }
            return 1000;
        }

        static string Key(GamePlayer p, StoryQuest s) => $"{p.ObjectId}|{s.QuestId}|{s.StepId}";

        /// <summary>One quest's step for one player: arrived? spawn? start? and the marker.</summary>
        static void Look(GamePlayer p, StoryQuest s)
        {
            StepDef st = s.Step_;
            if (st == null || !string.IsNullOrEmpty(s.Choosing))
                return;
            Zone z = st.At != null ? ZoneOf(st.Zone) : null;
            Vector3 at = z != null ? ToWorld(st.Zone, st.At) : Vector3.Zero;
            bool sameRegion = z != null && z.ZoneRegion == p.CurrentRegion;
            double dist = sameRegion ? Vector3.Distance(new Vector3(p.X, p.Y, at.Z), new Vector3(at.X, at.Y, at.Z)) / 40.0 : double.MaxValue;
            switch (st.Type)
            {
                case "reach":
                    if (dist <= st.Radius)
                        StepDone(p, s);
                    break;
                case "search":
                    if (dist <= 150)
                        EnsureClue(p, s, st, at);
                    break;
                case "kill":
                    if (st.Mob != null && dist <= 120)
                        EnsureMobs(p, s, st, at);
                    break;
                case "encounter":
                    if (dist <= st.WakeM)
                        StartEncounter(p, s, st, z);
                    break;
            }
            Marker(p, s, st, z, at);
        }

        // ---------------------------------------------------------------- the map marker

        static void Marker(GamePlayer p, StoryQuest s, StepDef st, Zone z, Vector3 at)
        {
            ushort region = 0;
            int x = 0, y = 0, zz = 0;
            if (st.Type is "talk" or "choice" && Npc(st.Npc) is StoryNpc n)
            {
                region = n.CurrentRegionID; x = n.X; y = n.Y; zz = n.Z;
            }
            else if (z != null)
            {
                region = z.ZoneRegion.ID; x = (int) at.X; y = (int) at.Y; zz = (int) at.Z;
            }
            if (region == 0)
                return;
            string sig = $"{s.QuestId}|{s.StepId}|{region}|{x / 200}|{y / 200}";
            if (_markers.TryGetValue(p, out string was) && was == sig)
                return;
            _markers[p] = sig;
            p.Out.SendMinotaurRelicMapUpdate(MarkerBase, region, x, y, zz);
        }

        static void ClearMarker(GamePlayer p)
        {
            _markers.TryRemove(p, out _);
            p.Out.SendMinotaurRelicMapRemove(MarkerBase);
            if (Active(p).FirstOrDefault() is StoryQuest other)
                Look(p, other);
        }

        // ---------------------------------------------------------------- search: a thing to click

        static readonly ConcurrentDictionary<string, StoryClue> _clues = new();

        static void EnsureClue(GamePlayer p, StoryQuest s, StepDef st, Vector3 at)
        {
            string key = Key(p, s);
            if (_clues.TryGetValue(key, out StoryClue c) && c.ObjectState == GameObject.eObjectState.Active)
                return;
            c = new StoryClue
            {
                Owner = p, QuestId = s.QuestId, StepId = s.StepId,
                Name = st.Clue?.Name ?? "something half-hidden",
                Model = st.Clue?.Model > 0 ? st.Clue.Model : (ushort) 1574,
                X = (int) at.X, Y = (int) at.Y, Z = (int) at.Z, Heading = 0,
                CurrentRegion = ZoneOf(st.Zone).ZoneRegion,
            };
            if (c.AddToWorld())
                _clues[key] = c;
        }

        public static void OnClue(GamePlayer p, StoryClue c)
        {
            StoryQuest s = Doing(p, c.QuestId);
            if (s == null || s.StepId != c.StepId)
            {
                p.Out.SendMessage("There is nothing more to find here.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            if (!p.IsWithinRadius(c, 400))
            {
                p.Out.SendMessage("You need to be closer to search that.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            StepDone(p, s);
        }

        // ---------------------------------------------------------------- kill: monsters of your own

        static void EnsureMobs(GamePlayer p, StoryQuest s, StepDef st, Vector3 at)
        {
            string key = Key(p, s);
            var list = _mobs.GetOrAdd(key, _ => new List<StoryMob>());
            lock (list)
            {
                list.RemoveAll(m => m.ObjectState != GameObject.eObjectState.Active || !m.IsAlive);
                int left = Math.Max(0, st.Count - s.Count);
                int want = Math.Min(left, Math.Min(4, Crowd(p, st.Count)));
                Zone z = ZoneOf(st.Zone);
                while (list.Count < want)
                {
                    StoryMob m = MakeMob(st.Mob, z, at, st.Radius, s.Def);
                    if (m == null)
                        break;
                    m.QuestKey = key;
                    list.Add(m);
                }
            }
        }

        /// <summary>A group quest grows with the group as events do: +15% a person, at most double.</summary>
        static int Crowd(GamePlayer p, int n)
        {
            int people = p.Group?.MemberCount ?? 1;
            return (int) Math.Ceiling(n * Math.Min(2.0, 1.0 + 0.15 * Math.Max(0, people - 1)));
        }

        static StoryMob MakeMob(NpcDef d, Zone z, Vector3 c, double radiusM, StoryQuestDef q)
        {
            if (d == null || z == null)
                return null;
            double a = Util.RandomDouble() * Math.PI * 2, r = Math.Sqrt(Util.RandomDouble()) * radiusM * 40;
            var m = new StoryMob();
            if (d.Template > 0 && NpcTemplateMgr.GetTemplate(d.Template) is NpcTemplate tpl)
                m.LoadTemplate(tpl);
            if (!string.IsNullOrEmpty(d.Name)) m.Name = d.Name;
            m.GuildName = d.Guild ?? q.Title;
            m.Level = (byte) Math.Clamp(d.Level > 0 ? d.Level : q.Level, 1, 255);
            if (d.Model > 0) m.Model = d.Model;
            if (d.Size > 0) m.Size = d.Size;
            if (!string.IsNullOrEmpty(d.Equipment))
                m.LoadEquipmentTemplateFromDatabase(d.Equipment);
            m.X = (int) (c.X + Math.Cos(a) * r);
            m.Y = (int) (c.Y + Math.Sin(a) * r);
            m.Z = (int) c.Z;
            m.Heading = (ushort) Util.Random(4095);
            m.CurrentRegion = z.ZoneRegion;
            m.Realm = eRealm.None;
            m.RespawnInterval = -1;
            m.RoamingRange = 0;
            m.LoadedFromScript = true;
            m.SetOwnBrain(new StandardMobBrain { AggroLevel = 100, AggroRange = 450 });
            if (!m.AddToWorld())
                return null;
            m.HealthMult = Math.Max(1, d.HealthMult);
            m.Health = m.MaxHealth;
            return m;
        }

        static void OnDying(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GameNPC dead)
                return;
            try
            {
                var credited = new HashSet<GamePlayer>();
                lock (dead.XpGainersLock)
                {
                    foreach (GameLiving g in dead.XPGainers.Keys)
                    {
                        GamePlayer gp = g as GamePlayer;
                        if (gp == null && g is GameNPC pet && pet.Brain is IControlledBrain cb)
                            gp = cb.GetPlayerOwner();
                        if (gp != null)
                            credited.Add(gp);
                        if (g is GameBot bot && bot.Group != null)
                            foreach (GamePlayer m in bot.Group.GetPlayersInTheGroup())
                                credited.Add(m);
                    }
                }
                foreach (GamePlayer p in credited.ToList())
                    if (p.Group != null)
                        foreach (GamePlayer m in p.Group.GetPlayersInTheGroup())
                            if (m.IsWithinRadius(dead, 5000))
                                credited.Add(m);
                foreach (GamePlayer p in credited)
                    foreach (StoryQuest s in Active(p).ToList())
                    {
                        StepDef st = s.Step_;
                        if (st?.Type != "kill")
                            continue;
                        bool match = (st.Mob != null && Same(st.Mob.Name, dead.Name)) || (!string.IsNullOrEmpty(st.Target) && Same(st.Target, dead.Name));
                        if (!match || (st.Zone > 0 && dead.CurrentZone?.ID != st.Zone && st.Mob == null))
                            continue;
                        int n = s.Count + 1;
                        if (n >= st.Count)
                            StepDone(p, s);
                        else
                        {
                            s.SetCount(n);
                            p.Out.SendMessage($"{s.Name}: {st.Goal} ({n}/{st.Count})", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                        }
                    }
            }
            catch (Exception ex)
            {
                log.Error("Story quests: a death", ex);
            }
        }

        // ---------------------------------------------------------------- encounter: a chain of your own

        static void StartEncounter(GamePlayer p, StoryQuest s, StepDef st, Zone z)
        {
            string key = Key(p, s);
            if (_encounters.ContainsKey(key) || (_encounterRetry.TryGetValue(key, out long after) && Now < after) || st.Stages.Count == 0 || z == null)
                return;
            var zd = new ZoneEventsDef { Zone = z.ID, Region = z.ZoneRegion.ID, Name = z.Description, Realm = (int) p.Realm };
            var def = new ChainDef
            {
                Id = "story_" + s.QuestId + "_" + s.StepId,
                Title = s.Def.Title,
                Levels = new[] { s.Def.Level, s.Def.Level + 2 },
                RestS = 8,
                Start = st.Start ?? st.Stages[0].Id,
                Stages = st.Stages,
                ZoneDef = zd,
            };
            GamePlayer owner = p;
            var chain = new ChainRuntime(def, z.ZoneRegion, z, Now)
            {
                Allow = l => l == owner || (owner.Group != null && owner.Group.IsInTheGroup(l)),
            };
            chain.OnEnded = outcome =>
            {
                _encounters.TryRemove(key, out _);
                StoryQuest still = Doing(owner, s.QuestId);
                if (still == null || still.StepId != st.Id)
                    return;
                if (outcome == "success")
                    StepDone(owner, still);
                else
                {
                    _encounterRetry[key] = Now + 20_000;
                    owner.Out.SendMessage($"{still.Name}: you were driven back. Gather yourself and try again.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                }
            };
            _encounters[key] = chain;
            chain.Begin(def.Start, Now);
        }

        // ---------------------------------------------------------------- tidying

        static void ClearStepWorld(GamePlayer p, StoryQuest s)
        {
            string key = Key(p, s);
            if (_clues.TryRemove(key, out StoryClue c) && c.ObjectState == GameObject.eObjectState.Active)
                c.RemoveFromWorld();
            if (_mobs.TryRemove(key, out var list))
                lock (list)
                    foreach (StoryMob m in list)
                        if (m.ObjectState == GameObject.eObjectState.Active && m.IsAlive && !m.InCombat)
                            m.RemoveFromWorld();
            _encounterRetry.TryRemove(key, out _);
            if (_encounters.TryRemove(key, out ChainRuntime chain))
            {
                chain.Quiet = true;                         // (the step went on without it: called off, no words)
                chain.OnEnded = null;
                chain.End("fail", Now);
            }
        }

        static void OnEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is GamePlayer p)
                foreach (StoryQuest s in Active(p).ToList())
                    StoryDialog.Log(p, s);
        }

        // ---------------------------------------------------------------- barks (owner 2026-11-06: "More use of the
        // chat bubbles"): a story NPC you walk past speaks up, over its head - whoever has words for you (a step of
        // yours here: its first line; a quest for you: its hook) - once in a while each

        static readonly ConcurrentDictionary<string, long> _barked = new();
        const long BARK_EVERY_MS = 300_000;
        const int BARK_RANGE = 700;                     // 17.5 m

        static void Barks(GamePlayer p, long now)
        {
            if (!NewClient.Is(p))
                return;
            foreach (StoryNpc n in _npcs.Values)
            {
                if (n.ObjectState != GameObject.eObjectState.Active || n.CurrentRegion != p.CurrentRegion || n.InCombat ||
                    !n.IsWithinRadius(p, BARK_RANGE))
                    continue;
                string key = p.ObjectId + "|" + n.Def.Id;
                if (_barked.TryGetValue(key, out long t) && now - t < BARK_EVERY_MS)
                    continue;
                string line = BarkFor(p, n);
                if (string.IsNullOrEmpty(line))
                    continue;
                _barked[key] = now;
                NpcSpeech.SayTo(n, p, StoryDialog.Bubble(line));
            }
        }

        static string BarkFor(GamePlayer p, StoryNpc n)
        {
            foreach (StoryQuest s in Active(p))
                if (s.Step_ is StepDef st && st.Type is "talk" or "choice" && Same(st.Npc, n.Def.Id) && string.IsNullOrEmpty(s.Choosing))
                    return Words(st.Say, p);
            if (_quests.Values.Any(q => Same(q.Giver, n.Def.Id) && CanTake(p, q)))
                return !string.IsNullOrEmpty(n.Def.Idle) ? Words(n.Def.Idle, p) : null;
            return null;
        }

        static void OnQuit(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not GamePlayer p)
                return;
            foreach (StoryQuest s in Active(p).ToList())
                ClearStepWorld(p, s);
            _markers.TryRemove(p, out _);
        }

        // ---------------------------------------------------------------- tests and the journal's abandon

        static bool Testing => File.Exists(Path.Combine(GameServer.Instance.Configuration.RootDirectory, "story-quests", ".testing"));

        public static string Command(GamePlayer p, string[] args)
        {
            string what = args.Length > 1 ? args[1].ToLowerInvariant() : "list";
            switch (what)
            {
                case "list":
                {
                    var sb = new StringBuilder();
                    foreach (StoryQuest s in Active(p))
                        sb.AppendLine($"{s.Name}: step {s.StepId} ({s.Step_?.Goal}) {s.Count}");
                    sb.AppendLine($"Done: {string.Join(", ", p.GetFinishedQuests().OfType<StoryQuest>().Select(q => q.QuestId + ":" + q.EndingTaken))}");
                    return sb.ToString();
                }
                case "start" when args.Length > 2 && Quest(args[2]) is StoryQuestDef q:
                {
                    if (Doing(p, q.Id) != null)
                        return "Already on it.";
                    var sq = new StoryQuest(p, q);
                    if (!p.AddQuest(sq))
                        return "Couldn't add it.";
                    if (args.Length > 3)
                        sq.SetStep(args[3]);
                    StepEntered(p, sq);
                    return $"Started {q.Id} at {sq.StepId}.";
                }
                case "step" when args.Length > 3 && Doing(p, args[2]) is StoryQuest s:
                    ClearStepWorld(p, s);
                    s.SetStep(args[3]);
                    StepEntered(p, s);
                    return $"{s.QuestId} now at {s.StepId}.";
                case "done" when args.Length > 2 && Doing(p, args[2]) is StoryQuest s2:
                    StepDone(p, s2);
                    return $"{s2.QuestId}: step done.";
                case "reset" when args.Length > 2:
                {
                    foreach (StoryQuest s3 in p.QuestList.Keys.OfType<StoryQuest>().Where(x => Same(x.QuestId, args[2])).ToList())
                    {
                        ClearStepWorld(p, s3);
                        s3.AbortQuest();
                    }
                    foreach (StoryQuest f in p.GetFinishedQuests().OfType<StoryQuest>().Where(x => Same(x.QuestId, args[2])).ToList())
                    {
                        p.RemoveFinishedQuest(f);
                        f.DeleteFromDatabase();
                    }
                    RefreshIndicators(p);
                    return $"{args[2]} forgotten.";
                }
                // testing only (runtime/server/story-quests/.testing present): move, click, answer as the probes need
                case "goto" or "talk" or "say" or "click" when !Testing:
                    return "Testing commands are off.";
                case "goto" when args.Length > 2:
                {
                    ushort region = 0; int x = 0, y = 0, z = 0;
                    if (Same(args[2], "npc") && args.Length > 3 && Npc(args[3]) is StoryNpc n)
                    {
                        region = n.CurrentRegionID; x = n.X + 120; y = n.Y; z = n.Z;
                    }
                    else if (Doing(p, args[2]) is StoryQuest gq && gq.Step_ is StepDef gs)
                    {
                        if (gs.At != null && ZoneOf(gs.Zone) is Zone gz)
                        {
                            Vector3 w = ToWorld(gs.Zone, gs.At);
                            region = gz.ZoneRegion.ID; x = (int) w.X; y = (int) w.Y; z = (int) w.Z;
                        }
                        else if (Npc(gs.Npc) is StoryNpc gn)
                        {
                            region = gn.CurrentRegionID; x = gn.X + 120; y = gn.Y; z = gn.Z;
                        }
                    }
                    if (region == 0)
                        return "Nowhere to go.";
                    p.MoveTo(region, x, y, z + 20, p.Heading);
                    return $"Moved to {region} {x} {y} {z}.";
                }
                case "talk" when args.Length > 2 && Npc(args[2]) is StoryNpc tn:
                    OnInteract(p, tn);
                    return $"(clicked {tn.Name})";
                case "say" when args.Length > 3 && Npc(args[2]) is StoryNpc sn:
                    OnWhisper(p, sn, string.Join(" ", args.Skip(3)));
                    return $"(said to {sn.Name})";
                case "click":
                {
                    StoryClue c = _clues.Values.Where(x => x.Owner == p && x.ObjectState == GameObject.eObjectState.Active).OrderBy(x => x.GetDistanceTo(p)).FirstOrDefault();
                    if (c == null)
                        return "No clue here.";
                    OnClue(p, c);
                    return $"(searched {c.Name})";
                }
                case "reload":
                    foreach (var n in _npcs.Values)
                        if (n.ObjectState == GameObject.eObjectState.Active)
                            n.RemoveFromWorld();
                    _npcs.Clear();
                    Load();
                    return $"{_quests.Count} quests.";
            }
            return "/storyquest list | start <id> [step] | step <id> <step> | done <id> | reset <id> | reload";
        }
    }

    /// <summary>A story quest's person: talks through StoryQuestManager, shows its quest marks to each player.</summary>
    public class StoryNpc : GameNPC
    {
        public StoryNpcDef Def;

        public override bool Interact(GamePlayer player)
        {
            if (Def.Hostile)
                return base.Interact(player);
            if (!base.Interact(player))
                return false;
            TurnTo(player, 10000);
            StoryQuestManager.OnInteract(player, this);
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (!base.WhisperReceive(source, text) || source is not GamePlayer p)
                return false;
            StoryQuestManager.OnWhisper(p, this, text);
            return true;
        }

        public override eQuestIndicator GetQuestIndicator(GamePlayer player) => StoryQuestManager.Indicator(player, this);
    }

    /// <summary>A monster a kill step spawned for one quester (and their group).</summary>
    public class StoryMob : GameNPC
    {
        public string QuestKey;
        public double HealthMult = 1;
        public override int MaxHealth => (int) Math.Max(1, base.MaxHealth * HealthMult);
    }

    /// <summary>Something a search step left for its quester to click.</summary>
    public class StoryClue : GameStaticItem
    {
        public GamePlayer Owner;
        public string QuestId;
        public string StepId;

        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            StoryQuestManager.OnClue(player, this);
            return true;
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&storyquest", ePrivLevel.Player, "Story quests: list yours; start / step / reset one (testing)",
        "/storyquest list | start <id> [step] | step <id> <step> | done <id> | reset <id> | reload")]
    public class StoryQuestCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            if (client?.Player == null)
                return;
            foreach (string line in StoryQuests.StoryQuestManager.Command(client.Player, args).Split('\n', StringSplitOptions.RemoveEmptyEntries))
                client.Out.SendMessage(line.TrimEnd('\r'), eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }
    }
}
