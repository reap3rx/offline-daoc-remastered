using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Numerics;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.StoryQuests;

namespace DOL.GS
{
    /// <summary>
    /// The companion quest's end (owner 2026-11-12: "the old person ... directs you to the direction they went, and there
    /// you'd go on a short quest where you save them from some sort of mini boss mob. After that, you talk to them, they
    /// thank you, and ask to join you"). Its last step ("companion": companion.json's "thank") puts the one you came for
    /// at the camp - the class, folk and sex you remembered for the old one, and the name that came with them - who turns
    /// to you, thanks you and asks to come along. Yes (any answer: they are coming) and they are your companion where they
    /// stand. The same kind of step in the companion's own story (cstory_*) is your companion speaking.
    /// The quest's words: {cname} the companion's name, {cclass} its class, {he} / {He} / {him} / {his} / {His}.
    /// </summary>
    public static partial class PersonalCompanions
    {
        // the one being rescued, before it is anyone's companion
        static readonly ConcurrentDictionary<GamePlayer, GameBot> _rescued = new();
        static readonly ConcurrentDictionary<GamePlayer, long> _spokeUp = new();

        static StoryQuest RescueQuest(GamePlayer p) =>
            StoryQuestManager.Active(p).FirstOrDefault(s => s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase));

        /// <summary>{cname}, {cclass} and he / she in a quest's words: the companion's (or, on its quest, the one being
        /// remembered).</summary>
        static string FillWords(GamePlayer p, string t)
        {
            string name = null, cls = null;
            bool? female = null;
            if (Load(p) is Record r)
            {
                name = r.Name;
                cls = r.Class.ToString();
                female = r.Gender == eGender.Female;
            }
            else if (RescueQuest(p) is StoryQuest s)
            {
                name = s.GetCustomProperty("c_name");
                if (int.TryParse(s.GetCustomProperty("c_class"), out int c))
                    cls = ((eCharacterClass) c).ToString();
                string sex = s.GetCustomProperty("c_sex");
                female = sex == "2" ? true : sex == "1" ? false : null;
            }
            if (!string.IsNullOrEmpty(name))
                t = t.Replace("{cname}", name);
            if (!string.IsNullOrEmpty(cls))
                t = t.Replace("{cclass}", cls).Replace("{clesson}", Lesson(cls));
            return female switch
            {
                true => t.Replace("{he}", "she").Replace("{He}", "She").Replace("{him}", "her").Replace("{his}", "her").Replace("{His}", "Her"),
                false => t.Replace("{he}", "he").Replace("{He}", "He").Replace("{him}", "him").Replace("{his}", "his").Replace("{His}", "His"),
                _ => t.Replace("{he}", "they").Replace("{He}", "They").Replace("{him}", "them").Replace("{his}", "their").Replace("{His}", "Their"),
            };
        }

        /// <summary>What its class's teacher taught it (its own story's words).</summary>
        static string Lesson(string cls) => Enum.TryParse(cls, out eCharacterClass c) ? c switch
        {
            eCharacterClass.Cleric or eCharacterClass.Friar or eCharacterClass.Healer or eCharacterClass.Shaman or
                eCharacterClass.Druid or eCharacterClass.Warden or eCharacterClass.Bard or eCharacterClass.Minstrel or
                eCharacterClass.Skald => "how to keep people breathing when everything says they shouldn't",
            eCharacterClass.Wizard or eCharacterClass.Theurgist or eCharacterClass.Sorcerer or eCharacterClass.Cabalist or
                eCharacterClass.Necromancer or eCharacterClass.Runemaster or eCharacterClass.Spiritmaster or
                eCharacterClass.Bonedancer or eCharacterClass.Eldritch or eCharacterClass.Enchanter or
                eCharacterClass.Mentalist or eCharacterClass.Animist => "how to bend the world without breaking it",
            eCharacterClass.Scout or eCharacterClass.Infiltrator or eCharacterClass.Hunter or eCharacterClass.Shadowblade or
                eCharacterClass.Ranger or eCharacterClass.Nightshade => "how to move without being seen, and strike without being missed",
            _ => "how to hold a line when everyone else is running",
        } : "everything I know";

