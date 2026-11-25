using System.Collections.Generic;

namespace DOL.GS.DynamicEvents
{
    /// <summary>
    /// Midgard's two campaigns (claude 2026-11-25, "Midgard - the plan", round 4: "Raumarik and Malmohus - Elite, campaign + raid").
    /// The same campaign as Albion's (AlbionCampaign.cs: four posts, held for thirty minutes or the enemy strikes back, then the
    /// raid; won, the zone is the host's for four hours), with Midgard's realm, soldiers and words:
    ///   - the King's March (Raumarik, the west thread's end): only Huscarl-Marshal Hallvard at the trappers' camp starts it, for a
    ///     player of level 45 or more; four posts west across the north (rk_cpN_assault) - the Icestrider Fells, the Wraith Moor,
    ///     the Winterwolf Run, the Fenrir Camp - then Hati's Howe (rk_hatis_howe: Hati, the wolf that hunts the moon, HatiRaid.cs).
    ///     Won, the endless-winter mist lifts off Raumarik.
    ///   - the Dragon-Oath (Malmohus, the south thread's end): only Volva Groa, come south from Myrkwood with the other half of the
    ///     dragon's name, starts it at Halla's camp, for a player of level 50 or more; four posts down to the temple (mh_cpN_assault)
    ///     - the Missionary Road, the Svartalf Foist, the Armguard Lines, the Temple Steps - then the Wyrm-Temple (mh_wyrm_temple:
    ///     the Drakulv Hierophant, HierophantRaid.cs). Won, the temple smoke lifts - and Gjalpinulva's lair is open: she can be
    ///     fought (sealed under Malmohus otherwise: MidGjalpinulva.cs, the bots' realm raids).
    /// </summary>
    public static class MidgardCampaigns
    {
        public const int SoldierTemplate = 60157473;                     // Midgard's guards (the Svasud look, as round 1's huscarls)
        public const string SoldierEquipment = "SvasudGuard";

