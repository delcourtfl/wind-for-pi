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

    curr = 0
    cnt = 0

    while True:
        curr = adc.read_u16() * 3.3 / 65536 # calculate voltage from bits
        t = time.localtime()

        doc.set("year/integerValue", t[0])
        doc.set("month/integerValue", t[1])
        doc.set("day/integerValue", t[2])
        doc.set("hour/integerValue", t[3])
        doc.set("minute/integerValue", t[4])
        doc.set("second/integerValue", t[5])
        doc.set("fullTime/timestampValue", dateToIso(time.localtime()))
        doc.set("value/doubleValue", curr)
        response = ufirestore.create("data/", doc,  document_id=dateToIso(t), bg=False, cb=False)
        print(cnt)
        print(response)
        sleep(1)
        cnt = cnt + 1

if __name__ == "__main__":
    main()