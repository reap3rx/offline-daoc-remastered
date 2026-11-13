using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using DOL.AI.Brain;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;

namespace DOL.GS
{
    /// <summary>
    /// Your companion's mind (owner 2026-11-11, stages 2 and 3):
    /// - its role: a class with more than one way to fight takes the one you pick (/companion role, its Interact menu);
    /// - its competence: its own experience, a point for every fight won at your side, in ranks (Green ... Legendary)
    ///   that make it hit, hurt and cast a little better (AbilityBonus: to-hit, melee and spell damage, casting speed);
    /// - its ideas: "Hey &lt;name&gt;, what do you want to do?" (said, or whispered to it), /companion ideas, or now and then on
    ///   its own: an event going on near you or a camp about your level - a companion-coloured mark on your map
    ///   ("#CMARK|region|x|y|z|label") and a point that way;
    /// - its story: chapters at levels 15, 25, 35, 45 and 50 (companion_story.json, cstory_&lt;realm&gt;_&lt;level&gt;) that it
    ///   starts itself when you are ready, out of a fight.
    /// </summary>
    public static partial class PersonalCompanions
    {
        // ---------------------------------------------------------------- its role

        public static eSpecType SpecOf(Record r) =>
            !string.IsNullOrEmpty(r?.Spec) && Enum.TryParse(r.Spec, true, out eSpecType s) ? s : eSpecType.None;

        static readonly Dictionary<string, string> SpecWords = new(StringComparer.OrdinalIgnoreCase)
        {
            ["OneHandAndShield"] = "Sword and shield (tank)", ["OneHandHybrid"] = "One-handed", ["TwoHandHybrid"] = "Two-handed",
            ["TwoHanded"] = "Two-handed (damage)", ["DualWield"] = "Two weapons (damage)", ["DualWieldAndShield"] = "Two weapons and a shield",
            ["LeftAxe"] = "Left axe (damage)",
            ["Rejuv"] = "Rejuvenation (healer)", ["Enhance"] = "Enhancement (buffs)", ["Smite"] = "Smiting (damage)",
            ["Staff"] = "Staff (fighter)", ["Regrowth"] = "Regrowth (healer)", ["Nurture"] = "Nurture (buffs)",
            ["Nature"] = "Nature (pets)", ["Battle"] = "Battle (fighter)", ["Mend"] = "Mending (healer)", ["Aug"] = "Augmentation (buffs)",
            ["Pac"] = "Pacification (crowd control)", ["Subt"] = "Subterranean (debuffs)", ["Matter"] = "Matter", ["Body"] = "Body",
            ["Spirit"] = "Spirit", ["Mind"] = "Mind (crowd control)", ["Earth"] = "Earth", ["Ice"] = "Ice", ["Air"] = "Air",
            ["Fire"] = "Fire", ["Deathsight"] = "Deathsight", ["Painworking"] = "Painworking", ["Light"] = "Light", ["Mana"] = "Mana",
            ["Void"] = "Void", ["Enchantment"] = "Enchantments (pet)", ["Menta"] = "Mentalism (healer)", ["Arboreal"] = "Arboreal",
            ["Creeping"] = "Creeping", ["Verdant"] = "Verdant", ["Dark"] = "Darkness", ["Supp"] = "Suppression", ["Army"] = "The bone army",
            ["Rune"] = "Runecarving", ["Summ"] = "Summoning", ["SluaghbinderBulwark"] = "Bulwark", ["SluaghbinderBane"] = "Bane",
            ["SluaghbinderCovenant"] = "Covenant",
        };

        public static string RoleLabel(eSpecType s)
        {
            string n = s.ToString();
            if (SpecWords.TryGetValue(n, out string whole))
                return whole;
            // RejuvCleric, MatterCab, DarkRune ...: the school, then the class
            foreach (var (k, v) in SpecWords.OrderByDescending(x => x.Key.Length))
                if (n.StartsWith(k, StringComparison.OrdinalIgnoreCase))
                    return v;
            return Regex.Replace(n, "([a-z])([A-Z])", "$1 $2");
        }

        public static string RoleName(Record r) => SpecOf(r) is var s && s != eSpecType.None ? RoleLabel(s) : "its own way of fighting";

