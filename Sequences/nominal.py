import pandas as pd
from ..Devices.HypernovaP1 import HypernovaP1 as HN
from ..Devices.KonicaMinolta import KonicaMinolta as KM
from ..Devices.zaberClass import Zaber

def nominal_capture(selected_recipe:dict, hn:HN,zaber:Zaber, km:KM,config:dict,) -> pd.DataFrame:
    origin = config["Positions"][selected_recipe['Origin']]
    print(f'Moving to Origin {origin}')
    zaber.move_absolute_async(*origin)

    captures = selected_recipe['Captures'] #dict
    data = {'capture_name':[],"X":[],"Y":[],"Z":[]}
    current_image = ""
    for i,capturekey in enumerate(captures.keys()):
        print(capturekey)
        capture = captures[capturekey]
        if capture["image"] == current_image:
            pass
        else:
            hn.display_image(capture["image"])
            print(f"displaying {capture["image"]}")
        
        pupil_position = config["Pupil_locations"][capture['pupil_position']]
        print(origin)
        print(pupil_position)
        stage_position = [x + y for x, y in zip(origin, pupil_position)]
        zaber.move_absolute_async(*stage_position)
        x,y,z = km.get_xyz()
        print(x,y,z)
        data['capture_name'].append(capturekey)
        data['X'].append(x)
        data['Y'].append(y)
        data['Z'].append(z)
        return pd.DataFrame(data)