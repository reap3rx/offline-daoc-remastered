using System;
using System.Collections.Generic;
using System.Linq;
using DOL.AI.Brain;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;
using DOL.GS.Reputation;

namespace DOL.GS.EasterEggs
{
    /// <summary>
    /// Silvermine's easter egg (owner 2026-11-22): the little island in the middle of the lake has one thing on it - an old
    /// Celt blademaster by a campfire, friendly, who talks to anyone. To anyone but a level 50 Blademaster he only makes a
    /// remark; to a level 50 Blademaster he offers a duel. He looks like any friendly NPC until it starts, then he's a
    /// purple. Win by bringing him to 1% health: he stops at once and gives two Legendary blades of the challenger's best
    /// weapon line (blades, blunt or piercing) - once per character; after that, a duel for the joy of it. Nobody else can
    /// touch him while he duels, and he can't be killed.
    /// </summary>
    public class OldBlademaster : GameNPC
    {
        public const string RewardKey = "_egg_fearghus_blades";        // in the challenger's reputation standing (saved)
        public const string Accept = "cross blades";
        public const int DuelMinutes = 10;
        public const int LeashRange = 3000;

        GamePlayer _challenger;
        long _duelStarted;
        bool _countingDown;
        int _ticks;
        public const int YieldAtPercent = 30;                  // he stops before he kills you (it's a duel, not a death)

        public bool Dueling => _challenger != null;

        // ------------------------------------------------------------------ what he says (pure: tested)

        /// <summary>The weapon line a Blademaster's two blades are made in: the best of blades, blunt and piercing (blades
        /// on a tie).</summary>
        public static eObjectType WeaponFor(Func<string, int> spec)
        {
            int b = spec("Blades"), u = spec("Blunt"), p = spec("Piercing");
            return u > b && u >= p ? eObjectType.Blunt : p > b && p > u ? eObjectType.Piercing : eObjectType.Blades;
        }

        public static bool MayDuel(GamePlayer p) => p != null && p.CharacterClass?.ID == (int) eCharacterClass.Blademaster && p.Level >= 50;

        /// <summary>His word to someone who talks to him.</summary>
        public static string Remark(bool blademaster, int level, bool rewarded, int roll)
        {
            if (blademaster && level >= 50)
                return rewarded
                    ? $"You again. You've my blades and you've my measure - and still you come back. Good. Shall we [{Accept}] again, for the joy of it?"
                    : $"Two blades, and the way you stand... fifty years of it, I'd say. I haven't had a real fight since the sheevra were pups. Will you [{Accept}] with an old man? To first blood - well, to nearly last.";
            if (blademaster)
                return (roll % 3) switch
                {
                    0 => "A blademaster! Your feet are wrong. Your left hand is lazy. Come back when they aren't, and we'll talk.",
                    1 => "I see the two blades. I see the stance. I see a good thirty years of mistakes still ahead of you. Go and make them.",
                    _ => "When you can cut a falling leaf in three before it lands, come back. Until then, sit, and watch the water."
                };
            return (roll % 4) switch
            {
                0 => "Pull up a stone. The fire's warm and the fish are biting. ...No, they're not. They never are.",
                1 => "Forty years I fought for the high king. Now I fight the midges. The midges are winning.",
                2 => "Nobody comes out here. Nobody but the herons. And now you. Don't scare the herons.",
                _ => "The island? It was here when I came. It'll be here when I go. That's more than you can say for most things."
            };
        }

        // ------------------------------------------------------------------ talking

        public override bool Interact(GamePlayer player)
        {
            if (!base.Interact(player))
                return false;
            if (Dueling)
            {
                if (player != _challenger)
                    NpcSpeech.SayTo(this, player, "Not now - I'm teaching.");
                return true;
            }
            ReputationService.Standing st = ReputationService.Of(player);
            if (st != null && st.Get(RewardKey) <= 0 && st.Get(RewardKey + "_owed") > 0)
            {
                Reward(player);                                  // (won with a full pack: here they are now)
                return true;
            }
            bool rewarded = st?.Get(RewardKey) > 0;
            NpcSpeech.SayTo(this, player, Remark(player.CharacterClass?.ID == (int) eCharacterClass.Blademaster, player.Level, rewarded, Util.Random(0, 11)));
            return true;
        }

