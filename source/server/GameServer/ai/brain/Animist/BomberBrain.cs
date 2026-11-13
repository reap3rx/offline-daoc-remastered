using System.Reflection;
using DOL.GS;
using DOL.GS.Spells;

namespace DOL.AI.Brain
{
    public class BomberBrain : ControlledMobBrain
    {
        private static readonly Logging.Logger log = Logging.LoggerManager.Create(MethodBase.GetCurrentMethod().DeclaringType);

        private Spell _spell;
        private SpellLine _spellLine;
        private long _expireTime = GameLoop.GameLoopTime + 60 * 1000;

        public BomberBrain(GameLiving owner, Spell spell, SpellLine spellLine) : base(owner)
        {
            _spell = spell;
            _spellLine = spellLine;
        }

        public override int ThinkInterval => 300;

        public override void Think()
        {
            if (GameLoop.GameLoopTime >= _expireTime)
                Body.Delete();

            if (Body.IsWithinRadius(Body.TargetObject, 150))
                DeliverPayload();
        }

        private void DeliverPayload()
        {
            Spell subSpell = SkillBase.GetSpellByID(_spell.SubSpellID);

            if (subSpell == null)
            {
                if (log.IsErrorEnabled && subSpell == null)
                    log.Error("Bomber SubspellID for Bomber SpellID: " + _spell.ID + " is not implemented yet");

                Body.Delete();
                return;
            }

            subSpell.Level = _spell.Level;

            if (Body.IsWithinRadius(Body.TargetObject, 350))
            {
                ISpellHandler spellHandler = ScriptMgr.CreateSpellHandler(m_owner, subSpell, SkillBase.GetSpellLine(_spellLine.KeyName));
                spellHandler.StartSpell(Body.TargetObject as GameLiving);
            }

            // gone, not dead (owner 2026-11-12: the wisp "falls and melts into the ground" - a health of 0 first made
            // the client keep it as a corpse that sinks; removed alive it simply vanishes as the payload goes off)
            Body.Delete();
        }

        public override void FollowOwner() { }
        public override void UpdatePetWindow() { }
    }
}
