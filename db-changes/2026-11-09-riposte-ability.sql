-- Riposte (owner 2026-11-09: "I want the Riposte skill that you train in Parry to appear in the training window when
-- you train it (with a tooltip) and for it to appear in the abilities window once it's trained"). An ability like
-- Shields' Guard: learned from the Parry line at 7, 14, 21, 29, 36, 43 and 50 (Riposte I-VII), every class that
-- trains Parry. The server's Action Combat reads its level (ActionCombat.RiposteLevel).
INSERT INTO Ability (KeyName, Name, InternalID, Description, IconID, Implementation, LastTimeRowUpdated)
VALUES ('Riposte', 'Riposte %n', 3100,
 'Action combat: every blow you parry is answered a moment later by a quick counter-strike - 15% of a main-hand swing, or half an off-hand swing when fighting with two weapons. After a timed parry you also turn aside the blows of other foes for a short while, one blow from each: Riposte I covers 1 more foe for 0.75 seconds, and each rank adds a foe and more time, up to 7 foes for 3 seconds at Riposte VII. Ripostes and turned blows only cover attackers in front of you.',
 0, NULL, '2026-11-09 00:00:00');
INSERT INTO SpecXAbility (Spec, SpecLevel, AbilityKey, AbilityLevel, ClassId, LastTimeRowUpdated) VALUES
 ('Parry', 7, 'Riposte', 1, 0, '2026-11-09 00:00:00'),
 ('Parry', 14, 'Riposte', 2, 0, '2026-11-09 00:00:00'),
 ('Parry', 21, 'Riposte', 3, 0, '2026-11-09 00:00:00'),
 ('Parry', 29, 'Riposte', 4, 0, '2026-11-09 00:00:00'),
 ('Parry', 36, 'Riposte', 5, 0, '2026-11-09 00:00:00'),
 ('Parry', 43, 'Riposte', 6, 0, '2026-11-09 00:00:00'),
 ('Parry', 50, 'Riposte', 7, 0, '2026-11-09 00:00:00');

-- UNDO
DELETE FROM SpecXAbility WHERE AbilityKey = 'Riposte';
DELETE FROM Ability WHERE KeyName = 'Riposte';
