using System;
using System.Collections.Generic;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Quests;

namespace DOL.GS
{
    /// <summary>Quest marker and appearance for one realm's stationary bounty giver.</summary>
    public sealed class BountyMasterNPC : GameNPC
    {
        public override eQuestIndicator GetQuestIndicator(GamePlayer player)
        {
            if (player == null || player.Realm != Realm)
                return eQuestIndicator.None;

            if (player.IsDoingQuest(typeof(BountyQuest)) is BountyQuest active)
                return active.IsReady ? eQuestIndicator.Finish : eQuestIndicator.None;

            return CanGiveQuest(typeof(BountyQuest), player) > 0
                ? eQuestIndicator.Available
                : eQuestIndicator.None;
        }
    }

    /// <summary>
    /// One Bounty Master in each zone's main settlement, handing out hunts in that zone (ZoneBounties). They are
    /// script-owned, not saved over existing village NPCs or monster spawns. Quest records, not NPC objects, own
    /// individual players' progress. A bounty is claimed at any Bounty Master of your realm. More masters are one line
    /// each in Places as each zone's review is done.
    /// </summary>
    public static class BountyMasterRuntime
    {
        private static readonly Dictionary<ushort, BountyMasterNPC> Masters = new();   // by zone

        /// <summary>The masters: realm, name, region, x, y, z, heading, model, gender. Their zone comes from where they
        /// stand.</summary>
        private static readonly (eRealm Realm, string Name, ushort Region, int X, int Y, int Z, ushort Heading, ushort Model, eGender Gender)[] Places =
        {
            // Lough Derg: Mag Mell, offset from the stable/healer clusters, on the village approach
            (eRealm.Hibernia, "Maelin Greenmantle", 200, 346750, 491480, 5200, 3416, 342, eGender.Female),
            // Connacht: Ardee, on the east side of the market (the zone brief, 2026-11-22)
            (eRealm.Hibernia, "Conn of the Hundred Hunts", 200, 342520, 469792, 5200, 1024, 337, eGender.Male),
            // Silvermine Mountains: Howth (the south town - the game names it Howth; the north one is Ardagh), on the east edge of the town (the zone brief, 2026-11-22)
            (eRealm.Hibernia, "Muirenn Trackwise", 200, 343688, 592864, 5460, 1024, 365, eGender.Female),
            // Lough Gur: Innis Carthaig, by the jetties (the zone brief, 2026-11-24)
            (eRealm.Hibernia, "Fiachna Lakewatch", 200, 333600, 719700, 4310, 1024, 337, eGender.Male),
            // the Bog of Cullen: Alainn Bin, on the north road out of town (the zone brief, 2026-11-24)
            (eRealm.Hibernia, "Roisin Bogtracker", 200, 403300, 764700, 4960, 0, 365, eGender.Female),
            // Camelot Hills: Cotswold
            (eRealm.Albion, "Dame Elowen Vale", 1, 560800, 511550, 2280, 761, 38, eGender.Female),
            // Black Mountains South: Humberton, on the west edge of the village green (Albion's plan, round 1, 2026-11-24)
            (eRealm.Albion, "Huntsman Garwyn Hale", 1, 507808, 476656, 2284, 3072, 9, eGender.Male),
            // Salisbury Plains: West Downs; Campacorentin Forest: Caer Ulfwych; Avalon Marsh: Adribard's Retreat (Albion's plan, round 2)
            (eRealm.Albion, "Outrider Gwenhael", 1, 578704, 556864, 2184, 1024, 38, eGender.Female),
            (eRealm.Albion, "Ranger Teyrnon", 1, 521808, 616512, 1800, 0, 9, eGender.Male),
            (eRealm.Albion, "Fowler Ednyfed", 1, 473632, 627520, 1744, 2048, 9, eGender.Male),
            // Black Mountains North: Swanton Keep; Cornwall: Cornwall Station; Lyonesse: the Remnant's camp (Albion's plan, round 3)
            (eRealm.Albion, "Huntress Gwenllian", 1, 511528, 382440, 7992, 1024, 38, eGender.Female),
            (eRealm.Albion, "Giant-Hunter Bran", 1, 408736, 652984, 4944, 1024, 9, eGender.Male),
            (eRealm.Albion, "Wrack-Hunter Tegen", 1, 340520, 676784, 2920, 3072, 38, eGender.Female),
            // Llyn Barfog: the Barfog merchants; Dartmoor: Grimspound (Albion's plan, round 4)
            (eRealm.Albion, "Huntsman Peredur", 1, 453592, 400240, 2088, 2048, 9, eGender.Male),
            (eRealm.Albion, "Slayer-Hunter Kyne", 1, 357056, 709320, 4964, 1024, 38, eGender.Female),
            // Mularn's zone
            (eRealm.Midgard, "Yrsa Wolfmark", 100, 804150, 724550, 4680, 2393, 218, eGender.Female),
            // East Svealand: Audliten (Midgard's plan, round 1)
            (eRealm.Midgard, "Trapper Gautr", 100, 727296, 760880, 4566, 1024, 213, eGender.Male),
            // West Svealand: Huginfel; Gotar: Fort Atla; Myrkwood: Galplen (Midgard's plan, round 2)
            (eRealm.Midgard, "Wolf-Tracker Solveig", 100, 711840, 784080, 4672, 1024, 168, eGender.Female),
            (eRealm.Midgard, "Hunter Ulfkell", 100, 749576, 815776, 4408, 2048, 213, eGender.Male),
            (eRealm.Midgard, "Beast-Slayer Thrand", 100, 797624, 893592, 4744, 2048, 213, eGender.Male),
            // Muspelheim: Brika's camp; Skona Ravine: the Stor Gothi's camp; Vanern Swamp: the Wardens' camp (Midgard's plan, round 3)
            (eRealm.Midgard, "Wyrm-Hunter Sigrid", 100, 869800, 645176, 5597, 2048, 168, eGender.Female),
            (eRealm.Midgard, "Wolf-Hunter Ozur", 100, 712728, 924800, 5039, 1024, 213, eGender.Male),
            (eRealm.Midgard, "Bog-Hunter Thorkatla", 100, 672112, 913472, 2110, 2048, 168, eGender.Female),
            // Raumarik: the trappers' camp; Malmohus: Halla's camp (Midgard's plan, round 4)
            (eRealm.Midgard, "Wolf-Slayer Ingrid", 100, 634624, 773480, 4480, 3072, 168, eGender.Female),
            (eRealm.Midgard, "Drake-Hunter Orm", 100, 728928, 987456, 2827, 2048, 213, eGender.Male),
        };

