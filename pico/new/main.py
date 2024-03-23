import time
import network
# import ufirestore
# from ufirestore.async_ufirestore import set_project_id, create
from ufirestore.json import FirebaseJson
import ntptime
from machine import Pin, ADC
import sys
import gc

import uasyncio
from async_queue import Queue

import aiohttp

class SessionError(Exception):
    pass

# https://stackoverflow.com/questions/77302815/issue-with-using-micropython-firebase-firestore-on-raspberry-pi-pico-w

def date_to_iso(dateArr):
    # Convert time structure to a formatted ISO 8601 string
    iso_format = "{}-{}-{}T{}:{}:{}Z".format(dateArr[0], dateArr[1], dateArr[2], dateArr[3], dateArr[4], dateArr[5], dateArr[6])
    return iso_format
    
async def connect_wifi(ssid, password):
    """Connect to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        print("Connecting to Wi-Fi", end="...")
        while not wlan.isconnected():
            print(".", end="")
            await uasyncio.sleep(2)
        print()
    print("Connected to Wi-Fi.")

async def sync_time(time_server):
    """Synchronize time with NTP server."""
    try:
        print("Local time before synchronization:", time.localtime())
        ntptime.host = time_server
        await uasyncio.sleep(2)  # Pause briefly before syncing time
        ntptime.settime()
        print("Local time after synchronization:", time.localtime())
        return True
    except Exception as e:
        print("Error syncing time:", e)
        return False

async def producer(queue, led):
    doc = FirebaseJson()

    adc = ADC(Pin(28, mode=Pin.IN))
    # calculate voltage from bits
    tension_factor = 3.3 / 65536
    factor = (993 + 222) / 222 * 1.03252
    total_factor = tension_factor * factor
    
    # INIT
    curr = 0
    cnt = 0
    index = 0
    
    delay_idle = 5
    delay_active = 0.150
    delay = 5
    is_idle = True
    threshold = 0 #0.100
    buffer_size = 100

    # LOOP
    try:
        while True:
            curr = adc.read_u16() * total_factor
            curr = round(curr, 2)
            
            if is_idle and curr > threshold:
                delay = delay_active
                is_idle = False
                t = date_to_iso(time.localtime())
                doc.set("time/timestampValue", t)
                
            if not is_idle:
                doc.set(f'{index}/doubleValue', curr)
                cnt += 1
                index = cnt % buffer_size
                print(index)

                if index == 0:
                    await queue.put((doc, t))
                    print("Send data to consumer")
                    
                    doc = FirebaseJson()
                    delay = delay_idle
                    is_idle = True
                            
            await uasyncio.sleep(delay)
                
    except Exception as e:
        led.value(False)
        print("Error in producer:", e)

async def consumer(queue, led):
    path = "https://firestore.googleapis.com/v1/projects/windforpi/databases/(default)/documents/data"
    retries = 10
    for _ in range(retries):
        async with aiohttp.ClientSession(path) as session:
            while True:
                try:
                    doc, t = await queue.get()
                    print("Sending data to firestore:", doc, "at time:", t)
                    host = "/?documentId=" + t
                    data = doc.process()
                    async with session.post(host, json=data) as resp:
                        assert resp.status == 200
                        rpost = await resp.text()
                        print(f"POST: {rpost}")
                except Exception as e:
                    led.value(False)
                    print("Error sending data to firestore:", e)

                # Explicitly trigger garbage collection to free up memory
                gc.collect()
                print("Free memory after sending data:", gc.mem_free())
    
    led.value(False)
    raise SessionError("Failed to restore session after retries")
        
async def main():
    # Main logic of your script
    print("Init")

    await connect_wifi("ElRanch_Wi-Fi", "1A2B3C4D12")
    if not await sync_time("1.europe.pool.ntp.org"):
        sys.exit(0)

    # set_project_id("windforpi")

    queue = Queue()
    
    led = Pin('LED', Pin.OUT)
    led.value(True)

    # Create producer and consumer coroutines
    producer_task = uasyncio.create_task(producer(queue, led))
    consumer_task = uasyncio.create_task(consumer(queue, led))

    # Wait for both tasks to complete
    await uasyncio.gather(producer_task, consumer_task)

if __name__ == "__main__":
    uasyncio.run(main())

