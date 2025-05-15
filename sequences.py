import pandas as pd
import os
from Devices.HypernovaP1 import HypernovaP1 as HN
from Devices.KonicaMinolta import KonicaMinolta as KM
from Devices.zaberClass import Zaber
from utils.utils import getRGB
from PIL import Image
from hypernova_tools.hypernova_tools.scripts.WPC_EVT2_alt import wpc_display_calibration_alt as wpc_alt
from hypernova_tools.hypernova_tools.utils.hn_tools import xyz_to_labde, write_lut_to_json_EVT1
import time
def nominal_capture(recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict) -> dict:
    origin = config["Positions"][recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)

    captures = recipe['Captures'] #dict
    print("captures: \n",captures)
    dataDict = {'capture_name':[],"X":[],"Y":[],"Z":[],"L*":[],"a*":[],"b*":[],"dE00*C":[],'temp-rb':[],'temp-g':[],'Ir':[],'Ig':[],'Ib':[]}
    current_image = ""
    for i,capturekey in enumerate(captures.keys()):
        print(capturekey)
        capture = captures[capturekey]
        if capture["image"] == current_image:
            pass
        else:
            hn.display_image(capture["image"])
            current_image = capture["image"]
            print(f"displaying {capture['image']}")
        
        pupil_position = config["Pupil_locations"][capture['pupil_position']]
        print(origin)
        print(pupil_position)
        stage_position = [x + y for x, y in zip(origin, pupil_position)]
        zaber.move_absolute_async(*stage_position)
        x,y,z = km.get_xyz()
        print(x,y,z)
        L,a,b,dE = xyz_to_labde(x,y,z)
        temp_rb = hn.get_redblue_led_temp()
        temp_g = hn.get_green_led_temp()
        currs = hn.get_led_currents()
        dataDict['capture_name'].append(capturekey)
        dataDict['X'].append(x)
        dataDict['Y'].append(y)
        dataDict['Z'].append(z)
        dataDict['L*'].append(L)
        dataDict['a*'].append(a)
        dataDict['b*'].append(b)
        dataDict['dE00*C'].append(dE)
        dataDict['temp-rb'].append(temp_rb)
        dataDict['temp-g'].append(temp_g)
        dataDict['Ir'].append(currs[0])
        dataDict['Ig'].append(currs[1])
        dataDict['Ib'].append(currs[2])

    return dataDict

def sweep_capture(recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict,levels:list) -> dict:
    origin = config["Positions"][recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)

    captures = recipe['Captures'] #dict
    print("captures: \n",captures)
    dataDict = {'capture_name':[],"X":[],"Y":[],"Z":[],"L*":[],"a*":[],"b*":[],"dE00*C":[],'temp-rb':[],'temp-g':[],'Ir':[],'Ig':[],'Ib':[]}
    current_image = ""
    for i,capturekey in enumerate(captures.keys()):
        print(capturekey)
        capture = captures[capturekey]
        if capture["image"] == current_image:
            pass
        else:
            hn.display_image(capture["image"])
            current_image = capture["image"]
            print(f"displaying {capture['image']}")
        
        pupil_position = config["Pupil_locations"][capture['pupil_position']]
        print(origin)
        print(pupil_position)
        stage_position = [x + y for x, y in zip(origin, pupil_position)]
        zaber.move_absolute_async(*stage_position)
        time.sleep(1)
        for level in levels:
            hn.set_luminance(level)
            time.sleep(0.5)
            x,y,z = km.get_xyz()
            print(x,y,z)
            L,a,b,dE = xyz_to_labde(x,y,z)
            temp_rb = hn.get_redblue_led_temp()
            temp_g = hn.get_green_led_temp()
            currs = hn.get_led_currents()
            dataDict['capture_name'].append(capturekey + "_" + str(level))
            dataDict['X'].append(x)
            dataDict['Y'].append(y)
            dataDict['Z'].append(z)
            dataDict['L*'].append(L)
            dataDict['a*'].append(a)
            dataDict['b*'].append(b)
            dataDict['dE00*C'].append(dE)
            dataDict['temp-rb'].append(temp_rb)
            dataDict['temp-g'].append(temp_g)
            dataDict['Ir'].append(currs[0])
            dataDict['Ig'].append(currs[1])
            dataDict['Ib'].append(currs[2])

    return dataDict

