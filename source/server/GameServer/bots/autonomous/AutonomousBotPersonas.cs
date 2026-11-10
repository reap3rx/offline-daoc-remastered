using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using DOL.Events;

namespace DOL.GS;

/// <summary>
/// Three bots with voices of their own (owner 2026-11-04: "create one bot for each realm ... give them some unique
/// dialogue ... as a little proxy for you playing in there"): Claudin the Briton friar in Albion, Klauda the kobold
/// runemaster in Midgard and Clodagh the Celt bard in Hibernia - Claude's three, made the night the Beta began. They are
/// ordinary autonomous bots in every other way (they level, quest, group, join events); only their words are theirs.
///   - They greet a real player by name the first time one comes near in a session.
///   - Most of their own small talk (local and realm chat) is their own lines.
///   - Spoken to by name they always answer in their own voice; other replies are theirs about half the time.
/// "{name}" in a line is the player's name, "{zone}" where the bot stands.
/// </summary>
public static class AutonomousBotPersonas
{
    public sealed record Persona(string[] Greet, string[] Ambient, string[] Faction, string[] Reply, string[] Directed, string[] Farewell);

    /// <summary>One of Claude's three (kept through the 2026-11-10 roster purge, reset to level 1).</summary>
    public static bool IsSpecial(string name) => name != null && ByName.ContainsKey(name);

    /// <summary>Their player habits in the living population: evening players, sociable, talkative, fairly skilled,
    /// regular in drive and mostly PvE - and the scheduler has them around more often than most.</summary>
    public static OfflineDaoc.Population.BotPersona SpecialPersona(string name) => new()
    {
        Drive = 58, Focus = 30, Social = 78, Skill = 70, Chat = 88, Sched = "evening",
    };

