using DOL.GS;

namespace DOL.AI.Brain
{
    /// <summary>
    /// A brain for the commanders
    /// </summary>
    public class CommanderBrain : ControlledMobBrain
	{
		public CommanderBrain(GameLiving owner) : base(owner) { }

        public bool MinionsAssisting => Body is CommanderPet commander && commander.MinionsAssisting;

        /// <summary>
        /// Determines if a given controlled brain is part of the commanders subpets
        /// </summary>
        /// <param name="brain">The brain to check</param>
        /// <returns>True if found, else false</returns>
        public bool FindPet(IControlledBrain brain)
		{
			if (Body.ControlledNpcList != null)
			{
				lock ((Body as CommanderPet).ControlledNpcListLock)
				{
					foreach (IControlledBrain icb in Body.ControlledNpcList)
					{
						if (brain == icb)
							return true;
					}
				}
			}

			return false;
		}

		public override void OnAttackedByEnemy(AttackData ad)
		{
			base.OnAttackedByEnemy(ad);

			// Notify subpets.
			if (Body.ControlledNpcList != null)
			{
				foreach (var controlledBrain in Body.ControlledNpcList)
				{
					if (controlledBrain is BdPetBrain bdPetBrain)
						bdPetBrain.OnOwnerAttacked(ad);
				}
			}
		}

		public override void OnOwnerAttacked(AttackData ad)
		{
			base.OnOwnerAttacked(ad);

			// Notify subpets.
			if (Body.ControlledNpcList != null)
			{
				foreach (var controlledBrain in Body.ControlledNpcList)
				{
					if (controlledBrain is BdPetBrain bdPetBrain)
						bdPetBrain.OnOwnerAttacked(ad);
				}
			}
		}

		/// <summary>
		/// Attack the target on command
		/// </summary>
		/// <param name="target">The target to attack</param>
		public override void Attack(GameObject target)
		{
			base.Attack(target);

			if (MinionsAssisting && Body.ControlledNpcList != null)
			{
				lock ((Body as CommanderPet).ControlledNpcListLock)
				{
					foreach (BdPetBrain icb in Body.ControlledNpcList)
						icb?.Attack(target);
				}
			}
		}

		public override void Disengage()
		{
			base.Disengage();

			if (Body.ControlledNpcList != null)
			{
				lock ((Body as CommanderPet).ControlledNpcListLock)
				{
					foreach (BdPetBrain icb in Body.ControlledNpcList)
					{
						if (icb != null)
							icb.Disengage();
					}
				}
			}
		}

		/// <summary>
		/// Defend a minion that is being attacked
		/// </summary>
		/// <param name="ad"></param>
		public void DefendMinion(GameLiving attacker)
		{
			if (AggressionState == eAggressionState.Passive || Body.IsAttacking || Body.TargetObject == attacker)
				return;

			Attack(attacker);
		}

		// ---------------------------------------------------------------- guarding the retinue (owner 2026-11-04)
		// "it would be cool if the main pet (the Commander) recognized when their sub pets were getting attacked
		// (especially the healer, but others too, besides the other fighter pets) and did their best to get the aggro
		// off of them": a foe hitting a healer, caster, debuffer or archer is pulled onto the commander - it goes to the
		// top of that foe's hate, and the commander turns on it unless it is already guarding the healer from another.
		// The fighters (BdMeleeBrain) hold their own. Not while the commander is passive.
		private readonly System.Collections.Generic.Dictionary<GameLiving, long> _guarded = new();
		private const int GuardRange = 2500;
		private const long GuardHate = 500;

		public void GuardMinion(GameLiving attacker, BdPetBrain minion)
		{
			if (attacker == null || minion == null || minion is BdMeleeBrain || !attacker.IsAlive || !Body.IsAlive)
				return;
			if (AggressionState == eAggressionState.Passive || attacker == Body || attacker == Owner)
				return;
			if (!Body.IsWithinRadius(attacker, GuardRange) || !GameServer.ServerRules.IsAllowedToAttack(Body, attacker, true))
				return;

			// to the top of its hate: what its favourite holds now, and a little more
			if (attacker is GameNPC npc && npc.Brain is StandardMobBrain mob && !(npc.Brain is IControlledBrain))
			{
				long top = 0;
				foreach (StandardMobBrain.OrderedAggroListElement e in mob.GetOrderedAggroList())
				{
					if (e.Living != Body && e.AggroAmount > top)
						top = e.AggroAmount;
				}
				long mine = mob.GetBaseAggroAmount(Body);
				long add = System.Math.Max(GuardHate, top - mine + GuardHate);
				mob.AddToAggroList(Body, add);
			}

			// turn on it: unless the commander is already on it, or keeping another foe off the healer
			if (Body.TargetObject == attacker)
				return;
			if (minion is not BdHealerBrain && Body.TargetObject is GameLiving now && now.IsAlive &&
				now.TargetObject is GameNPC { Brain: BdHealerBrain })
				return;
			long t = GameLoop.GameLoopTime;
			lock (_guarded)
			{
				if (_guarded.TryGetValue(attacker, out long last) && t - last < 3000)
					return;                                       // (once every few seconds a foe, not every blow)
				_guarded[attacker] = t;
				if (_guarded.Count > 16)
					_guarded.Clear();
			}
			Attack(attacker);
			if (Owner is GamePlayer player && minion.Body != null)
				player.Out.SendMessage($"{Body.GetName(0, true)} moves to protect {minion.Body.GetName(0, false)} from {attacker.GetName(0, false)}!",
					DOL.GS.PacketHandler.eChatType.CT_System, DOL.GS.PacketHandler.eChatLoc.CL_SystemWindow);
		}

