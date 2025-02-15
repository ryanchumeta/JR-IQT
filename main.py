# -*- coding: utf-8 -*-
from Devices.KonicaMinolta import KonicaMinolta as KM
from Devices.zaberClass import Zaber
from Devices.HypernovaP1 import HypernovaP1 as HN
import json
import os
import pandas as pd
from sequences import *
from datetime import datetime

date = datetime.today().strftime('%Y%m%d')
output_directory = f"Output/{date}"
os.makedirs(output_directory,exist_ok=True)
# import tester config
with open(r"C:\Users\ryanchu\Documents\projects\JRIQT\config\JRIQT.json",'r') as f:
    config = json.load(f)

# import recipes
with open(r"C:\Users\ryanchu\Documents\projects\JRIQT\config\JRIQT_recipe.json",'r') as f:
    recipes = json.load(f)

#connect to devices
try:
    zaber = Zaber(config['Zaber_COMPORT'])
    km = KM(config['KM_COMPORT'],config["KM_Calibration_Channel"],config['KM_Exposure_Time'])
    hn = HN(images_folder = config["Images_folder"]) # check initialization
except Exception as e:
    print(e)
    exit(1)

print("Please select recipe:")
recipes_list = list(recipes.keys())
for i,recipe in enumerate(recipes_list):
    print(f"{i+1}) {recipe}")
selection = int(input()) #int
sequence = recipes_list[selection-1]
data = None
origin = config["Positions"][recipes[sequence]['Origin']]
print(f'Moving to Origin {origin}')
zaber.move_absolute_async(*origin)
recipe = recipes[sequence]
match sequence:
    case "gamma":
        data = gamma_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config)
    case "WPC":
        data = wpc_alt(luminance_levels=list(map(int,(recipe["levels"].keys()))),color_error=recipe["color_error"],luminance_error=recipe["luminance_error"],km_exp=0,temp_iters=recipe["temp_iters"],iter_lim=recipe["iter_lim"],sufix="",run_num=0,km=km)
        wpc = write_lut_to_json_EVT1(wpc_dict=data,outputPath=output_directory)
    case "macbeth":
        macbeth_file = config["Macbeth_levels_file"]
        with open(macbeth_file) as file:
            macbeth_dict = json.load(file)
        data = macbeth_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config,macbeth_dict=macbeth_dict)
    
    case _:
        data = nominal_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config)
zaber.move_absolute_async(*origin)
km.disconnect()
zaber.closeConnection()
pd.DataFrame(data).to_csv(os.path.join(output_directory,f"{hn.sn}_{sequence}.csv"))
