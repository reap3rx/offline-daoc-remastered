using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Reputation;

namespace DOL.GS.EasterEggs
{
    /// <summary>
    /// Two small easter eggs from the zone briefs (owner 2026-11-22: "easter eggs in each zone ... smaller ones (like talking to
    /// someone, finding something, it doesn't matter, anything that seems unique or interesting)"):
    ///   - the Valley of Bri Leith: on Moon Lake's shore at night a scarlet fly sometimes finds you and follows. Stand still
    ///     and it lands on your hand, and leaves you a Wing of Etain (a keepsake: use it and you remember a hall that was
    ///     never yours) - once per character.
    ///   - Shannon Estuary: sit by Connla's Well at dawn and a hazelnut may fall on your head. Eat it, and for an hour you
    ///     understand the gulls.
    ///   - the Cliffs of Moher (claude 2026-11-24, the zone brief): stand still on the highest of the western cliffs, in the
    ///     Grey Man's fog, and sometimes you meet your own fetch. It walks to the edge, looks back, and leaves you the
    ///     Fetch's Penny - once per character. Flip it: it always comes up "not today".
    /// One timer looks at the players in Hibernia's region now and then; the items are made at start from a novelty bottle.
    /// </summary>
    public static class ZoneEggs
    {
        public const ushort Region = 200;
        public const string WingId = "egg_wing_of_etain", HazelId = "egg_hazelnut_of_connla", PennyId = "egg_fetch_s_penny";
        public const string CombId = "egg_aine_s_comb", TorcId = "egg_cullen_gold_torc";
        const string WingKey = "_egg_wing_of_etain", PennyKey = "_egg_fetch_s_penny", CombKey = "_egg_aine_s_comb", TorcKey = "_egg_cullen_gold_torc";
        const int TickMs = 10_000;

        // Moon Lake (Bri Leith 206: zone at 385024, 483328), its middle and the shore's ring (metres)
        const int BriX = 385024, BriY = 483328;
        static readonly (double x, double y) Lake = (1360, 1360);
        const double ShoreIn = 0, ShoreOut = 240;          // (the lake and its banks: the fly comes out over the water)
        // Connla's Well (Shannon 202: zone at 286720, 614400)
        const int ShaX = 286720, ShaY = 614400;
        static readonly (double x, double y) Well = (1350, 680);
        const double WellR = 160;
        // the highest of the western cliffs (Cliffs of Moher 203: zone at 221184, 417792): the south-west headland, ~205 m
        // over the sea, inside the sea-fog
        const int MohX = 221184, MohY = 417792;
        static readonly (double x, double y) Headland = (120, 1585);
        const double HeadlandR = 45;
        // Lough Gur 204 (zone at 286720, 679936): the east shore below Aine's Circle, at dawn - a woman combing her hair (owner
        // 2026-11-24, the zone brief: "Aine's Comb. Once per character")
        const int GurX = 286720, GurY = 679936;
        static readonly (double x, double y) CombShore = (1182, 884);
        const double CombR = 40;
        // the Bog of Cullen 205 (zone at 352256, 712704): a lone bog-light in the eastern bog at night that neither flees nor
        // fights - stand with it, and it shows you a hoard (the zone brief: "a Cullen Gold Torc. Once per character")
        const int CulX = 352256, CulY = 712704;
        static readonly (double x, double y) LoneLight = (1380, 560);
        const double LoneR = 35;

        sealed class Seen
        {
            public long FlySince;            // when the fly found them (0: it hasn't)
            public int StillX, StillY;       // where they stood when it found them
            public long StillSince;
            public long GullsUntil;
            public long NextGull;
            public long NextNut;
            public long FetchSince;          // when they were still on the headland (0: not)
            public int FetchX, FetchY;
            public long NextFetch;
            public long StandSince;          // Aine's shore, the lone light: still since (0: not there)
            public int StandX, StandY;
            public long NextStand;
        }

