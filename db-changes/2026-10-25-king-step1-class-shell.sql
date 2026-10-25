-- King / Queen (class 64), step 1: the class shell.
-- Career abilities (chain armor, slashing weapons, Evade I-VII), Slash + Parry,
-- realm abilities (Mercenary's list), start locations, starter gear (no shield)
-- and three "Herald of the Crown" trainers (Camelot, Briton start, Avalonian start).

INSERT INTO Specialization (KeyName, Name, Icon, Description, Implementation)
VALUES ('KingCareer', 'King Career', 0, 'King / Queen class career.', 'DOL.GS.LiveCareerSpecialization');

INSERT INTO ClassXSpecialization (ClassID, SpecKeyName, LevelAcquired) VALUES
 (64, 'KingCareer', -1000),
 (64, 'CharacterStyleUserCareer', -100),
 (64, 'LightTankCareer', -100),
 (64, 'Slash', -9),
 (64, 'Parry', -5);

INSERT INTO SpecXAbility (Spec, SpecLevel, AbilityKey, AbilityLevel, ClassId) VALUES
 ('KingCareer', 1, 'AlbArmor', 4, 0),
 ('KingCareer', 1, 'Weaponry: Slashing', 0, 0),
 ('KingCareer', 1, 'Evade', 1, 0),
 ('KingCareer', 5, 'Evade', 2, 0),
 ('KingCareer', 10, 'Evade', 3, 0),
 ('KingCareer', 20, 'Evade', 4, 0),
 ('KingCareer', 30, 'Evade', 5, 0),
 ('KingCareer', 40, 'Evade', 6, 0),
 ('KingCareer', 50, 'Evade', 7, 0);

INSERT INTO ClassXRealmAbility_Atlas (CharClass, AbilityKey, LastTimeRowUpdated, ClassXRealmAbility_Atlas_ID)
SELECT 64, AbilityKey, LastTimeRowUpdated, 'King-' || AbilityKey
FROM ClassXRealmAbility_Atlas WHERE CharClass = 11;

INSERT INTO StartupLocation (XPos, YPos, ZPos, Heading, Region, MinVersion, RealmID, RaceID, ClassID, ClientRegionID)
SELECT XPos, YPos, ZPos, Heading, Region, MinVersion, RealmID, RaceID, 64, ClientRegionID
FROM StartupLocation WHERE ClassID = 2 AND RealmID = 1 AND RaceID IN (1, 2);

INSERT INTO StarterEquipment (Class, TemplateID) VALUES
 ('64;', 'practice_sword'),
 ('64;', 'bronze_studded_helm'),
 ('64;', 'bronze_studded_vest'),
 ('64;', 'bronze_studded_legs'),
 ('64;', 'bronze_studded_arms'),
 ('64;', 'bronze_studded_gauntlets'),
 ('64;', 'bronze_studded_boots');

-- Trainers: copies of Captain Alphin (Camelot), Master Graent (Briton start), Master Dyrin (Avalonian start)
INSERT INTO Mob (ClassType, TranslationId, Name, Suffix, Guild, ExamineArticle, MessageArticle, X, Y, Z, Speed, Heading, Region, Model, Size,
  Strength, Constitution, Dexterity, Quickness, Intelligence, Piety, Empathy, Charisma, Level, Realm, EquipmentTemplateID, ItemsListTemplateID,
  NPCTemplateID, Race, Flags, AggroLevel, AggroRange, MeleeDamageType, RespawnInterval, FactionID, BodyType, HouseNumber, Brain, PathID, OwnerID,
  RoamingRange, IsCloakHoodUp, Gender, PackageID, VisibleWeaponSlots, LastTimeRowUpdated, Mob_ID)
SELECT 'DOL.GS.Trainer.KingTrainer', '', 'Herald of the Crown', '', 'King Trainer', '', '', X + 220, Y, Z, Speed, Heading, Region, 32, 52,
  Strength, Constitution, Dexterity, Quickness, Intelligence, Piety, Empathy, Charisma, 50, 1, 'ArmsmanTrainer', NULL,
  0, 0, Flags, 0, 0, MeleeDamageType, RespawnInterval, FactionID, BodyType, 0, '', '', '',
  0, 0, 0, 'King', VisibleWeaponSlots, '2026-10-25 00:00:00',
  CASE Mob_ID WHEN '72e7471e-7230-4822-a39d-b03310062461' THEN 'king_trainer_camelot'
              WHEN '1e0dc1a7-6b01-4a38-845d-f8ef417a09e1' THEN 'king_trainer_briton_start'
              ELSE 'king_trainer_avalonian_start' END
FROM Mob WHERE Mob_ID IN ('72e7471e-7230-4822-a39d-b03310062461', '1e0dc1a7-6b01-4a38-845d-f8ef417a09e1', 'e7de17db-bdcf-4864-a53c-2bca8e4a1575');

-- UNDO
DELETE FROM Mob WHERE Mob_ID IN ('king_trainer_camelot', 'king_trainer_briton_start', 'king_trainer_avalonian_start');
DELETE FROM StarterEquipment WHERE Class = '64;';
DELETE FROM StartupLocation WHERE ClassID = 64;
DELETE FROM ClassXRealmAbility_Atlas WHERE CharClass = 64;
DELETE FROM SpecXAbility WHERE Spec = 'KingCareer';
DELETE FROM ClassXSpecialization WHERE ClassID = 64;
DELETE FROM Specialization WHERE KeyName = 'KingCareer';
