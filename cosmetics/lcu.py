from lcu_driver import Connector
import json
from lcu_driver.connection import Connection
import asyncio
from cosmetics.selection.cosmetic_selector import CosmeticSelector, CosmeticDict
import traceback
from pathlib import Path
from cosmetics.paths import DATA_PATHS
import cosmetics.dragon as cdragon

import cosmetics.logging_config as logging_config
logger = logging_config.get_logger(__name__)

class LCUWrapper:
    PUUID:str = None
    selected_champion_id:int = 0
    selected_champ_skin_id:int = 0
    last_ward_skin_id:int = -1
    last_emote_id:int = -1
    COSMETIC_SELECTOR: CosmeticSelector = None

    connection: Connection = None

    def __init__(self):
        self.connector = Connector(loop=asyncio.new_event_loop())
        self.connector.ws.register('/lol-champ-select/v1/session', event_types=('UPDATE',))(self.on_champ_select_detected)
        self.connector.ready(self.on_connect)
        self.connector.close(self.on_disconnect)

    async def select_champion_skin(self):
        if self.selected_champion_id == 0:
            logger.info("Random champion skin selection failed. No champion selected.")
            return
        selected = self.COSMETIC_SELECTOR.select_random_skin(self.selected_champion_id, avoid=[self.selected_champ_skin_id])
        if selected:
            await self.set_champion_skin(selected)
        else:
            logger.info("Random champion skin selection failed.")

    async def select_ward_skin(self):
        selected = self.COSMETIC_SELECTOR.select_ward(self.selected_champ_skin_id, self.selected_champion_id, avoid = [self.last_ward_skin_id])
        assert selected is not None, "selected ward should never be None. User should have default ward at least"
        if selected:
            logger.info("     selected ward: {selected['name']}")
            await self.set_ward_skin(selected)

    async def select_emote(self):
        selected = self.COSMETIC_SELECTOR.select_emote(self.selected_champion_id, avoid = [self.last_ward_skin_id])
        if selected:
            await self.set_emote(selected)
        else:
            logger.info("     no emote selected")
    
    async def bann_ward(self):
        ward_skin_id = await self.get_current_ward()
        self.COSMETIC_SELECTOR.bann_ward(ward_skin_id)
        await self.select_ward_skin()
    
    async def bann_emote(self):
        emote_id = await self.get_current_emote()
        self.COSMETIC_SELECTOR.bann_emote(emote_id)
        await self.select_emote()
    
    async def bann_skin(self):
        self.COSMETIC_SELECTOR.bann_skin(self.selected_champion_id, self.selected_champ_skin_id)
        await self.select_champion_skin()

    async def favourite_emote(self):
        emote_id = await self.get_current_emote()
        self.COSMETIC_SELECTOR.favourite_emote(emote_id)

    # region registered functions
    async def on_champ_select_detected(self, connection: Connection, event):
        try:
            eventData = event.data
            pickPhase = eventData['timer']['phase']
            
            if pickPhase in ["FINALIZATION", "BAN_PICK"]:
                my_team = eventData['myTeam']
                me = [player for player in my_team if player["puuid"] == self.PUUID][0]
                
                selected_champion_id = me['championId']
                skin = me['selectedSkinId']

                if skin != self.selected_champ_skin_id and skin != 0: # the player just picked a new skin / locked in their champion
                    self.selected_champ_skin_id = skin # must be done before await , mutex
                    if selected_champion_id != self.selected_champion_id and selected_champion_id != 0:
                        self.selected_champion_id = selected_champion_id
                        logger.info(f"---Champion lock detected (champion {self.selected_champion_id})---")
                        await self.select_emote()

                    logger.info(f"---Champion skin selection detected (skin {self.selected_champ_skin_id})---")
                    await self.select_ward_skin()

            if pickPhase == "GAME_STARTING":
                self.selected_champion_id = 0
                self.selected_champ_skin_id = 0
        except Exception:
            logger.error(traceback.print_exc())

    # fired when LCU API is ready to be used
    async def on_connect(self, connection: Connection):
        try:
            self.connection = connection
            self.PUUID
            logger.info('LCU API is ready to be used.')

            # check if the user is already logged into his account
            # attemps to load champions for 10 minutes.
            for _ in range(60):
                summoner = await self.connection.request('get', '/lol-summoner/v1/current-summoner')
                if summoner.status == 200:
                    json_data = await summoner.json()
                    self.PUUID = json_data.get("puuid")
                    logger.info(f"Logged in as '{json_data.get("gameName")}' PUUID: {self.PUUID}")
                    try:
                        # grabs all our skinselector needs.
                        # data is placed into cache folder.
                        # so we can run pytests on that.
                        await self.get_ward_skins() # creates lcu_cache/ - 
                        await self.get_champions_big()
                        await self.get_emotes()
                        cdragon.clear_cache()

                        self.COSMETIC_SELECTOR = CosmeticSelector() # needs our owned ward info and minimal_skins.json from lcu

                        return
                    except DataRetrievalError as e:
                        logger.info(f"{e} trying again in 10 seconds...")
                    except Exception as e:
                        logger.error(f"on_connect failed: {traceback.print_exc()}")
                await asyncio.sleep(10)
            logger.info("Failed to get summoner info after several attempts. Is the client fully loaded?")
        except Exception:
            traceback.logger.info_exc()
            

    # fired when League Client is closed (or disconnected from websocket)
    async def on_disconnect(self, _):
        try:
            self.connection = None
            logger.info('The client has been closed!')
        except Exception:
            traceback.logger.info_exc()
    # endregion registered functions

    # region set api data
    async def set_emote(self, emoteEntry:CosmeticDict, emote_slot:str = "EMOTES_WHEEL_CENTER"):
        emote_id = emoteEntry["id"]
        emote_name = emoteEntry["name"]
        logger.info(f"setting emote to {emote_id} '{emote_name}' ... ")
        loadoutContent = {
            'loadout': {
                emote_slot: {
                    'contentID': '',
                    "inventoryType": "EMOTE",
                    "itemId": emote_id
                }
            }
        }
        changeLoadout = await self._set_loadout(loadoutContent)
        if changeLoadout.status != 200:
            logger.info(f"Failed. Status: {changeLoadout.status}")
        else:
            result = await changeLoadout.json()
            set_id = result["loadout"][emote_slot]["itemId"]
            self.last_emote_id = set_id
            if set_id != emote_id:
                logger.info(f"Failed. Emote set {set_id}")
            else:
                logger.info("Success.")

    async def set_ward_skin(self, wardSkinEntry:CosmeticDict):
        wardSkinId = wardSkinEntry['id']
        wardSkinName = wardSkinEntry['name']
        logger.info(f"setting ward skin to {wardSkinId} '{wardSkinName}' ... ")
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
        changeLoadout = await self._set_loadout(loadoutContent)
        if changeLoadout.status != 200:
            logger.info(f"Failed. Status: {changeLoadout.status}")
        else:
            result = await changeLoadout.json()
            set_id = result["loadout"]["WARD_SKIN_SLOT"]["itemId"]
            self.last_ward_skin_id = set_id
            if set_id != wardSkinId:
                logger.info(f"Failed. Ward set {set_id}")
            else:
                logger.info("Success.")

    async def _set_loadout(self, loadoutChange: dict):
        loadoutData = await self.get_endpoint('/lol-loadouts/v4/loadouts/scope/account')
        loadoutId = loadoutData[0]['id']
        # see documentation/loadout.json for an example
        return await self.connection.request('patch', f'/lol-loadouts/v4/loadouts/{loadoutId}', json=loadoutChange)

    async def set_champion_skin(self, skinEntry: CosmeticDict):
        champ_selected = await self.connection.request('get', '/lol-champ-select/v1/current-champion')
        if champ_selected.status != 404:
            logger.info(f"setting champion skin to {skinEntry["id"]} '{skinEntry["name"]}' ...")
            patchContent = {"selectedSkinId": skinEntry["id"] }
            result = await self.connection.request('patch', '/lol-champ-select/v1/session/my-selection', data=patchContent)
            if result.status != 204:
                logger.info(f"Failed to set champion skin. {result}") # for example 500 Internal Server Error when Skin is not owned
                return
            logger.info("Success.")
    # endregion

    # region get api data
    async def _get_summonerId(self) -> str:
        summoner = await self.get_endpoint('/lol-summoner/v1/current-summoner/account-and-summoner-ids')
        return summoner.get("summonerId")
    
    async def get_loadout(self):
        loadoutData = await self.get_endpoint('/lol-loadouts/v4/loadouts/scope/account')
        loadoutId = loadoutData[0]['id']
        # see documentation/loadout.json for an example
        return await self.get_endpoint(f'/lol-loadouts/v4/loadouts/{loadoutId}')
    
    async def get_current_emote(self, emote_slot:str = "EMOTES_WHEEL_CENTER"):
        loadout = await self.get_loadout()
        return loadout["loadout"][emote_slot]["itemId"]
    
    async def get_current_ward(self):
        loadout = await self.get_loadout()
        return loadout["loadout"]["WARD_SKIN_SLOT"]["itemId"]

    async def get_ward_skins(self):
        summonerId = await self._get_summonerId()
        ward_skins_data = await self.cache_endpoint(f'/lol-collections/v1/inventories/{summonerId}/ward-skins', "ward_skin_collection.json")

        my_ward_skins = [ward for ward in ward_skins_data if ward["ownership"]["owned"] or ward["name"] == "Default Ward"]
        logger.info(f"{len(my_ward_skins)} owned ward skins")
        self._save_json(my_ward_skins, "owned_ward_skin_collection.json")


    async def get_champions_big(self):
        summonerId = await self._get_summonerId()
        await self.cache_endpoint(f'/lol-champions/v1/inventories/{summonerId}/champions')
        
    async def get_emotes(self) -> None:
        await self.cache_endpoint('/lol-inventory/v1/inventory/emotes')

    async def cache_endpoint(self, endpoint:str, cache_name:str = None) -> dict | None:
        """
        Requests endpoint from LCU api and saves result in cache.
        If no cache_name is provided, save name will be generated from endpoint name

        Raises: 
            DataRetrievalError
        """
        json_data = await self.get_endpoint(endpoint)
        pretty_name = endpoint.split("/")[-1]
        if cache_name is None:
            cache_name = pretty_name+".json"
        self._save_json(json_data, cache_name)
        logger.info(f"cached {cache_name}")
        return json_data
    
    async def get_endpoint(self, endpoint:str) -> dict | None:
        result = await self.connection.request('get', endpoint)
        
        pretty_name = "/".join(endpoint.split("/")[-2:])
        if result.status != 404:
            json_data = await result.json()
            logger.info(f"endpoint requested '.../{pretty_name}'")
            return json_data
        else:
            raise DataRetrievalError(f"Fetching {endpoint} failed")
    # endregion

    def _save_json(self, data:dict, file_name:str) -> None:
        out_path = DATA_PATHS.lcu_cache / file_name
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

class DataRetrievalError(RuntimeError):
    pass
   

if __name__ == "__main__":
    # starts the connector
    w = LCUWrapper()
    w.connector.start()



