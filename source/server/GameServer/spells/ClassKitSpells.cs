using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using DOL.AI.Brain;
using DOL.GS.PacketHandler;

namespace DOL.GS.Spells
{
    /// <summary>
    /// The class kits' own spells (owner 2026-11-19, "Look at each caster and think of cool unique spells"; the list is
    /// in gameutils/ClassKits.cs): the ones DAoC's spell types can't already make.
    /// </summary>
    public static class ClassKitSpellHelp
    {
        /// <summary>Enemies of the caster within this distance of a spot.</summary>
        public static List<GameLiving> FoesNear(GameLiving caster, Point3D at, int radius)
        {
            var list = new List<GameLiving>();
            if (caster?.CurrentRegion == null)
                return list;
            var npcs = new List<GameNPC>();
            caster.CurrentRegion.GetInRadius(at, eGameObjectType.NPC, (ushort) radius, npcs);
            foreach (GameNPC n in npcs)
                if (n.IsAlive && GameServer.ServerRules.IsAllowedToAttack(caster, n, true))
                    list.Add(n);
            var players = new List<GamePlayer>();
            caster.CurrentRegion.GetInRadius(at, eGameObjectType.PLAYER, (ushort) radius, players);
            foreach (GamePlayer p in players)
                if (p.IsAlive && GameServer.ServerRules.IsAllowedToAttack(caster, p, true))
                    list.Add(p);
            return list;
        }

        /// <summary>Friends of the caster (its realm, alive, not enemies) within this distance of a spot.</summary>
        public static List<GameLiving> FriendsNear(GameLiving caster, Point3D at, int radius)
        {
            var list = new List<GameLiving>();
            if (caster?.CurrentRegion == null)
                return list;
            var players = new List<GamePlayer>();
            caster.CurrentRegion.GetInRadius(at, eGameObjectType.PLAYER, (ushort) radius, players);
            foreach (GamePlayer p in players)
                if (p.IsAlive && p.Realm == caster.Realm && !GameServer.ServerRules.IsAllowedToAttack(caster, p, true))
                    list.Add(p);
            var npcs = new List<GameNPC>();
            caster.CurrentRegion.GetInRadius(at, eGameObjectType.NPC, (ushort) radius, npcs);
            foreach (GameNPC n in npcs)
                if (n.IsAlive && n.Realm == caster.Realm && (n is GameBot || n.Brain is IControlledBrain) &&
                    !GameServer.ServerRules.IsAllowedToAttack(caster, n, true))
                    list.Add(n);
            return list;
        }

        /// <summary>Cast a kit's sub-spell (a snare, a root) from the caster on a target.</summary>
        public static void Sub(GameLiving caster, int spellId, GameLiving target)
        {
            Spell s = SkillBase.GetSpellByID(spellId);
            SpellLine line = SkillBase.GetSpellLine(GlobalSpellsLines.Item_Effects);
            if (s == null || line == null || target == null)
                return;
            ScriptMgr.CreateSpellHandler(caster, s, line)?.StartSpell(target);
        }

        /// <summary>A short-lived prop (brambles, sprouts, a mirror image): never saved, gone after its time.</summary>
        public static GameNPC Prop(GameLiving caster, Point3D at, ushort model, byte size, string name, GameNPC.eFlags flags, int lifeMs)
        {
            var n = new GameNPC
            {
                Name = name,
                Model = model,
                Size = size,
                Level = caster.Level,
                Realm = caster.Realm,
                X = at.X,
                Y = at.Y,
                Z = at.Z,
                Heading = caster.Heading,
                CurrentRegion = caster.CurrentRegion,
                Flags = flags,
                LoadedFromScript = true,
                RespawnInterval = -1,
            };
            n.SetOwnBrain(new BlankBrain());
            if (!n.AddToWorld())
                return null;
            new ECSGameTimer(n, _ =>
            {
                if (n.ObjectState == GameObject.eObjectState.Active)
                    n.Delete();
                return 0;
            }, lifeMs);
            return n;
        }
    }

