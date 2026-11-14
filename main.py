import pystray
from PIL import Image
import asyncio
import sys
from cosmetics.lcu import LCUWrapper
import threading
import cosmetics.logging_config as logging_config
from cosmetics.paths import DATA_PATHS
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path


logging_config.setup_logging()
logger = logging_config.get_logger()

LCU_wrapper = LCUWrapper(on_connect_callback= lambda: set_status("Initializing..."), 
                         on_ready_callback=lambda name: set_status(f"Hello {name}!", True), 
                         on_disconnect_callback=lambda: set_status("Waiting for League Client...", False),
                         on_error=lambda msg : set_status(msg, False))

tray_app = None # set in __main__

status_text = "Waiting for League Client..."
ready = False

def is_ready(item) -> bool:
    return ready

def set_status(text:str, is_ready: bool = False):
    global status_text, ready
    status_text = text
    ready = is_ready
    if tray_app is not None:
        tray_app.title = f"Cosmetics - {text}" # tooltip on hover
        tray_app.update_menu()

def start_lcu_connector():
    """Starts the LCU connector in a new thread."""
    logger.info("Starting LCU connector thread...")
    # The connector.start() is a blocking call, so it must run in a separate thread.
    LCU_wrapper.connector.start()

def run_lcu_function(func, *args, **kwargs):
    if LCU_wrapper.connection is None:
        logger.info("Error: LCU is not connected. Please open the League Client")
        return
    loop = LCU_wrapper.connector.loop
    future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)

    try:
        future.result()
    except Exception as e:
        logger.info(f"Error executing LCU function: {e}")

def on_random_ward_click(tray_app, item):
    run_lcu_function(LCU_wrapper.select_ward_skin)

def on_bann_ward(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_ward)

def on_random_emote(tray_app, item):
    run_lcu_function(LCU_wrapper.select_emote)

def on_bann_emote(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_emote)

def on_heart_emote(try_app, item):
    run_lcu_function(LCU_wrapper.favourite_emote)

def on_random_skin(tray_app, item):
    run_lcu_function(LCU_wrapper.select_champion_skin)

def on_bann_skin(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_skin)

def on_open_logs(tray_app, item):
    log_dir = DATA_PATHS.log_folder
    if log_dir is None or not log_dir.exists():
        logger.warning("Could not determine log folder")
        return
    if sys.platform == "win32":
        os.startfile(log_dir)
    else:
        logger.error("cannot open log folder in os other than windows.")

icon_image = Image.open(str(DATA_PATHS.assets_path/"icon.png"))
def quit_action(tray_app, item):
    logger.info("Buh Bye!")
    LCU_wrapper.connector.stop()
    tray_app.stop()

tray_menu = pystray.Menu(
        pystray.MenuItem(lambda item: status_text, None, enabled=False),
        pystray.MenuItem("Reroll Ward!", on_random_ward_click, enabled=is_ready),
        pystray.MenuItem("    Bann", on_bann_ward, enabled=is_ready),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Random Emote!", on_random_emote, enabled=is_ready),
        pystray.MenuItem("   Bann", on_bann_emote, enabled=is_ready),
        pystray.MenuItem("   Favourite", on_heart_emote, enabled=is_ready),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Random Skin!", on_random_skin, enabled=is_ready),
        pystray.MenuItem("   Bann", on_bann_skin, enabled=is_ready),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open log folder", on_open_logs),   # always available
        pystray.MenuItem("Exit", quit_action) # always available
    )

if __name__ == "__main__":
    logger.info("--------------- Hello there ----------------------")
    lcu_thread = threading.Thread(target=start_lcu_connector, daemon=True)
    lcu_thread.start()

    tray_app = pystray.Icon(
        name='Cosmetics',
        icon = icon_image,
        title="Cosmetics",
        menu=tray_menu
    )
    tray_app.title = f"Cosmetics - {status_text}" # tooltip on hover

    logger.info("Starting system tray icon. Right-click for menu")
    tray_app.run()
    logger.info("--------------Application stopped-----------------")
    for i in range(3):
        logger.info(" ")