def gamma_capture(recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict) -> dict:
    origin = config["Positions"][recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)
    levels = None
    if recipe["levels"] == "all":
        levels = range(256)
    else:
        levels = recipe["levels"]
    dataDict = {'gammaLevel':[], "redX":[], "redY":[], "redZ":[],
                "greenX":[], "greenY":[], "greenZ":[],
                "blueX":[], "blueY":[], "blueZ":[]}
    for color in ['red','green','blue']:
        dataDict['gammaLevel'] = levels
        for i in levels:
            imagePath = os.path.join(config["ImagesFolder"],f'gamma.png')
            img = Image.new('RGB', (600, 600), getRGB(color,i))
            img.save(imagePath)
            print("color: ", color, "gamma level: ",i)
            hn.display_image(imagePath)
            x,y,z = km.get_xyz()
            print(x,y,z)
            dataDict[f'{color}X'].append(x)
            dataDict[f'{color}Y'].append(y)
            dataDict[f'{color}Z'].append(z)
    return dataDict

def macbeth_capture(recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict,macbeth_dict:dict,dE00C_params:dict = {"kL": 1e9, "kC": 1, "kH": 1}) -> dict:
    origin = config["Positions"][recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)
    
    
    dataDict = {'color':[], "X":[], "Y":[], "Z":[],
                "Xnorm":[], "Ynorm":[], "Znorm":[],
                "L":[],"a":[],'b':[],
                "L_ref":[],"a_ref":[],'b_ref':[],
                "L_delta":[],"a_delta":[],'b_delta':[],
                'dE00C':[]}
    Ynorm = 1
    for image in macbeth_dict.keys():
        r,g,b = macbeth_dict[image]["Gray Code R"], macbeth_dict[image]["Gray Code G"], macbeth_dict[image]["Gray Code B"]
        imagePath = os.path.join(config["ImagesFolder"],f'macbeth.png')
        img = Image.new('RGB', (600, 600), (r,g,b))
        img.save(imagePath)
        hn.display_image(imagePath)
        x,y,z = km.get_xyz()
        if image == 'illuminant':
            Ynorm = y
        refL,refa,refb = macbeth_dict[image]["Reference L*"], macbeth_dict[image]["Reference a*"], macbeth_dict[image]["Reference b*"]

        dataDict['color'].append(image)
        dataDict['X'].append(x)
        dataDict['Y'].append(y)
        dataDict['Z'].append(z)
        dataDict['L_ref'].append(refL)
        dataDict['a_ref'].append(refa)
        dataDict['b_ref'].append(refb)
    dataDict['Xnorm'] = [x/Ynorm for x in dataDict['X']]
    dataDict['Ynorm'] = [y/Ynorm for y in dataDict['Y']]
    dataDict['Znorm'] = [z/Ynorm for z in dataDict['Z']]
    L_list, a_list, b_list, dE_list = zip(*[xyz_to_labde(dataDict['Xnorm'][i],dataDict['Ynorm'][i],dataDict['Znorm'][i],
                                                         (dataDict['L_ref'][i],dataDict['a_ref'][i],dataDict['b_ref'][i]),
                                                         params = dE00C_params) for i in range(len(dataDict['color']))])
    dataDict['L'] = list(L_list)
    dataDict['a'] = list(a_list)
    dataDict['b'] = list(b_list)
    dataDict['dE00C'] = list(dE_list)
    dataDict['L_delta'] = [dataDict['L'][i] - dataDict['L_ref'][i] for i in range(len(dataDict['color']))]
    dataDict['a_delta'] = [dataDict['a'][i] - dataDict['a_ref'][i] for i in range(len(dataDict['color']))]
    dataDict['b_delta'] = [dataDict['b'][i] - dataDict['b_ref'][i] for i in range(len(dataDict['color']))]

    print(dataDict)    
    return dataDict

#TODO
def WPC_capture(recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict):
    origin = config["Positions"][recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)
    WPC_dict = wpc_alt(recipe["levels"],recipe["color_error"],recipe["luminance_error"],0,recipe["temp_iters"],recipe["iter_lim"],"",0)
    calib = write_lut_to_json_EVT1(hn,WPC_dict)
    return WPC_dict,calib