        /// <summary>Any master of a realm (the first placed), for older saved contracts.</summary>
        public static BountyMasterNPC GetMaster(eRealm realm)
        {
            foreach (BountyMasterNPC m in Masters.Values)
                if (m.Realm == realm)
                    return m;
            return null;
        }

        public static BountyMasterNPC GetMasterForZone(ushort zoneId) =>
            zoneId != 0 && Masters.TryGetValue(zoneId, out BountyMasterNPC npc) ? npc : null;

        public static ushort ZoneOf(BountyMasterNPC master) => master?.CurrentZone?.ID ?? 0;

        [ScriptLoadedEvent]
        public static void ScriptLoaded(DOLEvent e, object sender, EventArgs args)
        {
            if (!ServerProperties.Properties.LOAD_QUESTS)
                return;

            foreach (var p in Places)
                AddMaster(p.Realm, p.Name, p.Region, p.X, p.Y, p.Z, p.Heading, p.Model, p.Gender);

            GameEventMgr.AddHandler(GamePlayerEvent.AcceptQuest, AcceptQuest);
            GameEventMgr.AddHandler(GamePlayerEvent.GameEntered, PlayerEntered);
            GameEventMgr.AddHandler(GamePlayerEvent.Quit, PlayerQuit);
        }

        [ScriptUnloadedEvent]
        public static void ScriptUnloaded(DOLEvent e, object sender, EventArgs args)
        {
            GameEventMgr.RemoveHandler(GamePlayerEvent.AcceptQuest, AcceptQuest);
            GameEventMgr.RemoveHandler(GamePlayerEvent.GameEntered, PlayerEntered);
            GameEventMgr.RemoveHandler(GamePlayerEvent.Quit, PlayerQuit);

            foreach (BountyMasterNPC master in Masters.Values)
            {
                GameEventMgr.RemoveHandler(master, GameObjectEvent.Interact, TalkToMaster);
                GameEventMgr.RemoveHandler(master, GameLivingEvent.WhisperReceive, TalkToMaster);
                master.RemoveQuestToGive(typeof(BountyQuest));
                if (master.ObjectState == GameObject.eObjectState.Active)
                    master.Delete();
            }

            Masters.Clear();
        }

