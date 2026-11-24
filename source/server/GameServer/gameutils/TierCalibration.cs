using System;
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
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// The power curve's test bench (owner 2026-11-19: "Make a stand in character ... in as neutral of an environment as
    /// you can, and as average as you can. No stat boosts, no companions, and have them fight mobs of every con. maybe at
    /// level 5, 15, 25, 35, 45, and 50 ... neutral armor (fine quality, no extra stats) of each type").
    ///
    /// "/calib run" on a stand-in character (a test database only): for each level, armour type, monster and con it sets
    /// the character's level and specs (weapon spec = level, parry = half), dresses it in plain armour of that type and a
    /// plain weapon (fine quality, no bonuses), puts a fresh monster of that con beside it somewhere quiet, lets them
    /// auto-attack until one falls (the character is pulled out at a fifth of its health, so it never dies) or a time
    /// runs out, and writes how fast each was hurting the other. Results: the server log ("[Calib]") and
    /// calibration.txt beside the server.
    /// </summary>
    public static class TierCalibration
    {
        /// <summary>Classic: the 2026-11-19 bench (trained, plain armour, fights to a finish). Base: the one-footing
        /// baseline (owner 2026-11-22: untrained, no armour, a plain blue-conned weapon, the monster's moves off) with
        /// DAoC's own numbers (Raw) - what OutCurve and InCurve are fitted on. Spell: the same for a caster's best
        /// untrained damage spell, the monster held at range. Check: the baseline again with the fitted numbers on.
        /// Base, Spell and Check keep both sides alive (healed under 40%) for the whole fight and count every blow.</summary>
        public enum Mode { Classic, Base, Spell, Check }

        public sealed class Case
        {
            public int Level;
            public eObjectType Armor;
            public sbyte Tier;
            public string Mob;
        }

        /// <summary>The bench's monster, while it fights with DAoC's own numbers (MonsterTiers.TryDamageFactor, SpellOut).</summary>
        public static bool Raw(GameNPC n)
        {
            Run r = _run;
            return r != null && n != null && n == r.Mob && r.Mode is Mode.Base or Mode.Spell;
        }

        /// <summary>The bench's monster with its moves off (MonsterMoves.Comp): plain swings, DAoC's own defences.</summary>
        public static bool Quiet(GameNPC n)
        {
            Run r = _run;
            return r != null && n != null && n == r.Mob && r.Mode != Mode.Classic;
        }

        sealed class Run
        {
            public GamePlayer P;
            public uint PrivWas;
            public Queue<Case> Cases;
            public Case Cur;
            public GameNPC Mob;
            public long Start, Next, LastLog;
            public int LastHp, LastMobHp, Taken, Dealt, BigHit, Hits;
            public int Done, Total;
            public Point3D Spot;
            public StringBuilder Out = new();
            public int FightMs;
            public bool Armed;
            public Dictionary<string, int> Mine = new(), Theirs = new();
            public double FIn, FOut;
            public Mode Mode;
            public readonly List<double> PBlows = new(), MBlows = new();   // each swing's damage, % of the other's health (0: no hit)
            public long PFirst, PLast, MFirst, MLast;
            public int Casts, Landed;
            public long NextCastAt;
            public double CastPct;
            public string SpellName = "";
            public int WeaponLevel;
        }

        static Run _run;

        /// <summary>Every melee blow (MonsterMoves.AfterBlow): the bench counts how its fighters' blows went.</summary>
        public static void Seen(AttackData ad)
        {
            Run r = _run;
            if (r?.Cur == null || !r.Armed || ad == null)
                return;
            Dictionary<string, int> d = ad.Attacker == r.P ? r.Mine : ad.Attacker == r.Mob ? r.Theirs : null;
            if (d == null)
                return;
            string k = ad.AttackResult.ToString();
            d[k] = d.GetValueOrDefault(k) + 1;
            if (r.Mode == Mode.Classic)
                return;
            bool hit = ad.AttackResult is eAttackResult.HitUnstyled or eAttackResult.HitStyle;
            long now = GameLoop.GameLoopTime;
            if (ad.Attacker == r.P)
            {
                r.PBlows.Add(hit ? (ad.Damage + ad.CriticalDamage) * 100.0 / Math.Max(1, r.Mob.MaxHealth) : 0);
                if (r.PFirst == 0) r.PFirst = now;
                r.PLast = now;
            }
            else
            {
                r.MBlows.Add(hit ? (ad.Damage + ad.CriticalDamage) * 100.0 / Math.Max(1, r.P.MaxHealth) : 0);
                if (r.MFirst == 0) r.MFirst = now;
                r.MLast = now;
            }
        }

        public static readonly int[] DefaultLevels = { 5, 15, 25, 35, 45, 50 };

        public static string Start(GamePlayer p, int[] levels, string[] mobs, int fightMs, bool allArmours, Mode mode = Mode.Classic)
        {
            if (_run != null)
                return "a run is going already (/calib stop)";
            if (p.ControlledBrain != null)
                return "dismiss your pet first";
            eObjectType[] armours = ArmoursFor(p.Realm);
            var cases = new Queue<Case>();
            if (mode is Mode.Base or Mode.Spell)
            {
                // DAoC's own numbers don't care about the con (the monster fights at your level): one fight per level and monster
                foreach (int l in levels.OrderBy(x => x))
                    foreach (string m in mobs)
                        cases.Enqueue(new Case { Level = l, Armor = eObjectType.GenericItem, Tier = MonsterTiers.Yellow, Mob = m });
            }
            else if (mode == Mode.Check)
            {
                foreach (int l in levels.OrderBy(x => x))
                    for (sbyte t = MonsterTiers.Green; t <= MonsterTiers.Purple; t++)
                        cases.Enqueue(new Case { Level = l, Armor = eObjectType.GenericItem, Tier = t, Mob = mobs[0] });
            }
            else
            foreach (int l in levels.OrderBy(x => x))
                foreach (eObjectType a in allArmours ? armours : new[] { armours[2] })
                    for (int mi = 0; mi < mobs.Length; mi++)
                    {
                        // the first monster in every armour, the others in the middle armour only (time)
                        if (mi > 0 && a != armours[2])
                            continue;
                        for (sbyte t = MonsterTiers.Green; t <= MonsterTiers.Red; t++)
                            cases.Enqueue(new Case { Level = l, Armor = a, Tier = t, Mob = mobs[mi] });
                    }
            foreach (string m in mobs.Distinct())
                if (Template(m) == null)
                    return $"no monster called \"{m}\" in the database";
            _run = new Run { P = p, PrivWas = p.Client.Account.PrivLevel, Cases = cases, Total = cases.Count, FightMs = fightMs, Mode = mode };
            _run.Out.AppendLine($"# calibration {DateTime.Now:yyyy-MM-dd HH:mm} - {p.Name}, {p.CharacterClass.Name}, mode {mode}, toughness {MonsterTiers.Toughness}, bite {MonsterTiers.Bite}");
            if (mode == Mode.Classic)
                _run.Out.AppendLine("# level armour mob tier | result secs | taken %/s, biggest hit % | dealt %/s | to die s, to kill s");
            else
                _run.Out.AppendLine("#B level mob tier secs | p: swings hit% mean%/swing meanHit% sdHit% interval | m: swings hit% mean%/swing meanHit% sdHit% interval | casts landed %/cast spell | in out | hp mobLevel mobHp weaponLevel");
            if (!FindSpot(_run))
                Log(_run, "no quiet spot found: fighting where you stand");
            p.Client.Account.PrivLevel = (uint) ePrivLevel.Player;    // (a GM can't be attacked)
            _ = new ECSGameTimer(p, Tick, 500);
            return $"{cases.Count} fights queued";
        }

        public static void Stop(string why)
        {
            Run r = _run;
            if (r == null)
                return;
            _run = null;
            End(r, why);
        }

        static eObjectType[] ArmoursFor(eRealm realm) => realm switch
        {
            eRealm.Albion => new[] { eObjectType.Cloth, eObjectType.Leather, eObjectType.Studded, eObjectType.Chain, eObjectType.Plate },
            eRealm.Midgard => new[] { eObjectType.Cloth, eObjectType.Leather, eObjectType.Studded, eObjectType.Chain },
            _ => new[] { eObjectType.Cloth, eObjectType.Leather, eObjectType.Reinforced, eObjectType.Scale }
        };

        static (eObjectType weapon, string spec, eWeaponDamageType dmg) WeaponFor(eRealm realm) => realm switch
        {
            eRealm.Albion => (eObjectType.SlashingWeapon, DOL.GS.Specs.Slash, eWeaponDamageType.Slash),
            eRealm.Midgard => (eObjectType.Sword, DOL.GS.Specs.Sword, eWeaponDamageType.Slash),
            _ => (eObjectType.Blades, DOL.GS.Specs.Blades, eWeaponDamageType.Slash)
        };

        // ------------------------------------------------------------------ the loop

        static int Tick(ECSGameTimer timer)
        {
            Run r = _run;
            if (r == null)
                return 0;
            try
            {
                GamePlayer p = r.P;
                if (p.ObjectState != GameObject.eObjectState.Active || p.Client == null)
                {
                    Stop("the character left");
                    return 0;
                }
                long now = GameLoop.GameLoopTime;
                if (r.Cur == null)
                {
                    if (now < r.Next)
                        return 250;
                    if (r.Cases.Count == 0)
                    {
                        Stop("done");
                        return 0;
                    }
                    Setup(r, r.Cases.Dequeue());
                    return 250;
                }

                // the fight
                if (!p.IsAlive)
                {
                    Finish(r, "died");
                    return 250;
                }
                p.Heading = p.GetHeading(r.Mob);
                if (p.TargetObject != r.Mob)
                    p.TargetObject = r.Mob;
                p.TargetInView = true;                            // (the client never confirmed a target the server set)
                if (r.Mode == Mode.Spell)
                    CastAt(r, p);
                else if (r.Mob.IsAlive && !p.attackComponent.AttackState)
                    p.attackComponent.RequestStartAttack(r.Mob);
                if (!r.Armed)
                {
                    // the clock starts when they meet (the monster's level, health and the fight's factors are set by
                    // then - MonsterTiers.Engage): both whole
                    if (r.Mode != Mode.Spell && p.GetDistanceTo(r.Mob) > 260 && now - r.Start < 4000)
                        return 250;
                    if (r.Mode == Mode.Spell && r.Mob.TierFightBase <= 0 && now - r.Start < 6000)
                        return 250;                         // (the first spell lands and sets its level)
                    r.PBlows.Clear();
                    r.MBlows.Clear();
                    r.PFirst = r.PLast = r.MFirst = r.MLast = 0;
                    r.Casts = r.Landed = 0;
                    r.CastPct = 0;
                    r.Armed = true;
                    r.Mob.Health = r.Mob.MaxHealth;
                    Heal(p);
                    r.Start = now;
                    r.LastHp = p.Health;
                    r.LastMobHp = r.Mob.Health;
                    r.Taken = r.Dealt = r.BigHit = r.Hits = 0;
                    r.Mine.Clear();
                    r.Theirs.Clear();
                    r.FIn = MonsterTiers.TryDamageFactor(r.Mob, p, out double fi) ? fi : 1;
                    r.FOut = MonsterTiers.TryDamageFactor(p, r.Mob, out double fo) ? fo : 1;
                    return 250;
                }
                if (r.Mode != Mode.Classic)
                    return KeepGoing(r, p, now);
                int hp = p.Health;
                if (hp < r.LastHp)
                {
                    int d = r.LastHp - hp;
                    r.Taken += d;
                    r.Hits++;
                    r.BigHit = Math.Max(r.BigHit, d);
                }
                r.LastHp = hp;
                int mhp = r.Mob.IsAlive ? r.Mob.Health : 0;
                if (mhp < r.LastMobHp)
                    r.Dealt += r.LastMobHp - mhp;
                r.LastMobHp = mhp;
                if (r.Mob.ObjectState != GameObject.eObjectState.Active && r.Mob.IsAlive)
                    Finish(r, "gone");
                else if (!r.Mob.IsAlive)
                    Finish(r, "killed");
                else if (hp <= p.MaxHealth / 5)
                    Finish(r, "pulled");
                else if (now - r.Start > r.FightMs)
                    Finish(r, "time");
                return 250;
            }
            catch (Exception e)
            {
                Console.WriteLine("[Calib] " + e);
                Stop("error: " + e.Message);
                return 0;
            }
        }

        static void Setup(Run r, Case c)
        {
            GamePlayer p = r.P;
            r.Cur = c;
            while (p.Level < c.Level)
                p.Level = (byte) Math.Min(c.Level, p.Level + 1);   // (level by level: the stat gains of each)
            if (r.Mode == Mode.Classic)
            {
                SetSpecs(p, c.Level);
                Dress(p, c.Level, c.Armor);
            }
            else
            {
                Untrained(p);
                r.WeaponLevel = DressBaseline(p, c.Level, r.Mode != Mode.Spell);
            }
            if (r.Spot != null && p.GetDistanceTo(r.Spot) > 300)
                p.MoveTo(p.CurrentRegionID, r.Spot.X, r.Spot.Y, r.Spot.Z, p.Heading);
            Heal(p);

            DbMob row = ZoneBuilds.CopyMob(Template(c.Mob));
            Point2D front = p.GetPointFromHeading(p.Heading, r.Mode == Mode.Spell ? 900 : 220);
            row.X = front.X;
            row.Y = front.Y;
            row.Z = p.Z;
            row.Region = p.CurrentRegionID;
            row.RespawnInterval = -1;
            row.RoamingRange = 0;
            row.PathID = null;
            var mob = new GameNPC();
            mob.LoadFromDatabase(row);
            mob.LoadedFromScript = true;
            mob.RespawnInterval = -1;
            mob.CurrentRegion = p.CurrentRegion;
            ZoneBuilds.Exempt.AddOrUpdate(mob, null);
            mob.AddToWorld();
            MonsterTiers.SetTier(mob, c.Tier);
            r.Mob = mob;
            if (r.Mode == Mode.Spell)
                mob.MaxSpeedBase = 0;                           // (held at range: a blow would break every cast)
            if (mob.Brain is StandardMobBrain b && r.Mode != Mode.Spell)
                b.AddToAggroList(p, 1000);
            p.TargetObject = mob;
            if (r.Mode != Mode.Spell)
                p.attackComponent.RequestStartAttack(mob);
            r.Start = GameLoop.GameLoopTime;
            r.LastHp = p.Health;
            r.LastMobHp = mob.Health;
            r.Taken = r.Dealt = r.BigHit = r.Hits = 0;
            r.Armed = false;
        }

        /// <summary>Base, Spell, Check: both kept on their feet for the whole fight (healed under 40%), every blow counted.</summary>
        static int KeepGoing(Run r, GamePlayer p, long now)
        {
            if (r.Mob.ObjectState != GameObject.eObjectState.Active)
            {
                Finish(r, "gone");
                return 250;
            }
            if (r.Mode == Mode.Spell)
            {
                int mhp = r.Mob.Health;
                if (mhp < r.LastMobHp)
                {
                    r.Landed++;
                    r.CastPct += (r.LastMobHp - mhp) * 100.0 / Math.Max(1, r.Mob.MaxHealth);
                }
                r.LastMobHp = mhp;
                p.Mana = p.MaxMana;
            }
            if (p.Health < p.MaxHealth * 0.4)
                Heal(p);
            if (r.Mob.Health < r.Mob.MaxHealth * 0.4)
                r.Mob.Health = r.Mob.MaxHealth;
            r.LastMobHp = r.Mob.Health;
            p.Endurance = p.MaxEndurance;
            if (now - r.Start > r.FightMs)
                Finish(r, "time");
            return 250;
        }

        /// <summary>A caster's best damage spell, fired at the monster every three seconds: straight through its spell
        /// handler (the same damage, resists and spread as a cast, without the cast bar and its queue).</summary>
        static void CastAt(Run r, GamePlayer p)
        {
            long now = GameLoop.GameLoopTime;
            if (!r.Mob.IsAlive || now < r.NextCastAt)
                return;
            r.NextCastAt = now + 3000;
            var (spell, line) = BestDamageSpell(p);
            if (spell == null)
                return;
            r.SpellName = $"{spell.Name} (L{spell.Level}, {spell.Damage} dmg, {line.Name})";
            p.TargetObject = r.Mob;
            ISpellHandler h = ScriptMgr.CreateSpellHandler(p, spell, line);
            if (h == null)
                return;
            MonsterTiers.Touch(p, r.Mob);                       // (its fight level, as a cast would set it)
            if (r.Armed)
                r.Casts++;
            h.StartSpell(r.Mob);
        }

        static (Spell, SpellLine) BestDamageSpell(GamePlayer p)
        {
            Spell best = null;
            SpellLine bestLine = null;
            foreach (var (line, skills) in p.GetAllUsableListSpells())
                foreach (Skill sk in skills)
                    if (sk is Spell sp && sp.Damage > 0 && sp.Target == eSpellTarget.ENEMY && sp.Radius == 0 &&
                        (sp.SpellType is eSpellType.DirectDamage or eSpellType.Bolt or eSpellType.DirectDamageNoVariance) &&
                        (best == null || sp.Damage > best.Damage))
                    {
                        best = sp;
                        bestLine = line;
                    }
            return (best, bestLine);
        }

        /// <summary>No training: every specialization the character has back to 1.</summary>
        static void Untrained(GamePlayer p)
        {
            foreach (Specialization s in p.GetSpecList())
                s.Level = 1;
            p.RefreshSpecDependantSkills(false);
            p.Out.SendUpdatePlayerSkills(true);
        }

        /// <summary>The baseline's kit: no armour; a plain one-hand weapon (fine quality, no bonuses) at the level that cons
        /// blue to this level, or nothing (a caster). Returns the weapon's level.</summary>
        static int DressBaseline(GamePlayer p, int level, bool weapon)
        {
            foreach (DbInventoryItem it in p.Inventory.EquippedItems.ToList())
                p.Inventory.RemoveItem(it);
            int wl = Math.Max(1, MonsterTiers.LevelFor(level, MonsterTiers.Blue, level));
            if (weapon)
            {
                var (wt, _, dmg) = WeaponFor(p.Realm);
                DbItemTemplate w = Plain(p.Realm, (int) eInventorySlot.RightHandWeapon, (int) wt);
                if (w != null)
                {
                    w.Level = wl;
                    w.DPS_AF = Math.Min(165, 12 + 3 * wl);
                    w.SPD_ABS = 37;
                    w.Hand = 0;
                    w.Type_Damage = (int) dmg;
                    w.Item_Type = (int) eInventorySlot.RightHandWeapon;
                    p.Inventory.AddItem(eInventorySlot.RightHandWeapon, GameInventoryItem.Create(w));
                }
            }
            p.SwitchWeapon(eActiveWeaponSlot.Standard);
            p.Out.SendCharStatsUpdate();
            p.Out.SendUpdateWeaponAndArmorStats();
            return wl;
        }

        static (int n, double hitPct, double mean, double meanHit, double sdHit) Stats(List<double> blows)
        {
            int n = blows.Count;
            var hits = blows.Where(b => b > 0).ToList();
            double mean = n > 0 ? blows.Sum() / n : 0, mh = hits.Count > 0 ? hits.Average() : 0;
            double sd = hits.Count > 1 ? Math.Sqrt(hits.Sum(h => (h - mh) * (h - mh)) / (hits.Count - 1)) : 0;
            return (n, n > 0 ? hits.Count * 100.0 / n : 0, mean, mh, sd);
        }

        static void FinishBaseline(Run r, Case c, double secs)
        {
            GamePlayer p = r.P;
            var ps = Stats(r.PBlows);
            var ms = Stats(r.MBlows);
            double pInt = ps.n > 1 ? (r.PLast - r.PFirst) / 1000.0 / (ps.n - 1) : 0;
            double mInt = ms.n > 1 ? (r.MLast - r.MFirst) / 1000.0 / (ms.n - 1) : 0;
            double perCast = r.Casts > 0 ? r.CastPct / r.Casts : 0;
            Log(r, string.Format(System.Globalization.CultureInfo.InvariantCulture,
                "B {0} {1} {2} {3:0.0} | p {4} {5:0.0} {6:0.###} {7:0.###} {8:0.###} {9:0.00} | m {10} {11:0.0} {12:0.###} {13:0.###} {14:0.###} {15:0.00} | " +
                "c {16} {17} {18:0.###} {19} | f {20:0.###} {21:0.###} | hp {22} {23} {24} w {25}",
                c.Level, c.Mob.Replace(' ', '_'), TierName(c.Tier), secs, ps.n, ps.hitPct, ps.mean, ps.meanHit, ps.sdHit, pInt,
                ms.n, ms.hitPct, ms.mean, ms.meanHit, ms.sdHit, mInt, r.Casts, r.Landed, perCast, r.SpellName.Replace(' ', '_'),
                r.FIn, r.FOut, p.MaxHealth, r.Mob.Level, r.Mob.MaxHealth, r.WeaponLevel));
        }

        static void Finish(Run r, string result)
        {
            GamePlayer p = r.P;
            Case c = r.Cur;
            double secs = Math.Max(0.5, (GameLoop.GameLoopTime - r.Start) / 1000.0);
            if (r.Mode != Mode.Classic)
                FinishBaseline(r, c, secs);
            int mobMax = Math.Max(1, r.Mob.MaxHealth);
            double taken = r.Taken * 100.0 / p.MaxHealth / secs, dealt = r.Dealt * 100.0 / mobMax / secs;
            double big = r.BigHit * 100.0 / p.MaxHealth;
            string line = $"{c.Level,2} {c.Armor,-10} {c.Mob,-24} {TierName(c.Tier),-6} | {result,-6} {secs,5:0.0} | " +
                $"{taken,5:0.0} {big,5:0.0} | {dealt,5:0.0} | {(taken > 0 ? 100 / taken : 999),6:0.0} {(dealt > 0 ? 100 / dealt : 999),6:0.0}" +
                $" | in x{r.FIn:0.00} out x{r.FOut:0.00} | hp {p.MaxHealth} mob L{r.Mob.Level} {mobMax} hp, hits {r.Hits}" +
                $" | mine {string.Join(",", r.Mine.Select(kv => kv.Key + " " + kv.Value))} | theirs {string.Join(",", r.Theirs.Select(kv => kv.Key + " " + kv.Value))}" +
                $" | last {p.attackComponent.attackAction?.LastAttackData?.AttackResult}, front {p.IsObjectInFront(r.Mob, 120)}, heading {p.Heading} want {p.GetHeading(r.Mob)}" +
                $" | swinging {p.attackComponent.AttackState}, {p.GetDistanceTo(r.Mob)} away, {p.ActiveWeapon?.Name ?? "no weapon"}, ac {ActionCombat.IsActive(p)}";
            if (r.Mode == Mode.Classic)
                Log(r, line);
            p.attackComponent.StopAttack();
            if (r.Mob.IsAlive || r.Mob.ObjectState == GameObject.eObjectState.Active)
                r.Mob.Delete();
            r.Mob = null;
            r.Cur = null;
            r.Done++;
            if (!p.IsAlive)
                Revive(p);
            Heal(p);
            r.Next = GameLoop.GameLoopTime + 2500;
            if (r.Done % 10 == 0)
                p.Out.SendMessage($"[Calib] {r.Done} / {r.Total}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        static void End(Run r, string why)
        {
            try
            {
                if (r.Mob != null && r.Mob.ObjectState == GameObject.eObjectState.Active)
                    r.Mob.Delete();
                r.P.attackComponent.StopAttack();
                if (r.P.Client?.Account != null)
                    r.P.Client.Account.PrivLevel = r.PrivWas;
                if (!r.P.IsAlive)
                    Revive(r.P);
                Heal(r.P);
            }
            catch (Exception)
            {
            }
            Log(r, $"# {why} after {r.Done} of {r.Total}");
            try
            {
                File.WriteAllText(Path.Combine(GameServer.Instance.Configuration.RootDirectory, "calibration.txt"), r.Out.ToString());
            }
            catch (Exception e)
            {
                Console.WriteLine("[Calib] couldn't write calibration.txt: " + e.Message);
            }
            r.P.Out?.SendMessage($"[Calib] {why}", eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }

        static void Log(Run r, string line)
        {
            r.Out.AppendLine(line);
            Console.WriteLine("[Calib] " + line);
        }

        static string TierName(sbyte t) => t switch
        {
            MonsterTiers.Green => "green", MonsterTiers.Blue => "blue", MonsterTiers.Yellow => "yellow",
            MonsterTiers.Orange => "orange", MonsterTiers.Red => "red", MonsterTiers.Purple => "purple", _ => "grey"
        };

        static void Heal(GamePlayer p)
        {
            p.Health = p.MaxHealth;
            p.Mana = p.MaxMana;
            p.Endurance = p.MaxEndurance;
        }

        static void Revive(GamePlayer p)
        {
            Heal(p);
            p.StopReleaseTimer();
            p.Out.SendPlayerRevive(p);
            p.Out.SendStatusUpdate();
            p.Notify(GamePlayerEvent.Revive, p);
        }

        // ------------------------------------------------------------------ a quiet spot

        static bool FindSpot(Run r)
        {
            GamePlayer p = r.P;
            Zone zone = p.CurrentZone;
            if (zone == null || !PathfindingProvider.Instance.IsAvailable || !PathfindingProvider.Instance.HasNavmesh(zone))
                return false;
            var c = new Vector3(p.X, p.Y, p.Z);
            for (int i = 0; i < 120; i++)
            {
                Vector3? v = PathfindingProvider.Instance.GetRandomPoint(zone, c, 9000, PathfindingProvider.Instance.DefaultFilters);
                if (!v.HasValue)
                    continue;
                var pt = new Point3D((int) v.Value.X, (int) v.Value.Y, (int) v.Value.Z);
                var near = new List<GameNPC>();
                p.CurrentRegion.GetInRadius(pt, eGameObjectType.NPC, 2200, near);
                if (near.Any(n => n.IsAlive))
                    continue;
                r.Spot = pt;
                p.MoveTo(p.CurrentRegionID, pt.X, pt.Y, pt.Z, p.Heading);
                Log(r, $"# spot {pt.X} {pt.Y} {pt.Z} (no one within 2200)");
                return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ the character: specs and plain gear

        static void SetSpecs(GamePlayer p, int level)
        {
            var (_, weaponSpec, _) = WeaponFor(p.Realm);
            SetSpec(p, weaponSpec, level);
            SetSpec(p, DOL.GS.Specs.Parry, Math.Max(1, level / 2));
            p.RefreshSpecDependantSkills(false);
            p.Out.SendUpdatePlayerSkills(true);
        }

        static void SetSpec(GamePlayer p, string key, int level)
        {
            Specialization s = p.GetSpecializationByName(key);
            if (s == null)
            {
                Specialization def = SkillBase.GetSpecialization(key);
                if (def == null)
                    return;
                p.AddSpecialization(def);
                s = p.GetSpecializationByName(key);
            }
            if (s != null)
                s.Level = level;
        }

        static readonly eInventorySlot[] ArmourSlots =
        {
            eInventorySlot.HeadArmor, eInventorySlot.HandsArmor, eInventorySlot.FeetArmor,
            eInventorySlot.TorsoArmor, eInventorySlot.LegsArmor, eInventorySlot.ArmsArmor
        };

        static readonly Dictionary<(int slot, int type), DbItemTemplate> _looks = new();

        /// <summary>Plain armour of a type and a plain one-hand weapon, fine quality (90%), no bonuses - DAoC's own
        /// numbers for their level: armour factor 2 per level (cloth 1), the type's absorption, weapon DPS 1.2 + 0.3 per
        /// level at 3.7 speed.</summary>
        static void Dress(GamePlayer p, int level, eObjectType armour)
        {
            foreach (DbInventoryItem it in p.Inventory.EquippedItems.ToList())
                p.Inventory.RemoveItem(it);
            foreach (eInventorySlot slot in ArmourSlots)
            {
                DbItemTemplate t = Plain(p.Realm, (int) slot, (int) armour);
                if (t == null)
                    continue;
                t.Level = level;
                t.DPS_AF = armour == eObjectType.Cloth ? Math.Min(50, level) : Math.Min(102, level * 2);
                t.SPD_ABS = armour switch
                {
                    eObjectType.Cloth => 0, eObjectType.Leather => 10, eObjectType.Studded or eObjectType.Reinforced => 19,
                    eObjectType.Chain or eObjectType.Scale => 27, eObjectType.Plate => 34, _ => 0
                };
                p.Inventory.AddItem(slot, GameInventoryItem.Create(t));
            }
            var (wt, _, dmg) = WeaponFor(p.Realm);
            DbItemTemplate w = Plain(p.Realm, (int) eInventorySlot.RightHandWeapon, (int) wt);
            if (w != null)
            {
                w.Level = level;
                w.DPS_AF = Math.Min(165, 12 + 3 * level);
                w.SPD_ABS = 37;
                w.Hand = 0;
                w.Type_Damage = (int) dmg;
                w.Item_Type = (int) eInventorySlot.RightHandWeapon;
                p.Inventory.AddItem(eInventorySlot.RightHandWeapon, GameInventoryItem.Create(w));
            }
            p.SwitchWeapon(eActiveWeaponSlot.Standard);
            p.Out.SendCharStatsUpdate();
            p.Out.SendUpdateWeaponAndArmorStats();
        }

        /// <summary>A fresh template of this slot and type: an existing item's look, every bonus, proc and charge off.</summary>
        static DbItemTemplate Plain(eRealm realm, int slot, int type)
        {
            if (!_looks.TryGetValue((slot, type), out DbItemTemplate look))
            {
                IList<DbItemTemplate> list = GameServer.Database.SelectObjects<DbItemTemplate>(
                    DB.Column("Object_Type").IsEqualTo(type).And(DB.Column("Item_Type").IsEqualTo(slot)));
                look = list.FirstOrDefault(i => i.Realm == (int) realm) ?? list.FirstOrDefault(i => i.Realm == 0) ?? list.FirstOrDefault();
                if (look == null && slot == (int) eInventorySlot.RightHandWeapon)
                {
                    list = GameServer.Database.SelectObjects<DbItemTemplate>(DB.Column("Object_Type").IsEqualTo(type));
                    look = list.FirstOrDefault(i => i.Realm == (int) realm) ?? list.FirstOrDefault();
                }
                _looks[(slot, type)] = look;
            }
            if (look == null)
                return null;
            var t = new DbItemTemplate();
            foreach (PropertyInfo pi in typeof(DbItemTemplate).GetProperties(BindingFlags.Public | BindingFlags.Instance))
            {
                if (!pi.CanRead || !pi.CanWrite || pi.GetIndexParameters().Length > 0)
                    continue;
                object v = pi.GetValue(look);
                string n = pi.Name;
                if ((n.StartsWith("Bonus") || n.StartsWith("ExtraBonus") || n.Contains("SpellID") || n.EndsWith("Charges") ||
                     n.StartsWith("Proc") || n.StartsWith("Poison")) && (pi.PropertyType == typeof(int) || pi.PropertyType == typeof(byte)))
                    v = Convert.ChangeType(0, pi.PropertyType);
                try
                {
                    pi.SetValue(t, v);
                }
                catch (Exception)
                {
                }
            }
            t.Id_nb = $"calib_{slot}_{type}_{Guid.NewGuid():N}".Substring(0, 40);
            t.Name = "plain " + ((eObjectType) type).ToString().ToLowerInvariant();
            t.Quality = 90;
            t.Condition = t.MaxCondition = 50000;
            t.Durability = t.MaxDurability = 50000;
            t.Realm = (int) realm;
            t.AllowUpdate = false;
            return t;
        }

        static readonly Dictionary<string, DbMob> _mobs = new(StringComparer.OrdinalIgnoreCase);

        static DbMob Template(string name)
        {
            if (_mobs.TryGetValue(name, out DbMob m))
                return m;
            m = GameServer.Database.SelectObjects<DbMob>(DB.Column("Name").IsEqualTo(name)).FirstOrDefault();
            _mobs[name] = m;
            return m;
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&calib", ePrivLevel.GM, "The power curve's test bench (TierCalibration) - a test character only!",
        "/calib run [levels 5,15,..] [fight seconds] [mob names separated by ;]  (every armour type with the first mob)",
        "/calib quick [levels] [secs] [mobs]  (the middle armour only)",
        "/calib base|spell|check [levels] [secs] [mobs]  (the one-footing baseline: DAoC's own numbers, a caster's spells, the fitted numbers)",
        "/calib stop")]
    public class CalibCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            string sub = args.Length > 1 ? args[1].ToLowerInvariant() : "";
            if (sub == "stop")
            {
                TierCalibration.Stop("stopped");
                return;
            }
            if (sub != "run" && sub != "quick" && sub != "base" && sub != "spell" && sub != "check")
            {
                DisplaySyntax(client);
                return;
            }
            int[] levels = args.Length > 2 ? args[2].Split(',', StringSplitOptions.RemoveEmptyEntries).Select(int.Parse).ToArray()
                : TierCalibration.DefaultLevels;
            int secs = args.Length > 3 ? int.Parse(args[3]) : 30;
            string[] mobs = args.Length > 4 ? string.Join(' ', args.Skip(4)).Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                : new[] { "rowdy", "lough wolf" };
            var mode = sub switch
            {
                "base" => TierCalibration.Mode.Base, "spell" => TierCalibration.Mode.Spell, "check" => TierCalibration.Mode.Check,
                _ => TierCalibration.Mode.Classic
            };
            string msg = TierCalibration.Start(client.Player, levels, mobs, secs * 1000, sub == "run", mode);
            client.Out.SendMessage("[Calib] " + msg, eChatType.CT_System, eChatLoc.CL_SystemWindow);
        }
    }
}
