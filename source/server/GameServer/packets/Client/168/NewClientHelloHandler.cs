using System.Text;

namespace DOL.GS.PacketHandler.Client.v168
{
    /// <summary>The new client's hello, sent before it logs in (see <see cref="NewClient"/>).</summary>
    [PacketHandler(PacketHandlerType.TCP, NewClient.HelloCode, "The new client's hello", eClientStatus.None)]
    public class NewClientHelloHandler : PacketHandler
    {
        protected override void HandlePacketInternal(GameClient client, GSPacketIn packet)
        {
            int kind = packet.ReadByte();
            if (kind != 1)
                return;
            int version = packet.ReadShort();
            int n = packet.ReadByte();
            var name = new byte[n];
            for (int i = 0; i < n; i++)
                name[i] = (byte) packet.ReadByte();
            NewClient.SetHello(client, version, Encoding.UTF8.GetString(name));
        }
    }
}
