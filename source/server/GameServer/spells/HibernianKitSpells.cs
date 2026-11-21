namespace DOL.GS.Spells
{
    /// <summary>The Druid's Rejuvenation (HibernianKits): a heal over time on a friend stacking to three; cast on three
    /// stacks it Blooms. Value: the heal each 3 seconds a stack.</summary>
    [SpellHandler(eSpellType.Rejuvenation)]
    public class RejuvenationSpellHandler : SpellHandler
    {
        public RejuvenationSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription =>
            $"Heals {Spell.Value} every 3 seconds for 15 seconds, stacking three times. Cast on three stacks it Blooms: the rest at once, and half again.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override void OnDirectEffect(GameLiving target) => HibernianKits.Rejuvenate(Caster, target, Spell);

        public override bool HasPositiveEffect => true;
    }

    /// <summary>The Druid's Gift of the Wild (HibernianKits): every buff the Druid knows on each of the group.</summary>
    [SpellHandler(eSpellType.GiftOfTheWild)]
    public class GiftOfTheWildSpellHandler : SpellHandler
    {
        public GiftOfTheWildSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        public override string ShortDescription => "Every buff you know - armor, strength, constitution, dexterity, quickness, acuity, haste - on your whole group.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override void OnDirectEffect(GameLiving target) => HibernianKits.GiveGift(Caster, target);

        public override bool HasPositiveEffect => true;
    }
}
