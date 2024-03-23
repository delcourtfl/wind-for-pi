import time
import network
import ufirestore
from ufirestore.json import FirebaseJson
import ntptime
from machine import Pin, ADC
import sys
import gc

import asyncio
from asyncio import Lock

# https://stackoverflow.com/questions/77302815/issue-with-using-micropython-firebase-firestore-on-raspberry-pi-pico-w

def dateToIso(dateArr):
    # Convert time structure to a formatted ISO 8601 string
    iso_format = "{}-{}-{}T{}:{}:{}Z".format(dateArr[0], dateArr[1], dateArr[2], dateArr[3], dateArr[4], dateArr[5], dateArr[6])
    return iso_format

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect("ElRanch_Wi-Fi", "1A2B3C4D12")
        print("Waiting for Wi-Fi connection", end="...")
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(1)
        print()
    print("Connected.")

def syncTime():
    # if needed, overwrite default time server
    ntptime.host = "1.europe.pool.ntp.org"
    try:
        print("Local time before synchronization: %s" %str(time.localtime()))
        # need internet connection
        ntptime.settime()
        print("Local time after synchronization: %s" %str(time.localtime()))
        return True
    except Exception as e:
        print("Error syncing time")
        print(type(e))
        print(e)
        return False
    
async def connect_wifi(ssid, password):
    """Connect to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        print("Connecting to Wi-Fi", end="...")
        while not wlan.isconnected():
            print(".", end="")
            await asyncio.sleep(1)
        print()
    print("Connected to Wi-Fi.")

async def sync_time(time_server):
    """Synchronize time with NTP server."""
    try:
        print("Local time before synchronization:", time.localtime())
        ntptime.host = time_server
        await asyncio.sleep(1)  # Pause briefly before syncing time
        ntptime.settime()
        print("Local time after synchronization:", time.localtime())
        return True
    except Exception as e:
        print("Error syncing time:", e)
        return False
    
async def sender_task(doc, id, firestore_lock):
    try:
        await firestore_lock.acquire()
        print("Sending data to firestore:", doc, "at time:", id)
        # response = await asyncio.get_event_loop().run_in_executor(None, ufirestore.create, "data/", doc, id)
        # response = ufirestore.create("data/", doc, document_id=id, bg=False, cb=False)
        # print(response)
        firestore_lock.release()
        
        # Explicitly trigger garbage collection to free up memory
        gc.collect()
        print("Free memory after sending data:", gc.mem_free())
        
    except Exception as e:
        print("Error in sender:", e)

async def main():
    # Main logic of your script
    print("Init")

    await connect_wifi("ElRanch_Wi-Fi", "1A2B3C4D12")
    if not await sync_time("1.europe.pool.ntp.org"):
        sys.exit(0)

    ufirestore.set_project_id("windforpi")
    
    shared_data = {
        "id": None,
        "value": None,
        "lock": Lock()  # Lock for synchronization
    }

    doc = FirebaseJson()

    adc = ADC(Pin(28, mode=Pin.IN))
    led = Pin('LED', Pin.OUT)
    led.value(True)
    # calculate voltage from bits
    tension_factor = 3.3 / 65536
    factor = (993 + 222) / 222 * 1.03252
    total_factor = tension_factor * factor
    
    # INIT
    curr = 0
    cnt = 0
    index = 0
    t = dateToIso(time.localtime())
    doc.set("time/timestampValue", t)

    firestore_lock = Lock()
    
    # LOOP
    try:
        while True:
            curr = adc.read_u16() * total_factor
            curr = round(curr, 2)
            doc.set(f'{index}/doubleValue', curr)

            await asyncio.sleep(0.15)
            cnt = cnt + 1
            index = cnt % 100
            print(index)

            if (index == 0):

                asyncio.create_task(sender_task(doc, t, firestore_lock))
                
                doc = FirebaseJson()
                t = dateToIso(time.localtime())
                doc.set("time/timestampValue", t)
                
    except Exception as e:
        print("Error in reader:", e)
        led.value(False)

if __name__ == "__main__":
    asyncio.run(main())