        public static readonly AlbionCampaign Winter = new()
        {
            Key = "winter", Title = "The King's March", Guild = "King Eirik's Host", Enemy = "Hati's host", Prefix = "rk_cp",
            RaidChain = "rk_hatis_howe", LiftKey = "raumarik", StateFile = "winter-campaign-state.json", Word = "for the King",
            Zone = 108, MinLevel = 45, Region = 100, Side = eRealm.Midgard, SoldierTemplate = MidgardCampaigns.SoldierTemplate, SoldierEquipment = MidgardCampaigns.SoldierEquipment,
            HostFaction = "kings_host", RaidPlaceName = "Hati's Howe", WhereName = "Raumarik", EnemyIsOne = true,
            Names = new[] { "the trappers' camp", "the Icestrider Fells", "the Wraith Moor", "the Winterwolf Run", "the Fenrir Camp" },
            Posts = new[]
            {
                null, new[] { 1300.0, 471.0, 111.7 }, new[] { 850.0, 650.0, 133.2 }, new[] { 650.0, 1100.0, 127.6 }, new[] { 450.0, 800.0, 119.2 }
            },
            HeldSites = new[]
            {
                new string[0],
                new[] { "cp1_garrison", "cp1_fells" },
                new[] { "cp2_garrison", "cp2_moor" },
                new[] { "cp3_garrison", "cp3_run", "moon_hunt" },
                new[] { "cp4_garrison", "cp4_camp" }
            },
            Seat = new[] { 320.0, 600.0, 124.6 },
            MarshalName = "Huscarl-Marshal Hallvard", MarshalGuild = "Marshal of the King's March", MarshalAt = new[] { 1110.0, 880.0, 112.0, 3072 },
            MarshalModel = 160, SoldierModel = 160,
            MarshalGreet = "Hati waits in his howe in the west, watching the moon run. When it runs close enough, he catches it - and the long winter comes down on " +
                           "all of Midgard. His host holds the north: the fells, the moor, the run, the Fenrir camp. King Eirik's Host takes them back one at a time, " +
                           "then the howe. It all goes back if we stop. Will you give the word? Say [for the King].",
            MarshalShout = "Horns! The King's March! Up onto the fells - and no one turns back!",
            CaptainName = "Banner-Huscarl of the King", SpearName = "huscarl of the King", ArcherName = "bowman of the King",
            TooLow = "Hati's host would have your bones before the first fell. Come back at level {0}, and the King's Host will march behind you.",
            Marching = "The King's March is already in the north. Go and join it.",
            NoOne = "No one went up onto the fells. The King's Host stands down at the trappers' camp.",
            Victorious = "Hati is broken at his howe! The King's Host holds Raumarik, the winter mist is lifting, and the moon runs free tonight.",
            Expired = "The mist comes back down over Raumarik, fell by fell. Hati's host has gathered again, and the King must march again.",
            PushedOut = "The King's Host has been driven out of Raumarik. It falls back on the trappers' camp.",
            CounterWord = "Hati's host strikes back at {0}!", HeldWord = "Holding {0} - {1} in {2}",
            Started = "The King's March is on in Raumarik! {0} has Hallvard's word. The Banner-Huscarl forms up for the Icestrider Fells - every sword is wanted.",
            Camp = () => new()
            {
                new SiegeNpcDef
                {
                    Kind = "marks", Name = "Quartermaster Ragnhild of the March", Guild = "King Eirik's Host", Model = 168, Pos = new[] { -6.0, 4.0 },
                    Greet = "Hati's own howe, and a King's huscarl standing in it. Marks of Valor, and the March's best - take it before the winter comes back.",
                    Stock = new()
                    {
                        new SiegeStockDef { Item = "rk108_mantle_of_the_king_s_march", Price = 260 },
                        new SiegeStockDef { Item = "rk108_moon_warden_s_torc", Price = 240 },
                        new SiegeStockDef { Item = "rk108_girdle_of_the_long_winter", Price = 220 },
                        new SiegeStockDef { Item = "rk108_ring_of_the_free_moon", Price = 220 },
                        new SiegeStockDef { Item = "rk108_winterwolf_hide_bracer_of_the_march", Price = 200 },
                        new SiegeStockDef { Item = "rk108_hati_s_fang_jewel", Price = 200 },
                    }
                },
                new SiegeNpcDef
                {
                    Kind = "idle", Name = "Seithkona Saga", Guild = "the Seithkona Circle", Model = 168, Pos = new[] { 5.0, 5.0 },
                    Greet = "Look up. The moon's running easy tonight - nothing behind her. The Circle sends its thanks. And says Hati isn't dead, only beaten."
                }
            }
        };

