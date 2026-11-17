using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
using DOL.Database;
using DOL.GS;
using DOL.GS.Database;
using NUnit.Framework;

namespace DOL.UnitTests
{
    /// <summary>Owner 2026-11-17: every bot, grouped or not, is scaled down against low monsters like a player
    /// ("That way everyone is the same").</summary>
    [TestFixture, NonParallelizable]
    public sealed class UT_LevelScalingBots
    {
        public class ReadDatabase : DispatchProxy
        {
            protected override object Invoke(MethodInfo method, object[] args)
            {
                if (!method.Name.StartsWith("Select") && !method.Name.StartsWith("Find"))
                    throw new InvalidOperationException("No database writes allowed: " + method.Name);
                Type type = method.ReturnType;
                return type.IsGenericType && typeof(IEnumerable).IsAssignableFrom(type)
                    ? Activator.CreateInstance(typeof(List<>).MakeGenericType(type.GetGenericArguments()[0])) : null;
            }
        }
        private static readonly IObjectDatabase Empty = DispatchProxy.Create<IObjectDatabase, ReadDatabase>();
        private sealed class Server : GameServer
        {
            protected override IObjectDatabase DataBaseImpl => Empty;
            protected override GS.ServerRules.IServerRules ServerRulesImpl => new GS.ServerRules.NormalServerRules();
        }
        private GameServer _previous;

        [SetUp] public void Setup()
        {
            _previous = GameServer.Instance;
            GameServer.LoadTestDouble((Server)RuntimeHelpers.GetUninitializedObject(typeof(Server)));
        }

        [TearDown] public void Cleanup() => GameServer.LoadTestDouble(_previous);

        private sealed class Bot : GameBot
        {
            private Bot() : base((OfflineWorldBotRecord)null) { }
            private byte _level;
            public override byte Level { get => _level; set => _level = value; }
            public override eRealm Realm { get => eRealm.Hibernia; set { } }
        }

        private sealed class Mob : GameNPC
        {
            private byte _level;
            public override byte Level { get => _level; set => _level = value; }
            public override eRealm Realm { get => eRealm.None; set { } }
        }

        private static T Make<T>(byte level) where T : GameLiving
        {
            var l = (T)RuntimeHelpers.GetUninitializedObject(typeof(T));
            typeof(GameNPC).GetField("m_brains", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(l, new ArrayList());
            l.Level = level;
            return l;
        }

        [Test]
        public void ASoloBotFightsALowMonsterAtItsLevelPlusThree()
        {
            var bot = Make<Bot>(12);
            var mob = Make<Mob>(5);
            int cap = LevelScaling.Cap(mob);
            Assert.That(cap, Is.LessThan(12));
            Assert.That(LevelScaling.Gap(bot, mob), Is.EqualTo(12 - cap));
            double expected = Math.Pow(cap / 12.0, 2.0);
            Assert.That(LevelScaling.DamageFactor(bot, mob), Is.EqualTo(Math.Max(0.1, expected)).Within(1e-9));
            Assert.That(LevelScaling.DamageFactor(mob, bot), Is.GreaterThan(1.0));
        }

        [Test]
        public void ABotAtTheMonstersLevelIsNotScaled()
        {
            var bot = Make<Bot>(6);
            var mob = Make<Mob>(5);
            Assert.That(LevelScaling.DamageFactor(bot, mob), Is.EqualTo(1.0));
            Assert.That(LevelScaling.DamageFactor(mob, bot), Is.EqualTo(1.0));
        }

        [Test]
        public void AFarHigherBotStillDealsATenth()
        {
            var bot = Make<Bot>(50);
            var mob = Make<Mob>(2);
            Assert.That(LevelScaling.DamageFactor(bot, mob), Is.EqualTo(0.1).Within(1e-9));
            Assert.That(LevelScaling.DamageFactor(mob, bot), Is.EqualTo(4.0).Within(1e-9));
        }
    }
}
