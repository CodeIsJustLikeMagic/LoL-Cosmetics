from lcu_driver import Connector
import json
from lcu_driver.connection import Connection
import asyncio
from cosmetics.skin_selector import SkinSelector, CosmeticDict
import traceback
import sys
from pathlib import Path

class LCUWrapper:
    PUUID:str = None
    selected_champion_id:int = 0
    selected_champ_skin_id:int = 0
    last_ward_skin_id:int = -1
    last_emote_id:int = -1
    SKIN_SELECTOR: SkinSelector = None

    cache_folder: Path = Path("data/lcu_cache")

    connection: Connection = None

    def __init__(self):
        self.connector = Connector(loop=asyncio.new_event_loop())
        self.connector.ws.register('/lol-champ-select/v1/session', event_types=('UPDATE',))(self.on_champ_select_detected)
        self.connector.ready(self.on_connect)
        self.connector.close(self.on_disconnect)
        self.cache_folder.mkdir(exist_ok=True, parents=True)

    async def select_champion_skin(self):
        if self.selected_champion_id == 0:
            print("Random champion skin selection failed. No champion selected.")
            return
        selected = self.SKIN_SELECTOR.select_random_skin(self.selected_champion_id, avoid=[self.selected_champ_skin_id])
        if selected:
            await self.set_champion_skin(selected)
        else:
            print("Random champion skin selection failed.")

    async def select_ward_skin(self):
        selected = self.SKIN_SELECTOR.select_ward(self.selected_champ_skin_id, self.selected_champion_id, avoid = [self.last_ward_skin_id])
        assert selected is not None, "selected ward should never be None. User should have default ward at least"
        if selected:
            print("     selected ward:", selected["name"])
            await self.set_ward_skin(selected)

    async def select_emote(self):
        selected =self.SKIN_SELECTOR.select_emote(self.selected_champion_id, avoid = [self.last_ward_skin_id])
        if selected:
            await self.set_emote(selected)
        else:
            print("     no emote selected")
    
    async def bann_ward(self):
        self.SKIN_SELECTOR.bann_ward(self.last_ward_skin_id)
        await self.select_ward_skin()
    
    async def bann_emote(self):
        self.SKIN_SELECTOR.bann_emote(self.last_emote_id)
        await self.select_emote()
    
    async def bann_skin(self):
        self.SKIN_SELECTOR.bann_skin(self.selected_champion_id, self.selected_champ_skin_id)
        await self.select_champion_skin()

    # region registered functions
    async def on_champ_select_detected(self, connection: Connection, event):
        try:
            eventData = event.data
            pickPhase = eventData['timer']['phase']
            #print()

            #print(f"Champ select phase: {pickPhase}")
            #print("before:", SELECTED_SKIN_ID, SELECTED_CAMPION_ID)
            
            if pickPhase in ["FINALIZATION", "BAN_PICK"]:
                my_team = eventData['myTeam']
                me = [player for player in my_team if player["puuid"] == self.PUUID][0]
                
                selected_champion_id = me['championId']
                skin = me['selectedSkinId']

                if skin != self.selected_champ_skin_id and skin != 0: # the player just picked a new skin / locked in their champion
                    self.selected_champ_skin_id = skin # must be done before await , mutex
                    if selected_champion_id != self.selected_champion_id and selected_champion_id != 0:
                        self.selected_champion_id = selected_champion_id
                        print(f"\n---Champion lock detected (champion {self.selected_champion_id})---")
                        await self.select_emote()

                    print(f"\n---Champion skin selection detected (skin {self.selected_champ_skin_id})---")
                    await self.select_ward_skin()

            if pickPhase == "GAME_STARTING":
                self.selected_champion_id = 0
                self.selected_champ_skin_id = 0
            #print("result:", pickPhase, SELECTED_SKIN_ID, SELECTED_CAMPION_ID)
        except Exception:
            traceback.print_exc()

    # fired when LCU API is ready to be used
    async def on_connect(self, connection: Connection):
        try:
            self.connection = connection
            self.PUUID
            print('LCU API is ready to be used.')

            # check if the user is already logged into his account
            for _ in range(6):
                summoner = await self.connection.request('get', '/lol-summoner/v1/current-summoner')
                if summoner.status == 200:
                    json_data = await summoner.json()
                    self.PUUID = json_data.get("puuid")
                    print("Logged in as ", json_data.get("gameName"), " PUUID:", self.PUUID)
                    try:
                        await self.get_ward_skins() # creates lcu_cache/ - 
                        await self.get_champions_big()
                        await self.get_emotes()
                        self.SKIN_SELECTOR = SkinSelector() # needs our owned ward info and minimal_skins.json from lcu
                        return
                    except DataRetrievalError as e:
                        print(e,"trying again ...")
                await asyncio.sleep(10)
            print("Failed to get summoner info after several attempts. Is the client fully loaded?")
        except Exception:
            traceback.print_exc()
            

    # fired when League Client is closed (or disconnected from websocket)
    async def on_disconnect(self, _):
        try:
            self.connection = None
            print('The client have been closed!')
        except Exception:
            traceback.print_exc()
    # endregion

    async def set_emote(self, emoteEntry:CosmeticDict, emote_slot:str = "EMOTES_WHEEL_CENTER"):
        emote_id = emoteEntry["id"]
        emote_name = emoteEntry["name"]
        print(f"LCU - setting emote to {emote_id} '{emote_name}' ... ",end="")
        loadoutContent = {
            'loadout': {
                emote_slot: {
                    'contentID': '',
                    "inventoryType": "EMOTE",
                    "itemId": emote_id
                }
            }
        }
        changeLoadout = await self._change_loadout(loadoutContent)
        if changeLoadout.status != 200:
            print("Failed. Status: ", changeLoadout.status)
        else:
            result = await changeLoadout.json()
            set_id = result["loadout"][emote_slot]["itemId"]
            self.last_emote_id = set_id
            if set_id != emote_id:
                print("Failed. Emote set ", set_id)
            else:
                print("Success.")
    
    async def _change_loadout(self, loadoutChange: dict):
        loadoutAccount = await self.connection.request('get', '/lol-loadouts/v4/loadouts/scope/account')
        loadoutData = await loadoutAccount.json()
        loadoutId = loadoutData[0]['id']
        # see documentation/loadout.json for an example
        return await self.connection.request('patch', f'/lol-loadouts/v4/loadouts/{loadoutId}', json=loadoutChange)

    async def set_ward_skin(self, wardSkinEntry:CosmeticDict):
        wardSkinId = wardSkinEntry['id']
        wardSkinName = wardSkinEntry['name']
        print(f"LCU - setting ward skin to {wardSkinId} '{wardSkinName}' ... ",end="")
        # change ward skin here
        loadoutContent = {
            'loadout': {
                'WARD_SKIN_SLOT': {
                    'contentId': '', 
                    'inventoryType': 'WARD_SKIN', 
                    'itemId': wardSkinId
                }
            }
        }
        changeLoadout = await self._change_loadout(loadoutContent)
        if changeLoadout.status != 200:
            print("Failed. Status: ", changeLoadout.status)
        else:
            result = await changeLoadout.json()
            set_id = result["loadout"]["WARD_SKIN_SLOT"]["itemId"]
            self.last_ward_skin_id = set_id
            if set_id != wardSkinId:
                print("Failed. Ward set ", set_id)
            else:
                print("Success.")

    async def set_champion_skin(self, skinEntry: CosmeticDict):
        champ_selected = await self.connection.request('get', '/lol-champ-select/v1/current-champion')
        if champ_selected.status != 404:
            print(f"LCU - setting champion skin to {skinEntry["id"]} '{skinEntry["name"]}' ...", end="")
            patchContent = {"selectedSkinId": skinEntry["id"] }
            result = await self.connection.request('patch', '/lol-champ-select/v1/session/my-selection', data=patchContent)
            if result.status != 204:
                print("Failed to set champion skin.", result) # for example 500 Internal Server Error when Skin is not owned
                return
            print("Success.")
            

    async def get_ward_skins(self):
        print("LCU - getting ward_skin_collection")
        summonerId = await self._get_summonerId()
        
        result = await self.connection.request('get', f'/lol-collections/v1/inventories/{summonerId}/ward-skins')
        if result.status != 404:
            ward_skins_data = await result.json()
            self.save_json(ward_skins_data, "ward_skin_collection.json")

            my_ward_skins = [ward for ward in ward_skins_data if ward["ownership"]["owned"] or ward["name"] == "Default Ward"]
            print(len(my_ward_skins), "owned ward skins")
            self.save_json(my_ward_skins, "owned_ward_skin_collection.json")
            print("LCU - got ward_skin_collection")
        else:
            raise DataRetrievalError("LCU - Fetching ward_skin_collection failed")


    async def get_champions_big(self):
        summonerId = await self._get_summonerId()
        
        result = await self.connection.request('get', f'/lol-champions/v1/inventories/{summonerId}/champions')
        print("get champions big result.status", result.status)
        if result.status != 404:
            champion_data = await result.json()
            print(champion_data)

            self.save_json(champion_data, "champions.json")
            print("LCU - got champions")
        else:
            raise DataRetrievalError("LCU - Fetching champions failed")
    
    
    async def _get_summonerId(self) -> str:
        summoner = await self.connection.request('get', '/lol-summoner/v1/current-summoner/account-and-summoner-ids')
        summoner = await summoner.json()
        return summoner.get("summonerId")
    
    async def get_emotes(self) -> None:
        result = await self.connection.request('get', f'/lol-inventory/v1/inventory/emotes')
        if result.status != 404:
            emotes_data = await result.json()

            self.save_json(emotes_data, "emotes.json")
            print("LCU - got emotes")
        else:
            raise DataRetrievalError("LCU - Fetching emotes failed.")

    def save_json(self, data:dict, file_name:str) -> None:
        out_path = self.cache_folder / file_name
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

class DataRetrievalError(RuntimeError):
    pass
   

if __name__ == "__main__":
    # starts the connector
    w = LCUWrapper()
    w.connector.start()



