using System;
using System.Reflection;
using DOL.Database;

namespace DOL.GS.DatabaseUpdate
{
    /// <summary>
    /// The loot overhaul's rows, made at every start (before the spells load): the forged weapons' proc spells - fire,
    /// frost, spark and snare, eight level bands each like the world's own ROG procs (8100-8137) - and the templates:
    /// the novelty potions and the Bubbling Flask, the treasure map, the companion kit token, and the Quartermaster of
    /// Valor's list (ValorQuartermasters.EnsureTemplates).
    /// </summary>
    [DatabaseUpdate]
    public class LootOverhaulDatabase : IDatabaseUpdater
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        static readonly double[] DdDamage = [6, 12, 17, 23, 29, 35, 40, 46];      // the world's DD procs (8020-8027)
        static readonly int[] BandLevel = [5, 10, 15, 20, 25, 30, 35, 40];

        public void Update()
        {
            try
            {
                for (int b = 0; b < 8; b++)
                {
                    Spell(LootOverhaul.ProcHeat + b, $"Level {BandLevel[b]} Fire Proc", "DirectDamage", 13, DdDamage[b], 0, 0, 4050, $"Burns the target for {DdDamage[b]}.");
                    Spell(LootOverhaul.ProcCold + b, $"Level {BandLevel[b]} Frost Proc", "DirectDamage", 11, DdDamage[b], 0, 0, 4504, $"Freezes the target for {DdDamage[b]}.");
                    Spell(LootOverhaul.ProcEnergy + b, $"Level {BandLevel[b]} Spark Proc", "DirectDamage", 12, DdDamage[b], 0, 0, 4355, $"Shocks the target for {DdDamage[b]}.");
                    Spell(LootOverhaul.ProcSnare + b, $"Level {BandLevel[b]} Rune Snare Proc", "SpeedDecrease", 10, 0, 35, 8, 873, "Slows the target by 35% for 8 seconds.");
                }
                foreach (var k in NoveltyPotions.Kinds)
                    Item(k.Id, k.Name, k.Model, 2, 20, k.Description);
                Item(NoveltyPotions.FlaskId, NoveltyPotions.FlaskName, 490, 2, 20,
                    "Bubbling Flask - who knows? Drink it and see, or have a merchant name it (/identify, 5 silver).");
                Item(LootUses.MapId, "Treasure Map", 498, 500, 5, "A rough map of this part of the world with a chest marked on it. Use it where you found it: the chest is marked on your map.");
                Item(LootUses.KitTokenId, "Companion Kit Token", 485, 10, 5, "Refits your companion's own kit at your level (what you gave it, and what it found, stay on).");
                ValorQuartermasters.EnsureTemplates();
            }
            catch (Exception e)
            {
                log.Error("Loot overhaul rows", e);
            }
        }

        static void Spell(int id, string name, string type, int damageType, double damage, double value, int duration, int effect, string description)
        {
            var s = GameServer.Database.FindObjectByKey<DbSpell>(id);
            bool fresh = s == null;
            s ??= new DbSpell();
            s.SpellID = id; s.Name = name; s.Type = type; s.DamageType = damageType; s.Damage = damage; s.Value = value;
            s.Duration = duration; s.ClientEffect = effect; s.Icon = effect; s.Target = "Enemy"; s.Description = description;
            s.Range = 0; s.Power = 0; s.CastTime = 0; s.PackageID = "LootOverhaul";
            if (fresh) GameServer.Database.AddObject(s); else GameServer.Database.SaveObject(s);
        }

        static void Item(string id, string name, int model, long price, int maxCount, string description)
        {
            var t = GameServer.Database.FindObjectByKey<DbItemTemplate>(id);
            bool fresh = t == null;
            t ??= new DbItemTemplate();
            t.Id_nb = id; t.Name = name; t.Model = model; t.Price = price; t.MaxCount = maxCount; t.PackSize = 1;
            t.Object_Type = (int) eObjectType.GenericItem; t.Item_Type = 0; t.Level = 1; t.Weight = 1; t.Realm = 0;
            t.Quality = 100; t.Condition = 50_000; t.MaxCondition = 50_000; t.Durability = 50_000; t.MaxDurability = 50_000;
            t.IsDropable = true; t.IsPickable = true; t.IsTradable = true; t.CanDropAsLoot = true; t.Description = description;
            if (fresh) GameServer.Database.AddObject(t); else GameServer.Database.SaveObject(t);
        }
    }
}
