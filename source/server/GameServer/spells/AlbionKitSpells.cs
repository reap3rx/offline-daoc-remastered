using System;
using System.Linq;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS.Spells
{
    /// <summary>Wizard - Rune of Embers (AlbionKits): a rune at your feet; the first enemy to step on it is burned and its
    /// swing broken. Radius: its reach; Duration: how long it waits; SubSpellID: the burst.</summary>
    [SpellHandler(eSpellType.RuneOfEmbers)]
    public class RuneOfEmbersSpellHandler : SpellHandler
    {
        public RuneOfEmbersSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"A rune of embers at your feet for {Spell.Duration / 1000} seconds: the first enemy to step on it is burned and its swing broken.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            GameLiving c = Caster;
            if (c?.CurrentRegion == null || !c.IsAlive)
                return;
            var at = new Point3D(c.X, c.Y, c.Z);
            GameNPC rune = ClassKitSpellHelp.Prop(c, at, 1704, 12, "rune of embers", GameNPC.eFlags.PEACE | GameNPC.eFlags.DONTSHOWNAME | GameNPC.eFlags.GHOST,
                Spell.Duration);
            long until = GameLoop.GameLoopTime + Spell.Duration;
            long nextFx = 0;
            int reach = Math.Max(100, Spell.Radius);
            new ECSGameTimer(c, _ =>
            {
                long now = GameLoop.GameLoopTime;
                if (now > until || c.ObjectState != GameObject.eObjectState.Active || rune == null || rune.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                if (now >= nextFx)
                {
                    nextFx = now + 2000;
                    foreach (GamePlayer v in rune.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                        v.Out.SendSpellEffectAnimation(rune, rune, (ushort) Spell.ClientEffect, 0, false, 1);
                }
                GameLiving foe = ClassKitSpellHelp.FoesNear(c, at, reach).FirstOrDefault();
                if (foe == null)
                    return 250;
                ClassKitSpellHelp.Sub(c, Spell.SubSpellID, foe);
                ClassKitSpellHelp.Sub(c, AlbionKits.RuneStagger, foe);
                MessageToCaster($"Your rune bursts under {foe.GetName(0, false)}!", eChatType.CT_Spell);
                rune.Delete();
                return 0;
            }, 300);
        }
    }

    /// <summary>Wizard - Ice Shell (AlbionKits): frozen in ice for its Duration - nothing hurts you, you can't act.</summary>
    [SpellHandler(eSpellType.IceShell)]
    public class IceShellSpellHandler : SpellHandler
    {
        public IceShellSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"Instant: you freeze in a shell of ice for {Spell.Duration / 1000} seconds - nothing hurts you, and you can't act.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            if (Caster == null || !Caster.IsAlive)
                return;
            AlbionKits.Shell(Caster, Math.Max(1000, Spell.Duration), (ushort) Spell.ClientEffect);
            MessageToCaster("Ice closes over you - nothing can touch you.", eChatType.CT_Spell);
        }

        public override bool HasPositiveEffect => true;
    }

    /// <summary>Theurgist - Wall of Ice (AlbionKits): ThornWall's wall, of ice; it chills what crosses it.</summary>
    [SpellHandler(eSpellType.IceWall)]
    public class IceWallSpellHandler : ThornWallSpellHandler
    {
        public IceWallSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        protected override ushort PropModel => 1704;
        protected override byte PropSize => 14;
        protected override string PropName => "wall of ice";

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
            $"A wall of ice stands across the ground for {Spell.Duration / 1000} seconds; whatever crosses it is chilled and attacks slower.";
    }

    /// <summary>Cleric - Sanctuary (AlbionKits): Verdant Pulse's circle, of holy light.</summary>
    [SpellHandler(eSpellType.Sanctuary)]
    public class SanctuarySpellHandler : VerdantPulseSpellHandler
    {
        public SanctuarySpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        protected override ushort PropModel => 1704;
        protected override byte PropSize => 16;
        protected override string PropName => "sanctuary";

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
                return 3000;
            }, 100);
        }

        public override string ShortDescription =>
            $"A circle of holy light at your feet for {Spell.Duration / 1000} seconds, healing your side within it every 2 seconds.";
    }

    /// <summary>Sorcerer - Thrall's Sacrifice (AlbionKits): for its Duration your charmed pet takes half of each blow on you,
    /// to Value, while it's near.</summary>
    [SpellHandler(eSpellType.ThrallsSacrifice)]
    public class ThrallsSacrificeSpellHandler : SpellHandler
    {
        public ThrallsSacrificeSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"Your charmed pet throws itself in the way: for {Spell.Duration / 1000} seconds half of each blow on you goes to it instead (up to {Spell.Value}).";

        public override bool CheckBeginCast(GameLiving selectedTarget)
        {
            if (Caster.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive)
            {
                MessageToCaster("You have no thrall to sacrifice.", eChatType.CT_SpellResisted);
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
            AlbionKits.StartThrall(Caster, (int) Spell.Value, Math.Max(1000, Spell.Duration));
            if (Caster.ControlledBrain?.Body is GameNPC pet)
                foreach (GamePlayer v in pet.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendSpellEffectAnimation(Caster, pet, (ushort) Spell.ClientEffect, 0, false, 1);
            MessageToCaster("Your thrall stands between you and harm.", eChatType.CT_Spell);
        }

        public override bool HasPositiveEffect => true;
    }

    /// <summary>Cabalist - Simulacrum Swap (AlbionKits): you and your simulacrum trade places; whatever was on you turns on it.</summary>
    [SpellHandler(eSpellType.SimulacrumSwap)]
    public class SimulacrumSwapSpellHandler : SpellHandler
    {
        public SimulacrumSwapSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription => "Instant: you and your simulacrum trade places, and whatever was on you turns on it.";

        public override bool CheckBeginCast(GameLiving selectedTarget)
        {
            if (Caster.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive || !Caster.IsWithinRadius(pet, 2000))
            {
                MessageToCaster("Your simulacrum must be near to trade places with it.", eChatType.CT_SpellResisted);
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
            GameLiving c = Caster;
            if (c?.ControlledBrain?.Body is not GameNPC pet || !pet.IsAlive)
                return;
            int cx = c.X, cy = c.Y, cz = c.Z;
            ushort ch = c.Heading;
            c.MoveTo(c.CurrentRegionID, pet.X, pet.Y, pet.Z, pet.Heading);
            pet.MoveTo(pet.CurrentRegionID, cx, cy, cz, ch);
            foreach (GameNPC foe in pet.GetNPCsInRadius(2000))
                if (foe.IsAlive && foe.Brain is StandardMobBrain b && foe.TargetObject == c)
                    b.AddToAggroList(pet, 100000);
            foreach (GamePlayer v in c.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
            {
                v.Out.SendSpellEffectAnimation(c, c, (ushort) Spell.ClientEffect, 0, false, 1);
                v.Out.SendSpellEffectAnimation(c, pet, (ushort) Spell.ClientEffect, 0, false, 1);
            }
        }

        public override bool HasPositiveEffect => true;
    }

    /// <summary>Friar - Habit of the Order; Cleric - Blessing of Avalon (AlbionKits): every buff the healer knows on each of
    /// the group.</summary>
    [SpellHandler(eSpellType.AlbionBlessing)]
    public class AlbionBlessingSpellHandler : SpellHandler
    {
        public AlbionBlessingSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription => Spell.Description;

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override void OnDirectEffect(GameLiving target) => AlbionKits.Bless(Caster, target, Spell);

        public override bool HasPositiveEffect => true;
    }
}