        static readonly ConcurrentDictionary<GamePlayer, Seen> _seen = new();

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                Ensure(WingId, "Wing of Etain", "A single scarlet wing, longer than your hand and warm as one. Use it, and remember.", 0);
                Ensure(HazelId, "Hazelnut of Connla's Well", "One of the nine hazels' nuts, fallen into the well. They say whoever eats one knows things. Eat it.", 1);
                Ensure(PennyId, "The Fetch's Penny", "A cold copper penny, worn smooth on both sides. Your fetch gave it to you on the cliffs of Moher. Flip it.", 0);
                Ensure(CombId, "Aine's Comb", "A comb of pale gold, left on the stones of Lough Gur at dawn. Its owner wasn't there when you got close. Use it.", 0);
                Ensure(TorcId, "Cullen Gold Torc", "A torc of old red gold out of the Bog of Cullen, three thousand years buried. A light showed you where. Use it.", 0);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ZoneEggs] " + ex.Message);
            }
            _ = new ECSGameTimer(null, _ => { Tick(); return TickMs; }, 20_000);
        }

        static void Ensure(string id, string name, string words, long price)
        {
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(id) != null ||
                GameServer.Database.FindObjectByKey<DbItemTemplate>("novelty_glow") is not DbItemTemplate from)
                return;
            var t = (DbItemTemplate) from.Clone();
            t.Id_nb = id;
            t.Name = name;
            t.Description = words;
            t.Price = price;
            t.IsTradable = false;
            t.AllowAdd = true;
            GameServer.Database.AddObject(t);
        }

        // ------------------------------------------------------------------ the rules (pure: tested)

        public static double Dist((double x, double y) a, (double x, double y) b) => Math.Sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));

        /// <summary>On Moon Lake's shore (zone metres): not in the middle, not far off.</summary>
        public static bool OnShore(double mx, double my) { double d = Dist((mx, my), Lake); return d >= ShoreIn && d <= ShoreOut; }

        public static bool AtWell(double mx, double my) => Dist((mx, my), Well) <= WellR;

        public static bool OnHeadland(double mx, double my) => Dist((mx, my), Headland) <= HeadlandR;

        public static bool OnAinesShore(double mx, double my) => Dist((mx, my), CombShore) <= CombR;

        public static bool ByTheLoneLight(double mx, double my) => Dist((mx, my), LoneLight) <= LoneR;

        /// <summary>Dawn by the game's clock (ms into the day): five to eight.</summary>
        public static bool Dawn(uint ms) => ms >= 5 * 3_600_000u && ms < 8 * 3_600_000u;

        public static readonly string[] Gulls =
        {
            "A gull overhead: \"Fish. FISH. Mine. MINE.\"",
            "Two gulls on a post: \"He's got bread.\" \"He hasn't got bread.\" \"He's got the LOOK of bread.\"",
            "A gull, to nobody: \"The eriu are fishing above the ford again. Nobody ever listens to me.\"",
            "A gull, very old: \"The well rose before. It'll rise again. Keep your feet dry and your beak shut.\"",
            "A gull, delighted: \"Somebody dropped a pie on the quay at Connla! A whole pie!\"",
            "Gulls, all together: \"MINE. MINE. MINE.\""
        };

        // ------------------------------------------------------------------ the timer

        static void Tick()
        {
            try
            {
                Region r = WorldMgr.GetRegion(Region);
                if (r == null)
                    return;
                long now = GameLoop.GameLoopTime;
                bool night = r.IsNightTime;
                bool dawn = Dawn(WorldMgr.GetCurrentGameTime());
                foreach (GamePlayer p in ClientService.Instance.GetPlayers())
                {
                    if (p == null || p.CurrentRegionID != Region || !p.IsAlive)
                        continue;
                    Seen s = _seen.GetOrAdd(p, _ => new Seen());
                    Gull(p, s, now);
                    double bx = (p.X - BriX) / 40.0, by = (p.Y - BriY) / 40.0;
                    if (night && bx is >= 0 and < 1638 && by is >= 0 and < 1638)
                        Fly(p, s, now, bx, by);
                    else
                        s.FlySince = 0;
                    double sx = (p.X - ShaX) / 40.0, sy = (p.Y - ShaY) / 40.0;
                    if (dawn && sx is >= 0 and < 1638 && sy is >= 0 and < 1638 && AtWell(sx, sy))
                        Nut(p, s, now);
                    double cx = (p.X - MohX) / 40.0, cy = (p.Y - MohY) / 40.0;
                    if (cx is >= 0 and < 1638 && cy is >= 0 and < 1638 && OnHeadland(cx, cy))
                        Fetch(p, s, now);
                    else
                        s.FetchSince = 0;
                    double gx = (p.X - GurX) / 40.0, gy = (p.Y - GurY) / 40.0, ux = (p.X - CulX) / 40.0, uy = (p.Y - CulY) / 40.0;
                    if (dawn && gx is >= 0 and < 1638 && gy is >= 0 and < 1638 && OnAinesShore(gx, gy))
                        Stand(p, s, now, CombKey, CombId,
                            "At the water's edge a woman is sitting on a stone, combing her long hair, and the comb catches the dawn. You come closer - and the stone is empty, and the lake is very still, and on the stone lies the comb. (Aine's Comb)");
                    else if (night && ux is >= 0 and < 1638 && uy is >= 0 and < 1638 && ByTheLoneLight(ux, uy))
                        Stand(p, s, now, TorcKey, TorcId,
                            "A single bog-light hangs in front of you, not fleeing, not coming on. It drifts away a few paces, stops, waits. You follow it off the path - and it sinks into the turf at your feet and goes out. When you dig, there's gold. (Cullen Gold Torc)");
                    else
                        s.StandSince = 0;
                }
                foreach (GamePlayer gone in _seen.Keys)
                    if (gone.ObjectState != GameObject.eObjectState.Active)
                        _seen.TryRemove(gone, out _);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ZoneEggs] " + ex.Message);
            }
        }

        static void Fly(GamePlayer p, Seen s, long now, double mx, double my)
        {
            ReputationService.Standing st = ReputationService.Of(p);
            if (st == null || st.Get(WingKey) > 0 || !OnShore(mx, my))
            {
                s.FlySince = 0;
                return;
            }
            if (s.FlySince == 0)
            {
                if (!Util.Chance(8))                            // (about one ten-second look in twelve)
                    return;
                s.FlySince = now;
                s.StillX = p.X; s.StillY = p.Y; s.StillSince = now;
                p.Out.SendMessage("A scarlet fly the size of a sparrow comes out of the dark over the water and circles you, very close.",
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                return;
            }
            if (Math.Abs(p.X - s.StillX) > 60 || Math.Abs(p.Y - s.StillY) > 60)
            {
                s.StillX = p.X; s.StillY = p.Y; s.StillSince = now;
                if (now - s.FlySince > 120_000)
                {
                    s.FlySince = 0;
                    p.Out.SendMessage("The scarlet fly loses interest and goes back out over the lake.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                }
                else
                    p.Out.SendMessage("The scarlet fly follows you, keeping just out of reach.", eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return;
            }
            if (now - s.StillSince < 20_000)
                return;
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(WingId) is not DbItemTemplate t)
                return;
            if (!p.Inventory.AddTemplate(GameInventoryItem.Create(t), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                return;
            lock (st.Sync)
            {
                st.Points[WingKey] = 1;
                st.Dirty = true;
            }
            ReputationService.Save(p);
            s.FlySince = 0;
            p.Out.SendMessage("The scarlet fly lands on your hand. For a heartbeat you see a golden hall under a hill, and a man with yellow hair turning to look at you - then it's gone, and in your palm is a single scarlet wing. (Wing of Etain)",
                eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        static void Nut(GamePlayer p, Seen s, long now)
        {
            if (now < s.NextNut)
                return;
            s.NextNut = now + 600_000;                          // (a look every ten minutes at most)
            if (!Util.Chance(25) || GameServer.Database.FindObjectByKey<DbItemTemplate>(HazelId) is not DbItemTemplate t)
                return;
            if (p.Inventory.AddTemplate(GameInventoryItem.Create(t), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                p.Out.SendMessage("Plink. A hazelnut falls out of nowhere and bounces off your head. It's warm, and it smells of the well. (Hazelnut of Connla's Well)",
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        static void Fetch(GamePlayer p, Seen s, long now)
        {
            if (s.FetchSince == 0 || Math.Abs(p.X - s.FetchX) > 60 || Math.Abs(p.Y - s.FetchY) > 60)
            {
                s.FetchSince = now;
                s.FetchX = p.X; s.FetchY = p.Y;
                return;
            }
            if (now - s.FetchSince < 30_000 || now < s.NextFetch)
                return;
            s.NextFetch = now + 300_000;                        // (a look every five minutes of standing there)
            ReputationService.Standing st = ReputationService.Of(p);
            if (st == null || st.Get(PennyKey) > 0 || !Util.Chance(35))
                return;
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(PennyId) is not DbItemTemplate t)
                return;
            if (!p.Inventory.AddTemplate(GameInventoryItem.Create(t), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                return;
            lock (st.Sync)
            {
                st.Points[PennyKey] = 1;
                st.Dirty = true;
            }
            ReputationService.Save(p);
            p.Out.SendMessage("Someone comes out of the fog beside you. Your face, your walk, your gear - but grey, all of it, like a drawing in ash. It goes to the very edge and looks down at the sea for a long moment. Then it looks back at you, presses something cold into your hand, and walks away along the edge into the fog, and is gone. (The Fetch's Penny)",
                eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        /// <summary>Stood still in the place for half a minute: a chance, every five minutes, at the place's gift - once per character.</summary>
        static void Stand(GamePlayer p, Seen s, long now, string key, string id, string words)
        {
            if (s.StandSince == 0 || Math.Abs(p.X - s.StandX) > 60 || Math.Abs(p.Y - s.StandY) > 60)
            {
                s.StandSince = now;
                s.StandX = p.X; s.StandY = p.Y;
                return;
            }
            if (now - s.StandSince < 30_000 || now < s.NextStand)
                return;
            s.NextStand = now + 300_000;
            ReputationService.Standing st = ReputationService.Of(p);
            if (st == null || st.Get(key) > 0 || !Util.Chance(35))
                return;
            if (GameServer.Database.FindObjectByKey<DbItemTemplate>(id) is not DbItemTemplate t)
                return;
            if (!p.Inventory.AddTemplate(GameInventoryItem.Create(t), 1, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
                return;
            lock (st.Sync)
            {
                st.Points[key] = 1;
                st.Dirty = true;
            }
            ReputationService.Save(p);
            p.Out.SendMessage(words, eChatType.CT_Important, eChatLoc.CL_SystemWindow);
        }

        public static readonly string[] Flips =
        {
            "You flip the penny. It comes down worn-side up. Not today.",
            "You flip the penny. It lands on its edge, wobbles, and falls the way it always falls. Not today.",
            "You flip the penny. Somewhere very far off, a gull laughs. Not today.",
            "You flip the penny. It's cold enough to sting. Not today - but it's thinking about it."
        };

        static void Gull(GamePlayer p, Seen s, long now)
        {
            if (s.GullsUntil <= now || now < s.NextGull)
                return;
            s.NextGull = now + 150_000 + Util.Random(0, 120_000);
            p.Out.SendMessage(Gulls[Util.Random(0, Gulls.Length - 1)], eChatType.CT_Say, eChatLoc.CL_ChatWindow);
        }

        // ------------------------------------------------------------------ using them (LootUses.TryUse)

        public static bool TryUse(GamePlayer p, DbInventoryItem item)
        {
            if (item?.Id_nb == WingId)
            {
                p.Out.SendMessage("You turn the scarlet wing in the light. Somewhere under a hill, a harp is playing, and somebody is waiting.",
                    eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return true;
            }
            if (item?.Id_nb == CombId)
            {
                p.Out.SendMessage("You draw Aine's comb through your hair. For a moment the whole world is very still, and very bright, and you are the loveliest thing in it.",
                    eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return true;
            }
            if (item?.Id_nb == TorcId)
            {
                p.Out.SendMessage("You turn the old torc in your hands. It's warm. Somewhere under the bog, a king who wore it three thousand years ago turns over in his sleep.",
                    eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return true;
            }
            if (item?.Id_nb == PennyId)
            {
                p.Out.SendMessage(Flips[Util.Random(0, Flips.Length - 1)], eChatType.CT_System, eChatLoc.CL_SystemWindow);
                return true;
            }
            if (item?.Id_nb == HazelId)
            {
                Seen s = _seen.GetOrAdd(p, _ => new Seen());
                s.GullsUntil = GameLoop.GameLoopTime + 3_600_000;
                s.NextGull = GameLoop.GameLoopTime + 20_000;
                p.Inventory.RemoveCountFromStack(item, 1);
                p.Out.SendMessage("You crack the hazelnut and eat it. The world goes very clear for a moment - and the gulls' crying turns into words.",
                    eChatType.CT_Important, eChatLoc.CL_SystemWindow);
                return true;
            }
            return false;
        }
    }
}
