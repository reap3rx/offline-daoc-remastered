-- King / Queen (class 64): armor progression like the other Albion hybrids.
-- Studded from level 1 (the starter set), chain mail from level 20 (was: chain from level 1).
-- Matches the loot rules (GeneratedUniqueItem.GetAlbionArmorType: studded below 20, chain from 20).

UPDATE SpecXAbility SET AbilityLevel = 3 WHERE Spec = 'KingCareer' AND AbilityKey = 'AlbArmor' AND SpecLevel = 1;
INSERT INTO SpecXAbility (Spec, SpecLevel, AbilityKey, AbilityLevel, ClassId) VALUES ('KingCareer', 20, 'AlbArmor', 4, 0);

-- UNDO
DELETE FROM SpecXAbility WHERE Spec = 'KingCareer' AND AbilityKey = 'AlbArmor' AND SpecLevel = 20;
UPDATE SpecXAbility SET AbilityLevel = 4 WHERE Spec = 'KingCareer' AND AbilityKey = 'AlbArmor' AND SpecLevel = 1;
