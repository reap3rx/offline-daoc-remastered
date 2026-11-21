using System;
using DOL.Database;
using DOL.Events;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// The Quartermaster of Valor's potions (owner 2026-11-20 bugs doc: "Have two different types of potions for Health,
    /// Endurance, and Power: Regen buff ones (not usable in combat) and replenishing ones that are usable in combat"):
    ///   Draughts (usable in combat, a minute between uses): restore a share of your health / endurance / power at once.
    ///   Tonics (not in combat): ten minutes of strong regeneration while you are out of combat - a pulse every 3 seconds.
    /// Shares of your maximum, so one potion serves every level. Ten uses each, 1 Mark of Valor. Spells 30850-30855
    /// (scripted at start-up, the "Item Effects" line); templates valor_draught_* / valor_tonic_*.
    /// </summary>
    /// <summary>A potion's spell that can refuse to be drunk (GamePlayer's potion use asks before a charge is spent).</summary>
    public interface IDrinkCheck
    {
        /// <summary>Why it can't be drunk now (told to the player), or null.</summary>
        string WhyNot(GamePlayer drinker);
    }

    public static class ValorPotions
    {
        public enum Pool { Health = 0, Endurance = 1, Power = 2 }

        public static readonly (string Id, string Name, int Spell, Pool Pool, bool Tonic, int Model, string Desc)[] Kinds =
        [
            ("valor_draught_health", "Draught of Mending", 30850, Pool.Health, false, 2547,
                "Usable in combat: restores 30% of your health at once. One minute between uses."),
            ("valor_draught_endurance", "Draught of Second Wind", 30851, Pool.Endurance, false, 2546,
                "Usable in combat: restores 40% of your endurance at once. One minute between uses."),
            ("valor_draught_power", "Draught of Clarity", 30852, Pool.Power, false, 2545,
                "Usable in combat: restores 30% of your power at once. One minute between uses."),
            ("valor_tonic_health", "Tonic of Recovery", 30853, Pool.Health, true, 2547,
                "Not in combat: for ten minutes you recover 4% of your health every 3 seconds while out of combat."),
            ("valor_tonic_endurance", "Tonic of Vigor", 30854, Pool.Endurance, true, 2546,
                "Not in combat: for ten minutes you recover 5% of your endurance every 3 seconds while out of combat."),
            ("valor_tonic_power", "Tonic of Focus", 30855, Pool.Power, true, 2545,
                "Not in combat: for ten minutes you recover 4% of your power every 3 seconds while out of combat."),
        ];

        public const int TonicMinutes = 10, PulseMs = 3000, DraughtReuseS = 60;

        static double Share(Pool pool, bool tonic) => tonic ? (pool == Pool.Endurance ? 5 : 4) : (pool == Pool.Endurance ? 40 : 30);

        /// <summary>The templates (ValorQuartermasters.EnsureTemplates, at the start).</summary>
        internal static void EnsureTemplates()
        {
            var basis = GameServer.Database.FindObjectByKey<DbItemTemplate>("Elixir_of_Healing");
            foreach (var k in Kinds)
            {
                var t = GameServer.Database.FindObjectByKey<DbItemTemplate>(k.Id);
                bool fresh = t == null;
                t ??= new DbItemTemplate();
                t.Id_nb = k.Id; t.Name = k.Name; t.Model = k.Model;
                t.Object_Type = basis?.Object_Type ?? (int) eObjectType.Magical; t.Item_Type = basis?.Item_Type ?? 40;
                t.SpellID = k.Spell; t.Charges = 10; t.MaxCharges = 10; t.CanUseEvery = k.Tonic ? 5 : DraughtReuseS;
                t.Price = 1; t.Level = 1; t.Weight = 1; t.Quality = 100; t.Condition = 50_000; t.MaxCondition = 50_000;
                t.Durability = 50_000; t.MaxDurability = 50_000; t.PackSize = 1; t.MaxCount = 1; t.IsDropable = true; t.IsPickable = true;
                t.IsTradable = true; t.Description = k.Desc;
                if (fresh) GameServer.Database.AddObject(t); else GameServer.Database.SaveObject(t);
            }
        }

        [GameServerStartedEvent]
        public static void OnServerStarted(DOLEvent e, object sender, EventArgs args)
        {
            try
            {
                foreach (var k in Kinds)
                {
                    if (SkillBase.GetSpellByID(k.Spell) is Spell taken)
                    {
                        Console.WriteLine($"[ValorPotions] spell {k.Spell} is already {taken.Name}");
                        continue;
                    }
                    var d = new DbSpell
                    {
                        SpellID = k.Spell, Name = k.Name, Type = k.Tonic ? "ValorTonic" : "ValorDraught", Target = "Self",
                        Value = Share(k.Pool, k.Tonic), DamageType = (int) k.Pool, Duration = k.Tonic ? TonicMinutes * 60 : 0,
                        Frequency = k.Tonic ? PulseMs / 100 : 0, ClientEffect = IconFor(k.Pool, k.Tonic),
                        Icon = IconFor(k.Pool, k.Tonic), Description = k.Desc,
                        SpellGroup = k.Spell, SharedTimerGroup = k.Spell,   // (its own reuse: GamePlayer's potion timer goes by this)
                    };
                    SkillBase.AddScriptedSpell(GlobalSpellsLines.Item_Effects, new Spell(d, 1));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ValorPotions] " + ex);
            }
        }

        /// <summary>Restore a share of a pool's maximum; how much it gave.</summary>
        public static int Restore(GameLiving t, Pool pool, double percent)
        {
            switch (pool)
            {
                case Pool.Health:
                {
                    int want = Math.Min(t.MaxHealth - t.Health, (int) Math.Ceiling(t.MaxHealth * percent / 100));
                    if (want > 0) t.ChangeHealth(t, eHealthChangeType.Spell, want);
                    return Math.Max(0, want);
                }
                case Pool.Endurance:
                {
                    int want = Math.Min(t.MaxEndurance - t.Endurance, (int) Math.Ceiling(t.MaxEndurance * percent / 100));
                    if (want > 0) t.ChangeEndurance(t, eEnduranceChangeType.Spell, want);
                    return Math.Max(0, want);
                }
                default:
                {
                    int want = Math.Min(t.MaxMana - t.Mana, (int) Math.Ceiling(t.MaxMana * percent / 100));
                    if (want > 0) t.ChangeMana(t, eManaChangeType.Spell, want);
                    return Math.Max(0, want);
                }
            }
        }

        /// <summary>The game's own icons (owner 2026-11-20: the Tonic of Vigor showed a speed buff's): the regeneration
        /// buffs' for the tonics, a heal / endurance restore / power buff for the draughts.</summary>
        static int IconFor(Pool p, bool tonic) => (p, tonic) switch
        {
            (Pool.Health, true) => 8077, (Pool.Endurance, true) => 8079, (Pool.Power, true) => 8084,
            (Pool.Health, false) => 4851, (Pool.Endurance, false) => 8064, _ => 979
        };

        public static string Word(Pool p) => p switch { Pool.Health => "health", Pool.Endurance => "endurance", _ => "power" };
    }
}

