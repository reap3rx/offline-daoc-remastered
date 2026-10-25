-- King / Queen (class 64), step 5: Dismiss Troops (Fealty 5).
-- Instant, no power: the commander sends away all of its retainers; the commander itself stays.
-- Needs the step 5 server build (DismissRetainers spell handler).

INSERT INTO Spell (SpellID, ClientEffect, Icon, Name, Description, Target, Range, Power, CastTime, Damage, DamageType, Type, Duration, Frequency, Pulse, PulsePower, Radius, RecastDelay, ResurrectHealth, ResurrectMana, Value, Concentration, LifeDrainReturn, AmnesiaChance, Message1, Message2, Message3, Message4, InstrumentRequirement, SpellGroup, EffectGroup, SubSpellID, MoveCast, Uninterruptible, IsFocus, SharedTimerGroup, IsPrimary, IsSecondary, AllowBolt, PackageID, TooltipId, LastTimeRowUpdated, Spell_ID) VALUES (64140, 1070, 1070, 'Dismiss Troops', 'Your commander dismisses every retainer under its command, so others can be called without dismissing the commander.', 'Self', 0, 0, 0.0, 0.0, 0, 'DismissRetainers', 0, 0, 0, 0, 0, 0, 3, 0, 0.0, 0, 0, 0, '', '', '', '', 0, 64140, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'King_Fealty', 20740, '2026-10-25 00:00:00', '64140');
INSERT INTO LineXSpell (LineName, SpellID, Level, LastTimeRowUpdated, LineXSpell_ID) VALUES ('Oaths of Fealty', 64140, 5, '2026-10-25 00:00:00', 'Oaths of Fealty_64140');

-- UNDO
DELETE FROM LineXSpell WHERE LineXSpell_ID = 'Oaths of Fealty_64140';
DELETE FROM Spell WHERE SpellID = 64140;
