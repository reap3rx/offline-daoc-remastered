-- King / Queen: move Dismiss Troops from Fealty 5 to Fealty 4.
-- The client casts list spells by (line, level); at 5 it shared the slot with Summon Squire, so a quickbar
-- copy of Dismiss Troops cast Summon Squire instead. Every level from 5 to 10 is taken; 4 is the nearest free one.

UPDATE LineXSpell SET Level = 4 WHERE LineXSpell_ID = 'Oaths of Fealty_64140';

-- UNDO
UPDATE LineXSpell SET Level = 5 WHERE LineXSpell_ID = 'Oaths of Fealty_64140';