namespace DOL.GS.Spells
{
    /// <summary>A Draught (ValorPotions): a share of a pool back at once - in combat too.</summary>
    [SpellHandler(eSpellType.ValorDraught)]
    public class ValorDraughtSpellHandler : SpellHandler, IDrinkCheck
    {
        public ValorDraughtSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription => $"Restores {Spell.Value}% of your {ValorPotions.Word((ValorPotions.Pool) Spell.DamageType)} at once.";

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        /// <summary>Already full: not drunk (no charge spent, no wait started).</summary>
        public string WhyNot(GamePlayer p)
        {
            var pool = (ValorPotions.Pool) Spell.DamageType;
            bool full = pool switch
            {
                ValorPotions.Pool.Health => p.Health >= p.MaxHealth,
                ValorPotions.Pool.Endurance => p.Endurance >= p.MaxEndurance,
                _ => p.Mana >= p.MaxMana
            };
            return full ? $"Your {ValorPotions.Word(pool)} is already full." : null;
        }

        public override void OnDirectEffect(GameLiving target)
        {
            if (target == null || !target.IsAlive)
                return;
            var pool = (ValorPotions.Pool) Spell.DamageType;
            int got = ValorPotions.Restore(target, pool, Spell.Value);
            SendEffectAnimation(target, 0, false, 1);
            MessageToLiving(target, got > 0 ? $"You recover {got} {ValorPotions.Word(pool)}." : $"Your {ValorPotions.Word(pool)} is already full.", eChatType.CT_Spell);
        }
    }

    /// <summary>A Tonic (ValorPotions): ten minutes of strong regeneration while out of combat; not drunk in combat.</summary>
    [SpellHandler(eSpellType.ValorTonic)]
    public class ValorTonicSpellHandler : HoTSpellHandler, IDrinkCheck
    {
        public ValorTonicSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription =>
            $"For {Spell.Duration / 60000} minutes, out of combat, you recover {Spell.Value}% of your {ValorPotions.Word((ValorPotions.Pool) Spell.DamageType)} every {Spell.Frequency / 1000} seconds.";

        public string WhyNot(GamePlayer p) => p.InCombat ? "You can't drink a tonic in the middle of a fight." : null;

        public override void OnDirectEffect(GameLiving target)
        {
            if (target == null || !target.IsAlive || target.ObjectState != GameObject.eObjectState.Active || target.InCombat)
                return;
            ValorPotions.Restore(target, (ValorPotions.Pool) Spell.DamageType, Spell.Value);   // (quietly, every pulse)
        }
    }
}
