""""
Hypernova-1 P1 & EVT1
API for communicating via Android Debugging Brigde with devices of RT600 and RT700 architechtures 
"""
import time
import os
import json
import re
from utils.utils import run_adb_command

class HypernovaP1():
    """Class to communicate w Hypernova devices via ABD 
    """
    def __init__(self,images_folder = "") -> None:
        self.sn=run_adb_command("adb devices").split()[4]
        self.set_root()
        self.wakeup_display()
        self.set_timeout()
        self.disable_autobrightness()
        self.disable_wear_sensor()
        self.get_device_type()
        self.upload_white_square_pic()
        self.start_test_app()
        self.show_next_image()
        self.set_luminance(1000)
        self.images_folder = images_folder
        # self.enable_calib()

    def get_device_type(self) -> str:
        # result = run_adb_command("adb shell sgdeviceid | grep RT")
        result = "RT700"
        if "RT600" in result:
            self.device_type = "RT600"
        elif "RT700" in result:
            self.device_type = "RT700"
        else:
            raise RuntimeError("Device of unknown artichecture! Can't initialize")
        return self.device_type

    def enable_calib(self) ->  None:
        pass
        # run_adb_command("adb shell /mnt/vendor/persist/lcos/calib.sh")

    def set_root(self) ->  None:
        run_adb_command("adb root")
    
    def set_timeout(self) -> None:
        run_adb_command('adb shell settings put system screen_off_timeout 3600000')

    def disable_wear_sensor(self) -> None:
        run_adb_command('adb shell settings put global wear_detection_enabled 0')

    def disable_autobrightness(self) -> None:
        run_adb_command('adb shell settings put system screen_brightness_mode 0') 

    def remove_all_pictures(self) -> None:
        run_adb_command("adb shell rm -rf /data/data/com.meta.smartglass.app.displaytest/files/pictures/*")

    def upload_white_square_pic(self) -> None:
        p = r'C:\Users\ryanchu\Documents\projects\zaberStage\images\white.png'
        run_adb_command(f'adb push {p} /data/data/com.meta.smartglass.app.displaytest/files/pictures')

    def resize_display(self) -> None:
        run_adb_command('adb shell wm size 640x640')
    
    def push_image(self,image) -> None:
        print('push image')
        run_adb_command(f"adb push {image} /data/data/com.meta.smartglass.app.displaytest/files/pictures")
    
    def display_image(self,image) -> None:
        if not self.images_folder:
            print("no images folder, can't display")
            return
        else:
            self.remove_all_pictures()
            self.stop_test_app()
            impath = os.path.join(self.images_folder,image)
            self.push_image(impath)
            
            self.start_test_app()
            self.show_next_image()
            time.sleep(1.2)
        
    def wakeup_display(self) -> None:
        run_adb_command('adb shell input keyevent KEYCODE_WAKEUP')

    def start_test_app(self) ->  None:
        """ start display test  app
        """
        run_adb_command("adb shell am start com.meta.smartglass.app.displaytest/.MainActivity")
    
    def stop_test_app(self) -> None:
        run_adb_command('adb shell am force-stop com.meta.smartglass.app.displaytest')
    def toggle_display(self) -> None:
        run_adb_command("adb shell input keyevent 26")

    def show_next_image(self) -> None:
        #show white image (the only image that we loaded)
        run_adb_command("adb shell input keyevent 44")

    def set_lcos_voltages(self) ->  None:
        run_adb_command("adb shell 'echo 4000 > /sys/class/lcos-i2c-OP03010/lcos-i2c-OP03010/device/pixel_voltage'")

    def set_ito_voltages(self) -> None:
        run_adb_command("adb shell 'echo POS_RED_ITO_MV:1000 POS_GREEN_ITO_MV:500 POS_BLUE_ITO_MV:500 NEG_RED_ITO_MV:-1000 NEG_GREEN_ITO_MV:-500 NEG_BLUE_ITO_MV:-500 > /sys/class/lcos-i2c-OP03010/lcos-i2c-OP03010/device/ito_voltage'")
    
    def setup_for_wpc(self):
        """Set sytem up for WPC: load white image, start test app, setup screen calibration
        """
        self.remove_all_pictures()
        self.upload_white_square_pic()
        #set screen size
        self.start_test_app()
        # show white image
        self.show_next_image()
        #set lcos voltages
        # self.set_lcos_voltages()
        #set ito voltages
        # self.set_ito_voltages()
        #set lcos voltages again
        # self.set_lcos_voltages()

    def setup_for_redshift(self) -> None:
        """Setup teh hypernova device to run a redshift test:
                - lauch display
                - set resolution
                - launch display test app
                - load white square image
        """
        run_adb_command('adb shell wm size 640x640') # set display to 640x640
        run_adb_command("adb shell rm -f /data/data/com.meta.smartglass.app.displaytest/files/pictures/*")   # removing all existing images
        run_adb_command("adb push /Users/nataliaorlova/Documents/hypernova1/HN_WPC_white_image/* /data/data/com.meta.smartglass.app.displaytest/files/pictures") # loading only white square image
        run_adb_command("adb shell input keyevent 44")   # show white image

    def get_green_led_temp(self) -> float:
        """Read green LED temperature value from device

        Returns
        -------
        float
            green LED temperature value, in micro degrees celcius
        """
        if self.device_type == 'RT600':
            result = run_adb_command("adb shell cat /sys/class/thermal/tz-by-name/display-gtemp/temp")
            temp = float(result)/1000
        else:
            result = run_adb_command("adb shell tdb shell lcos readtemp g")
            pat = r"^\tRead LCOS temperature from (rb|g)\n\t\tTemperature: (\d+)\n"
            r = re.match(pat, result)
            if r is not None: 
                temp = float(r.group(2))/1000
            else:
                raise ValueError(f"Can parse temp line {result}")
        return temp

    def get_redblue_led_temp(self) -> float:
        """Read red and blue LED temperature from device

        Returns
        -------
        float
            red and blue LED temperature value, in micro degrees celcius 
        """
        if self.device_type == 'RT600':
            result = run_adb_command("adb shell cat /sys/class/thermal/tz-by-name/display-rbtemp/temp")
            temp = float(result)/1000
        else:
            result = run_adb_command("adb shell tdb shell lcos readtemp rb")
            pat = r"^\tRead LCOS temperature from (rb|g)\n\t\tTemperature: (\d+)\n"
            r = re.match(pat, result)
            if r is not None:
                temp = float(r.group(2))/1000
            else:
                raise ValueError(f"Can parse temp line {result}")
        return temp

    def get_led_voltages_hex(self) -> tuple:
        """Get led voltages from the device 

        Returns
        -------
        str
            returns string of hexidecimal values 
        """
        result = run_adb_command("adb shell i2ctransfer -yf 0 w1@0x29 0x25 r5")
        hex_values = result.split()
        return (hex_values[0], hex_values[1], hex_values[2], hex_values[4])
    
    def get_led_voltages(self) -> tuple:
        """_summary_
        """
        if self.device_type=="RT600":
            result=run_adb_command("adb shell cat /sys/class/display-led-driver/raa491901/led_voltages")
        else: 
            result=run_adb_command("adb shell tdb shell lcos get-led-voltages")

        voltages = result.split()
        v_r = voltages[0].split(':')[1]
        v_g = voltages[1].split(':')[1]
        v_b = voltages[2].split(':')[1]

        return (float(v_r), float(v_g), float(v_b))

    def get_led_resolution(self) -> str:
        """Read LED driver resolution 
        """
        if self.device_type == 'RT600':
            result = run_adb_command('adb shell cat /sys/class/display-led-driver/raa491901/bit_res_setting')
            resol = result.split()[0]
        else:
            result = run_adb_command('adb shell tdb shell lcos getledbitres')
            pat = r"^\tLED Bit resolution: (high|low|auto)\n"
            r = re.match(pat, result)
            if r is not None:
                resol = r.group(1)
            else:
                raise ValueError(f"Can parse resolution line {result}")
        return resol


    def set_led_resolution(self, value:str)-> None:
        """Sets resolution of LED driver

        Parameters
        ----------
        value : str
            "high", "low" or "auto"
        """
        if self.device_type == 'RT600':
            run_adb_command(f'adb shell "echo "{value}" >  /sys/class/display-led-driver/raa491901/bit_res_setting"')
            resol = self.get_led_resolution()
            if resol != value:
                print("Setting resolution failed - check syntax or device")
        else:
            run_adb_command(f"adb shell tdb shell lcos set-led-bitres-setting {value}")
            resol = self.get_led_resolution()
            if resol != value:
                print("Setting resolution failed - check syntax or device")

    def set_led_gains(self, gains : list) -> None:
        """Sets LED gains

        Parameters
        ----------
        gains : list
            list w values for R, G and B LED gains
        """
        # set_gains
        red = int(round(gains[0],0))
        green = int(round(gains[1], 0))
        blue = int(round(gains[2],0))
        print(f"Setting gains to {red}, {green}, {blue}")
        if self.device_type=="RT600":
            run_adb_command(f'adb shell \"echo \\"RED:{red} GREEN:{green} BLUE:{blue}\\" > /sys/class/display-led-driver/raa491901/led_gains"')
        else:
            run_adb_command(f"adb shell tdb shell lcos setledgains {red} {green} {blue}")
    
    def get_led_gains(self):
        if self.device_type == "RT600":
            result = run_adb_command("adb shell cat /sys/class/display-led-driver/raa491901/led_gains")
            gains = result.split()
            g_r = gains[0].split(':')[1]
            g_g = gains[1].split(':')[1]
            g_b = gains[2].split(':')[1]
        else:
            result = run_adb_command("adb shell tdb shell lcos getledgains")
            pat = r'^\tLED Gains: r = (\d+), g = (\d+), b = (\d+)\n'
            r = re.match(pat, result)
            if r is not None:
                g_r=r.group(1)
                g_g=r.group(2)
                g_b=r.group(3)
            else: 
                raise ValueError(f"Can parse gain line {result}")
        return (float(g_r), float(g_g), float(g_b))

    def get_led_currents(self) -> tuple:
        """Gets currents for RGB LEDs

        Returns
        -------
        tuple
            values, floats
        """
        if self.device_type == 'RT600':
            result=run_adb_command("adb shell cat /sys/class/display-led-driver/raa491901/led_currents")
            currents = result.split()
            i_r = currents[0].split(':')[1]
            i_g = currents[1].split(':')[1]
            i_b = currents[2].split(':')[1]
        else:
            result=run_adb_command("adb shell tdb shell lcos getledcurrents")
            pat = r'^\tLED Currents: r = (\d+), g = (\d+), b = (\d+)\n'
            r = re.match(pat, result)
            if r is not None:
                i_r=r.group(1)
                i_g=r.group(2)
                i_b=r.group(3)
            else: 
                raise ValueError(f"Can parse current line {result}")
        return (float(i_r), float(i_g), float(i_b))
    
    def calc_gains_for_currents(self, currents) -> tuple:
        """Caltulate gains given currents and resolution

        Returns
        -------
        tuple
            gains for red, green and blue LEDs
        """
        I = {'red' : currents[0], 'green' : currents[1], 'blue' : currents[1]}
    
        sf = self.get_slopes_offsets_from_json()
        r = self.get_led_resolution()
        colors = ['red', 'green', 'blue']
        G = {}
        for c in colors:
            G[c] = round((I[c]/1000 - sf[f'{r}_resolution_offset'][c]['offset'])/sf[f'{r}_resolution_offset'][c]['slope'],1)
        return (G['red'], G['green'], G['blue'])


    def set_led_currents(self, r : float, g: float, b: float) :
        """Sets currents of RGB LEDs, plus sets the resolution mode based on all curents values 
        Parameters
        ----------
        R : float
            Value for Red LED
        G : float
            Value for Green LED
        B : float
            Values for Blue LED
        """
        if r > 250000 or g > 250000 or b > 250000:
            raise ValueError(f'currents too high: {r}, {g}, {b}')
        elif r < 0 or g < 0 or b < 0:
            raise ValueError(f'currents cannot be negative: {r}, {g}, {b}')
        
        currents = [r,g,b]
        gains = self.calc_gains_for_currents(currents)
        # print(f"Gains for new currents are  {gains[0]}, {gains[1]}, {gains[2]}")
        # print(f"Current resolution is {self.get_led_resolution()}")
        if (gains[0] > 1023) or (gains[1]>1023) or (gains[2] > 1023) :
            # print("One of the gains is above 1023, changing resolution to low")
            self.set_led_resolution('low')
        # if r >= 4000 or g >= 4000 or b >= 4000:
        #     self.set_led_resolution("low")
        elif (gains[0] < 0) or (gains[1] < 0) or (gains[2] < 0) :
            # print("One of the gains is below 0, changing resolution to high")
            self.set_led_resolution("high")
        # else: 
        #     print("Resolution doesn't need adjustment per current LED gains")
        

        if self.device_type == 'RT600':
            result = run_adb_command(f'adb shell \"echo \\"RED:{str(round(r))} GREEN:{str(round(g))} BLUE:{str(round(b))}\\" > /sys/class/display-led-driver/raa491901/led_currents"')
            run_adb_command('adb shell "echo pwm > /sys/class/display-led-driver/raa491901/led_mode"')
            run_adb_command("adb shell i2ctransfer -yf 0 w1@0x29 0x02 r1")
            time.sleep(1)
            # print(f"Current resolution is {self.get_led_resolution()}, LED currents are {self.get_led_currents()}")
        else:
            result = run_adb_command(f"adb shell tdb shell lcos setledcurrents {str(round(r))} {str(round(g))} {str(round(b))}")
            # print(f"Current resolution is {self.get_led_resolution()}, LED currents are {self.get_led_currents()}")
        print(result)


    def set_luminance(self, luminance : int) -> None:
        """Sets luminance using brightnessControlCLI  - same command for RT600 or RT700

        Parameters
        ----------
        luminance : int
            luminance value
        """
        result = run_adb_command(f"adb shell brightnessControlCli set {str(luminance)}")
        print(result)

    def get_led_driver_settings(self) -> dict:
        """Gets offsets and slopes for high and low resoluton modes
        Returns
        -------
        tuple
            values, floats
        """
        result=run_adb_command("adb shell cat /sys/class/display-led-driver/raa491901/interpolation_coeffs")
        r = result.split()

        output = {}

        output['slope_hires'] = float(r[0].split(':')[1])/1000000
        output['offset_hires'] = float(r[1].split(':')[1])/1000
        
        output['slope_lowres'] = float(r[2].split(':')[1])/1000000
        output['offset_lowres'] = float(r[3].split(':')[1])/1000

        return output

    def get_slopes_offsets_from_json(self) -> dict:
        """Pull LED driver seting re slopes and offsets fomr json file

        Returns
        -------
        dict
            dictionary with settings

        Raises
        ------
        FileExistsError
            If json file cailed to be pulled ofmr DUT
        """
        run_adb_command("adb pull /mnt/vendor/persist/calibration/display_wpc_fatp_calibration_data.json")
        json_filename = 'display_wpc_fatp_calibration_data.json'
        json_abs_path = os.path.join(os.getcwd(), json_filename)

        if os.path.isfile(json_abs_path): 
            with open(json_abs_path, 'r') as f:
                json_data = json.load(f)
        else:
            raise FileExistsError('json calibration file was not pulled correctly from DUT. Debug...')
        return json_data['led_driver_setting_data'] 

    def enable_one_color(self, color : str) ->  None:
        """Enables only one channel : red, green or blue

        Parameters
        ----------
        color : string
            string corresponding to color, for red: "red" or "r", for green: "green" or "g", for blue: "blue" or "b"
        """

        if self.device_type == 'RT600':
            if color == 'red' or color == "r":
                run_adb_command("adb shell i2ctransfer -yf 0 w3@0x64 0x00 0x8c 0x71")
            elif color =='green' or color == "g":
                run_adb_command("adb shell i2ctransfer -yf 0 w3@0x64 0x00 0x8c 0x72")
            elif color == 'blue' or color == "b":
                run_adb_command("adb shell i2ctransfer -yf 0 w3@0x64 0x00 0x8c 0x74")
            else:
                raise RuntimeError('Incorrect color, only avilable are red, green or blue')
        elif self.device_type == 'RT700':
            if color == 'red' or color == "r":
                run_adb_command("adb shell tdb shell lcos i2c w 0x64 0x008C 0x71")
            elif color =='green' or color == "g":
                run_adb_command("adb shell tdb shell lcos i2c w 0x64 0x008C 0x72")
            elif color == 'blue' or color == "b":
                run_adb_command("adb shell tdb shell lcos i2c w 0x64 0x008C 0x74")
            else:
                raise RuntimeError('Incorrect color, only avilable are red, green or blue')
        else: 
            raise RuntimeError('Incorrect device type')
        return

    def enable_all_leds(self) -> None:
        """Enables all LED, Typically after some colors ahere filtered
        """
        if self.device_type == 'RT600':
            run_adb_command("adb shell i2ctransfer -yf 0 w3@0x64 0x008C 0x77")
        else: 
            run_adb_command("adb shell tdb shell lcos i2c w 0x64 0x008C 0x77")
        return
        
    