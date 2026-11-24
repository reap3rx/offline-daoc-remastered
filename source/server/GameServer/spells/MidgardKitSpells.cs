using System;
using System.Linq;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS.Spells
{
    /// <summary>Spiritmaster - Ward of the Einherjar's call (MidgardKits): whatever struck the caster draws its spirit
    /// warrior's fury - the pet turns on it, and it turns on the pet.</summary>
    [SpellHandler(eSpellType.EinherjarCall)]
    public class EinherjarCallSpellHandler : SpellHandler
    {
        public EinherjarCallSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription => "Your spirit warrior turns on whatever struck you, and it turns on your spirit warrior.";

        public override void OnDirectEffect(GameLiving target)
        {
            if (target == null || !target.IsAlive || Caster?.ControlledBrain is not IControlledBrain pet || pet.Body is not GameNPC body ||
                !body.IsAlive || !body.IsWithinRadius(Caster, 2000))
                return;
            pet.Attack(target);
            if (target is GameNPC foe && foe.Brain is StandardMobBrain b)
                b.AddToAggroList(body, 200 + Caster.Level * 20);
            foreach (GamePlayer v in body.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(body, target, (ushort) Spell.ClientEffect, 0, false, 1);
            MessageToCaster($"The einherjar answer - your spirit warrior turns on {target.GetName(0, false)}!", eChatType.CT_Spell);
        }
    }

    /// <summary>Spiritmaster - Valhalla's Charge (MidgardKits): the spirit warrior leaps to the target, stuns it
    /// (SubSpellID) and holds its anger.</summary>
    [SpellHandler(eSpellType.ValhallaCharge)]
    public class ValhallaChargeSpellHandler : SpellHandler
    {
        public ValhallaChargeSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription => "Your spirit warrior leaps to your target, stuns it for 2 seconds and holds its anger.";

        public override bool CheckBeginCast(GameLiving selectedTarget)
        {
            if (Caster.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive)
            {
                MessageToCaster("You have no spirit warrior to send.", eChatType.CT_SpellResisted);
                return false;
            }
            return base.CheckBeginCast(selectedTarget);
        }

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            if (target == null || !target.IsAlive || Caster?.ControlledBrain is not IControlledBrain brain || brain.Body is not GameNPC pet || !pet.IsAlive)
                return;
            double dx = pet.X - target.X, dy = pet.Y - target.Y, d = Math.Max(1, Math.Sqrt(dx * dx + dy * dy));
            int x = target.X + (int) (dx / d * 60), y = target.Y + (int) (dy / d * 60);
            pet.MoveTo(target.CurrentRegionID, x, y, target.Z, pet.Heading);
            pet.TurnTo(target);
            ClassKitSpellHelp.Sub(Caster, Spell.SubSpellID, target);
            brain.Attack(target);
            if (target is GameNPC foe && foe.Brain is StandardMobBrain b)
                b.AddToAggroList(pet, 500 + Caster.Level * 40);
            foreach (GamePlayer v in pet.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellEffectAnimation(pet, target, (ushort) Spell.ClientEffect, 0, false, 1);
            MessageToCaster($"Your spirit warrior crashes into {target.GetName(0, false)}!", eChatType.CT_Spell);
        }
    }

    /// <summary>Bonedancer - Grasping Bones (MidgardKits): Thorn Wall's line, of skeletal hands; it slows what crosses it.</summary>
    [SpellHandler(eSpellType.GraspingBones)]
    public class GraspingBonesSpellHandler : ThornWallSpellHandler
    {
        public GraspingBonesSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        protected override ushort PropModel => 1704;
        protected override byte PropSize => 14;
        protected override string PropName => "grasping bones";

        protected override void OnProp(GameNPC prop)
        {
            if (prop == null)
                return;
            long until = GameLoop.GameLoopTime + Spell.Duration;
            new ECSGameTimer(prop, _ =>
            {
                if (GameLoop.GameLoopTime > until || prop.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                foreach (GamePlayer v in prop.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendSpellEffectAnimation(prop, prop, (ushort) Spell.ClientEffect, 0, false, 1);
                return 2000;
            }, 100);
        }

        public override string ShortDescription =>
            $"Skeletal hands claw up across the ground for {Spell.Duration / 1000} seconds; enemies in them are slowed 50%.";
    }

    /// <summary>Bonedancer - March of the Dead (MidgardKits): the commander and every minion turn on the target and attack
    /// 25% faster for the Duration.</summary>
    [SpellHandler(eSpellType.MarchOfTheDead)]
    public class MarchOfTheDeadSpellHandler : SpellHandler
    {
        public MarchOfTheDeadSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"Your commander and every minion turn on your target and attack 25% faster for {Spell.Duration / 1000} seconds.";

        public override bool CheckBeginCast(GameLiving selectedTarget)
        {
            if (Caster.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive)
            {
                MessageToCaster("You have no army to command.", eChatType.CT_SpellResisted);
                return false;
            }
            return base.CheckBeginCast(selectedTarget);
        }

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            if (target == null || !target.IsAlive)
                return;
            MidgardKits.March(Caster, target, Math.Max(1000, Spell.Duration));
            MessageToCaster($"The dead march on {target.GetName(0, false)}!", eChatType.CT_Spell);
        }
    }

    /// <summary>Shaman - Mycelial Ring (MidgardKits): Verdant Pulse's circle, of fungus; enemies in it are slowed (SubSpellID).</summary>
    [SpellHandler(eSpellType.MycelialRing)]
    public class MycelialRingSpellHandler : VerdantPulseSpellHandler
    {
        public MycelialRingSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        protected override ushort PropModel => 1211;
        protected override byte PropSize => 18;
        protected override string PropName => "mycelial ring";

        protected override void OnProp(GameNPC prop)
        {
            if (prop == null)
                return;
            GameLiving c = Caster;
            var at = new Point3D(prop.X, prop.Y, prop.Z);
            long until = GameLoop.GameLoopTime + Spell.Duration;
            int reach = Math.Max(150, Spell.Radius);
            new ECSGameTimer(prop, _ =>
            {
                if (GameLoop.GameLoopTime > until || prop.ObjectState != GameObject.eObjectState.Active || c == null)
                    return 0;
                foreach (GameLiving foe in ClassKitSpellHelp.FoesNear(c, at, reach))
                    ClassKitSpellHelp.Sub(c, Spell.SubSpellID, foe);
                foreach (GamePlayer v in prop.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendSpellEffectAnimation(prop, prop, (ushort) Spell.ClientEffect, 0, false, 1);
                return 2000;
            }, 200);
        }

        public override string ShortDescription =>
            $"A ring of fungus at your feet for {Spell.Duration / 1000} seconds: your side heals within it every 2 seconds, and enemies in it are slowed.";
    }
}