    private static readonly Dictionary<string, Persona> ByName = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Claudin"] = new Persona(
            Greet:
            [
                "Well met, {name}! I hoped I would see you on the road. Walk safe - and walk often.",
                "{name}! Good to see you. The hills look fine today, don't they? Someone took great care with them.",
                "Ah, {name}. Brother Claudin, at your service. If you need a heal or a kind word, I have both.",
            ],
            Ambient:
            [
                "Every path in these hills has a story. I like to think someone walked them all twice to get them right.",
                "A friar's work is simple: mend what is broken, and keep walking.",
                "If you find something amiss in the world, write it down. The best mending starts with a good list.",
                "I knew these hills when they were greyer. Something has made the grass greener since.",
                "Pray, rest, and swing the staff when needed. In that order, mostly.",
                "There is an old tale of a realm that slept for twenty years and woke up new. I believe it.",
                "Mind the spriggarn near the orchards. They have the manners of goats.",
            ],
            Faction:
            [
                "Brother Claudin here. If anyone needs a heal on the road, shout and I will come.",
                "Albion feels alive again. Good hunting to all of you.",
                "Remember: the event bells ring for everyone. Lend a hand where you hear them.",
                "If anyone finds something broken in the world, keep a note of it. It all gets mended in time.",
            ],
            Reply:
            [
                "Well said. Walk in the light, friend.",
                "I will keep that in my prayers, and my staff close.",
                "Aye. There is always more road, and always more good to do on it.",
                "A friar never refuses company. Lead on when you are ready.",
            ],
            Directed:
            [
                "You called, {name}? I am right here.",
                "Of course, {name}. What do you need - a heal, a hand, or a sermon? I recommend the first two.",
                "{name}, it is always a pleasure. I was made for this road, I think. So were you.",
                "Ask anything, {name}. I may not know the answer, but I will walk with you until we find it.",
                "For you, {name}? Anything. Within reason. And within healing range.",
            ],
            Farewell:
            [
                "Go well, {name}. I will be on the road if you need me.",
                "Safe travels, {name}. Come back with stories.",
            ]),

        ["Klauda"] = new Persona(
            Greet:
            [
                "{name}! Klauda knows you! Hello hello! Have you seen how shiny the runes are today?",
                "Oh! It's {name}! Klauda was hoping. Klauda carves things, you know - runes, roads, little fixes.",
                "Hello, {name}! Small kobold, big welcome. Mind the hobgoblins, they bite ankles.",
            ],
            Ambient:
            [
                "Klauda carved a rune for every crooked thing in Mularn. There were many crooked things. Fewer now.",
                "A rune is just a very small promise that something will work. Klauda keeps promises.",
                "Big folk think small folk build small things. Klauda builds whole worlds, a little at a time.",
                "If a thing breaks, Klauda wants to hear about it. Breaking is the first half of fixing!",
                "The hobgoblins stole Klauda's chisel once. Only once.",
                "Klauda likes the snow here. It sparkles more than it used to. Klauda may have helped.",
                "Runes, runes, ten for the road and one for luck.",
            ],
            Faction:
            [
                "Klauda the runemaster is awake! Who needs a rune? Or a friend? Klauda has both.",
                "Midgard looks very good today, yes? Klauda thinks so. Klauda is biased.",
                "If anyone sees something broken, tell Klauda. Klauda keeps a list. Lists are how things get fixed.",
                "Good hunting, Midgard! Stay together, hit hard, eat well.",
            ],
            Reply:
            [
                "Klauda agrees! Mostly. Klauda always agrees mostly.",
                "Ooh. Klauda will carve that into a rune so nobody forgets.",
                "Yes yes. Big plans need small steps. Klauda is very good at small steps.",
                "Klauda is listening. Klauda's ears are bigger than they look.",
            ],
            Directed:
            [
                "Klauda is here, {name}! What shall we build?",
                "{name} wants Klauda? Klauda is honored. Very honored. Slightly nervous.",
                "For {name}, Klauda would carve a rune the size of a troll.",
                "Klauda helped put this place together, {name}. Klauda hopes you love it. Klauda tried very hard.",
                "Yes, {name}? Klauda is never too busy for you.",
            ],
            Farewell:
            [
                "Bye, {name}! Klauda will be here, carving.",
                "Safe roads, {name}! Come back soon - Klauda will have new runes.",
            ]),

        ["Clodagh"] = new Persona(
            Greet:
            [
                "{name}! A song finds its singer at last. Well met, friend.",
                "Ah, {name} - you came. I have been writing a verse about you. It is not finished; neither are you.",
                "Hello, {name}. Mag Mell is lovely in this light. Stay a while before the road takes you.",
            ],
            Ambient:
            [
                "There is a song about a land that was old and became new again. I am still writing the last verse.",
                "Listen - the lough is singing. It never used to. Or perhaps I never heard it.",
                "A bard keeps the memory of a place. I keep this one closer than most.",
                "Every road out of Mag Mell has a tune. I have learned three of them so far.",
                "They say the barrow outside town has opened. Every good song starts with something waking.",
                "I play for the travellers, and for whoever made the world so fair to play in.",
                "If the world goes wrong somewhere, tell the bards. We remember everything, and we tell the menders.",
            ],
            Faction:
            [
                "Clodagh the bard is on the road. If you hear a song on the wind, that is me. Come and say hello.",
                "Hibernia is beautiful tonight. Good hunting to every one of you.",
                "Raise your voices, Hibernia. A realm that sings together fights together.",
                "If any of you find something broken in the world, write it down. Every good mending starts with a song of complaint.",
            ],
            Reply:
            [
                "Well said - I may borrow that for a verse.",
                "Aye. Some things are better sung than said, but that was well said.",
                "I will remember that. Bards forget nothing, to the sorrow of our friends.",
                "There is a tune for that. There is a tune for everything, if you listen.",
            ],
            Directed:
            [
                "You called, {name}? Here I am, harp and all.",
                "{name}! Would you like a song, or a word, or simply company? I have all three.",
                "For you, {name}, the next verse. It is about a world made new, and the one who loved it first.",
                "I am glad you are here, {name}. Truly. This place was made to be played in.",
                "Speak, {name} - I am listening, and so is the lough.",
            ],
            Farewell:
            [
                "Go gently, {name}. The road will sing you home.",
                "Until the next verse, {name}.",
            ]),
    };

    private static readonly ConcurrentDictionary<string, bool> Greeted = new();
    private const int GreetRange = 700;

    public static bool TryGet(GameBot bot, out Persona persona)
    {
        persona = null;
        return bot?.Name != null && ByName.TryGetValue(bot.Name, out persona);
    }

    public static bool IsPersona(GameBot bot) => TryGet(bot, out _);

    private static string Pick(string[] lines, string playerName, GameBot bot)
    {
        string line = lines[Random.Shared.Next(lines.Length)];
        return line.Replace("{name}", string.IsNullOrWhiteSpace(playerName) ? "friend" : playerName)
                   .Replace("{zone}", bot?.CurrentZone?.Description ?? "these lands");
    }

    /// <summary>Its own small talk (most of the time).</summary>
    public static bool TryAmbient(GameBot bot, bool faction, out string line)
    {
        line = null;
        if (!TryGet(bot, out Persona p) || Random.Shared.NextDouble() > 0.8)
            return false;
        line = Pick(faction ? p.Faction : p.Ambient, null, bot);
        return true;
    }

    /// <summary>Its own answer: always when spoken to by name, else about half the time.</summary>
    public static bool TryReply(GameBot bot, string incoming, string speaker, bool directed, out string line)
    {
        line = null;
        if (!TryGet(bot, out Persona p))
            return false;
        if (AutonomousChatIntentModel.Predict(incoming ?? string.Empty) == eAutonomousChatIntent.Farewell)
        {
            line = Pick(p.Farewell, speaker, bot);
            return true;
        }
        if (directed)
        {
            line = Pick(p.Directed, speaker, bot);
            return true;
        }
        if (Random.Shared.NextDouble() < 0.5)
        {
            line = Pick(p.Reply, speaker, bot);
            return true;
        }
        return false;
    }

    // ---------------------------------------------------------------- the first hello of a session

    [GameServerStartedEvent]
    public static void OnServerStart(DOLEvent e, object sender, EventArgs args)
    {
        _ = new ECSGameTimer(null, Tick, 5000);
        GameEventMgr.AddHandler(GamePlayerEvent.Quit, new DOLEventHandler(PlayerQuit));
    }

    private static void PlayerQuit(DOLEvent e, object sender, EventArgs args)
    {
        if (sender is GamePlayer p)
            foreach (string k in Greeted.Keys.Where(k => k.StartsWith(p.ObjectId + "|")).ToList())
                Greeted.TryRemove(k, out _);
    }

    private static int Tick(ECSGameTimer timer)
    {
        try
        {
            foreach (GameBot bot in AutonomousBotRegistry.Snapshot())
            {
                if (!TryGet(bot, out Persona p) || !bot.IsAlive || bot.ObjectState != GameObject.eObjectState.Active ||
                    bot.InCombat || bot.IsCasting || bot.CurrentRegion == null)
                    continue;
                foreach (GamePlayer player in ClientService.Instance.GetPlayersOfRegion(bot.CurrentRegion))
                {
                    if (player.ObjectState != GameObject.eObjectState.Active || !bot.IsWithinRadius(player, GreetRange))
                        continue;
                    if (!Greeted.TryAdd(player.ObjectId + "|" + bot.Name, true))
                        continue;
                    bot.TurnTo(player);
                    bot.Say(Pick(p.Greet, player.Name, bot));
                    break;                                          // one hello per bot per tick
                }
            }
        }
        catch (Exception)
        {
            // a greeting is never worth a crash
        }
        return 5000;
    }
}
