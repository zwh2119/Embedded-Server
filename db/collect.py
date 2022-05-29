import asyncio
from bleak import BleakClient
import sys

DEBUG = False
LASTING_TIME = 20

devices = [
    "C4:39:0D:A9:91:89",
    "E6:7A:B7:B0:45:9D",
    "F2:02:E0:8D:B8:05"
]
MODEL_NBR_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"

output_cache = {}
output_cnt = 0

def output(address, data):

    global output_cache
    global output_cnt

    output_cnt = output_cnt + 1

    if output_cnt % 3 != 0:
        return

    if DEBUG:
        (ax, ay, az, wx, wy, wz, Roll, Pitch,
         Yaw, alx, aly, alz, agx, agy, agz) = data
        print("address: {}, ax: {}, ay: {}, az: {}, wx: {}, wy: {}, wz: {}, Roll: {}, Pitch: {}, Yaw: {}, alx: {}, aly: {}, alz: {}, agx: {}, agy: {}, agz:{}".format(
            address, ax, ay, az, wx, wy, wz, Roll, Pitch, Yaw, alx, aly, alz, agx, agy, agz))

    output_cache[address] = data
    for device in devices:
        if device not in output_cache:
            return

    for i in range(len(devices)):
        (ax, ay, az, wx, wy, wz, Roll, Pitch,
         Yaw, alx, aly, alz, agx, agy, agz) = output_cache[devices[i]]
        print("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(
            ax, ay, az, wx, wy, wz, Roll, Pitch, Yaw, alx, aly, alz, agx, agy, agz), end="")
        if(i != len(devices) - 1):
            print(",", end="")
    print()

    sys.stdout.flush()

alpha = 0.8
last = ()

def process_data(data):

    global last

    if len(data) != 20:
        raise Exception("Unexpected data length: {}".format(len(data)))
    if data[0] != 0x55 or data[1] != 0x61:
        raise Exception("Unexpected data header bytes: {}".format(data[:2]))

    axL = data[2]
    axH = data[3]
    ayL = data[4]
    ayH = data[5]
    azL = data[6]
    azH = data[7]

    k_a = 16
    ax = ((axH << 8) | axL) / 32768.0 * k_a
    ay = ((ayH << 8) | ayL) / 32768.0 * k_a
    az = ((azH << 8) | azL) / 32768.0 * k_a

    if ax >= k_a:
        ax -= 2 * k_a
    if ay >= k_a:
        ay -= 2 * k_a
    if az >= k_a:
        az -= 2 * k_a

    wxL = data[8]
    wxH = data[9]
    wyL = data[10]
    wyH = data[11]
    wzL = data[12]
    wzH = data[13]

    k_g = 2000

    wx = ((wxH << 8) | wxL) / 32768.0 * k_g
    wy = ((wyH << 8) | wyL) / 32768.0 * k_g
    wz = ((wzH << 8) | wzL) / 32768.0 * k_g

    if wx >= k_g:
        wx -= 2 * k_g
    if wy >= k_g:
        wy -= 2 * k_g
    if wz >= k_g:
        wz -= 2 * k_g

    RollL = data[14]
    RollH = data[15]
    PitchL = data[16]
    PitchH = data[17]
    YawL = data[18]
    YawH = data[19]

    k_angle = 180

    Roll = ((RollH << 8) | RollL) / 32768.0 * k_angle
    Pitch = ((PitchH << 8) | PitchL) / 32768.0 * k_angle
    Yaw = ((YawH << 8) | YawL) / 32768.0 * k_angle

    if Roll >= k_angle:
        Roll -= 2 * k_angle
    if Pitch >= k_angle:
        Pitch -= 2 * k_angle
    if Yaw >= k_angle:
        Yaw -= 2 * k_angle

    agx = ax
    agy = ay
    agz = az

    alx = 0
    aly = 0
    alz = 0

    if len(last) != 0:
        (lax, lay, laz, lwx, lwy, lwz, lRoll, lPitch,
         lYaw, lalx, laly, lalz, lagx, lagy, lagz) = last
        agx = alpha * lagx + (1 - alpha) * ax
        agy = alpha * lagy + (1 - alpha) * ay
        agz = alpha * lagz + (1 - alpha) * az

        alx = ax - agx
        aly = ay - agy
        alz = az - agz

    last = (ax, ay, az, wx, wy, wz, Roll, Pitch,
            Yaw, alx, aly, alz, agx, agy, agz)

    return last


def notification_handler(address):
    """Simple notification handler which prints the data received."""

    def handler(sender, data):
        output(address, process_data(data))

    return handler


async def run(address):

    while True:
        if DEBUG:
            print("Connecting to: {}".format(address))
        try:
            client = BleakClient(address)
            await client.connect()
            await client.start_notify(MODEL_NBR_UUID, notification_handler(address))
        except:
            if DEBUG:
                print("Failed to connect to: {}".format(address))
            if DEBUG:
                print("Retrying...: {}".format(address))
        else:
            break

    await asyncio.sleep(LASTING_TIME)
    await client.stop_notify(MODEL_NBR_UUID)


async def main():
    tasks = [run(address) for address in devices]
    await asyncio.gather(*tasks)
    # svcs = await client.get_services()
    # print("Services:")
    # for service in svcs:
    #     print(service)

    # print("Characteristics:")
    # for char in service.characteristics:
    #     print(char)

asyncio.run(main())
