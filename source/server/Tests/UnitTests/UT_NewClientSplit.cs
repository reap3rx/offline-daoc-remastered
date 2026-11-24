using System.Linq;
using System.Text;
using DOL.GS;
using NUnit.Framework;

namespace DOL.UnitTests;

/// <summary>Long lines to the new client go in pieces under the 2048-byte packet limit (NewClient.Split).</summary>
[TestFixture]
public sealed class UT_NewClientSplit
{
    [Test]
    public void PiecesStayUnderTheLimitAndJoinBack()
    {
        string line = "#ZMARK|" + string.Concat(Enumerable.Repeat("{\"note\":\"Dergans – training ground é\"},", 200));
        var pieces = NewClient.Split(line, 1800);
        Assert.Multiple(() =>
        {
            Assert.That(pieces.Count, Is.GreaterThan(1));
            Assert.That(pieces.All(p => Encoding.UTF8.GetByteCount(p) <= 1800), Is.True);
            Assert.That(string.Concat(pieces), Is.EqualTo(line));
        });
    }

    [Test]
    public void AShortLineIsOnePiece() =>
        Assert.That(NewClient.Split("#PRIV|3|1", 1800), Is.EqualTo(new[] { "#PRIV|3|1" }));
}