        public static readonly AlbionCampaign Wyrm = new()
        {
            Key = "wyrm", Title = "The Dragon-Oath", Guild = "the Oath of the Volur", Enemy = "the drakulv", Prefix = "mh_cp",
            RaidChain = "mh_wyrm_temple", LiftKey = "malmohus", StateFile = "wyrm-campaign-state.json", Word = "by the Oath",
            Zone = 116, MinLevel = 50, Region = 100, Side = eRealm.Midgard, SoldierTemplate = MidgardCampaigns.SoldierTemplate, SoldierEquipment = MidgardCampaigns.SoldierEquipment,
            HostFaction = "volur_oath", RaidPlaceName = "the Wyrm-Temple", WhereName = "Malmohus",
            Names = new[] { "Halla's camp", "the Missionary Road", "the Svartalf Foist", "the Armguard Lines", "the Temple Steps" },
            Posts = new[]
            {
                null, new[] { 600.0, 300.0, 84.6 }, new[] { 1350.0, 500.0, 104.7 }, new[] { 750.0, 850.0, 100.9 }, new[] { 700.0, 1200.0, 71.4 }
            },
            HeldSites = new[]
            {
                new string[0],
                new[] { "cp1_garrison", "cp1_road" },
                new[] { "cp2_garrison", "cp2_foist", "foist_hall" },
                new[] { "cp3_garrison", "cp3_lines" },
                new[] { "cp4_garrison", "cp4_steps", "disciples" }
            },
            Seat = new[] { 900.0, 1380.0, 133.8 },
            MarshalName = "Volva Groa", MarshalGuild = "Keeper of the Dragon-Oath", MarshalAt = new[] { 1010.0, 510.0, 71.3, 2048 },
            MarshalModel = 157, SoldierModel = 160,
            MarshalGreet = "The Hierophant has half of Gjalpinulva's true name. I have the other half - that's why they hunted me through Myrkwood. If he gets it, " +
                           "she wakes all the way, and her brood with her. The volur and the King's huscarls have sworn the Oath: we take Malmohus back a road at a " +
                           "time - the missionary road, the svartalf foist, the armguard lines, the temple steps - then his temple. Will you swear it? Say [by the Oath].",
            MarshalShout = "The Oath is sworn! Up the missionary road - and no one turns back!",
            CaptainName = "Oath-Captain of the Volur", SpearName = "oath-sworn huscarl", ArcherName = "oath-sworn bowman",
            TooLow = "The drakulv would feed you to her brood before the first road. Come back at level {0}, and the Oath will march behind you.",
            Marching = "The Dragon-Oath is already sworn. Go and join it.",
            NoOne = "No one went up the missionary road. The Oath stands down at Halla's camp.",
            Victorious = "The Hierophant is broken at the Wyrm-Temple, and the half-name dies with him! The Dragon-Oath holds Malmohus, the temple smoke is lifting - " +
                         "and Gjalpinulva's lair stands open. She sleeps, still. Not deeply.",
            Expired = "The temple smoke comes back over Malmohus. The drakulv have a new Hierophant, and Gjalpinulva's lair is sealed in her sleep once more.",
            PushedOut = "The Dragon-Oath has been driven out of Malmohus. It falls back on Halla's camp.",
            CounterWord = "The drakulv strike back at {0}!", HeldWord = "Holding {0} - {1} in {2}",
            Started = "The Dragon-Oath is sworn in Malmohus! {0} has Volva Groa's word. The Oath-Captain forms up for the Missionary Road - every sword is wanted.",
            Camp = () => new()
            {
                new SiegeNpcDef
                {
                    Kind = "marks", Name = "Quartermaster Svein of the Oath", Guild = "the Oath of the Volur", Model = 213, Pos = new[] { -6.0, 4.0 },
                    Greet = "The Wyrm-Temple, and the Oath's banner over it. Marks of Valor, and the Oath's best - take it before the smoke comes back.",
                    Stock = new()
                    {
                        new SiegeStockDef { Item = "mh116_mantle_of_the_dragon_oath", Price = 260 },
                        new SiegeStockDef { Item = "mh116_true_name_torc", Price = 240 },
                        new SiegeStockDef { Item = "mh116_girdle_of_the_wyrm_temple", Price = 220 },
                        new SiegeStockDef { Item = "mh116_ring_of_the_broken_rite", Price = 220 },
                        new SiegeStockDef { Item = "mh116_scale_breaker_bracer", Price = 200 },
                        new SiegeStockDef { Item = "mh116_volva_s_eye_jewel", Price = 200 },
                    }
                },
                new SiegeNpcDef
                {
                    Kind = "idle", Name = "Hallveig the Apprentice", Guild = "the Seidr-Folk", Model = 168, Pos = new[] { 5.0, 5.0 },
                    Greet = "Groa says the name's safe now - his half died with him. South-west of here, in her lair, Gjalpinulva is turning in her sleep. " +
                            "I'd bring friends. A lot of friends."
                }
            }
        };
    }
}
