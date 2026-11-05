-- King / Queen (class 64): the summons drawn as pets, not as buffs (owner 2026-11-04: "Some of the pet spell icons
-- share the same icon style as the buffs ... Maybe they should look more like the pet icons for other classes?").
-- The footman shared Might of the Cub's fist (1451) and the bowman Swift Hand's (1471). Now every summon is a figure, as
-- the other pet classes' are:
--   commanders: the framed figures, the frame rising with the rank - Squire 801, Shieldbearer 802, Sergeant-at-Arms 803,
--     Knight-Errant 804, Knight 805 (the icons the Cabalist's simulacra use);
--   retainers, one colour per kind - armsman brown (101), cleric white (451), scout teal on gold (7217),
--     sorcerer violet (2801), wizard ice blue (261).
UPDATE Spell SET Icon = 801 WHERE SpellID = 64100;
UPDATE Spell SET Icon = 802 WHERE SpellID = 64101;
UPDATE Spell SET Icon = 803 WHERE SpellID = 64102;
UPDATE Spell SET Icon = 804 WHERE SpellID = 64103;
UPDATE Spell SET Icon = 805 WHERE SpellID = 64104;
UPDATE Spell SET Icon = 101 WHERE SpellID BETWEEN 64110 AND 64114;
UPDATE Spell SET Icon = 451 WHERE SpellID BETWEEN 64115 AND 64119;
UPDATE Spell SET Icon = 7217 WHERE SpellID BETWEEN 64120 AND 64124;
UPDATE Spell SET Icon = 2801 WHERE SpellID BETWEEN 64125 AND 64129;
UPDATE Spell SET Icon = 261 WHERE SpellID BETWEEN 64130 AND 64134;