        static void OnStepBegan(GamePlayer p, StoryQuest s)
        {
            bool rescue = s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase);
            if (rescue && s.Step_?.Type == "encounter")
                return;                              // (TickRescues: they're in the fight once you come near)
            if (s.Step_?.Type != "companion")
                return;
            if (rescue && EnsureRescued(p, s) is GameBot saved)
                saved.Flags &= ~GameNPC.eFlags.PEACE;
            // a moment for the fight to settle, then they speak
            new ECSGameTimer(p, _ =>
            {
                SpeakUp(p, false);
                return 0;
            }, 2500);
        }

        /// <summary>A log-in in the middle of the last step: they are where you left them.</summary>
        static void ResumeRescue(GamePlayer p)
        {
            if (RescueQuest(p) is StoryQuest s && s.Step_?.Type is "companion" or "encounter")
                EnsureRescued(p, s);
        }

        static void EndRescue(GamePlayer p)
        {
            if (_rescued.TryRemove(p, out GameBot bot))
            {
                ForgetRescueHandlers(bot);
                if (bot.ObjectState == GameObject.eObjectState.Active)
                    bot.Delete();
            }
            _spokeUp.TryRemove(p, out _);
        }

        /// <summary>The one you came for, at the camp: hurt, but on their feet.</summary>
        static GameBot EnsureRescued(GamePlayer p, StoryQuest s)
        {
            if (_rescued.TryGetValue(p, out GameBot have) && have.ObjectState == GameObject.eObjectState.Active)
                return have;
            StepDef st = s.Step_;
            if (st?.At == null || !int.TryParse(s.GetCustomProperty("c_class"), out int c) || !int.TryParse(s.GetCustomProperty("c_race"), out int r))
                return null;
            string name = s.GetCustomProperty("c_name");
            eGender g = s.GetCustomProperty("c_sex") == "2" ? eGender.Female : eGender.Male;
            if (string.IsNullOrEmpty(name))
            {
                name = NewName(p, (eCharacterClass) c, g);
                s.SetCustomProperty("c_name", name);
                s.SaveIntoDatabase();
            }
            Zone z = WorldMgr.GetZone((ushort) st.Zone);
            if (z == null || z.ZoneRegion == null)
                return null;
            Vector3 at = StoryQuestManager.ToWorld(st.Zone, st.At);
            GameBot bot;
            try
            {
                bot = new GameBot(p, (byte) c, name, (byte) r, (byte) g, temporaryGroupHelper: true, equipmentLevel: p.Level, botLevel: p.Level);
            }
            catch (Exception ex)
            {
                log.Error($"Companion: the rescued {(eCharacterClass) c} for {p.Name}", ex);
                return null;
            }
            bot.X = (int) at.X + 60;
            bot.Y = (int) at.Y + 40;
            bot.Z = (int) at.Z;
            bot.CurrentRegionID = z.ZoneRegion.ID;
            bot.Heading = bot.GetHeading(p);
            if (!bot.AddToWorld())
            {
                bot.Delete();
                return null;
            }
            bot.Health = Math.Max(1, bot.MaxHealth / 3);
            bot.StopFollowing();
            if (st.Type == "encounter")
                bot.Flags |= GameNPC.eFlags.PEACE;           // (the rowdies can't finish them off before you get there)
            GameEventMgr.AddHandler(bot, GameObjectEvent.Interact, new DOLEventHandler(OnRescuedInteract));
            GameEventMgr.AddHandler(bot, GameLivingEvent.WhisperReceive, new DOLEventHandler(OnRescuedWhisper));
            _rescued[p] = bot;
            return bot;
        }

        static void ForgetRescueHandlers(GameBot bot)
        {
            GameEventMgr.RemoveHandler(bot, GameObjectEvent.Interact, new DOLEventHandler(OnRescuedInteract));
            GameEventMgr.RemoveHandler(bot, GameLivingEvent.WhisperReceive, new DOLEventHandler(OnRescuedWhisper));
        }

        static void OnRescuedInteract(DOLEvent e, object sender, EventArgs args)
        {
            if (args is InteractEventArgs ia && ia.Source is GamePlayer p && _rescued.TryGetValue(p, out GameBot bot) && bot == sender)
                SpeakUp(p, force: true);
        }

        static void OnRescuedWhisper(DOLEvent e, object sender, EventArgs args)
        {
            if (args is WhisperReceiveEventArgs wa && wa.Source is GamePlayer p && _rescued.TryGetValue(p, out GameBot bot) && bot == sender)
                Answered(p);
        }

        /// <summary>The speaker of a "companion" step: the one you rescued, or your companion in its own story.</summary>
        static GameBot Speaker(GamePlayer p, StoryQuest s) =>
            s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase)
                ? (_rescued.TryGetValue(p, out GameBot b) && b.ObjectState == GameObject.eObjectState.Active ? b : EnsureRescued(p, s))
                : Of(p);

        /// <summary>Whether a story step is waiting on your companion's words (its Interact menu's TALK).</summary>
        public static bool HasWordsFor(GamePlayer p) => SpeakingQuest(p) != null;

        static StoryQuest SpeakingQuest(GamePlayer p) =>
            StoryQuestManager.Active(p).FirstOrDefault(s => s.Step_?.Type == "companion");

        /// <summary>A "companion" step's words, from them, with its [answers] (the dialog window; a click on them, or
        /// /companion speak, brings it back).</summary>
        public static string SpeakUp(GamePlayer p) => SpeakUp(p, true);

        static string SpeakUp(GamePlayer p, bool force)
        {
            StoryQuest s = SpeakingQuest(p);
            if (s == null)
                return Load(p) == null ? "You have no companion." : $"{Load(p).Name} has nothing pressing to say just now.";
            GameBot bot = Speaker(p, s);
            if (bot == null || !bot.IsAlive)
                return "They aren't here to talk to.";
            if (!p.IsWithinRadius(bot, 1200))
                return $"{bot.Name} is too far away to talk to.";
            long now = GameLoop.GameLoopTime;
            if (!force && _spokeUp.TryGetValue(p, out long at) && now - at < 8000)
                return null;
            _spokeUp[p] = now;
            bot.StopMoving();
            bot.TurnTo(p);
            if (p.TargetObject != bot)
            {
                p.TargetObject = bot;
                p.Out.SendChangeTarget(bot);
            }
            string say = StoryQuestManager.Fill(p, s.Step_.Say ?? "");
            if (string.IsNullOrWhiteSpace(say))
                say = "Shall we go on? [Yes]";
            StoryDialog.Say(p, bot, say, "choice", null, s);
            return null;
        }

        /// <summary>Their question answered (whatever the button: they are coming).</summary>
        static void Answered(GamePlayer p)
        {
            StoryQuest s = SpeakingQuest(p);
            if (s == null)
                return;
            GameBot who = Speaker(p, s);
            bool rescue = s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase);
            StoryQuestManager.CompleteStep(p, s);
            // a last word in place of the question (its window otherwise stayed open on the answered choice)
            if (who != null && who.ObjectState == GameObject.eObjectState.Active)
                StoryDialog.Say(p, who, rescue ? $"Then it's settled. Lead on, {p.Name} - I'm right behind you." : "Right. On we go, then.",
                    "talk", null, null, bubble: false);
        }

        /// <summary>A whisper or a word to your companion during a "companion" step answers it.</summary>
        static bool AnswerByWord(GamePlayer p, string text)
        {
            StoryQuest s = SpeakingQuest(p);
            if (s == null || s.QuestId.StartsWith("companion_", StringComparison.OrdinalIgnoreCase))
                return false;
            string say = s.Step_.Say ?? "";
            foreach (System.Text.RegularExpressions.Match m in System.Text.RegularExpressions.Regex.Matches(say, @"\[([^\]]+)\]"))
                if (text.Contains(m.Groups[1].Value, StringComparison.OrdinalIgnoreCase))
                {
                    Answered(p);
                    return true;
                }
            return false;
        }

        /// <summary>The tick's part: a rescued one whose step has passed goes; one too far behind you waits.</summary>
        static void TickRescues()
        {
            foreach (var (p, bot) in _rescued.ToArray())
            {
                StoryQuest s = p.ObjectState == GameObject.eObjectState.Active ? RescueQuest(p) : null;
                if (s == null || s.Step_?.Type is not ("companion" or "encounter") || bot.ObjectState != GameObject.eObjectState.Active)
                {
                    EndRescue(p);
                    continue;
                }
                // they hold their ground at the camp (a helper with no group would go looking for its owner)
                if (s.Step_.At != null && WorldMgr.GetZone((ushort) s.Step_.Zone) is Zone z && z.ZoneRegion != null)
                {
                    Vector3 home = StoryQuestManager.ToWorld(s.Step_.Zone, s.Step_.At) + new Vector3(60, 40, 0);
                    if (bot.CurrentRegionID != z.ZoneRegion.ID || Vector2.Distance(new Vector2(bot.X, bot.Y), new Vector2(home.X, home.Y)) > 250)
                    {
                        bot.StopFollowing();
                        bot.MoveTo(z.ZoneRegion.ID, (int) home.X, (int) home.Y, (int) home.Z, bot.Heading);
                    }
                }
            }
            // the one you came for is in the fight when you get there (owner 2026-11-12: "save them from some sort of
            // mini boss") - spawned as you come near, so they aren't left alone at the camp while you're in town
            foreach (GamePlayer p in ClientService.Instance.GetPlayers())
            {
                if (_rescued.ContainsKey(p) || RescueQuest(p) is not StoryQuest s || s.Step_?.Type != "encounter" || s.Step_.At == null)
                    continue;
                if (WorldMgr.GetZone((ushort) s.Step_.Zone) is not Zone z || z.ZoneRegion == null || p.CurrentRegionID != z.ZoneRegion.ID)
                    continue;
                Vector3 at = StoryQuestManager.ToWorld(s.Step_.Zone, s.Step_.At);
                if (Vector2.Distance(new Vector2(p.X, p.Y), new Vector2(at.X, at.Y)) < 4000)
                    EnsureRescued(p, s);
            }
        }
    }
}