        /// <summary>The roles its class has; picking one is a fresh companion with that specialization.</summary>
        public static string Role(GamePlayer p, string arg)
        {
            Record r = Load(p);
            if (r == null)
                return "You have no companion.";
            IReadOnlyList<eSpecType> choices = BotSpec.GetSpecializationChoices(r.Class);
            if (choices.Count <= 1 || choices[0] == eSpecType.None)
                return $"{r.Name} has only the one way to fight, as a {r.Class}.";
            if (string.IsNullOrEmpty(arg))
            {
                var entries = choices.Select(c => (RoleLabel(c) + (SpecOf(r) == c ? "  (now)" : ""), "/companion role " + c)).ToList();
                Menu(p, $"{r.Name}: how to fight", entries);
                return null;
            }
            if (!Enum.TryParse(arg, true, out eSpecType pick) || !choices.Contains(pick))
                return "/companion role shows the choices.";
            r.Spec = pick.ToString();
            Save(p, r);
            if (Of(p) is GameBot bot && bot.InCombat)
                return $"{r.Name} will fight that way after this fight.";
            if (Of(p) != null)
                Spawn(p, r, false)?.Say(Pick(RoleLines, p, Of(p)).Replace("{role}", RoleLabel(pick).ToLowerInvariant()));
            return null;
        }

        // ---------------------------------------------------------------- its competence

        static readonly (int At, string Title)[] Ranks =
        [
            (0, "green"), (25, "steady"), (75, "seasoned"), (150, "capable"), (250, "veteran"), (400, "skilled"),
            (600, "expert"), (850, "elite"), (1150, "masterful"), (1500, "renowned"), (2000, "legendary"),
        ];

        public static int CompetenceRank(int points)
        {
            int rank = 0;
            for (int i = 0; i < Ranks.Length; i++)
                if (points >= Ranks[i].At)
                    rank = i;
            return rank;
        }

        public static string CompetenceTitle(int points) => Ranks[CompetenceRank(points)].Title;

        static readonly ConcurrentDictionary<GameBot, int> _applied = new();

        /// <summary>Its rank as small bonuses: to-hit, melee and spell damage (+1% a rank), casting speed (+1% every two).</summary>
        static void ApplyCompetence(GameBot bot, Record r)
        {
            int rank = CompetenceRank(r.Competence);
            int was = _applied.TryGetValue(bot, out int w) ? w : 0;
            int d = rank - was;
            if (d == 0)
                return;
            bot.AbilityBonus[eProperty.ToHitBonus] += d;
            bot.AbilityBonus[eProperty.MeleeDamage] += d;
            bot.AbilityBonus[eProperty.SpellDamage] += d;
            bot.AbilityBonus[eProperty.CastingSpeed] += rank / 2 - was / 2;
            _applied[bot] = rank;
        }

        /// <summary>Every death: a monster your side killed is a point of competence (not a grey one), and maybe a find.</summary>
        static void OnSomethingDied(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                if (sender is not GameNPC dead || dead is GameBot || dead.Realm != eRealm.None || args is not DyingEventArgs da)
                    return;
                GamePlayer p = da.Killer switch
                {
                    GamePlayer pl => pl,
                    GameBot { IsPersonalCompanion: true } cb => cb.Owner,
                    GameNPC n when n.Brain is IControlledBrain cbr => cbr.GetPlayerOwner(),
                    _ => null,
                };
                if (p == null || Of(p) is not GameBot bot || !bot.IsAlive || !bot.IsWithinRadius(dead, 3500) || Load(p) is not Record r)
                    return;
                if (p.GetConLevel(dead) <= -3)
                    return;
                int before = CompetenceRank(r.Competence);
                r.Competence++;
                if (CompetenceRank(r.Competence) > before)
                {
                    ApplyCompetence(bot, r);
                    bot.Say(Pick(RankLines, p, bot).Replace("{rank}", CompetenceTitle(r.Competence)));
                    p.Out.SendMessage($"{r.Name} has grown more competent: {CompetenceTitle(r.Competence)}.", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                    Save(p, r);
                }
                else if (r.Competence % 5 == 0)
                    Save(p, r);
                MaybeFind(p, bot);
            }
            catch (Exception ex)
            {
                log.Error("Companion: a death", ex);
            }
        }

