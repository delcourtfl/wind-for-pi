import time
import network
import ufirestore
from time import sleep 
from ufirestore.json import FirebaseJson
import ntptime
from machine import Pin, ADC
import sys
import _thread
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
    ntptime.NTP_DELTA = 10
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

async def reader_task(shared_data):
    
    doc = FirebaseJson()

    adc = ADC(Pin(28, mode=Pin.IN))
    led = machine.Pin('LED', machine.Pin.OUT)
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
                
                await shared_data["lock"].acquire()
                shared_data["value"] = doc
                shared_data["id"] = t
                shared_data["empty"] = False
                shared_data["lock"].release()
                           
                print("Data written to shared object")
                
                t = dateToIso(time.localtime())
                doc.set("time/timestampValue", t)
                
    except Exception as e:
        print("Error in reader:", e)
        led.value(False)
    
async def main():
    # Main logic of your script
    print("Init")

    connect()
    res = syncTime()
    if not res:
        sys.exit(0)

    ufirestore.set_project_id("windforpi")
    
    shared_data = {
        "id": None,
        "value": None,
        "empty": True,
        "lock": Lock()  # Lock for synchronization
    }
    
    reader = asyncio.create_task(reader_task(shared_data))
    
    while True:
        try:
            # Acquire the lock
            if not shared_data["empty"]:
                
                await shared_data["lock"].acquire()
                doc = shared_data["value"]
                id = shared_data["id"]
                shared_data["empty"] = True
                
                print("Sending data to firestore:", doc, "at time:", id)
                response = ufirestore.create("data/", doc, document_id=id, bg=False, cb=False)
                print(response)
                shared_data["lock"].release()
                
                # Explicitly trigger garbage collection to free up memory
                gc.collect()
                print("Free memory after sending data:", gc.mem_free())

            await asyncio.sleep(10)
            
        except Exception as e:
            print("Error in sender:", e)
            

if __name__ == "__main__":
    asyncio.run(main())
