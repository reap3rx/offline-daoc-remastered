using DOL.Database;
using DOL.GS.PacketHandler;
using DOL.GS.Styles;
using DOL.Language;

namespace DOL.GS
{
    public class PlayerAttackAction : AttackAction
    {
        private GamePlayer _playerOwner;
        private bool _quickSwing;               // Action Combat: this round is a plain swing (its damage by the time since the last)
        private Style _reactiveStyle;           // Action Combat: the reactive style this round uses ...
        private AttackData _reactiveOpening;    // ... and the opening it answers (spent once it lands)

        public PlayerAttackAction(GamePlayer owner) : base(owner)
        {
            _playerOwner = owner;
        }

        public override void OnAimInterrupt(GameObject attacker)
        {
            string attackTypeMsg;

            if (_playerOwner.ActiveWeapon != null && _playerOwner.ActiveWeapon.Object_Type == (int)eObjectType.Thrown)
                attackTypeMsg = LanguageMgr.GetTranslation(_playerOwner.Client.Account.Language, "GamePlayer.Attack.Type.Throw");
            else
                attackTypeMsg = LanguageMgr.GetTranslation(_playerOwner.Client.Account.Language, "GamePlayer.Attack.Type.Shot");

            if (attacker is GameNPC npcAttacker)
                _playerOwner.Out.SendMessage(LanguageMgr.GetTranslation(_playerOwner.Client.Account.Language, "GamePlayer.Attack.Interrupted", attacker.GetName(0, true, _playerOwner.Client.Account.Language, npcAttacker), attackTypeMsg), eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
            else
                _playerOwner.Out.SendMessage(LanguageMgr.GetTranslation(_playerOwner.Client.Account.Language, "GamePlayer.Attack.Interrupted", attacker.GetName(0, true), attackTypeMsg), eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
        }

        protected override bool PrepareMeleeAttack()
        {
            // Action Combat: no auto-attack - a round only happens for a click (a swing or a style).
            ActionCombatState action = _playerOwner.ActionCombat;

            if (action is { Enabled: true })
            {
                if (_target == null)
                {
                    action.SwingQueued = false;
                    ActionCombat.ClearReady(_playerOwner);
                    _interval = TICK_INTERVAL_FOR_NON_ATTACK;
                    return false;
                }

                ActionCombat.PollReady(_playerOwner);

                if (!action.SwingQueued && StyleComponent.NextCombatStyle == null)
                {
                    _interval = ActionCombat.IdlePollMs;
                    return false;
                }
            }

            _combatStyle = StyleComponent.GetStyleToUse();

            // Action Combat: a reaction answers one opening only (no spamming a reactive off one parry).
            _reactiveStyle = null;
            _reactiveOpening = null;

            if (action is { Enabled: true } && _combatStyle != null)
            {
                if (ActionCombat.IsOpeningSpent(_playerOwner, _combatStyle))
                    _combatStyle = null;
                else if (ActionCombat.KindOf(_combatStyle) == "reactive")
                {
                    _reactiveStyle = _combatStyle;
                    _reactiveOpening = ActionCombat.OpeningOf(_playerOwner, _combatStyle);
                }
            }

            // Check if we still have enough endurance for the style and update `_weapon` if needed.
            if (_combatStyle != null)
            {
                DbInventoryItem styleWeapon = (eObjectType) _combatStyle.WeaponTypeRequirement is eObjectType.Shield ? _leftWeapon : _weapon;

                if (styleWeapon != null && !StyleProcessor.CheckEnduranceCost(_playerOwner, styleWeapon, _combatStyle))
                    _combatStyle = null;
                else
                    _weapon = styleWeapon;
            }

            // Action Combat: a plain swing lands for the share of the weapon's swing time since the last blow.
            _quickSwing = action is { Enabled: true } && _combatStyle == null;

            if (_quickSwing)
                _effectiveness *= ActionCombat.QuickDamageFor(ActionCombat.SinceLastSwing(_playerOwner), ActionCombat.FullSwingMs(_playerOwner));

            return base.PrepareMeleeAttack();
        }

        protected override bool PrepareRangedAttack()
        {
            // Action Combat: shots are drawn and loosed by hand (ActionCombat.StartDraw / Loose), never by attack mode.
            if (_playerOwner.ActionCombat is { Enabled: true })
            {
                _interval = TICK_INTERVAL_FOR_NON_ATTACK;
                return false;
            }

            if (base.PrepareRangedAttack())
            {
                // This is also done in weaponAction.Execute(), but we must unstealth immediately if the call is delayed.
                if (_ticksToTarget > 0)
                    _playerOwner.Stealth(false);

                return true;
            }

            return false;
        }

        protected override void PerformRangedAttack()
        {
            _playerOwner.rangeAttackComponent.RemoveEnduranceAndAmmoOnShot();
            base.PerformRangedAttack();

            if (_playerOwner.rangeAttackComponent.Ammo.Count == 0)
                _playerOwner.rangeAttackComponent.UpdateAmmo(_playerOwner.ActiveWeapon);
        }

        protected override bool FinalizeMeleeAttack()
        {
            bool attacked = base.FinalizeMeleeAttack();
            ActionCombatState action = _playerOwner.ActionCombat;

            if (action is { Enabled: true })
            {
                // The click is spent either way: out of range or not facing it is a whiff, never a buffered swing.
                action.SwingQueued = false;
                StyleComponent.NextCombatStyle = null;
                StyleComponent.NextCombatBackupStyle = null;

                int full = AttackComponent.AttackSpeed(_weapon, _leftWeapon);

                if (!attacked)
                {
                    ActionCombat.MarkSwing(_playerOwner, full / 2);                // a whiff still costs a moment
                    ActionCombat.Send(_playerOwner, "whiff");
                    _interval = ActionCombat.IdlePollMs;
                    return false;
                }

                if (_reactiveStyle != null)
                    ActionCombat.SpendOpening(_playerOwner, _reactiveStyle, _reactiveOpening);

                ActionCombat.MarkSwing(_playerOwner, full);

                if (action.FumblePending)
                {
                    action.FumblePending = false;
                    action.FumbledUntil = GameLoop.GameLoopTime + full * 2;
                    ActionCombat.Send(_playerOwner, "timer|" + (full * 2) + "|" + (full * 2));
                }

                // the action only polls from here: the next click (QueueSwing / QueueStyle) brings its round forward
                _interval = ActionCombat.IdlePollMs;
                ActionCombat.PollReady(_playerOwner, true);
            }

            if (attacked)
            {
                if (_playerOwner.UseDetailedCombatLog)
                    _playerOwner.Out.SendMessage($"Attack Speed: {_interval / 1000.0}s", eChatType.CT_DamageAdd, eChatLoc.CL_SystemWindow);

                StyleComponent.NextCombatStyle = null;
                StyleComponent.NextCombatBackupStyle = null;
                return true;
            }

            return false;
        }

        public override void CleanUp()
        {
            ActionCombatState action = _playerOwner.ActionCombat;

            if (action is { Enabled: true })
            {
                action.SwingQueued = false;
                ActionCombat.ClearReady(_playerOwner);
            }

            base.CleanUp();
        }

        protected override bool FinalizeRangedAttack()
        {
            bool stopAttack = false;

            if (_playerOwner.rangeAttackComponent.RangedAttackState is not eRangedAttackState.AimFireReload)
                stopAttack = true;
            else if (_playerOwner.Endurance < RangeAttackComponent.DEFAULT_ENDURANCE_COST)
            {
                stopAttack = true;
                _playerOwner.Out.SendMessage(LanguageMgr.GetTranslation(_playerOwner.Client.Account.Language, "GamePlayer.StartAttack.TiredUse", _weapon.Name), eChatType.CT_YouHit, eChatLoc.CL_SystemWindow);
            }
            else
            {
                DbInventoryItem ammo = _playerOwner.rangeAttackComponent.Ammo;

                if (ammo == null || ammo.Count == 0)
                    stopAttack = true;
            }

            if (stopAttack)
            {
                _playerOwner.rangeAttackComponent.RangedAttackState = eRangedAttackState.None;
                AttackComponent.StopAttack();
                return false;
            }

            return base.FinalizeRangedAttack();
        }
    }
}
