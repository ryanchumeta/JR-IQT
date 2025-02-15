import subprocess
import time
import skimage as ski
import numpy as np


def waitForDevice(timeout=120):
    start_time = time.time()
    while time.time() - start_time < timeout:
        print("Waiting for device...")
        time.sleep(6)
        output = subprocess.check_output(['adb', 'devices'])
        devices = output.decode().strip().replace('List of devices attached', '').split()
        if devices:
            print('device found')
            pass
        else:
            continue
        # need to make sure you can send command
        try:
            subprocess.check_output('adb shell am start com.meta.smartglass.app.displaytest/.MainActivity')
            print('initialized and ready to go')
            time.sleep(10)
            return
        except:
            print('not initialized yet')
            pass
    raise Exception("No device found within the specified timeout.")

def getRGB(color:str,gamma:int):
    r,g,b = 0,0,0
    match (color):
        case 'red':
            r = gamma
        case 'green':
            g = gamma
        case 'blue':
            b = gamma
    return(r,g,b)