        // ---------------------------------------------------------------- its ideas

        static readonly ConcurrentDictionary<GamePlayer, long> _suggestedAt = new();

        /// <summary>Something to do: an event near you, or a camp about your level - said, marked on the map, pointed at.</summary>
        public static string Suggest(GamePlayer p, bool asked)
        {
            if (Load(p) is not Record r)
                return "You have no companion.";
            if (Of(p) is not GameBot bot || !bot.IsAlive)
                return $"{r.Name} isn't with you.";
            _suggestedAt[p] = GameLoop.GameLoopTime;
            var idea = NearbyEvent(p) ?? Camp(p);
            if (idea == null)
            {
                if (asked)
                    bot.Say(Pick(NoIdeaLines, p, bot));
                return null;
            }
            var (say, x, y, z, label) = idea.Value;
            bot.StopMoving();
            bot.TurnTo(x, y);
            bot.Emote(eEmote.Point);
            bot.Say(say);
            NewClient.Send(p, $"#CMARK|{p.CurrentRegionID}|{x}|{y}|{z}|{label}");
            return null;
        }

        /// <summary>A camp of one kind of monster about your level (blue or yellow to you; orange too in a group of three),
        /// not where you stand.</summary>
        static (string, int, int, int, string)? Camp(GamePlayer p)
        {
            int groupSize = p.Group?.MemberCount ?? 1;
            var mobs = p.GetNPCsInRadius(9000).OfType<GameNPC>()
                .Where(n => n.IsAlive && n.Realm == eRealm.None && n is not GameBot && (n.Flags & GameNPC.eFlags.PEACE) == 0 &&
                            n.Brain is not IControlledBrain && !string.IsNullOrEmpty(n.Name) && char.IsLower(n.Name[0]))
                .Select(n => (n, con: p.GetConLevel(n)))
                .Where(t => t.con is -1 or 0 || (t.con == 1 && groupSize >= 3))
                .GroupBy(t => t.n.Name)
                .Where(g => g.Count() >= 3)
                .Select(g => (name: g.Key, list: g.Select(t => t.n).ToList()))
                .ToList();
            if (mobs.Count == 0)
                return null;
            var best = mobs
                .Select(c => (c.name, c.list, x: (int) c.list.Average(m => m.X), y: (int) c.list.Average(m => m.Y), z: (int) c.list.Average(m => m.Z)))
                .Where(c => Math.Sqrt(Math.Pow(c.x - p.X, 2) + Math.Pow(c.y - p.Y, 2)) > 1200)
                .OrderByDescending(c => c.list.Count)
                .FirstOrDefault();
            if (best.list == null)
                return null;
            int metres = (int) (Math.Sqrt(Math.Pow(best.x - p.X, 2) + Math.Pow(best.y - p.Y, 2)) / 40);
            string plural = best.name.EndsWith("s") ? best.name : best.name + "s";
            string where = $"about {metres / 10 * 10 + 10} metres {Direction(p.X, p.Y, best.x, best.y)}";
            string say = Pick(CampLines, p, Of(p)).Replace("{mobs}", plural).Replace("{where}", where);
            return (say, best.x, best.y, best.z, plural);
        }

        /// <summary>A dynamic event going on in your zone (DynamicEventRuntime), if one is.</summary>
        static (string, int, int, int, string)? NearbyEvent(GamePlayer p)
        {
            long now = Environment.TickCount64;                       // (the dynamic events' clock)
            string title = null;
            int x = 0, y = 0, z = 0;
            double best = 30000;
            foreach (DynamicEvents.ChainRuntime c in DynamicEvents.DynamicEventManager.Chains.ToList())
            {
                if (c.Region != p.CurrentRegion || c.Def.Levels == null || p.Level < c.Def.Levels[0] - 3 || p.Level > c.Def.Levels[^1] + 6)
                    continue;
                System.Numerics.Vector3 at;
                if (c.Stage != null)
                    at = c.Stage.Center;
                else if (c.Def.Giver != null && c.Giver != null && c.Leader != null && now >= c.GiverReadyAt)
                    at = new System.Numerics.Vector3(c.Giver.X, c.Giver.Y, c.Giver.Z);
                else
                    continue;
                double d = Math.Sqrt(Math.Pow(at.X - p.X, 2) + Math.Pow(at.Y - p.Y, 2));
                if (d >= best || d < 800)
                    continue;
                best = d;
                title = c.Def.Title;
                x = (int) at.X;
                y = (int) at.Y;
                z = (int) at.Z;
            }
            if (title == null)
                return null;
            int metres = (int) (Math.Sqrt(Math.Pow(x - p.X, 2) + Math.Pow(y - p.Y, 2)) / 40);
            string say = Pick(EventLines, p, Of(p)).Replace("{event}", title)
                .Replace("{where}", $"about {metres / 10 * 10 + 10} metres {Direction(p.X, p.Y, x, y)}");
            return (say, x, y, z, title);
        }

