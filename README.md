# LoL Cosmetics Selector

Use more of your League of Legends skins, emotes, and ward skins!

When you lock in a champion or pick a skin, Cosmetics automatically selects a matching ward skin and champion emote.

Right-clicking the system tray icon gives you access to:
    - Random Champion Skin: Requests a random skin (including chromas) for your selected champion.
    - Cosmetic Re-rolls: Re-roll your current ward skin or emote on the fly.
    - Preference Management: Ban or favorite current cosmetics.

## How Ward Selection Works

When you select a champion skin, the app searches for a ward skin matching the skin's theme using keyword matching and custom multiverses.

### Keyword Extraction
    - Ward Keywords: Derived from the ward's name, its set name, or event names mentioned in its description text.
    - Skin Keywords: Derived from the skin's universe name, its underlying skinlines, and the skin title (excluding the champion name).

### Multiverse Grouping (`config/multiverse.json`)
To widen the available pool of matching ward skins, Riot's official skin universes are grouped into broader, user-editable multiverses.
For example the Winter multiverse combines the Glacial, Tales of Borealis, Winter Sports, Blackfrost, and Snowdown universes so you get a broader, thematic selection of winter wards.

## How Emote Selection Works

The central emote slot is automatically set to a random owned emote featuring your selected champion.
  - Banning: You can ban unwanted emotes via the system tray menu. Banning re-rolls the emote immediately and excludes it from future picks.
  - Favourite + Fallback Pool: If you don't own any emotes for your selected champion, the app randomly picks from your favorited list.
  - You can bann and favourite emotes outside of champ select. Simply choose the emote to target by setting it as central emote via the League Client Emotes tab. Then bann or favourite in the system tray app. Unfortuantly the Riot Client doesnt live-update emote swtiches. You need to switch to a different tab and pack to see the effekt.

Bans and favorites are saved to `config/preferences.json`, pre-populated with a default list you can edit at any time.
