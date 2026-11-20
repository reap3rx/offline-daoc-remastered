using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using DOL.GS.Commands;
using DOL.GS.PacketHandler;
using DOL.GS.Spells;

namespace DOL.GS
{
    /// <summary>
    /// Channelled casting (owner 2026-11-19: "hold the spell button down to channel it ... Quick ... Normal ... Powered
    /// ... cast bar"). A spell with ranks in its family (SpellFamilies), held on its key, is channelled instead of cast:
    ///   - let go before the quick mark (a tap, a click): it is cast as ever - the current rank at its own cast time;
    ///   - let go between the quick mark and the cast time: the rank before it goes off at once (Quick);
    ///   - let go once the cast time is reached: the current rank (Normal);
    ///   - still held at the powered mark: the next rank - learned or not yet - goes off (Powered).
    /// The quick mark is the cast time times 0.6, down to 0.4 with dexterity; the powered mark the cast time times
    /// PoweredTimes. No rank before: no quick mark (an early release casts at the cast time); no rank after: no powered
    /// mark (held, it goes off at the cast time). Moving or being interrupted breaks the channel. Each rank costs its own
    /// power; the one that goes off is cast with no cast time of its own (the channel was its cast).
    ///
    /// The client: "/channel hold" just before its UseSpell (the key is down) and "/channel release" when the key comes
    /// up; told "#CH|start|quickMs|normalMs|poweredMs|prev|cur|next" and "#CH|end|name-or-empty".
    /// </summary>
    public static class ChannelCasting
    {
        public const double PoweredTimes = 1.6;
        public const int MinQuickMs = 300;
        const int HoldPendingMs = 1500;

        sealed class State
        {
            public long HoldAt;                       // "/channel hold" came (its UseSpell next)
            public bool Active;
            public long Start;
            public int QuickMs, NormalMs, PoweredMs;
            public Spell Prev, Cur, Next;
            public SpellLine Line;
            public bool Committed;                    // let go before the quick mark: the current rank at the cast time
            public int X, Y;
            public int Serial;
        }

        static readonly ConditionalWeakTable<GamePlayer, State> _states = new();

        static State Of(GamePlayer p) => _states.GetValue(p, _ => new State());

        public static void Hold(GamePlayer p) => Of(p).HoldAt = GameLoop.GameLoopTime;

        public static bool IsChannelling(GamePlayer p) => p != null && _states.TryGetValue(p, out State s) && s.Active;

        /// <summary>The quick mark's share of the cast time: 0.6, less with dexterity (to 0.4 at 160).</summary>
        public static double QuickShare(int dex) => Math.Clamp(0.6 - (dex - 60) / 500.0, 0.4, 0.6);

        /// <summary>The ranks around a spell in its line: the one before (learned) and the one after (any).</summary>
        public static (Spell prev, Spell next) Ranks(Spell spell, SpellLine line)
        {
            if (spell == null || line == null)
                return (null, null);
            List<Spell> list = SkillBase.GetSpellList(line.KeyName);
            Spell prev = SpellFamilies.PreviousRank(spell, list);
            object k = SpellFamilies.Key(spell);
            Spell next = list.Where(s => s.ID != spell.ID && (s.Level > spell.Level || s.Level == spell.Level && s.ID > spell.ID) && Equals(SpellFamilies.Key(s), k))
                .OrderBy(s => s.Level).ThenBy(s => s.ID).FirstOrDefault();
            return (prev, next);
        }

        static bool Channelable(Spell s) =>
            s != null && s.CastTime > 0 && !s.NeedInstrument && s is not Song && !s.IsPulsing && !SpellFamilies.IsPet(s);

        /// <summary>UseSpellHandler: a held key's spell. True when it is channelled (the cast is the channel's).</summary>
        public static bool TryBegin(GamePlayer p, Spell spell, SpellLine line)
        {
            State st = Of(p);
            bool held = st.HoldAt > 0 && GameLoop.GameLoopTime - st.HoldAt <= HoldPendingMs;
            st.HoldAt = 0;
            if (st.Active)
                Cancel(p, st, null);                    // (another spell asked for: the channel gives way)
            if (!held || st.Active || !Channelable(spell) || line == null || !p.IsAlive)
                return false;
            if (p.IsCasting || p.IsMoving || p.IsStunned || p.IsMezzed || p.IsSilenced || ManaShield.IsWarding(p))
                return false;                          // (the ordinary cast says why not)
            if (p.GetSkillDisabledDuration(spell) > 0)
                return false;
            var (prev, next) = Ranks(spell, line);
            if (prev == null && next == null)
                return false;
            int normal;
            try
            {
                normal = ScriptMgr.CreateSpellHandler(p, spell, line) is SpellHandler sh ? p.CalculateCastingTime(sh) : spell.CastTime;
            }
            catch (Exception)
            {
                normal = spell.CastTime;
            }
            normal = Math.Max(500, normal);
            int dex = p.GetModified(eProperty.Dexterity);
            st.Active = true;
            st.Committed = false;
            st.Start = GameLoop.GameLoopTime;
            st.NormalMs = normal;
            st.QuickMs = prev != null ? Math.Max(MinQuickMs, (int) (normal * QuickShare(dex))) : 0;
            st.PoweredMs = next != null ? (int) (normal * PoweredTimes) : 0;
            st.Prev = prev;
            st.Cur = spell;
            st.Next = next;
            st.Line = line;
            st.X = p.X;
            st.Y = p.Y;
            int serial = ++st.Serial;
            p.Out.SendMessage($"You begin channelling {spell.Name}.", eChatType.CT_Spell, eChatLoc.CL_SystemWindow);
            int shown = st.PoweredMs > 0 ? st.PoweredMs : st.NormalMs;
            foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendSpellCastAnimation(p, spell.ClientEffect, (ushort) Math.Max(1, shown / 100));
            NewClient.Send(p, $"#CH|start|{st.QuickMs}|{st.NormalMs}|{st.PoweredMs}|{Clean(prev?.Name)}|{Clean(spell.Name)}|{Clean(next?.Name)}");
            new ECSGameTimer(p, _ => Tick(p, st, serial), 100);
            return true;
        }

