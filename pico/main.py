import time
import network
import ufirestore
from time import sleep 
from ufirestore.json import FirebaseJson
import ntptime
from machine import Pin, ADC

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
    except:
        print("Error syncing time")

def main():
    # Main logic of your script
    print("Init")

    connect()
    syncTime()

    ufirestore.set_project_id("windforpi")

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
    t = dateToIso(time.localtime())
    doc.set("time/timestampValue", t)
    
    # LOOP
    while True:

        curr = adc.read_u16() * total_factor
        doc.set(f'{index}/doubleValue', curr)

        sleep(0.1)
        cnt = cnt + 1
        index = cnt % 200

        if (index == 0):

            response = ufirestore.create("data/", doc,  document_id=t, bg=False, cb=False)
        
            print(cnt)
            print(response)
            
            t = dateToIso(time.localtime())
            doc.set("time/timestampValue", t)

if __name__ == "__main__":
    main()