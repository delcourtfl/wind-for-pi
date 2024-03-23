import time
import network
#import ufirestore
from ufirestore.async_ufirestore import set_project_id, create
from ufirestore.json import FirebaseJson
import ntptime
from machine import Pin, ADC
import sys
import gc

import uasyncio
from async_queue import Queue
import errno

import aiohttp

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

async def producer(queue):
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
    t = date_to_iso(time.localtime())
    doc.set("time/timestampValue", t)

    # LOOP
    try:
        while True:
            curr = adc.read_u16() * total_factor
            curr = round(curr, 2)
            doc.set(f'{index}/doubleValue', curr)

            cnt += 1
            index = cnt % 10
            print(index)

            if index == 0:
                await queue.put((doc, t))
                print("Send data to consumer")
                
                doc = FirebaseJson()
                t = date_to_iso(time.localtime())
                doc.set("time/timestampValue", t)
                
            await uasyncio.sleep(1)#0.150)
                
    except Exception as e:
        print("Error in producer:", e)
        led.value(False)

async def consumer(queue):
    while True:
        try:
#             response = await create("data/", doc, document_id=t, bg=False, cb=False)
            async with aiohttp.ClientSession(path) as session:
                doc, t = await queue.get()
                print("Sending data to firestore:", doc, "at time:", t)
                host = "https://firestore.googleapis.com/v1/projects/windforpi/databases/(default)/documents/data/?documentId=" + t
                data = doc.process()
                async with session.post("", json=data) as resp:
                    #assert resp.status == 200
                    print(resp)
                    rpost = await resp.text()
                    print(f"POST: {rpost}")
                    response = resp
            print(response)
        except Exception as e:
            print(e)
            print("Error sending data to firestore:", e)

        # Explicitly trigger garbage collection to free up memory
        gc.collect()
        print("Free memory after sending data:", gc.mem_free())
        
async def main():
    # Main logic of your script
    print("Init")

    await connect_wifi("ElRanch_Wi-Fi", "1A2B3C4D12")
    if not await sync_time("1.europe.pool.ntp.org"):
        sys.exit(0)

    set_project_id("windforpi")

    queue = Queue()
    
    #import uaiohttpclient as aiohttp
    #import uasyncio as asyncio

#     try:
#         port = 443
#         t = date_to_iso(time.localtime())
#         host = "https://firestore.googleapis.com/v1/projects/windforpi/databases/(default)/documents/data/?documentId=" + t
#         print('Testing:', host, port)
#         doc = FirebaseJson()
# #         response = create("data/", doc, document_id=t, bg=False, cb=False)
#         
# #         resp = await aiohttp.request("GET", host)
# #         print(resp)
# #         print(await resp.read())
#         async with aiohttp.ClientSession(host) as session:
#             data = doc.process()
#             async with session.post("", json=data) as resp:
#                 #assert resp.status == 200
#                 print(resp)
#                 rpost = await resp.text()
#                 print(f"POST: {rpost}")
# #         reader, writer = await asyncio.open_connection(host, port)
# #         print(reader, writer)
# #         writer.close()
#         print("ok")
# #         print(response)
#         return True
# #     except Exception as e:
# #         print("error")
#     except OSError as exc:
#         print(errno.errorcode[exc])
#         print(exc)
#         return False

    # Create producer and consumer coroutines
    producer_task = uasyncio.create_task(producer(queue))
    consumer_task = uasyncio.create_task(consumer(queue))

    # Wait for both tasks to complete
    await uasyncio.gather(producer_task, consumer_task)

if __name__ == "__main__":
    uasyncio.run(main())