        public static void UpdateIndicator(GamePlayer player)
        {
            if (player == null)
                return;
            foreach (BountyMasterNPC master in Masters.Values)
                if (master.Realm == player.Realm && master.CurrentRegionID == player.CurrentRegionID)
                    player.Out.SendNPCsQuestEffect(master, master.GetQuestIndicator(player));
        }

        private static void AddMaster(eRealm realm, string name, ushort regionId, int x, int y, int z,
            ushort heading, ushort model, eGender gender)
        {
            Region region = WorldMgr.GetRegion(regionId);
            if (region == null || region.IsDisabled)
                return;

            BountyMasterNPC master = new()
            {
                Name = name,
                GuildName = "Bounty Master",
                Realm = realm,
                Gender = gender,
                Model = model,
                Size = 52,
                Level = 50,
                CurrentRegionID = regionId,
                CurrentRegion = region,
                X = x,
                Y = y,
                Z = z,
                Heading = heading,
                LoadedFromScript = true,
                MaxSpeedBase = 0,
                BodyType = (ushort)NpcTemplateMgr.eBodyType.Humanoid,
            };

            master.Flags |= GameNPC.eFlags.PEACE;
            DressMaster(master);
            if (!master.AddToWorld())
                return;

            ushort zone = ZoneOf(master);
            if (zone == 0 || Masters.ContainsKey(zone))
            {
                master.Delete();
                return;
            }
            Masters[zone] = master;
            master.AddQuestToGive(typeof(BountyQuest));
            GameEventMgr.AddHandler(master, GameObjectEvent.Interact, TalkToMaster);
            GameEventMgr.AddHandler(master, GameLivingEvent.WhisperReceive, TalkToMaster);
        }

