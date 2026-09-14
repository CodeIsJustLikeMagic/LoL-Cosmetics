# LoL Cosmetics Selector

**Use more of your League of Legends skins, chromas, emotes, and ward skins!**

When you lock in a champion or pick a skin, Cosmetics **automatically** selects a matching ward skin and champion emote.

Right-clicking the system tray icon gives you access to:
- Random Champion Skin: Requests a random skin (including chromas) for your selected champion.
- Cosmetic Re-rolls: Re-roll your current ward skin or emote.
- Preference Management: Ban or favorite current cosmetics.

## How Ward Selection Works

When you select a champion skin, the app searches for a ward skin matching the skin's theme using keyword matching and custom multiverses.

#### Keyword Extraction
- Ward Keywords: Derived from the ward's name, its set name, or event names mentioned in its description text.
- Skin Keywords: Derived from the skin's universe name, all skinline names in the universe and all skin names in the universe.

#### Multiverse Grouping (`config/multiverse.json`)
To widen the available pool of matching ward skins, Riot's official skin universes are grouped into broader, user-editable multiverses.
For example the custom "Winter" multiverse combines the Glacial, Tales of Borealis, Winter Sports, Blackfrost, and Snowdown universes so you get a broader, thematic selection of winter wards.

## How Emote Selection Works

The **central emote slot** is automatically set to a random owned emote featuring your selected champion (thanks to Riot's emote annotations!).
- Banning: You can ban unwanted emotes via the system tray menu. Banning re-rolls the emote immediately and excludes it from future picks.
- Favourite + Fallback Pool: If you don't own any emotes for your selected champion, the app randomly picks from your favorited list.
- You can ban and favourite emotes outside of champ select. Simply choose the emote to target by setting it as central emote via the League Client Emotes tab. Then ban or favourite in Cosmetics system tray app. Unfortuantly the Riot Client doesn't live-update emotes. You need to switch to a different tab and back to see the effect.

Bans and favorites are saved to `config/preferences.json`, pre-populated with a default list you can edit at any time.

## How Champion Skin Selection Works:

Champion skin selection is not done automatically. You must trigger it via the system tray menu.
The skin is selected purely randomly from skins owned for the champion. Skins can be banned to remove them from current and future selections.
If the selected skin has chromas, a random choma is choosen.

## Riot APIs & Data Sources

League Client Update (**LCU**) API:
- Monitoring: Detects client lifecycle events (login/disconnect) and tracks real-time champion lock-in and skin selection during Champ Select.
- Account Inventory: Fetches ownership information about skins, ward skins and emotes of the active account.
- Client Actions: Sends requests to automatically equip selected ward skins, emotes, and champion skins/chromas.

**Community Dragon**:
- Serves as the primary data source for skins, ward skins and emotes.

## Legal Stuff

LoL Cosmetics Selector isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing League of Legends. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc. League of Legends © Riot Games, Inc.
