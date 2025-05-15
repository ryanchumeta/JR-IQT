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
comment = "Position_B_Cal_with_lens"
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
    exit()
home = input("Press Enter to home, 0 to skip")
if home == "":
    zaber.home_all()
zaber.move_absolute_async(*config["Positions"]["Hypernova_Center"]) ############## KEEP AN EYE ON THIS
    
while True:
    try:
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
        # input("Load DUT")
        recipe = recipes[sequence]
        if sequence == "gamma":
            data = gamma_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config)
        elif sequence == "WPC":
            data = wpc_alt(luminance_levels=list(map(int,(recipe["levels"].keys()))),color_error=recipe["color_error"],luminance_error=recipe["luminance_error"],km_exp=0,temp_iters=recipe["temp_iters"],iter_lim=recipe["iter_lim"],sufix="",run_num=0,km=km)
            wpc = write_lut_to_json_EVT1(wpc_dict=data,outputPath=output_directory)
        elif sequence == "macbeth":
            macbeth_file = config["Macbeth_levels_file"]
            with open(macbeth_file) as file:
                macbeth_dict = json.load(file)
            data = macbeth_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config,macbeth_dict=macbeth_dict)
        elif sequence in ["test_recipe_sweep2","test_recipe_sweep2_relay_optic"]:
            LUM_TABLE_VAL = {5000:"low",2660:"low",1414:"low",750:"low",500:"low",400:"high",310:"high",195:"high",120:"high",75:"high",48:"high",30:"high"}

            data = sweep_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config,levels = LUM_TABLE_VAL.keys())
        else:
            data = nominal_capture(recipe=recipe,hn=hn,zaber=zaber,km=km,config=config)

        pd.DataFrame(data).to_csv(os.path.join(output_directory,f"{hn.sn}_{sequence}_{datetime.now().strftime('%H%M%S')}_{comment}.csv"))
        zaber.move_absolute_async(*origin)
    except KeyboardInterrupt:
        km.disconnect()
        zaber.closeConnection()
    