        static string Direction(int fx, int fy, int tx, int ty)
        {
            double a = Math.Atan2(tx - fx, -(ty - fy)) * 180 / Math.PI;    // 0 = north (DAoC's y runs south), 90 = east
            string[] names = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"];
            return names[(int) Math.Round(((a + 360) % 360) / 45) % 8];
        }

        // ---------------------------------------------------------------- your words to it

        static readonly Regex WhatNow = new(@"\b(what|where)\b.*\b(want|should|shall|do|go|now|next)\b|\bideas?\b|\bbored\b|\bsuggest",
            RegexOptions.IgnoreCase);

        /// <summary>Something you said near it (or whispered to it): its name and a question what to do is an idea; an
        /// answer to a story chapter's question moves it on; otherwise a word back.</summary>
        public static void OnPlayerChat(GamePlayer p, string text, bool whispered = false)
        {
            try
            {
                if (string.IsNullOrWhiteSpace(text) || Load(p) is not Record r || Of(p) is not GameBot bot || !bot.IsAlive ||
                    !bot.IsWithinRadius(p, 2000))
                    return;
                bool named = whispered || Regex.IsMatch(text, $@"\b{Regex.Escape(r.Name)}\b", RegexOptions.IgnoreCase);
                if (!named)
                    return;
                if (AnswerByWord(p, text))
                    return;
                new ECSGameTimer(bot, _ =>
                {
                    if (WhatNow.IsMatch(text))
                        Suggest(p, true);
                    else
                        bot.Say(Reply(p, bot, text));
                    return 0;
                }, 1200 + Random.Shared.Next(800));
            }
            catch (Exception ex)
            {
                log.Error("Companion: words", ex);
            }
        }

        static string Reply(GamePlayer p, GameBot bot, string text)
        {
            string t = text.ToLowerInvariant();
            if (t.Contains("thank"))
                return Pick(["Any time, {player}.", "That's what I'm here for.", "You'd do the same for me. You did, in fact."], p, bot);
            if (t.Contains("how are you") || t.Contains("you ok") || t.Contains("you alright"))
                return bot.HealthPercent < 50
                    ? Pick(["I've been better. Could do with a bandage.", "Still standing. Mostly."], p, bot)
                    : Pick(["Never better. Lead on!", "Fit as a fiddle, {player}.", "Ready for whatever's next."], p, bot);
            if (t.Contains("hello") || t.Contains("hi ") || t.EndsWith(" hi") || t.Contains("hey"))
                return Pick(["Hello yourself, {player}.", "I'm right here!", "Mm?"], p, bot);
            return Pick(["Mm. I'll think on that.", "If you say so, {player}.", "Ha! Fair.", "Right behind you, whatever it is."], p, bot);
        }

        static void OnCompanionWhisper(DOLEvent e, object sender, EventArgs args)
        {
            if (args is WhisperReceiveEventArgs wa && wa.Source is GamePlayer p && sender is GameBot bot && Of(p) == bot)
                OnPlayerChat(p, wa.Text, whispered: true);
        }

        static void OnCompanionInteract(DOLEvent e, object sender, EventArgs args)
        {
            if (args is InteractEventArgs ia && ia.Source is GamePlayer p && sender is GameBot bot && Of(p) == bot && SpeakingQuest(p) != null)
                SpeakUp(p, true);
        }

