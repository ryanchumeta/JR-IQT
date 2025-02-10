from zaber_motion import Units
from zaber_motion.ascii import Connection
import serial.tools.list_ports


class Zaber():

	def __init__(self,port=""):
		self.stageConnection = None 
		self.axes = None
		self.port = port
		self.start()

	def start(self):
		axes = [None,None,None]
		print("Connection to stage")
		if self.port:
			print(f"at port {self.port}")
			connection = Connection.open_serial_port("COM6")
			# devices = connection.detect_devices()
	
			self.stageConnection = connection
			self.stageConnection.enable_alerts()
			
			axes[0] = self.stageConnection.detect_devices()[0].get_axis(1)
			axes[1] = self.stageConnection.detect_devices()[2].get_axis(1)
			axes[2] = self.stageConnection.detect_devices()[1].get_axis(1)
			self.axes = axes
		
		else:
			print("looking for ports")
			ports = serial.tools.list_ports.comports()
			for port in ports:
				print(port.device)
				try:
					connection = Connection.open_serial_port(port.device)
					# devices = connection.detect_devices()
					
					self.stageConnection = connection
					self.stageConnection.enable_alerts()
					
					axes[0] = self.stageConnection.detect_devices()[0].get_axis(1)
					axes[1] = self.stageConnection.detect_devices()[2].get_axis(1)
					axes[2] = self.stageConnection.detect_devices()[1].get_axis(1)
					self.axes = axes
					break
				except Exception as e:
					print(e)
					continue

			else:
				print("cannot connect to stage")
				return False
		print('Connected to stage!')
		return True
		
		
    
      

	def move_relative(self,axis,distance):
		print(f'moving axis {axis} by {distance} mm')
		self.axes[axis].move_relative(distance, Units.LENGTH_MILLIMETRES)

	def move_absolute(self,axis,position,waitIdle=True):
		try:
			self.axes[axis].move_absolute(position, Units.LENGTH_MILLIMETRES,wait_until_idle=waitIdle)
		except Exception as error:
			print(error)

	def get_current_position(self,axis):
		return round(self.axes[axis].get_position(Units.LENGTH_MILLIMETRES),3)
	def getAxisLimit(self,axis):
		return self.axes[axis].settings.get("limit.max",Units.LENGTH_MILLIMETRES)
	def home_all(self):
		self.stageConnection.home_all()
	def move_absolute_async(self,x,y,z):
		self.axes[0].move_absolute(x, Units.LENGTH_MILLIMETRES, wait_until_idle=False, velocity = 4, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)
		self.axes[1].move_absolute(y, Units.LENGTH_MILLIMETRES, wait_until_idle=False, velocity = 4, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)
		self.axes[2].move_absolute(z, Units.LENGTH_MILLIMETRES, wait_until_idle=False, velocity = 4, velocity_unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)
		self.axes[0].wait_until_idle()
		self.axes[1].wait_until_idle()
		self.axes[2].wait_until_idle()

		
	def closeConnection(self):
		self.stageConnection.close()
	


	
     

  
  