        public override bool WhisperReceive(GameLiving source, string text)
        {
            if (!base.WhisperReceive(source, text) || source is not GamePlayer p)
                return false;
            if (Dueling && p == _challenger && p.Client?.Account?.PrivLevel > (uint) ePrivLevel.Player &&
                string.Equals(text?.Trim(), "yield", StringComparison.OrdinalIgnoreCase))
            {
                EndDuel(true, "ENOUGH! Enough. ...A GM's blade, is it? Fine. You've won.");   // (testing the ending)
                return true;
            }
            if (!string.Equals(text?.Trim(), Accept, StringComparison.OrdinalIgnoreCase) || Dueling || _countingDown || !MayDuel(p))
                return true;
            if (!IsWithinRadius(p, 600))
            {
                NpcSpeech.SayTo(this, p, "Come closer. I'm old, not a fool - I don't shout across water.");
                return true;
            }
            _countingDown = true;
            Say($"Ha! Up, then. On your guard, {p.Name} - three heartbeats.");
            new ECSGameTimer(this, _ =>
            {
                _countingDown = false;
                if (p.IsAlive && p.ObjectState == eObjectState.Active && IsWithinRadius(p, 1200))
                    StartDuel(p);
                return 0;
            }, 3000);
            return true;
        }

        void Say(string text)
        {
            foreach (GamePlayer pl in GetPlayersInRadius(WorldMgr.SAY_DISTANCE))
                pl.Out.SendMessage($"{Name} says, \"{text}\"", eChatType.CT_Say, eChatLoc.CL_ChatWindow);
        }

        // ------------------------------------------------------------------ the duel

        void StartDuel(GamePlayer p)
        {
            _challenger = p;
            _duelStarted = GameLoop.GameLoopTime;
            Realm = eRealm.None;
            Flags &= ~eFlags.PEACE;
            Health = MaxHealth;
            MonsterTiers.SetTier(this, MonsterTiers.Purple);   // a purple to whoever looks, from the first blow
            Refresh();
            (Brain as StandardMobBrain)?.AddToAggroList(p, 1000);
            StartAttack(p);
            _ticks = 0;
            new ECSGameTimer(this, _ => Watch(), 500);
        }

        int Watch()
        {
            if (!Dueling)
                return 0;
            GamePlayer p = _challenger;
            if (!p.IsAlive)
            {
                EndDuel(false, "Get up. Get UP. ...There. You'll mend. Come back when you've stopped bleeding and we'll go again.");
                return 0;
            }
            if (p.HealthPercent < YieldAtPercent)
            {
                EndDuel(false, "Hold! HOLD. Yield - you're beaten, and I'd sooner not bury you. Mend, practise, and come back. I'll be here. I'm always here.");
                return 0;
            }
            if (p.ObjectState != eObjectState.Active || p.CurrentRegion != CurrentRegion || !IsWithinRadius(p, LeashRange))
            {
                EndDuel(false, "Running? Ha. Wise, maybe.");
                return 0;
            }
            if (GameLoop.GameLoopTime - _duelStarted > DuelMinutes * 60_000)
            {
                EndDuel(false, "Enough - the fire's going out, and so am I. We'll call it a draw. I'll call it a draw. You can call it what you like.");
                return 0;
            }
            if (TargetObject != p || attackComponent?.AttackState != true)
                StartAttack(p);
            if (++_ticks % 10 == 0)
                Console.WriteLine($"[OldBlademaster] duel with {p.Name}: him {Health}/{MaxHealth} attacking={attackComponent?.AttackState} target={TargetObject?.Name}; {p.Name} {p.Health}/{p.MaxHealth}");
            return 500;
        }

