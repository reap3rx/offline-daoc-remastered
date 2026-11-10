#nullable enable
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace OfflineDaoc.Population;

/// <summary>
/// Lore names for the bots (owner 2026-11-10, "Living Bot Population - Plan": "Each race gets its own name style, built
/// from curated name parts per race and sex ... Every name passes a screen before it's used"). The parts and the screen's
/// lists live in bot_names.json (runtime\data\bots), so a style can be struck or a name part added without code.
/// A name is a first part and a last part of the bot's race and sex (now and then with a short bridge between, when the
/// plain pairs run out), then the screen:
///   - no crude sound anywhere in it, nor at its start or end - as written and as it would be read aloud;
///   - not a lore or famous name (Arthur, Merlin, Odin, Lugh ...), nor any player's, bot's or NPC's;
///   - no near-copy of another (the same letters once doubles, y / i, ph / f, c / k and the like are folded);
///   - 3 to 12 letters, one capital, nothing hard to say (no four consonants together, no three of a letter).
/// </summary>
public sealed class BotLoreNames
{
    public sealed class Parts
    {
        public List<string> First { get; set; } = [];
        public List<string> Last { get; set; } = [];
    }

    public sealed class Data
    {
        public List<string> Blocked_anywhere { get; set; } = [];
        public List<string> Blocked_edges { get; set; } = [];
        public List<string> Reserved { get; set; } = [];
        public Dictionary<string, Dictionary<string, Parts>> Races { get; set; } = new();
    }

    public static readonly IReadOnlyDictionary<int, string> RaceNames = new Dictionary<int, string>
    {
        [1] = "Briton", [2] = "Avalonian", [3] = "Highlander", [4] = "Saracen", [5] = "Norseman", [6] = "Troll",
        [7] = "Dwarf", [8] = "Kobold", [9] = "Celt", [10] = "Firbolg", [11] = "Elf", [12] = "Lurikeen", [13] = "Inconnu",
        [14] = "Valkyn", [15] = "Sylvan",
    };

    private static readonly string[] Bridges = ["a", "e", "i", "o", "an", "en", "el", "ar", "or", "in", "is", "ul"];
    private static readonly HashSet<char> Vowels = ['a', 'e', 'i', 'o', 'u', 'y'];
    private static readonly HashSet<string> AllowedVowelRuns = ["aoi", "uai", "eoi", "iai"];
    // the consonant clusters a name may end on
    private static readonly HashSet<string> AllowedEndings =
    [
        "ld", "nd", "rd", "rn", "rt", "rk", "st", "th", "sh", "ch", "ck", "nk", "ng", "ll", "ss", "ff", "rr", "ns", "rs",
        "nt", "lt", "gh", "mh", "dh", "bh", "nn", "mm", "kk", "rg", "rm", "lf", "lm", "lk", "sk", "tz", "ft", "rf", "rl",
        "ls", "rth", "rst", "ndr", "lds", "ght", "nds", "nch", "rch", "lch", "nth",
    ];

    private readonly Data _data;
    private readonly HashSet<string> _reserved;
    private readonly HashSet<string> _taken = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> _skeletons = new(StringComparer.Ordinal);

    public BotLoreNames(Data data)
    {
        _data = data;
        _reserved = new HashSet<string>(data.Reserved.Select(n => n.Trim()), StringComparer.OrdinalIgnoreCase);
    }

    public static BotLoreNames Load(string path)
    {
        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        Data data = JsonSerializer.Deserialize<Data>(File.ReadAllText(path), options)
                    ?? throw new InvalidDataException($"{path} holds no name data.");
        return new BotLoreNames(data);
    }

    /// <summary>Names already used (players, bots, NPCs): no new name equals one or is a near-copy of one.</summary>
    public void Reserve(IEnumerable<string> names)
    {
        foreach (string n in names)
        {
            if (string.IsNullOrWhiteSpace(n))
                continue;
            string name = n.Trim();
            _taken.Add(name);
            if (name.All(char.IsLetter))
                _skeletons.Add(Skeleton(name));
        }
    }

