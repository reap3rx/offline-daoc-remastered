namespace DOL.GS.Spells
{
	[SpellHandler(eSpellType.NightshadeNuke)]
	public class NightshadeNuke : DirectDamageSpellHandler
	{
		public NightshadeNuke(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

		/// <summary>Dart of Night also breaks the target's spell (HibernianHybrids).</summary>
		public override void OnDirectEffect(GameLiving target)
		{
			base.OnDirectEffect(target);
			HibernianHybrids.AfterNightshadeNuke(Caster, Spell, target);
		}
	}
}