        void EndDuel(bool won, string say)
        {
            GamePlayer p = _challenger;
            _challenger = null;
            StopAttack();
            (Brain as StandardMobBrain)?.ClearAggroList();
            Realm = eRealm.Hibernia;
            Flags |= eFlags.PEACE;
            Health = MaxHealth;
            MonsterTiers.SetTier(this, MonsterTiers.None);
            Refresh();
            MoveTo(CurrentRegionID, SpawnPoint.X, SpawnPoint.Y, SpawnPoint.Z, Heading);
            Say(say);
            if (won && p != null)
                Reward(p);
        }

        /// <summary>Everyone near sees him as he is now (friend or purple).</summary>
        void Refresh()
        {
            foreach (GamePlayer pl in GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            {
                pl.Out.SendNPCCreate(this);
                if (Inventory != null)
                    pl.Out.SendLivingEquipmentUpdate(this);
                MonsterTiers.PushTiers(pl);
            }
        }

        public override void TakeDamage(GameObject source, eDamageType damageType, int damageAmount, int criticalAmount)
        {
            GameObject who = source is GameNPC n && n.Brain is IControlledBrain b ? b.GetLivingOwner() : source;
            if (!Dueling || who != _challenger)
                return;                                          // (a duel: nobody else's blow lands)
            int floor = Math.Max(1, MaxHealth / 100);
            int total = damageAmount + criticalAmount;
            if (Health - total > floor)
            {
                base.TakeDamage(source, damageType, damageAmount, criticalAmount);
                return;
            }
            int allowed = Math.Max(0, Health - floor);
            base.TakeDamage(source, damageType, Math.Min(damageAmount, allowed), Math.Max(0, Math.Min(criticalAmount, allowed - damageAmount)));
            Health = Math.Max(Health, floor);
            EndDuel(true, "ENOUGH! Enough. ...Ha. Ha! I felt that one in my grandfather's bones. Put up your blades. You've won.");
        }

        public override void Die(GameObject killer)
        {
            if (Dueling || ObjectState == eObjectState.Active)
            {
                Health = Math.Max(1, MaxHealth / 100);
                if (Dueling)
                    EndDuel(true, "ENOUGH! Enough. Put up your blades. You've won.");
                return;                                          // (he can't be killed)
            }
            base.Die(killer);
        }

        // ------------------------------------------------------------------ the blades

        void Reward(GamePlayer p)
        {
            ReputationService.Standing s = ReputationService.Of(p);
            if (s == null || s.Get(RewardKey) > 0)
            {
                Say("Same time next year? Ha. Same time tomorrow.");
                return;
            }
            if (!p.Inventory.IsSlotsFree(2, eInventorySlot.FirstBackpack, eInventorySlot.LastBackpack))
            {
                NpcSpeech.SayTo(this, p, "I've something for you - two things - and your pack's too full to take them. Make room, and talk to me again.");
                s.Points[RewardKey + "_owed"] = 1;
                s.Dirty = true;
                return;
            }
            eObjectType type = WeaponFor(p.GetBaseSpecLevel);
            DbItemTemplate first = Blade(p, type, eInventorySlot.RightHandWeapon, "Fearghus's First Lesson",
                "The old master's main blade. 'Strike first. Strike true. Strike once, if you can.'");
            DbItemTemplate last = Blade(p, type, eInventorySlot.LeftHandWeapon, "Fearghus's Last Lesson",
                "The old master's off-hand blade. 'And when the first one misses - this.'");
            foreach (DbItemTemplate t in new[] { first, last }.Where(t => t != null))
            {
                DbInventoryItem item = GameInventoryItem.Create(t);
                if (p.Inventory.AddItem(eInventorySlot.FirstEmptyBackpack, item))
                {
                    InventoryLogging.LogInventoryAction(this, p, eInventoryActionType.Quest, item.Template, 1);
                    p.Out.SendMessage($"Fearghus the Grey gives you {item.Name}.", eChatType.CT_Loot, eChatLoc.CL_SystemWindow);
                }
            }
            lock (s.Sync)
            {
                s.Points[RewardKey] = 1;
                s.Points.TryRemove(RewardKey + "_owed", out _);
                s.Dirty = true;
            }
            ReputationService.Save(p);
            NpcSpeech.SayTo(this, p, "Take these. They were mine, when I was young and foolish - which is to say, the last time I lost. Carry them well.");
        }

        static DbItemTemplate Blade(GamePlayer p, eObjectType type, eInventorySlot slot, string name, string words)
        {
            try
            {
                var g = new GeneratedUniqueItem(false, eRealm.Hibernia, eCharacterClass.Blademaster, 51, type, slot);
                g.Quality = 100;
                SpecialLoot.AddOneBonus(g, p, 50);
                string forged = LootOverhaul.Forge(g, 50, true);
                SpecialLoot.BetterLook(g, 50);
                g.Name = name;
                g.Description = $"Legendary{(forged != null ? ", " + forged.ToLowerInvariant() : "")}. {words}";
                g.Price = Money.SetAutoPrice(g.Level, g.Quality);
                g.IsTradable = false;
                g.AllowAdd = true;
                return g;
            }
            catch (Exception e)
            {
                Console.WriteLine($"[OldBlademaster] {name}: {e.Message}");
                return null;
            }
        }

        // ------------------------------------------------------------------ putting him on the island

        public const ushort Region = 200;
        public const int X0 = 319488 + 905 * 40, Y0 = 548864 + 682 * 40, Z0 = 4672;    // Silvermine, the lake's island (905, 682 m)

        static OldBlademaster _him;
        static GameNPC _fire;

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args) =>
            _ = new ECSGameTimer(null, _ => Spawn() ? 0 : 30_000, 15_000);