        static string Clean(string s) => (s ?? "").Replace("|", "/");

        static int Tick(GamePlayer p, State st, int serial)
        {
            if (!st.Active || st.Serial != serial)
                return 0;
            if (!p.IsAlive || p.ObjectState != GameObject.eObjectState.Active)
            {
                Cancel(p, st, null);
                return 0;
            }
            long dx = p.X - st.X, dy = p.Y - st.Y;
            if (dx * dx + dy * dy > 24 * 24 || p.IsStunned || p.IsMezzed || p.IsSilenced)
            {
                Cancel(p, st, "You move and your channel breaks!");
                return 0;
            }
            if (p.IsBeingInterruptedByOther && p.InterruptTime > st.Start && p.LastInterrupter != p)
            {
                Cancel(p, st, $"{p.LastInterrupter?.GetName(0, true) ?? "Something"} breaks your channel!");
                return 0;
            }
            long el = GameLoop.GameLoopTime - st.Start;
            if (st.PoweredMs > 0 && el >= st.PoweredMs && !st.Committed)
            {
                Fire(p, st, st.Next, "powered");
                return 0;
            }
            if (el >= st.NormalMs && (st.Committed || st.PoweredMs <= 0))
            {
                Fire(p, st, st.Cur, "normal");
                return 0;
            }
            return 100;
        }

        /// <summary>"/channel release": the key came up.</summary>
        public static void Release(GamePlayer p)
        {
            if (!_states.TryGetValue(p, out State st) || !st.Active || st.Committed)
                return;
            long el = GameLoop.GameLoopTime - st.Start;
            if (st.QuickMs <= 0 ? el < st.NormalMs : el < st.QuickMs)
                st.Committed = true;                    // a tap: cast as ever, at the cast time (Tick)
            else if (el < st.NormalMs)
                Fire(p, st, st.Prev, "quick");
            else
                Fire(p, st, st.Cur, "normal");
        }

        public static void Cancel(GamePlayer p)
        {
            if (_states.TryGetValue(p, out State st) && st.Active)
                Cancel(p, st, "You stop channelling.");
        }

        static void Cancel(GamePlayer p, State st, string why)
        {
            st.Active = false;
            st.Serial++;
            foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                v.Out.SendInterruptAnimation(p);
            NewClient.Send(p, "#CH|end|");
            if (why != null)
                p.Out.SendMessage(why, eChatType.CT_SpellResisted, eChatLoc.CL_SystemWindow);
        }

        static void Fire(GamePlayer p, State st, Spell rank, string how)
        {
            st.Active = false;
            st.Serial++;
            rank ??= st.Cur;
            Spell instant = rank.Copy();
            instant.CastTime = 0;                       // (the channel was its cast)
            NewClient.Send(p, $"#CH|end|{Clean(rank.Name)}|{how}");
            if (!p.CastSpell(instant, st.Line))
            {
                foreach (GamePlayer v in p.GetPlayersInRadius(WorldMgr.VISIBILITY_DISTANCE))
                    v.Out.SendInterruptAnimation(p);
            }
        }
    }
}

namespace DOL.GS.Commands
{
    [CmdAttribute("&channel", ePrivLevel.Player, "Channelled casting (the client's held spell keys)", "/channel hold | release | cancel")]
    public class ChannelCommandHandler : AbstractCommandHandler, ICommandHandler
    {
        public void OnCommand(GameClient client, string[] args)
        {
            GamePlayer p = client?.Player;
            if (p == null || args.Length < 2)
                return;
            switch (args[1].ToLowerInvariant())
            {
                case "hold": ChannelCasting.Hold(p); break;
                case "release": ChannelCasting.Release(p); break;
                case "cancel": ChannelCasting.Cancel(p); break;
            }
        }
    }
}