        private static void DressMaster(BountyMasterNPC master)
        {
            GameNpcInventoryTemplate outfit = new();
            switch (master.Realm)
            {
                case eRealm.Hibernia:
                    // Celtic woodland hunter: moss-green reinforced pieces,
                    // dark cloak, and an existing in-game ranger bow.
                    outfit.AddNPCEquipment(eInventorySlot.TorsoArmor, 403, 69);
                    outfit.AddNPCEquipment(eInventorySlot.ArmsArmor, 405, 62);
                    outfit.AddNPCEquipment(eInventorySlot.LegsArmor, 404, 69);
                    outfit.AddNPCEquipment(eInventorySlot.HandsArmor, 406, 62);
                    outfit.AddNPCEquipment(eInventorySlot.FeetArmor, 407, 62);
                    outfit.AddNPCEquipment(eInventorySlot.Cloak, 57, 43);
                    outfit.AddNPCEquipment(eInventorySlot.DistanceWeapon, 471, 0);
                    master.IsCloakHoodUp = true;
                    master.VisibleActiveWeaponSlots = (byte)eInventorySlot.DistanceWeapon;
                    break;

                case eRealm.Albion:
                    // Weathered silver plate and a crimson field cloak.
                    outfit.AddNPCEquipment(eInventorySlot.TorsoArmor, 713, 0);
                    outfit.AddNPCEquipment(eInventorySlot.ArmsArmor, 715, 0);
                    outfit.AddNPCEquipment(eInventorySlot.LegsArmor, 714, 0);
                    outfit.AddNPCEquipment(eInventorySlot.HandsArmor, 716, 0);
                    outfit.AddNPCEquipment(eInventorySlot.FeetArmor, 717, 0);
                    outfit.AddNPCEquipment(eInventorySlot.Cloak, 4105, 27);
                    outfit.AddNPCEquipment(eInventorySlot.RightHandWeapon, 67, 0);
                    master.VisibleActiveWeaponSlots = 16;
                    break;

                case eRealm.Midgard:
                    // Fur-trimmed dark studded gear and a northern hunter's bow.
                    outfit.AddNPCEquipment(eInventorySlot.TorsoArmor, 250, 19);
                    outfit.AddNPCEquipment(eInventorySlot.ArmsArmor, 252, 19);
                    outfit.AddNPCEquipment(eInventorySlot.LegsArmor, 251, 19);
                    outfit.AddNPCEquipment(eInventorySlot.HandsArmor, 253, 19);
                    outfit.AddNPCEquipment(eInventorySlot.FeetArmor, 254, 19);
                    outfit.AddNPCEquipment(eInventorySlot.Cloak, 326, 32);
                    outfit.AddNPCEquipment(eInventorySlot.DistanceWeapon, 564, 0);
                    master.VisibleActiveWeaponSlots = (byte)eInventorySlot.DistanceWeapon;
                    break;
            }

            master.Inventory = outfit.CloseTemplate();
            master.InitializeActiveWeaponFromInventory();
        }

        private const string OfferedDifficultyKey = "BountyOfferedDifficulty";
        private const string OfferedZoneKey = "BountyOfferedZone";
        private const string OfferedEventKey = "BountyOfferedEvent";

        /// <summary>The event bounty last offered (a chain id), or null; read once when the quest is accepted.</summary>
        internal static string TakeOfferedEvent(GamePlayer player)
        {
            if (player == null)
                return null;
            string id = player.TempProperties.GetProperty<string>(OfferedEventKey);
            player.TempProperties.RemoveProperty(OfferedEventKey);
            return id;
        }
        private const string RerollDifficultyKey = "BountyRerollDifficulty";
        private const string UpdateDifficultyKey = "BountyUpdateDifficulty";

        /// <summary>The size last offered by a Bounty Master; read once when the quest is accepted.</summary>
        internal static BountyDifficulty TakeOfferedDifficulty(GamePlayer player) => TakeDifficulty(player, OfferedDifficultyKey);

        /// <summary>The zone of the Bounty Master who made the offer; read once when the quest is accepted.</summary>
        internal static ushort TakeOfferedZone(GamePlayer player)
        {
            if (player == null)
                return 0;
            ushort zone = player.TempProperties.GetProperty<ushort>(OfferedZoneKey);
            player.TempProperties.RemoveProperty(OfferedZoneKey);
            return zone;
        }

        private static BountyDifficulty TakeDifficulty(GamePlayer player, string key)
        {
            if (player == null)
                return BountyDifficulty.Normal;
            BountyDifficulty difficulty = player.TempProperties.GetProperty(key, BountyDifficulty.Normal);
            player.TempProperties.RemoveProperty(key);
            return difficulty;
        }

        private static string Lower(BountyDifficulty size) => ZoneBounties.SizeName(size).ToLowerInvariant();

        private static string Bulbs(BountyDifficulty difficulty, bool rerolled)
        {
            int bulbs = BountyDifficultyRules.Bulbs(difficulty, rerolled);
            return $"{bulbs} XP bulb{(bulbs == 1 ? "" : "s")}";
        }

        private static string ZoneName(BountyMasterNPC master) => master?.CurrentZone?.Description ?? "these lands";