        public static bool Spawn()
        {
            try
            {
                if (_him?.ObjectState == eObjectState.Active)
                    return true;
                Region r = WorldMgr.GetRegion(Region);
                if (r == null)
                    return false;
                var npc = new OldBlademaster
                {
                    Name = "Fearghus the Grey", GuildName = "Blademaster, long retired", Model = 292, Size = 52, Level = 50,
                    Realm = eRealm.Hibernia, X = X0, Y = Y0, Z = Z0, Heading = 3000, CurrentRegion = r,
                    RespawnInterval = -1, LoadedFromScript = true, LeftHandSwingChance = 50, MaxSpeedBase = 220,
                };
                npc.Flags |= eFlags.PEACE;
                var inv = new GameNpcInventoryTemplate();
                if (!inv.LoadFromDatabase("BlademasterTrainer2"))
                    inv = new GameNpcInventoryTemplate();
                inv.AddNPCEquipment(eInventorySlot.RightHandWeapon, 444);
                inv.AddNPCEquipment(eInventorySlot.LeftHandWeapon, 444);
                npc.Inventory = inv.CloseTemplate();
                npc.SwitchWeapon(eActiveWeaponSlot.Standard);
                npc.SetOwnBrain(new StandardMobBrain { AggroLevel = 0, AggroRange = 0 });
                if (!npc.AddToWorld())
                    return false;
                npc.SpawnPoint = new Point3D(npc.X, npc.Y, npc.Z);
                _him = npc;
                var fire = new GameNPC
                {
                    Name = "campfire", Model = 1686, Size = 50, Level = 1, Realm = eRealm.Hibernia, X = X0 - 280, Y = Y0 + 320, Z = Z0,
                    CurrentRegion = r, RespawnInterval = -1, LoadedFromScript = true,
                };
                fire.Flags |= eFlags.PEACE | eFlags.CANTTARGET | eFlags.DONTSHOWNAME;
                if (fire.AddToWorld())
                    _fire = fire;
                Console.WriteLine($"[OldBlademaster] Fearghus the Grey sits by his fire on the island ({X0} {Y0})");
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[OldBlademaster] {ex.Message}");
                return true;                                     // (don't keep trying a broken spawn)
            }
        }
    }
}