    /// <summary>A screened, unused name for this race (offline_world_bots.RaceId) and sex (1 male, 2 female), or null
    /// when its parts are used up.</summary>
    public string? Generate(int raceId, int gender, Random rng)
    {
        if (!RaceNames.TryGetValue(raceId, out string? race) || !_data.Races.TryGetValue(race, out var bySex))
            return null;
        if (!bySex.TryGetValue(gender == 2 ? "female" : "male", out Parts? parts) || parts.First.Count == 0 || parts.Last.Count == 0)
            return null;
        for (int attempt = 0; attempt < 600; attempt++)
        {
            string first = parts.First[rng.Next(parts.First.Count)];
            string last = parts.Last[rng.Next(parts.Last.Count)];
            string bridge = attempt >= 300 ? Bridges[rng.Next(Bridges.Length)] : "";
            string name = Normalize(first + bridge + last);
            if (TryTake(name))
                return name;
        }
        return null;
    }

    private bool TryTake(string name)
    {
        if (Screen(name) != null || _taken.Contains(name))
            return false;
        string sk = Skeleton(name);
        if (!_skeletons.Add(sk))
            return false;
        _taken.Add(name);
        return true;
    }

    /// <summary>Why a name fails the screen (null: it passes). Used names aren't checked here (Reserve / TryTake).</summary>
    public string? Screen(string name)
    {
        if (name.Length < 3 || name.Length > 12)
            return "length";
        if (!name.All(c => c is >= 'a' and <= 'z' or >= 'A' and <= 'Z'))
            return "letters";
        if (!char.IsUpper(name[0]) || name.Skip(1).Any(char.IsUpper))
            return "capitals";
        if (_reserved.Contains(name))
            return "reserved";
        string lower = name.ToLowerInvariant();
        foreach (string form in new[] { lower, Spoken(lower) })
        {
            foreach (string bad in _data.Blocked_anywhere)
                if (form.Contains(bad, StringComparison.Ordinal))
                    return "blocked:" + bad;
            foreach (string bad in _data.Blocked_edges)
                if (form.StartsWith(bad, StringComparison.Ordinal) || form.EndsWith(bad, StringComparison.Ordinal) || form == bad)
                    return "blocked-edge:" + bad;
        }
        int run = 0;
        for (int i = 0; i < lower.Length; i++)
        {
            run = Vowels.Contains(lower[i]) ? 0 : run + 1;
            if (run >= 4)
                return "consonants";
            if (i >= 2 && lower[i] == lower[i - 1] && lower[i] == lower[i - 2])
                return "triple";
        }
        if (lower.Contains('q') && !lower.Contains("qu"))
            return "q";
        for (int i = 0; i + 3 <= lower.Length; i++)
            if (Vowels.Contains(lower[i]) && Vowels.Contains(lower[i + 1]) && Vowels.Contains(lower[i + 2]) &&
                !AllowedVowelRuns.Contains(lower.Substring(i, 3)))
                return "vowels";                              // (Ruaeaidh, Naeoia - Aoife's aoi is fine)
        int tail = 0;
        while (tail < lower.Length && !Vowels.Contains(lower[lower.Length - 1 - tail]))
            tail++;
        if (tail >= 2 && !(tail == 2 && AllowedEndings.Contains(lower[^2..])) && !(tail == 3 && AllowedEndings.Contains(lower[^3..])))
            return "ending";                                  // (Tadn, Likb, Fizmp)
        for (int i = 0; i + 3 <= lower.Length; i++)
            if (lower.IndexOf(lower.Substring(i, 3), i + 3, StringComparison.Ordinal) >= 0)
                return "repeat";                              // (Gwenwen, Tiktik: a part said twice)
        return null;
    }

    /// <summary>The word as it would be said: ph f, ck k, c k, x ks, z s, qu kw.</summary>
    public static string Spoken(string lower) => lower
        .Replace("ph", "f").Replace("ck", "k").Replace("qu", "kw").Replace("c", "k").Replace("x", "ks").Replace("z", "s");

    /// <summary>A name's bones for spotting near-copies: spoken, y as i, vowels kept but doubled letters folded.</summary>
    public static string Skeleton(string name)
    {
        string s = Spoken(name.ToLowerInvariant()).Replace('y', 'i').Replace("h", "");
        var sb = new StringBuilder();
        foreach (char c in s)
            if (sb.Length == 0 || sb[^1] != c)
                sb.Append(c);
        return sb.ToString();
    }

    public static string Normalize(string raw)
    {
        string s = raw.ToLowerInvariant().Replace("aa", "a").Replace("ii", "i").Replace("yy", "y");
        return s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];
    }
}