    /// <summary>Eldritch - Void Step: a short blink forward; where you stood, a patch of darkness snares what stays in
    /// it. Value: the distance; Radius: the patch; Duration: how long the patch lasts; SubSpellID: the snare.</summary>
    [SpellHandler(eSpellType.VoidStep)]
    public class VoidStepSpellHandler : SpellHandler
    {
        public VoidStepSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        // (its Duration is how long its patch / images last, not a lasting effect on the target: always the direct effect)
        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"You step through the void {Spell.Value / 64:0} metres ahead. The darkness you leave snares enemies in it for {Spell.Duration / 1000} seconds.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            GameLiving c = Caster;
            if (c?.CurrentRegion == null || !c.IsAlive)
                return;
            var from = new Point3D(c.X, c.Y, c.Z);
            Point3D to = BlinkSpot(c, (int) Spell.Value);
            Console.WriteLine($"[ClassKits] {c.Name} Void Step from {from.X} {from.Y} {from.Z} to {(to == null ? "nowhere" : $"{to.X} {to.Y} {to.Z}")}");
            if (to == null)
            {
                MessageToCaster("There's no room to step there.", eChatType.CT_SpellResisted);
                return;
            }
            c.MoveTo(c.CurrentRegionID, to.X, to.Y, to.Z, c.Heading);
            if (Spell.Duration <= 0 || Spell.SubSpellID <= 0)
                return;
            ClassKitSpellHelp.Prop(c, from, 1704, 20, "void rift", GameNPC.eFlags.PEACE | GameNPC.eFlags.DONTSHOWNAME | GameNPC.eFlags.GHOST,
                Spell.Duration);
            long until = GameLoop.GameLoopTime + Spell.Duration;
            new ECSGameTimer(c, _ =>
            {
                if (GameLoop.GameLoopTime > until || c.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                foreach (GameLiving foe in ClassKitSpellHelp.FoesNear(c, from, Math.Max(100, Spell.Radius)))
                    ClassKitSpellHelp.Sub(c, Spell.SubSpellID, foe);
                return 750;
            }, 100);
        }

        /// <summary>Where a blink lands: straight ahead on the ground (the navmesh), shortened until there is ground.</summary>
        public static Point3D BlinkSpot(GameLiving c, int distance)
        {
            for (int d = distance; d >= distance / 3; d -= distance / 6)
            {
                Point2D p = c.GetPointFromHeading(c.Heading, d);
                var v = new Vector3(p.X, p.Y, c.Z);
                Zone zone = c.CurrentRegion.GetZone(p.X, p.Y);
                if (zone == null)
                    continue;
                if (PathfindingProvider.Instance.IsAvailable && PathfindingProvider.Instance.HasNavmesh(zone))
                {
                    Vector3? g = PathfindingProvider.Instance.GetClosestPoint(zone, v, 128, 128, 600, PathfindingProvider.Instance.DefaultFilters);
                    if (!g.HasValue)
                        continue;
                    return new Point3D((int) g.Value.X, (int) g.Value.Y, (int) g.Value.Z);
                }
                return new Point3D(p.X, p.Y, c.Z);
            }
            return null;
        }
    }