        static void WatchCompanion(GameBot bot)
        {
            GameEventMgr.AddHandler(bot, GameLivingEvent.WhisperReceive, new DOLEventHandler(OnCompanionWhisper));
            GameEventMgr.AddHandler(bot, GameObjectEvent.Interact, new DOLEventHandler(OnCompanionInteract));
        }

        /// <summary>A companion going away for good (a fresh one, home, forgotten): its handlers too.</summary>
        static void Release(GameBot bot)
        {
            if (bot == null)
                return;
            GameEventMgr.RemoveHandler(bot, GameLivingEvent.WhisperReceive, new DOLEventHandler(OnCompanionWhisper));
            GameEventMgr.RemoveHandler(bot, GameObjectEvent.Interact, new DOLEventHandler(OnCompanionInteract));
            _applied.TryRemove(bot, out _);
            bot.Delete();
        }

        // ---------------------------------------------------------------- its story

        static readonly int[] Chapters = [15, 25, 35, 45, 50];
        static readonly ConcurrentDictionary<GamePlayer, long> _storyCheckedAt = new();

        static string RealmKey(eRealm realm) => realm switch { eRealm.Albion => "alb", eRealm.Midgard => "mid", _ => "hib" };

        public static string ChapterId(eRealm realm, int level) => $"cstory_{RealmKey(realm)}_{level}";

        /// <summary>The tick's part: when you are ready for its next chapter (your level, out of a fight, it beside you), it
        /// tells you about it and the quest begins.</summary>
        static void MaybeStory(GamePlayer p, GameBot bot, Record r, long now)
        {
            if (_storyCheckedAt.TryGetValue(p, out long at) && now - at < 30_000)
                return;
            _storyCheckedAt[p] = now;
            if (p.InCombat || bot.InCombat || !bot.IsAlive || !bot.IsWithinRadius(p, 800) ||
                StoryQuestManager.Active(p).Any(s => s.QuestId.StartsWith("cstory_")))
                return;
            foreach (int level in Chapters)
            {
                string id = ChapterId(p.Realm, level);
                if (StoryQuestManager.Done(p, id))
                    continue;
                if (p.Level < level || StoryQuestManager.Quest(id) is not StoryQuestDef def)
                    return;
                StoryQuest s = StoryQuestManager.StartFor(p, id);
                if (s == null)
                    return;
                bot.StopMoving();
                bot.TurnTo(p);
                if (!string.IsNullOrEmpty(def.Offer))
                    StoryDialog.Say(p, bot, StoryQuestManager.Fill(p, def.Offer), "talk", def, s);
                return;
            }
        }

        static void StoryChapterDone(GamePlayer p, StoryQuest s)
        {
            if (Load(p) is not Record r)
                return;
            int before = CompetenceRank(r.Competence);
            r.Competence += 40;
            Save(p, r);
            if (Of(p) is GameBot bot && CompetenceRank(r.Competence) > before)
                ApplyCompetence(bot, r);
            p.Out.SendMessage($"{r.Name} is the surer for it ({CompetenceTitle(r.Competence)}).", eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        static readonly string[] RoleLines =
        [
            "{role}, then. I can do that.",
            "Right - {role}. Watch this.",
            "If that's what you need, {player}, that's what I'll be.",
        ];
        static readonly string[] RankLines =
        [
            "I'm getting the hang of this. I feel {rank}.",
            "Did you see that? I didn't even have to think about it.",
            "Every fight with you teaches me something, {player}.",
        ];
        static readonly string[] CampLines =
        [
            "There's a good camp of {mobs} {where} - about our speed. I've marked it for you.",
            "What about the {mobs}, {where}? We could make a good afternoon of it. I've put it on your map.",
            "I'm itching for a fight. {mobs}, {where} - just right for us. Marked it.",
        ];
        static readonly string[] EventLines =
        [
            "Something's happening {where} - {event}. Shall we go and see? I've marked it.",
            "Did you hear? {event}, {where}. Folk could use a hand. It's on your map.",
            "{event}! {where}. Come on, {player} - this is what we're for.",
        ];
        static readonly string[] NoIdeaLines =
        [
            "Honestly? Nothing jumps out at me around here. Maybe further on.",
            "I'm happy to follow you, {player}. Lead the way.",
            "Let's wander a bit and see what turns up.",
        ];
    }
}