        private static void TalkToMaster(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is not BountyMasterNPC master || args is not SourceEventArgs source ||
                source.Source is not GamePlayer player || player.Realm != master.Realm ||
                !master.IsWithinRadius(player, 600))
                return;

            BountyQuest active = player.IsDoingQuest(typeof(BountyQuest)) as BountyQuest;
            if (e == GameObjectEvent.Interact)
            {
                string swap = active?.CanSwapToZone == true
                    ? $" Your contract is from the old realm-wide ledger: [swap bounty] to trade it, free, for a hunt in {ZoneName(master)}."
                    : string.Empty;
                if (active == null)
                {
                    var live = ZoneBounties.LiveEvent(master.CurrentZone);
                    string ev = live != null
                        ? $" And {live.Def.Title} is under way right now: take an [event bounty] to help there."
                        : string.Empty;
                    master.SayTo(player, $"I keep {ZoneName(master)}'s ledger of those who threaten our folk. Take a [solo bounty], " +
                        "a [small group bounty] for two to four of you, or a [large group bounty] for a full group. " +
                        "Whatever your level, I pay at it when you return. Or ask [how bounties work]." + ev);
                }
                else if (active.IsReady)
                {
                    master.SayTo(player, $"You have felled {active.Target?.Name}. Choose [claim reward] to close the ledger. " +
                        "Your target remains marked on its local map until you do. You may also [show location] or [reroll] at half pay." + swap);
                }
                else
                {
                    master.SayTo(player, $"Your mark is {active.Target?.Name} in {active.Target?.ZoneName}: " +
                        $"{active.Progress}/{active.RequiredKills} slain. Ask to [show location], or [reroll] for another target at half pay." + swap);
                }
                return;
            }

            if (e != GameLivingEvent.WhisperReceive || args is not WhisperReceiveEventArgs whisper)
                return;

            string text = whisper.Text.Trim().ToLowerInvariant();
            switch (text)
            {
                case "a bounty":
                case "take a bounty":
                case "bounty":
                    OfferBounty(master, player, active, BountyDifficulty.Normal);
                    return;

                case "event bounty":
                    OfferEventBounty(master, player, active);
                    return;

                case "how bounties work":
                    master.SayTo(player, $"Every hunt is in {ZoneName(master)}. A solo hunt is 8 greens, 6 blues or 3 yellows. " +
                        "A small group hunts 8 yellows or two of the oranges, the lieutenants. A large group goes after a red camp boss " +
                        "or something worse. Bring friends or bots for the bigger ones; the con colours mean the same whatever your level.");
                    master.SayTo(player, "I pay at your level when you claim, so a hunt is never wasted however long it takes: " +
                        "2, 4 or 8 XP bulbs, 1-3 class items a little above your level, and 1, 3 or 8 Marks of Valor. " +
                        "At level 50 the experience becomes gold, and a large group's hunt pays exceptional gear.");
                    master.SayTo(player, "The journal counts kills; anyone in your group who is near counts. Press BOUNTY MAP for the " +
                        "red dot on the zone's map. A reroll keeps the size or picks a smaller one, and pays half until you finish. " +
                        "You can claim at any Bounty Master of the realm.");
                    return;

                case "show location":
                    if (active != null)
                    {
                        active.ShowMarker();
                        master.SayTo(player, $"Seek {active.Target?.Name} in {active.Target?.ZoneName}. " +
                            "Open that zone's local map to see the red bounty dot. " +
                            "The journal's BOUNTY MAP button opens your current map; /bountylocation refreshes the marker.");
                    }
                    return;

                case "reroll":
                    if (active == null)
                        return;
                    if (!active.IsZone)
                    {
                        AskReroll(player, active, active.Difficulty);
                        return;
                    }
                    master.SayTo(player, active.Difficulty switch
                    {
                        BountyDifficulty.VeryHard => "Reroll to which hunt? [reroll large group], [reroll small group] or [reroll solo]. It pays half of the one you choose.",
                        BountyDifficulty.Hard => "Reroll to which hunt? [reroll small group] or [reroll solo]. It pays half of the one you choose.",
                        _ => "Reroll for another solo hunt? [reroll solo]. It pays half."
                    });
                    return;

                case "swap bounty":
                case "update bounty":
                    if (active?.CanSwapToZone == true)
                        master.SayTo(player, $"Trade your old contract, free, for a hunt in {ZoneName(master)}: " +
                            "[swap solo], [swap small group] or [swap large group]. Your current kill progress is replaced.");
                    return;

                case "claim reward":
                case "reward":
                    if (active?.IsReady == true)
                    {
                        active.QuestGiver = master;
                        active.Claim();
                    }
                    return;
            }

