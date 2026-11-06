using System.Runtime.CompilerServices;
using System.Text;
using DOL.GS.PacketHandler;

namespace DOL.GS
{
    /// <summary>
    /// The new (Godot) client's own channel (owner 2026-11-05: "I don't intend on using the old client anymore at all ...
    /// want to not be limited by that when exploring new things"). The new client says hello before it logs in
    /// (<see cref="HelloCode"/>: what it is and which version of this channel it speaks); the server then has its own
    /// message for it (<see cref="LineCode"/>), instead of the tagged system-chat lines ("#WAL|...", "#SAY|...") it used to
    /// hide the new client's data in so the classic client would only show them as chat. The classic client is turned
    /// away at login (server property require_new_client).
    ///
    /// Client -> server, 0x2E: u8 kind (1 = hello), u16 channel version, u8-length name.
    /// Server -> client, 0x3E: u8 kind (1 = a line: u16 length, UTF-8 "TAG|payload" - the same lines the tagged chat
    /// carried, so each feature's format is unchanged; later kinds for richer messages).
    /// </summary>
    public static class NewClient
    {
        public const byte HelloCode = 0x2E;
        public const byte LineCode = 0x3E;
        public const byte KindLine = 1;

        public sealed class Hello
        {
            public int Version;
            public string Name;
        }

        private static readonly ConditionalWeakTable<GameClient, Hello> _hellos = new();

        public static void SetHello(GameClient c, int version, string name)
        {
            if (c == null)
                return;
            _hellos.AddOrUpdate(c, new Hello { Version = version, Name = name });
        }

        /// <summary>The channel version this client speaks (0: it never said hello - the classic client, or a bot).</summary>
        public static int Version(GameClient c) => c != null && _hellos.TryGetValue(c, out Hello h) ? h.Version : 0;

        public static bool Is(GamePlayer p) => Version(p?.Client) > 0;

        /// <summary>A line for the new client ("#WAL|..." and so on); nothing for anyone else.</summary>
        public static void Send(GamePlayer p, string line)
        {
            if (p?.Client == null || p.Out == null || !Is(p) || string.IsNullOrEmpty(line))
                return;
            byte[] b = Encoding.UTF8.GetBytes(line);
            if (b.Length > 60000)
                return;                                        // (a packet's size is a u16; nothing sent is near it)
            using var pak = PooledObjectFactory.GetForTick<GSTCPPacketOut>().Init(LineCode);
            pak.WriteByte(KindLine);
            pak.WriteShort((ushort) b.Length);
            pak.Write(b, 0, b.Length);
            p.Out.SendTCP(pak);
        }
    }
}