		/// <summary>
		/// Make sure the subpets are following the commander
		/// </summary>
		/// <param name="target"></param>
		public override void Follow(GameObject target)
		{
			base.Follow(target);
			SubPetFollow();
		}

		/// <summary>
		/// Direct all the sub pets to follow the commander
		/// </summary>
		private void SubPetFollow(bool force = true)
		{
			if (Body.ControlledNpcList != null)
			{
				lock ((Body as CommanderPet).ControlledNpcListLock)
				{
					foreach (BdPetBrain icb in Body.ControlledNpcList)
					{
						if (icb == null)
							continue;

						if (force || !icb.Body.IsAttacking)
							icb.FollowOwner();
					}
				}
			}
		}

		/// <summary>
		/// Direct all the sub pets to follow the commander
		/// </summary>
		public override void Stay()
		{
			base.Stay();
			SubPetFollow();
		}

		/// <summary>
		/// Direct all the sub pets to follow the commander
		/// </summary>
		public override void ComeHere()
		{
			base.ComeHere();
			SubPetFollow();
		}

		/// <summary>
		/// Direct all the sub pets to follow the commander
		/// </summary>
		/// <param name="target"></param>
		public override void Goto(GameObject target)
		{
			base.Goto(target);
			SubPetFollow();
		}

		public override void SetAggressionState(eAggressionState state)
		{
			base.SetAggressionState(state);
			if (Body.ControlledNpcList != null)
			{
				lock ((Body as CommanderPet).ControlledNpcListLock)
				{
					foreach (BdPetBrain icb in Body.ControlledNpcList)
					{
						if (icb != null)
							icb.SetAggressionState(state);
					}
				}
			}
		}

		public override void FollowOwner()
		{
			base.FollowOwner();
			SubPetFollow(false);
		}

		/// <summary>
		/// Checks if any spells need casting
		/// </summary>
		/// <param name="type">Which type should we go through and check for?</param>
		/// <returns></returns>
		public override bool CheckSpells(eCheckSpellType type)
		{
			bool casted = false;

			if (type == eCheckSpellType.Offensive && Body is CommanderPet pet
				&& pet.PreferredSpell != CommanderPet.eCommanderPreferredSpell.None
				&& !pet.IsCasting && !pet.IsBeingInterrupted && pet.TargetObject is GameLiving living && living.IsAlive)

			{
				Spell spellDamage = pet.CommSpellDamage;
				Spell spellDamageDebuff = pet.CommSpellDamageDebuff;
				Spell spellDot = pet.CommSpellDot;
				Spell spellDebuff = pet.CommSpellDebuff;
				Spell spellOther = pet.CommSpellOther;

				Spell cast = null;
				switch (pet.PreferredSpell)
				{
					case CommanderPet.eCommanderPreferredSpell.Debuff:
						if (spellDebuff != null && !living.HasEffect(spellDebuff))
							cast = spellDebuff;
						break;
					case CommanderPet.eCommanderPreferredSpell.Other:
						cast = spellOther;
						break;
				}

				if (cast == null)
				{
					// Pick a damage spell
					if (spellDot != null && !living.HasEffect(spellDot))
						cast = spellDot;
					else if (spellDamageDebuff != null && (!living.HasEffect(spellDamageDebuff) || spellDamage == null))
						cast = spellDamageDebuff;
					else if (spellDamage != null)
						cast = spellDamage;
				}

				if (cast != null)
					casted = Body.CastSpell(cast, m_mobSpellLine);
			}

			if (casted)
			{
				// Check instant spells, but only cast one to prevent spamming
				if (Body.CanCastInstantHarmfulSpells)
					foreach (Spell spell in Body.InstantHarmfulSpells)
					{
						if (Body.CastSpell(spell, m_mobSpellLine))
							break;
					}
			}
			else
				// Only call base method if we didn't cast anything, 
				//	otherwise it tries to cast a second offensive spell
				casted = base.CheckSpells(type);

			return casted;
		}

		public override int ModifyDamageWithTaunt(int damage)
		{
			// TODO: Move 'CommanderPet.Taunting' to the brain.
			if (Body is CommanderPet commanderPet)
			{
				int tauntScale = GS.ServerProperties.Properties.PET_BD_COMMANDER_TAUNT_VALUE;

				if (commanderPet.Taunting && tauntScale > 100)
					damage = (int)(damage * tauntScale / 100.0);
			}

			return base.ModifyDamageWithTaunt(damage);
		}
	}
}