            BountyDifficulty choice;
            if (text.EndsWith(" bounty") && ZoneBounties.TryParseSize(text[..^" bounty".Length], out choice))
                OfferBounty(master, player, active, choice);
            else if (text.StartsWith("reroll ") && ZoneBounties.TryParseSize(text["reroll ".Length..], out choice))
            {
                if (active != null && choice <= active.Difficulty)
                    AskReroll(player, active, choice);
            }
            else if ((text.StartsWith("swap ") || text.StartsWith("update ")) &&
                     ZoneBounties.TryParseSize(text[(text.IndexOf(' ') + 1)..], out choice))
            {
                if (active?.CanSwapToZone == true)
                {
                    player.TempProperties.SetProperty(UpdateDifficultyKey, choice);
                    player.Out.SendCustomDialog($"Trade your old bounty for a new {Lower(choice)} hunt in {ZoneName(master)}, free of penalty? " +
                        "Your current kill progress will be lost.", ConfirmUpdate);
                }
            }
        }

        private static void OfferBounty(BountyMasterNPC master, GamePlayer player, BountyQuest active, BountyDifficulty size)
        {
            if (active != null || master.CanGiveQuest(typeof(BountyQuest), player) <= 0)
                return;

            player.TempProperties.SetProperty(OfferedDifficultyKey, size);
            player.TempProperties.SetProperty(OfferedZoneKey, ZoneOf(master));
            player.TempProperties.RemoveProperty(OfferedEventKey);

            string what = size switch
            {
                BountyDifficulty.VeryHard => "a red camp boss or worse, for a full group",
                BountyDifficulty.Hard => "yellows in number or the oranges, for two to four",
                _ => "greens, blues or a few yellows, for one"
            };
            string pay = player.Level >= 50
                ? $"{ZoneBounties.CapGold(size, false)} gold, 1-3 {(size == BountyDifficulty.VeryHard ? "exceptional " : "")}class items"
                : $"{Bulbs(size, false)} at your level, 1-3 level {BountyDifficultyRules.GearLevel((byte)player.Level, size)} class items";
            string offer = $"Accept a {Lower(size)} hunt in {ZoneName(master)}? It points at {what}; the journal tracks kills. " +
                $"Return for {pay} and {ZoneBounties.Marks(size, false)} Marks of Valor, paid at your level when you claim. " +
                "The red dot appears on the zone's map.";
            player.Out.SendQuestSubscribeCommand(master, QuestMgr.GetIDForQuestType(typeof(BountyQuest)), offer);
        }

        private static void OfferEventBounty(BountyMasterNPC master, GamePlayer player, BountyQuest active)
        {
            if (active != null || master.CanGiveQuest(typeof(BountyQuest), player) <= 0)
                return;
            var live = ZoneBounties.LiveEvent(master.CurrentZone);
            if (live == null)
            {
                master.SayTo(player, "Nothing is stirring out there right now. Ask me again when you hear of trouble.");
                return;
            }
            player.TempProperties.SetProperty(OfferedDifficultyKey, BountyDifficulty.Hard);
            player.TempProperties.SetProperty(OfferedZoneKey, ZoneOf(master));
            player.TempProperties.SetProperty(OfferedEventKey, live.Def.Id);
            string offer = $"Accept an event bounty? Help with {live.Def.Title}: slay {ZoneBounties.EventKills} of its monsters " +
                "(a boss counts 3). It pays as a small group's hunt, at your level when you claim: " +
                $"{Bulbs(BountyDifficulty.Hard, false)}, 1-3 class items and {ZoneBounties.Marks(BountyDifficulty.Hard, false)} Marks of Valor.";
            player.Out.SendQuestSubscribeCommand(master, QuestMgr.GetIDForQuestType(typeof(BountyQuest)), offer);
        }

