import pystray
from PIL import Image, ImageDraw
import time
import asyncio
from cosmetics.lcu import LCUWrapper
import threading

LCU_wrapper = LCUWrapper()

def start_lcu_connector():
    """Starts the LCU connector in a new thread."""
    print("Starting LCU connector thread...")
    # The connector.start() is a blocking call, so it must run in a separate thread.
    LCU_wrapper.connector.start()

def run_lcu_function(func, *args, **kwargs):
    if LCU_wrapper.connection is None:
        print("Error: LCU is not connected. Please open the League Client")
        return
    loop = LCU_wrapper.connector.loop
    future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)

    try:
        future.result()
    except Exception as e:
        print(f"Error executing LCU function: {e}")

def on_random_ward_click(tray_app, item):
    run_lcu_function(LCU_wrapper.select_ward_skin)

def on_bann_ward(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_ward)

def on_ranodm_emote(tray_app, item):
    run_lcu_function(LCU_wrapper.select_emote)

def on_bann_emote(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_emote)

def on_random_skin(tray_app, item):
    run_lcu_function(LCU_wrapper.select_champion_skin)

def on_bann_skin(tray_app, item):
    run_lcu_function(LCU_wrapper.bann_skin)

icon_image = Image.open("assets/icon.png") 
def quit_action(tray_app, item):
    print("Buh Bye!")
    LCU_wrapper.connector.stop()
    tray_app.stop()

tray_menu = pystray.Menu(
        pystray.MenuItem("Random Ward!", on_random_ward_click),
        pystray.MenuItem("Bann Ward", on_bann_ward),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Random Emote!", on_ranodm_emote),
        pystray.MenuItem("Bann Emote", on_bann_emote),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Random Skin!", on_random_skin),
        pystray.MenuItem("Bann Skin", on_bann_skin),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", quit_action)
    )

if __name__ == "__main__":

    lcu_thread = threading.Thread(target=start_lcu_connector, daemon=True)
    lcu_thread.start()

    tray_app = pystray.Icon(
        name='Varie-T',
        icon = icon_image,
        title="Varie-T",
        menu=tray_menu
    )

    print("Starting system tray icon. Right-click for menu")
    tray_app.run()
    print("Application stopped")