    /// <summary>Enchanter - Mirror Image: two images of you step out; whatever is on you turns on them until they
    /// shatter or fade. Value: each image's health in % of yours; Duration: how long they last.</summary>
    [SpellHandler(eSpellType.MirrorImage)]
    public class MirrorImageSpellHandler : SpellHandler
    {
        public MirrorImageSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        // (its Duration is how long its patch / images last, not a lasting effect on the target: always the direct effect)
        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"Two images of you step out and draw your enemies' attacks for {Spell.Duration / 1000} seconds, until they shatter.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            GameLiving c = Caster;
            if (c?.CurrentRegion == null || !c.IsAlive)
                return;
            var images = new List<GameNPC>();
            foreach (int side in new[] { -1, 1 })
            {
                ushort h = (ushort) ((c.Heading + side * 1024 + 4096) % 4096);
                Point2D p = c.GetPointFromHeading(h, 120);
                GameNPC img = ClassKitSpellHelp.Prop(c, new Point3D(p.X, p.Y, c.Z), c.Model, (byte) (c is GameNPC cn && cn.Size > 0 ? cn.Size : 50),
                    c.Name, GameNPC.eFlags.GHOST, Spell.Duration);
                if (img == null)
                    continue;
                img.MaxSpeedBase = 0;
                img.Health = Math.Max(1, (int) (img.MaxHealth * Math.Clamp(Spell.Value, 5, 100) / 100.0));
                images.Add(img);
            }
            if (images.Count == 0)
                return;
            // whatever has you in mind turns to them
            int i = 0;
            foreach (GameNPC foe in c.GetNPCsInRadius(1500))
                if (foe.IsAlive && foe.Brain is StandardMobBrain b && foe.TargetObject == c)
                {
                    GameNPC img = images[i++ % images.Count];
                    b.AddToAggroList(img, 100000);
                }
        }
    }

    /// <summary>Animist - Thorn Wall: a short line of brambles across the ground target, across your line of sight; it
    /// snares whatever crosses it. Radius: each bramble's reach; Duration: how long they stand; SubSpellID: the snare.</summary>
    [SpellHandler(eSpellType.ThornWall)]
    public class ThornWallSpellHandler : SpellHandler
    {
        public ThornWallSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        // (a Theurgist's Wall of Ice is the same wall, of ice: AlbionKitSpells)
        protected virtual ushort PropModel => 903;
        protected virtual byte PropSize => 26;
        protected virtual string PropName => "brambles";
        protected virtual void OnProp(GameNPC prop) { }

        // (its Duration is how long its patch / images last, not a lasting effect on the target: always the direct effect)
        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"A line of brambles grows across the ground for {Spell.Duration / 1000} seconds, snaring enemies that cross it.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override bool CheckBeginCast(GameLiving selectedTarget)
        {
            if (Caster is GamePlayer p && (p.GroundTarget == null || !p.IsWithinRadius(p.GroundTarget, Spell.CalculateEffectiveRange(p))))
            {
                MessageToCaster("You must place a ground target in range first.", eChatType.CT_SpellResisted);
                return false;
            }
            return base.CheckBeginCast(selectedTarget);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            GameLiving c = Caster;
            Point3D centre = (c as GamePlayer)?.GroundTarget ?? (target != null ? new Point3D(target.X, target.Y, target.Z) : null);
            if (c?.CurrentRegion == null || centre == null)
                return;
            // across the caster's view of the spot
            double ax = centre.X - c.X, ay = centre.Y - c.Y, al = Math.Max(1, Math.Sqrt(ax * ax + ay * ay));
            double px = -ay / al, py = ax / al;
            var points = new List<Point3D>();
            for (int k = -2; k <= 2; k++)
                points.Add(new Point3D((int) (centre.X + px * k * 110), (int) (centre.Y + py * k * 110), centre.Z));
            foreach (Point3D pt in points)
                OnProp(ClassKitSpellHelp.Prop(c, pt, PropModel, PropSize, PropName, GameNPC.eFlags.PEACE | GameNPC.eFlags.DONTSHOWNAME, Spell.Duration));
            long until = GameLoop.GameLoopTime + Spell.Duration;
            int reach = Math.Max(80, Spell.Radius);
            new ECSGameTimer(c, _ =>
            {
                if (GameLoop.GameLoopTime > until || c.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                var hit = new HashSet<GameLiving>();
                foreach (Point3D pt in points)
                    foreach (GameLiving foe in ClassKitSpellHelp.FoesNear(c, pt, reach))
                        if (hit.Add(foe))
                            ClassKitSpellHelp.Sub(c, Spell.SubSpellID, foe);
                return 500;
            }, 100);
        }
    }

    /// <summary>Druid - Verdant Pulse: green shoots spring up at your feet and heal whoever of your side stands among
    /// them, every two seconds. Value: each pulse's healing at level 50 (less below); Radius; Duration.</summary>
    [SpellHandler(eSpellType.VerdantPulse)]
    public class VerdantPulseSpellHandler : SpellHandler
    {
        public VerdantPulseSpellHandler(GameLiving caster, Spell spell, SpellLine line) : base(caster, spell, line) { }

        // (a Cleric's Sanctuary is the same circle, of light: AlbionKitSpells)
        protected virtual ushort PropModel => 1211;
        protected virtual byte PropSize => 22;
        protected virtual string PropName => "verdant shoots";
        protected virtual void OnProp(GameNPC prop) { }

        // (its Duration is how long its patch / images last, not a lasting effect on the target: always the direct effect)
        public override void ApplyEffectOnTarget(GameLiving target) => OnDirectEffect(target);

        public override string ShortDescription =>
            $"Green shoots spring up around you for {Spell.Duration / 1000} seconds, healing your side within them every 2 seconds.";

        public override void FinishSpellCast(GameLiving target)
        {
            m_caster.Mana -= PowerCost(target);
            base.FinishSpellCast(target);
        }

        public override void OnDirectEffect(GameLiving target)
        {
            GameLiving c = Caster;
            if (c?.CurrentRegion == null || !c.IsAlive)
                return;
            var at = new Point3D(c.X, c.Y, c.Z);
            OnProp(ClassKitSpellHelp.Prop(c, at, PropModel, PropSize, PropName, GameNPC.eFlags.PEACE | GameNPC.eFlags.DONTSHOWNAME, Spell.Duration));
            long until = GameLoop.GameLoopTime + Spell.Duration;
            int heal = Math.Max(5, (int) (Spell.Value * (c.Level + 5) / 55.0));
            new ECSGameTimer(c, _ =>
            {
                if (GameLoop.GameLoopTime > until || c.ObjectState != GameObject.eObjectState.Active)
                    return 0;
                foreach (GameLiving f in ClassKitSpellHelp.FriendsNear(c, at, Math.Max(150, Spell.Radius)))
                {
                    if (f.Health >= f.MaxHealth)
                        continue;
                    int healed = f.ChangeHealth(c, eHealthChangeType.Spell, heal);
                    if (healed > 0)
                        foreach (GamePlayer v in f.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                            v.Out.SendSpellEffectAnimation(c, f, Spell.ClientEffect, 0, false, 1);
                }
                return 2000;
            }, 300);
        }
    }
}