        private static void AskReroll(GamePlayer player, BountyQuest active, BountyDifficulty difficulty)
        {
            player.TempProperties.SetProperty(RerollDifficultyKey, difficulty);
            player.Out.SendCustomDialog(active.IsZone
                    ? $"Choose a different {Lower(difficulty)} hunt? This bounty will pay only half ({Bulbs(difficulty, true)}), even after further rerolls."
                    : active.AssignedLevel == 50
                    ? "Choose a different great foe? Level-50 gold and equipment rewards are unchanged."
                    : $"Choose a different monster? This bounty will pay only {BountyDifficultyRules.Bulbs(difficulty, true)} XP bulbs " +
                      "at its assigned level, even after further rerolls.",
                ConfirmReroll);
        }

        private static void ConfirmReroll(GamePlayer player, byte response)
        {
            BountyDifficulty difficulty = TakeDifficulty(player, RerollDifficultyKey);
            if (response != 0x01 || player?.IsDoingQuest(typeof(BountyQuest)) is not BountyQuest quest ||
                !NearOwnMaster(player, out _))
                return;
            quest.Reroll(difficulty);
        }

        private static void ConfirmUpdate(GamePlayer player, byte response)
        {
            BountyDifficulty difficulty = TakeDifficulty(player, UpdateDifficultyKey);
            if (response != 0x01 || player?.IsDoingQuest(typeof(BountyQuest)) is not BountyQuest quest ||
                !NearOwnMaster(player, out BountyMasterNPC master))
                return;
            quest.SwapToZone(ZoneOf(master), difficulty);
        }

        /// <summary>The nearest Bounty Master of the player's realm within talking range, if any.</summary>
        private static bool NearOwnMaster(GamePlayer player, out BountyMasterNPC master)
        {
            master = null;
            if (player == null)
                return false;
            foreach (BountyMasterNPC m in Masters.Values)
                if (m.Realm == player.Realm && m.CurrentRegionID == player.CurrentRegionID && m.IsWithinRadius(player, 600))
                {
                    master = m;
                    return true;
                }
            return false;
        }

        private static void AcceptQuest(DOLEvent e, object sender, EventArgs args)
        {
            if (e != GamePlayerEvent.AcceptQuest || args is not QuestEventArgs accepted ||
                QuestMgr.GetQuestTypeForID(accepted.QuestID) != typeof(BountyQuest) ||
                !NearOwnMaster(accepted.Player, out BountyMasterNPC master) ||
                accepted.Player.IsDoingQuest(typeof(BountyQuest)) != null ||
                master.CanGiveQuest(typeof(BountyQuest), accepted.Player) <= 0)
                return;

            master.GiveQuest(typeof(BountyQuest), accepted.Player, 1);
        }

        private static void PlayerEntered(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is GamePlayer player && player.IsDoingQuest(typeof(BountyQuest)) is BountyQuest quest)
            {
                quest.QuestGiver = (quest.IsZone ? GetMasterForZone(quest.ZoneId) : null) ?? GetMaster(player.Realm);
                quest.NormalizeLegacyOnLogin();
                quest.ShowMarker();
                UpdateIndicator(player);
            }
        }

        private static void PlayerQuit(DOLEvent e, object sender, EventArgs args)
        {
            if (sender is GamePlayer player)
                BountyMapMarkers.Clear(player);
        }
    }
}
