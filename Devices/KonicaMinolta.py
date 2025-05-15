"""
Class for connecting to and getting XYZ data from Konica Minolta Color Analyzer 410

"""
import re
import serial
import time

class KonicaMinolta():
    """Class to communicate wiht a Konica Minolta color analyzer cA410
    """
    delimiter = '\r\n'
    def __init__(self, port, calibration_channel,exposure):
        self.port = port
        self.exposure=exposure
        self.ser = None
        self.delimiter = '\r\n'
        self.calibration_channel = calibration_channel
        self.out = None
        self.x = None
        self.y = None
        self.z = None
        self.connect()

    def connect(self):
        """
        Initializes the serial connection and send the parameters for measurement, 
        including the correct calibration channel
        """
        print('initializing KM')
        com_port = serial.Serial(
                    port=self.port,
                    baudrate=38400,
                    bytesize=7,
                    timeout=0.25, # min value should be calculated using formula in the com protocol datasheet 
                    parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_TWO,
                )
        self.ser = com_port

        self.ser.write(("COM,1" + self.delimiter).encode())
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r':
            print('\tStarted communications with data processor on KM.')
        else:
            print('\tFailed to start communications with data processor on KM, debug me')

        self.ser.write(("STR,23" + self.delimiter).encode())
        self.out = self.ser.readline().decode('ascii')
        
        if self.out != 'OK00,2\r':
            self.ser.write(("ZRC" + self.delimiter).encode())
            time.sleep(5)
            self.out = self.ser.readline().decode('ascii')
            if self.out == 'OK00\r':
                print('\tZero calibration executed.')
            else:
                print('\tFailed to execture zero calibration, debug me')
       
        
      
        
        self.ser.write((f"SCS,5,{self.exposure}" + self.delimiter).encode()) #Setting synch mode to MANUAL 
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet synchronization Mode to internal on KM')
        else:
            print('\tFailed to set synchronization Mode to internal on KM, debug me')
        
        self.ser.write(("FSC,1" + self.delimiter).encode()) # measurement speed, 1 = fast
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet measurement speed to fast on KM')
        else:
            print('\tFailed to set measurement speed to fast on KM, debug me')

        self.ser.write(("OPR,1" + self.delimiter).encode())
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet output probe to P1.')
        else:
            print('\tFailed to set output probe to P1, debug me')


        self.ser.write(("VSN,1" + self.delimiter).encode()) # single or double frame measurement
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet measuremnt type to single frame.')
        else:
            print('\tFailed to set measuremnt type to single frame, debug me')

        self.ser.write(("MMS,1" + self.delimiter).encode()) # simultaneous color and flicker measurements - 1 is only color, 0 is both, 2 is only flicker
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet measuremnt type to color measurement only.')
        else:
            print('\tFailed to set measuremnt type to color measurement only, debug me')

        self.ser.write(("MDS,7" + self.delimiter).encode()) # [7] means X,Y and Z mode
        self.out = self.ser.readline().decode('ascii')
        if self.out == 'OK00\r': 
            print('\tSet Display Mode to X,Y,Z.')
        else:
            print('\tFailed to set Display Mode to X,Y,Z, debug me')

        channel_setting = 'MCH,' + str(self.calibration_channel) # set calibration channel TODO: use this to select appropriate channel for each brightness leve
        self.ser.write((channel_setting + self.delimiter).encode())
        if self.out == 'OK00\r': 
            print(f'\tSet calibration channel to {self.calibration_channel}')
        else:
            print(f'\tFailed to set calibration channel to {self.calibration_channel}, debug me')

        self.ser.write(("LUS,1" + self.delimiter).encode()) # measurement units, 1 = cd/m2, 0 - flux 
        self.ser.write((channel_setting + self.delimiter).encode())
        if self.out == 'OK00\r': 
            print('\tSet measurement units to cd/m2')
        else:
            print('\tFailed to set measurement units to cd/m2, debug me')

        print('Finished initializing KM')
        return
    
    def change_calibration_channel(self,calibration_channel:int) -> None:
        """Sets calibration channel to use 

        Parameters
        ----------
        calChannel : int
            calibration channel
        """

        channel_setting = 'MCH,' + str(calibration_channel)
        self.ser.write((channel_setting + self.delimiter).encode())
        

    def get_xyz(self) -> tuple:
        """
        Execute measurement of a tristimulus color coordinates via serial 
            Serial command returns "Error code,[1],[2],[3],[4],[5],[6],[7]"
            Error codes: 
            OK00 : Normal completion; if anything else returned - needs debugging; 
            [1] Probe number
            [2] Display mode, set in init by "MDS" command to 7, if not 7 - raise erorr
            [3] X - these are the tristim values to return by fn
            [4] Y
            [5] Z
            [6] Temperature shift from zero calibration measurement, -99.99 to +99.99, in degrees Celcuius, don't need this value as device will not return OK00 is temp varies by too much 
            [7] FMA flicker value, since were not measuring flicker, mode is set to JEITA and this value should always be -999999
            Example return strings: 
            'OK00,P1,7,2947.9417,3262.4584,3410.7795,+1.07,-99999999\r'
            'OK00,P1,7,2890.9042,3246.5969,3367.1378,+1.07,-99999999\r'
            'OK00,P1,7,2872.3677,3246.7783,3365.0454,+1.09,-99999999\r'
        Returns 
        -------
        Tuple
            X, Y and Z 
        """
        # print("\nTaking Measurement on KM:")
        m=None
        i=0
        while m is None:
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.write(("MES,1" + self.delimiter).encode()) 
            self.out = self.ser.readline().decode('ascii')
            # print(f"KM Output is : '{self.out}'")
            line = self.out
            m = re.match("^([OE][KR]\d+),P1,(7),(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+),[-+]\d+\.\d+,-99999999", line)
            i += 1
            if i >= 10:
                raise RuntimeError('KM measurements failed after 10 iterations, check connection')
        
        assert m.group(1) == 'OK00', f"error returned is not OK00, but {m.group(1)}, see KM refference."
        # error_code = m.group(1)

        assert m.group(2) == '7', f"Display mode is not set to correct value, {m.group(2)}, should be 7"
        # display_mode = m.group(2)
        x = m.group(3)
        y = m.group(4)
        z = m.group(5)
        return float(x), float(y), float(z)

    def disconnect(self):
        """Close connection to KM
        """
        self.ser.write(("COM,0" + self.delimiter).encode())