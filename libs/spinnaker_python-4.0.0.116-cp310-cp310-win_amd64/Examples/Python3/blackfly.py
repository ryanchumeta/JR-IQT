import PySpin
import sys
import time


class blackfly():

    def __init__(self,format:str,exposure:float):
        self.system = None
        self.cam_list = None
        self.cam = None
        self.connected = False
        self.nodemap = None
        self.exposure = exposure
        match format:
            case "mono16":
                self.format = PySpin.PixelFormat_Mono16
            case "mono8":
                self.format = PySpin.PixelFormat_Mono8
            case _:
                self.format = PySpin.PixelFormat_Mono8
        if self.connect():
            self.connected = True
        else:
            print("Can't connect to camera")
        if self.connected:
            self.configure_custom_image_settings()
            self.configure_exposure()

    def connect(self):
        
        """
        Example entry point; please see Enumeration example for more in-depth
        comments on preparing and cleaning up the system.

        :return: True if successful, False otherwise.
        :rtype: bool
        """
        result = True

        # Retrieve singleton reference to system object
        system = PySpin.System.GetInstance()
        self.system = system
        # Get current library version
        version = system.GetLibraryVersion()
        print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

        # Retrieve list of cameras from the system
        cam_list = system.GetCameras()
        self.cam_list = cam_list
        num_cameras = self.cam_list.GetSize()

        print('Number of cameras detected: %d' % num_cameras)

        # Finish if there are no cameras
        if num_cameras == 0:
            # Clear camera list before releasing system
            self.cam_list.Clear()

            # Release system instance
            self.system.ReleaseInstance()

            print('Not enough cameras!')
            input('Done! Press Enter to exit...')
            return False

        # Run example on each camera
        for i, cam in enumerate(cam_list):

            print('Found camera %d...' % i)

            self.cam = cam
        nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
        self.nodemap = nodemap_tldevice
        result &= self.print_device_info()
        self.cam.Init()
            

        return result
    
    def reset_trigger(cam):
        """
        This function returns the camera to a normal state by turning off trigger mode.

        :param cam: Camera to acquire images from.
        :type cam: CameraPtr
        :returns: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            result = True
            # Ensure trigger mode off
            # The trigger must be disabled in order to configure whether the source
            # is software or hardware.
            if cam.TriggerMode.GetAccessMode() != PySpin.RW:
                print('Unable to disable trigger mode (node retrieval). Aborting...')
                return False

            cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)

            print('Trigger mode disabled...')

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result

    def reset_exposure(self):
        """
        This function returns the camera to a normal state by re-enabling automatic exposure.

        :param cam: Camera to reset exposure on.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            result = True

            # Turn automatic exposure back on
            #
            # *** NOTES ***
            # Automatic exposure is turned on in order to return the camera to its
            # default state.

            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to enable automatic exposure (node retrieval). Non-fatal error...')
                return False

            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

            print('Automatic exposure enabled...')

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result
    def print_device_info(self):
        """
        This function prints the device information of the camera from the transport
        layer; please see NodeMapInfo example for more in-depth comments on printing
        device information from the nodemap.

        :param nodemap: Transport layer device nodemap.
        :type nodemap: INodeMap
        :returns: True if successful, False otherwise.
        :rtype: bool
        """

        print('*** DEVICE INFORMATION ***\n')

        try:
            result = True
            node_device_information = PySpin.CCategoryPtr(self.nodemap.GetNode('DeviceInformation'))

            if PySpin.IsReadable(node_device_information):
                features = node_device_information.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    print('%s: %s' % (node_feature.GetName(),
                                    node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

            else:
                print('Device control information not readable.')

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return result


    def disconnect(self):
        result = True
        # Release reference to camera
        # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
        # cleaned up when going out of scope.
        # The usage of del is preferred to assigning the variable to None.
        try:
            
            self.reset_exposure()
            self.reset_trigger()
            self.cam.DeInit()
            del self.cam

            # Clear camera list before releasing system
            self.cam_list.Clear()

            # Release system instance
            self.system.ReleaseInstance()
        except:
            return False

        return result


    def acquire_image(self):
        """
        This function acquires and saves an images from a device.
        Please see Acquisition example for more in-depth comments on acquiring images.

        :param cam: Camera to acquire images from.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """

        print('*** IMAGE ACQUISITION ***\n')
        try:
            result = True

            # Set acquisition mode to continuous
            if self.cam.AcquisitionMode.GetAccessMode() != PySpin.RW:
                print('Unable to set acquisition mode to continuous. Aborting...')
                return False

            self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            print('Acquisition mode set to continuous...')

            #  Begin acquiring images
            self.cam.BeginAcquisition()

            print('Acquiring images...')

            # Get device serial number for filename
            device_serial_number = ''
            if self.cam.TLDevice.DeviceSerialNumber.GetAccessMode() == PySpin.RO:
                device_serial_number = self.cam.TLDevice.DeviceSerialNumber.GetValue()

                # print('Device serial number retrieved as %s...' % device_serial_number)

            # Retrieve, convert, and save images

            # Create ImageProcessor instance for post processing images
            processor = PySpin.ImageProcessor()

            # Set default image processor color processing method
            #
            # *** NOTES ***
            # By default, if no specific color processing algorithm is set, the image
            # processor will default to NEAREST_NEIGHBOR method.
            processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)

            
            try:

                #  Retrieve the next image from the trigger
                result &= self.grab_next_image_by_trigger()

                #  Retrieve next received image
                image_result = self.cam.GetNextImage(1000)

                #  Ensure image completion
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                else:

                    #  Print image information
                    width = image_result.GetWidth()
                    height = image_result.GetHeight()
                    print('Grabbed Image width = %d, height = %d' % (width, height))

                    #  Convert image to mono 16
                    image_converted = processor.Convert(image_result, PySpin.PixelFormat_Mono16)
                    imageND = image_converted.GetNDArray()
                    from PIL import Image
                    im = Image.fromarray(imageND)
                    im.show()

                    # Create a unique filename
                    filename = f"sup_{time.strftime('%S')}.jpg"

                    # Save image
                    image_converted.Save(filename)

                    print('Image saved at %s\n' % filename)

                    #  Release image
                    image_result.Release()

            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False

            # End acquisition
            self.cam.EndAcquisition()

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return result


    def grab_next_image_by_trigger(self):
        """
        This function acquires an image by executing the trigger node.

        :param cam: Camera to acquire images from.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        try:
            result = True
            # Use trigger to capture image
            # The software trigger only feigns being executed by the Enter key;
            # what might not be immediately apparent is that there is not a
            # continuous stream of images being captured; in other examples that
            # acquire images, the camera captures a continuous stream of images.
            # When an image is retrieved, it is plucked from the stream.


            # Execute software trigger
            if self.cam.TriggerSoftware.GetAccessMode() != PySpin.WO:
                print('Unable to execute trigger. Aborting...')
                return False

            self.cam.TriggerSoftware.Execute()
            time.sleep(2)

            # TODO: Blackfly and Flea3 GEV cameras need 2 second delay after software trigger

            

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return result

    def configure_custom_image_settings(self):
        """
        Configures a number of settings on the camera including offsets X and Y,
        width, height, and pixel format. These settings must be applied before
        BeginAcquisition() is called; otherwise, those nodes would be read only.
        Also, it is important to note that settings are applied immediately.
        This means if you plan to reduce the width and move the x offset accordingly,
        you need to apply such changes in the appropriate order.

        :param cam: Camera to configure settings on.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        print('\n*** CONFIGURING CUSTOM IMAGE SETTINGS ***\n')

        try:
            result = True

            # Apply mono 8 pixel format
            #
            # *** NOTES ***
            # In QuickSpin, enumeration nodes are as easy to set as other node
            # types. This is because enum values representing each entry node
            # are added to the API.
            if self.cam.PixelFormat.GetAccessMode() == PySpin.RW:
                self.cam.PixelFormat.SetValue(self.format)
                print('Pixel format set to %s...' % self.cam.PixelFormat.GetCurrentEntry().GetSymbolic())

            else:
                print('Pixel format not available...')
                result = False

            # Apply minimum to offset X
            #
            # *** NOTES ***
            # Numeric nodes have both a minimum and maximum. A minimum is retrieved
            # with the method GetMin(). Sometimes it can be important to check
            # minimums to ensure that your desired value is within range.
            if self.cam.OffsetX.GetAccessMode() == PySpin.RW:
                self.cam.OffsetX.SetValue(self.cam.OffsetX.GetMin())
                print('Offset X set to %d...' % self.cam.OffsetX.GetValue())

            else:
                print('Offset X not available...')
                result = False

            # Apply minimum to offset Y
            #
            # *** NOTES ***
            # It is often desirable to check the increment as well. The increment
            # is a number of which a desired value must be a multiple. Certain
            # nodes, such as those corresponding to offsets X and Y, have an
            # increment of 1, which basically means that any value within range
            # is appropriate. The increment is retrieved with the method GetInc().
            if self.cam.OffsetY.GetAccessMode() == PySpin.RW:
                self.cam.OffsetY.SetValue(self.cam.OffsetY.GetMin())
                print('Offset Y set to %d...' % self.cam.OffsetY.GetValue())

            else:
                print('Offset Y not available...')
                result = False

            # Set maximum width
            #
            # *** NOTES ***
            # Other nodes, such as those corresponding to image width and height,
            # might have an increment other than 1. In these cases, it can be
            # important to check that the desired value is a multiple of the
            # increment.
            #
            # This is often the case for width and height nodes. However, because
            # these nodes are being set to their maximums, there is no real reason
            # to check against the increment.
            if self.cam.Width.GetAccessMode() == PySpin.RW and self.cam.Width.GetInc() != 0 and self.cam.Width.GetMax != 0:
                self.cam.Width.SetValue(self.cam.Width.GetMax())
                print('Width set to %i...' % self.cam.Width.GetValue())

            else:
                print('Width not available...')
                result = False

            # Set maximum height
            #
            # *** NOTES ***
            # A maximum is retrieved with the method GetMax(). A node's minimum and
            # maximum should always be a multiple of its increment.
            if self.cam.Height.GetAccessMode() == PySpin.RW and self.cam.Height.GetInc() != 0 and self.cam.Height.GetMax != 0:
                self.cam.Height.SetValue(self.cam.Height.GetMax())
                print('Height set to %i...' % self.cam.Height.GetValue())

            else:
                print('Height not available...')
                result = False

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

        return result
    def configure_exposure(self):
        """
        This function configures a custom exposure time. Automatic exposure is turned
        off in order to allow for the customization, and then the custom setting is
        applied.

        :param cam: Camera to configure exposure for.
        :type cam: CameraPtr
        :return: True if successful, False otherwise.
        :rtype: bool
        """

        print('*** CONFIGURING EXPOSURE ***\n')

        try:
            result = True

            # Turn off automatic exposure mode
            #
            # *** NOTES ***
            # Automatic exposure prevents the manual configuration of exposure
            # times and needs to be turned off for this example. Enumerations
            # representing entry nodes have been added to QuickSpin. This allows
            # for the much easier setting of enumeration nodes to new values.
            #
            # The naming convention of QuickSpin enums is the name of the
            # enumeration node followed by an underscore and the symbolic of
            # the entry node. Selecting "Off" on the "ExposureAuto" node is
            # thus named "ExposureAuto_Off".
            #
            # *** LATER ***
            # Exposure time can be set automatically or manually as needed. This
            # example turns automatic exposure off to set it manually and back
            # on to return the camera to its default state.

            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic exposure. Aborting...')
                return False

            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            print('Automatic exposure disabled...')

            # Set exposure time manually; exposure time recorded in microseconds
            #
            # *** NOTES ***
            # Notice that the node is checked for availability and writability
            # prior to the setting of the node. In QuickSpin, availability and
            # writability are ensured by checking the access mode.
            #
            # Further, it is ensured that the desired exposure time does not exceed
            # the maximum. Exposure time is counted in microseconds - this can be
            # found out either by retrieving the unit with the GetUnit() method or
            # by checking SpinView.

            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print('Unable to set exposure time. Aborting...')
                return False

            # Ensure desired exposure time does not exceed the maximum
            exposure_time_to_set = self.exposure
            exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), exposure_time_to_set)
            self.cam.ExposureTime.SetValue(exposure_time_to_set)
            print('Shutter time set to %s us...\n' % exposure_time_to_set)

        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result
    
    
if __name__=="__main__":
    bf = blackfly(format = "mono16",exposure = 500000.0)
    x = "0"
    while x=="0":
        bf.acquire_image()
        x = input("Press 0 to take image, 1 to exit")
    print("exited")
    bf.disconnect()