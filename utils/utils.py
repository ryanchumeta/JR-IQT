import subprocess
import time
import skimage as ski
import numpy as np


def run_adb_command(command:str) -> str:
    """Runs any adb command w exitcode check using subprocess
    """
    command_succeded = False
    while not command_succeded:
        results = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if results.returncode == 0:
            command_succeded = True
        else:
            print(f"Adb command {command} failed with error {results.stderr}, rerunning in 2 seconds")
            time.sleep(2)
    return results.stdout

def xyz_to_labde(x:int, y:int, z:int) -> tuple:
    """Convert tristimulus coordinates XYZ to LabDE

    Parameters
    ----------
    x : _type_
        _description_
    y : _type_
        _description_
    z : _type_
        _description_

    Returns
    -------
    _type_
        _description_
    """
    # print("\nCalculating Lab and de00:")
    data = np.array([x,y,z], dtype=float)
    illuminant = np.array([0.9504, 1.0000, 1.0888], dtype=float)  # D65
    # Perform calculations and conversions
    data_lab = ski.color.xyz2lab(data / data[1]) # Normalize each row to the luminance value
    # print("data in Lab: ", data_lab)
    illuminant_lab = ski.color.xyz2lab(illuminant) # Calculate LAB value for illuminant reference
    data_de00c = ski.color.deltaE_ciede2000(data_lab, illuminant_lab, kL=1e10, kC=1, kH=1)
    # print(f'de00: {round(data_de00c, 2)}\n')
    return (data_lab[0], data_lab[1], data_lab [2], data_de00c)

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