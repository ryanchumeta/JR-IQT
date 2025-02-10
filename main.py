# -*- coding: utf-8 -*-
from Devices.KonicaMinolta import KonicaMinolta as KM
from Devices.zaberClass import Zaber
from Devices.HypernovaP1 import HypernovaP1 as HN
import json
import os
import pandas as pd
from Sequences.nominal import nominal_capture

# import tester config
with open(r"C:\Users\ryanchu\Documents\projects\zaberStage\config\JRIQT.json",'r') as f:
    config = json.load(f)

# import recipes
with open(r"C:\Users\ryanchu\Documents\projects\zaberStage\config\JRIQT_recipe.json",'r') as f:
    recipes = json.load(f)

#connect to devices
zaber = Zaber(config['Zaber_COMPORT'])
km = KM(config['KM_COMPORT'],config["KM_Calibration_Channel"],config['KM_Exposure_Time'])
hn = HN(images_folder = config["Images_folder"]) # check initialization
print("Please select recipe:")
recipes_list = list(recipes.keys())
for i,recipe in enumerate(recipes_list):
    print(f"{i+1}) {recipe}")
selection = int(input()) #int
sequence = recipes_list[selection-1]
data = None
match sequence:
    case "gamma":
        pass
    case "WPC":
        pass
    case _:
        data = nominal_capture(selected_recipe=recipes[sequence],hn=hn,zaber=zaber,km=km,config=config)
data.to_csv(os.path.join())
