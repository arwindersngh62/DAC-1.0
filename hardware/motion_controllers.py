"""Classes for linear stages, rotation mounts, etc.

Each motion controller class is a subclass of
_MotionControllerTemplate. This is to try and ensure that all motion
controllers have a small set of standard methods. Each class can then
extend the basic functionality.

"""
# Standard packages
import time
import re
import math
import os
from ctypes import *
import numpy as np

# Custom packages
from . import connections


class _MotionControllerTemplate:
    """Base class for a motion controller.

    Contains variables and methods universal to all (most) motion
    controllers. Create a subclass from this template, then implement
    the methods in the specific way required.

    """

    def __init__(
        self,
        connection_type: str = 'serial',
        **connection_overloads
    ):
        self._connection_type = connection_type
        self._connection_overloads = connection_overloads
        self._connection_defaults = dict()
        self.connection = self.make_connection()
        self.nat_cmds = self._NativeCommands(self.connection)

    class _NativeCommands:
        """Native commands for the instrument.

        A class containing methods that have names following
        (as closely as possible) the naming conventions used in
        the manual for the device.

        """

        def __init__(self, connection):
            self.connection = connection

        pass

    def make_connection(self):
        """Connect to an instrument with a given protocol."""
        # Get default kwargs for the given protocol
        try:
            self._connection_kwargs =\
                self._connection_defaults[self._connection_type]
        except KeyError:  # connection type not implemented/available
            err_msg = '{} is not a valid connection type'\
                .format(self._connection_type)
            raise KeyError(err_msg)

        # Overload, or append, items from _connection_overloads
        for keyword in self._connection_overloads:
            self._connection_kwargs[keyword] =\
                self._connection_overloads[keyword]

        # Connect the instrument
        connection = connections.select_connection(
            self._connection_type,
            **self._connection_kwargs)
        return connection

    def initialize(self,):
        """Run the iControl default initilization routine."""
        raise NotImplementedError

    def get_instrument_id(self,):
        """Get the equivalent of *IDN?."""
        raise NotImplementedError

    def reboot(self,):
        """Effectively like power-cycling the device."""
        raise NotImplementedError

    def load_defaults(self,):
        """Load/Restore manufacturer default parameters."""
        raise NotImplementedError

    def query_error_code(self,):
        """Return error string."""
        raise NotImplementedError

    def find_home_position(self, axis,):
        """Locate and set the default home position."""
        raise NotImplementedError

    def set_home_position(self, axis,):
        """Set the current location as the home position."""
        raise NotImplementedError

    def query_home_position(self, axis,):
        """Return the current home position."""
        raise NotImplementedError

    def find_travel_limits(self, axis,):
        """Locate or return the travel limits."""
        raise NotImplementedError

    def set_travel_limits(self, axis,):
        """Set the (soft) travel limits."""
        raise NotImplementedError

    def query_travel_limits(self, axis,):
        """Return the current travel limits."""
        raise NotImplementedError

    def query_current_position(self, axis,):
        """Return the current position."""
        raise NotImplementedError

    def query_target_position(self, axis,):
        """Return the target position."""
        raise NotImplementedError

    def move_absolute(self, position, axis,):
        """Move to an absolute location."""
        raise NotImplementedError

    def move_relative(self, distance, axis,):
        """Move relative to current position."""
        raise NotImplementedError

    def query_motion_status(self,):
        """Determine if stage is moving."""
        raise NotImplementedError

    def stop_motion(self, axis,):
        """Stop all motion."""
        raise NotImplementedError


class ESP300_Control(_MotionControllerTemplate):
    _precision = 0.001
    _twait = 0.3
    
    """
        Attributes
    ----------
    connection : connections.? instance
        A connection to an instrument using the protocol selected by
        connection_type. An instance of 'connections.?', where ?
        follows from connection_type.
    """
    
    def __init__(
        self,
        connection_type: str = 'serial',
        **connection_overloads
    ):
        """constructor.

        Parameters
        ----------
        connection_type : str, optional, default: 'serial'
            Connection protocol
        **connection_overloads
            Connection keyword arguments (kwargs) that overide default
            values in the dictionary _connection_defaults
        """
        
        self._connection_type = connection_type
        self._connection_overloads = connection_overloads
        self._connection_defaults = {
            'serial': {
                'get_instrument_id': False,
                'terminating_char': '\n',
                'port': 'COM3',
                'baudrate': 19200,
                'timeout': 1,
            },
            'visa': {
                'resource_name': 'GPIB0::1::INSTR',
            }
        }
        _precision = 0.001
        _twait = 0.3
        self.connection = self.make_connection()
        #For GPIB connection
        #self.Instrument = connections.VISAConnection(resource_name = 'GPIB0::2::INSTR')
        
        #For Serial connection
        # self.Instrument = connections.SerialInstrument(
                # get_instrument_id=True,
                # terminating_char='\n\r',
                # port='COM3',
                # baudrate=19200,
                # bytesize=serial.EIGHTBITS,
                # stopbits=serial.STOPBITS_ONE,
                # parity=serial.PARITY_NONE
                # )

        #self.Instrument.write(('1MF').encode())
        #self.Instrument(('2MF'+self._term).encode())
        #self.Instrument(('3MF'+self._term).encode())

    # --- Naive commands --- #

    def ID(self, axis):
        command = (str(axis) + 'ID?')
        response = self.connection.transaction(command)
        print(str(response))
        return response
        # requests the ID of the controller

    def MO(self, axis):
        command = (str(axis) + 'MO')
        self.connection.send(command)
        # activates the chosen controller axis

    def MF(self, axis):
        command = (str(axis) + 'MF')
        self.connection.send(command)
        # deactivates the axis of the controller

    def DH(self, axis):
        command = (str(axis) + 'DH')
        self.connection.send(command)
        # Sets new zero/home position

    def OR(self, axis):
        command = (str(axis) + 'OR')
        self.connection.send(command)
        # This command executes a Home search routine on the axis

    def TP(self, axis):
        command = (str(axis) + 'TP')
        return self.connection.transaction(command)
        #read actual position

    def ST(self, axis):
        command = (str(axis) + 'ST')
        self.connection.send(command)
        # stop the motion of the stage

    def MT_plus(self, axis):
        command = (str(axis) + 'MT+')
        self.connection.send(command)
        # Move to upper hardware travel limit

    def MT_minus(self, axis):
        command = (str(axis) + 'MT-')
        self.connection.send(command)
        # Move to lower hardware travel limit

    def PA(self, axis, newpos=float()):
        command = (str(axis) + 'PA' + str(newpos))
        self.connection.send(command)
        # Move to absolute position

    def PR(self, axis, delay):
        command = (str(axis) + 'PR' + str(delay))
        self.connection.send(command)
        # Move to relative position

    def MZ_plus(self, axis):
        command = (str(axis) + 'MZ+')
        self.connection.send(command)
        # Move to nearest upper index

    def MZ_minus(self, axis):
        command = (str(axis) + 'MZ-')
        self.connection.send(command)
        # Move to nearest lower index

    def TV(self, axis):
        command = (str(axis) + 'TV')
        return self.connection.transaction(command)
        # Get actual velocity

    def VA(self, axis, velo):
        command = (str(axis) + 'VA' + str(velo))
        self.connection.send(command)
        time.sleep(self._twait)
        # Set velocity

    def VU_question(self, axis):
        command = (str(axis) + 'VU?')
        return self.connection.transaction(command)
        # Get maximum velocity

    def VU(self, axis, max_velo):
        command = (str(axis) + 'VU' + str(max_velo))
        self.connection.send(command)
        # Set maximum velocity

    def TB_question(self):
        command = "TB?"
        return self.connection.transaction(command)
        # read error message

    def TE_question(self):
        command = "TE?"
        return self.connection.transaction(command)
        # read error code




    # --- Custom Commands --- #

    # def send(self, command):
        # self.Instrument.send(
            # (command + self.Instrument.terminating_char).encode()
        # )

    # def read_raw(self,):
        # return self.Instrument.read_raw()

    # def transaction(self, command):
        # self.send(command)
        # time.sleep(self._twait)
        # return self.read_raw()
            
    def get_id(self, axis):
        return self.ID(axis)

    def axis_on(self, axis):
        self.MO(axis)
    
    def axis_off(self, axis):
        self.MF(axis)
        
    def set_home_pos(self, axis):
        self.DH(axis)
        time.sleep(self._twait)
        accpos = self.get_pos(axis)
        if accpos == 0:
            print('New Home position is set')
        else:
            print("New Home not set! Try again!")

    def move_home(self, axis):
        self.OR(axis)
        time.sleep(0.5)
        accpos = self.get_pos(axis)
        while accpos != 0.0:
            time.sleep(self._twait)
            accpos = self.get_pos(axis)
        else:
            time.sleep(0.5)
        
    def get_pos(self, axis):
        response = self.TP(axis)
        response = float(response)
        print('Current Position: '+ str(response))
        return response
    
    def stop_motion(self, axis):
        self.ST(axis)
        time.sleep(self._twait)
        response = self.get_pos(axis)
        print('Motion stoped! Position:'+ str(response ))
        return response

    def upper_travel_lim(self, axis):
        self.MT_plus(axis)
        print('Moving to upper hardware limit!')
        
    def lower_travel_lim(self, axis):
        self.MT_minus(axis)
        print('Moving to lower hardware limit!')
        
    def move_abs(self, axis, newpos):
        self.PA(axis, newpos)
        time.sleep(0.5)
        accpos = self.get_pos(axis)
        dif = abs(newpos - accpos)
        precision = 0.001
        while dif > precision:
            time.sleep(0.5)
            accpos = self.get_pos(axis)
            dif = abs(newpos - accpos)
        
        print('New position is:' + str(accpos))
        
        
    def move_rel(self, axis, delay):
        self.PR(axis, delay)

    def move_nearest_up(self, axis):
        self.MZ_plus(axis)
        
    def move_nearest_down(self, axis):
        self.MZ_minus(axis)
    
    def get_velocity(self, axis):
        response = self.TV(axis)
        print(str(response))
        
    def set_velocity(self, axis, velo): #velo in units/s
        self.VA(axis, velo)
        print('Velocity is changed to:' + str(velo) + 'units/s')
        
    def get_max_velocity(self, axis):
        response = self.VU_question(axis)
        print(str(response))
        
    def set_max_velocity(self, axis, max_velo):
        self.VU(axis, max_velo)

    def read_errors(self):
        error_code = self.TE_question()
        error_msg = self.TB_question()
        print((str(error_code) + str(error_msg)))


class PI_E873_3QTU(_MotionControllerTemplate):
    """PI_E873_3QTU subclass.

    Attributes
    ----------
    connection : connections.? instance
        A connection to an instrument using the protocol selected by
        connection_type. An instance of 'connections.?', where ?
        follows from connection_type.
    nat_cmds : _NativeCommands instance
        Contains methods that have names following (as closely as
        possible) the naming conventions used in the manual for the
        device.

    """

    def __init__(
        self,
        connection_type: str = 'serial',
        **connection_overloads
    ):
        """PI_E873_3QTU constructor.

        Parameters
        ----------
        connection_type : str, optional, default: 'serial'
            Connection protocol
        **connection_overloads
            Connection keyword arguments (kwargs) that overide default
            values in the dictionary _connection_defaults

        """
        self._connection_type = connection_type
        self._connection_overloads = connection_overloads
        self._connection_defaults = {
            'serial': {
                'get_instrument_id': False,
                'terminating_char': '\n',
                'port': 'COM28',
                'baudrate': 115200,
                'timeout': 1,
            },
            'ethernet': {
                'get_instrument_id': False,
                'terminating_char': '\n',
                'ip_addr': '10.4.101.23',
                'port': 23,
                'timeout': 3,
                'buffersize': 1024,
            }
        }
        self.connection = self.make_connection()
        self.nat_cmds = self._NativeCommands(self.connection)


    class _NativeCommands(_MotionControllerTemplate._NativeCommands):

        def num4(self):
            # Request Status Register (p. 122)
            return self.connection.transaction(chr(4))

        def num5(self,):
            # Request Motion Status (p. 123)
            # Response: The response <uint> is bit-encoded and returned as the
            #           hexadecimal sum of the following codes:
            #           1=First axis in motion
            #           2=Second axis in motion
            #           4=Third axis in motion
            #           ...
            # Examples: 0 indicates motion of all axes complete
            #           3 indicates that the first and the second axis are in motion
            return self.connection.transaction(chr(5))

        def num7(self,):
            # Request Controller Ready Status (p. 123)
            return self.connection.transaction(chr(7))

        def num8(self,):
            # Query If Macro Is Running (p. 123)
            return self.connection.transaction(chr(8))

        def num24(self,):
            # Stop All Axes (p. 124)
            self.connection.send(chr(24))

        def IDN_query(self,):
            # Get Device Identification (p. 124)
            return self.connection.transaction('*IDN?')

        def ADD(self, Variable, FLOAT1, FLOAT2,):
            # Add and Save To Variable (p. 125)
            self.connection.send('ADD' +
                              ' ' +
                              str(Variable) +
                              ' ' +
                              str(FLOAT1) +
                              ' ' +
                              str(FLOAT2)
                              )

        def CCL(self, Level, PSWD=None,):
            # Set Command Level (p. 127)
            if PSWD is None:
                self.connection.send('CCL' + ' ' + str(Level))
            else:
                self.connection.send('CCL' + ' ' + str(Level) + ' ' + str(PSWD))

        def CCL_query(self,):
            # Get Command Level (p. 128)
            return self.connection.transaction('CCL?')

        def CPY(self, Variable, CMD_query,):
            # Copy query result Into Variable (p. 128)
            self.connection.send('CPY' +
                              ' ' +
                              str(Variable) +
                              ' ' +
                              str(CMD_query)
                              )

        def CST_query(self, AxisIDs: tuple = None):
            # Get Assignment Of Stages To Axes (p. 129)
            command = 'CST?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        # def CSV? Get Current Syntax Version (p. 130)

        # def CTO {<TrigOutID> <CTOPam> <Value>} Set Configuration Of Trigger Output (p. 130)

        # def CTO? [{<TrigOutID> <CTOPam>}] Get Configuration Of Trigger Output (p. 133)

        # def DEL <uint> Delay The Command Interpreter (p. 133)

        def DFH(self, AxisIDs: tuple = None):
            # Define Home Position (p. 134)
            # Current position set as home position
            command = 'DFH'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        def DFH_query(self, AxisIDs: tuple = None):
            # Get Home Position Definition (p. 135)
            command = 'DFH?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        # def DIO {<DIOID> <OutputOn>} Set Digital Output Lines (p. 136)

        # def DIO? [{<DIOID>}] Get Digital Input Lines (p. 136)

        # def DRC {<RecTableID> <Source> <RecOption>} Set Data Recorder Configuration (p. 137)

        # def DRC? [{<RecTableID>}] Get Data Recorder Configuration (p. 138)

        # def DRL? [{<RecTableID>}] Get Number Of Recorded Points (p. 139)

        # def DRR? [<StartPoint> <NumberOfPoints> [{<RecTableID>}]] Get Recorded Data Values (p. 139)

        # def DRT {<RecTableID> <TriggerSource> <Value>} Set Data Recorder Trigger Source (p. 141)

        # def DRT? [{<RecTableID>}] Get Data Recorder Trigger Source (p. 142)

        # def ERR? Get Error Number (p. 142)

        def FED(self, AxisIDs: tuple, EdgeIDs: tuple, Params: tuple):
            # Find Edge (p. 143)
            # Move to a reference position (pos/neg limit, center...),
            # without "referencing" the axis.
            command = 'FED'
            for AxisID, EdgeID, Param in zip(AxisIDs, EdgeIDs, Params):
                command += ' ' + str(AxisID) + ' ' + str(EdgeID) + ' ' + str(Param)
            self.connection.send(command)

        def FNL(self, AxisIDs: tuple = None):
            # Fast Reference Move To Negative Limit (p. 145)
            # Moves stage to negative limit and sets absolute position
            command = 'FNL'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        def FPL(self, AxisIDs: tuple = None):
            # Fast Reference Move To Positive Limit (p. 146)
            # Moves stage to positive limit and sets absolute position
            command = 'FPL'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        def FRF(self, AxisIDs: tuple = None):
            # Fast Reference Move To Reference Switch (p. 147)
            # Moves stage to center reference position and sets absolute position
            command = 'FRF'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        def FRF_query(self, AxisIDs: tuple = None):
            # Get Referencing Result (p. 148)
            command = 'FRF?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.transaction(command)

        def GOH(self, AxisIDs: tuple = None):
            # Go To Home Position (p. 149)
            command = 'GOH'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        # def HAR? [{<AxisID>}] Indicate Hard Stops (p. 149)

        # def HDR? Get All Data Recorder Options (p. 150)

        # def HDT {<HIDeviceID> <HIDeviceAxis> <HIDTableID>} Set HID Default Lookup Table (p. 151)

        # def HDT? [{<HIDeviceID> <HIDeviceAxis>}] Get HID Default Lookup Table (p. 152)

        # def HIA {<AxisID> <MotionParam> <HIDeviceID> <HIDeviceAxis>}

        # def Configure Control Done By HID Axis (p. 153)

        # def HIA? [{<AxisID> <MotionParam>}] Get Configuration Of Control Done By HID Axis (p.154)

        # def HIB? [{<HIDeviceID> <HIDeviceButton>}] Get State Of HID Button (p. 154)

        # def HIE? [{<HIDeviceID> <HIDeviceAxis>}] Get Deflection Of HID Axis (p. 155)

        # def HIN {<AxisID> <HIDControlState>} Set Activation State For HID Control (p. 156)

        # def HIN? [{<AxisID>}] Get Activation State Of HID Control (p. 157)

        # def HIS? [{<HIDeviceID> <HIDItemID> <HIDPropID>}] Get Configuration Of HI Device (p. 157)

        # def HIT {<HIDTableID> <HIDTableAddr> <HIDTableValue>} Fill HID Lookup Table (p. 160)

        # def HIT? [<StartPoint> [<NumberOfPoints> [{<HIDTableID>}]]] Get HID Lookup Table Values (p. 161)

        def HLP_query(self,):
            # Get List of Available Commands (p. 163)
            self.connection.send('HLP?')
            reply = b''
            time.sleep(0.05)  # Wait for response
            while self.connection.connection.in_waiting != 0:  # serial buffer not empty
                reply += self.connection.read_all()
            print('<> arguments \n' +
                  '[] optional arguments \n' +
                  '{} repeated arguments \n' +
                  reply
                  )

        def HLT(self, AxisIDs: tuple = None):
            # Halt Motion Smoothly (p. 164)
            command = 'HLT'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            self.connection.send(command)

        # def HPA? Get List Of Available Parameters (p. 164)

        def IFS(self, InterfacePams: tuple, PamValues: tuple, Pswd='100'):
            # Set Interface Parameters As Default Values (p. 166)
            command = 'IFS' + ' ' + Pswd
            for InterfacePam, PamValue in zip(InterfacePams, PamValues):
                    command += ' ' + str(InterfacePam) + ' ' + str(PamValue)
            self.connection.send(command)

        def IFS_query(self, InterfacePams: tuple = None):
            # Get Interface Parameters As Default Values (p. 167)
            command = 'IFS?'
            if InterfacePams is not None:
                for InterfacePam in InterfacePams:
                    command += ' ' + str(InterfacePam)
            print(command)
            self.connection.transaction(command)

        # def JRC <Jump> <CMD?> <OP> <Value> Jump Relatively Depending On Condition (p. 168)

        # def LIM? [{<AxisID>}] Indicate Limit Switches (p. 169)

        # def MAC <keyword> {<parameter>}

        # def BEG <macro>

        # def DEF <macro>

        # def DEF?

        # def DEL <macro>

        # def END

        def ERR_query(self,):
            return self.connection.transaction('ERR?')

        # def NSTART <macro> <uint> [<String1> [<String2>]]

        # def START <macro> [<String1> [<String2>]] Call Macro Function (p. 169)

        # def MAC? [<macroname>] List Macros (p. 172)

        def MAN_query(self, CMD: str):
            # Get Help String For Command (p. 173)
            print(self.connection.transaction('MAN?' + ' ' + CMD))

        # def MEX <CMD?> <OP> <Value> Stop Macro Execution Due To Condition (p. 174)

        def MOV(self, AxisIDs: tuple, Positions: tuple):
            # Set Target Position (p. 175)
            command = 'MOV'
            for axisID, Position in zip(AxisIDs, Positions):
                    command += ' ' + str(axisID) + ' ' + str(Position)
            self.connection.send(command)

        def MOV_query(self, AxisIDs: tuple = None):
            # Get Target Position (p. 176)
            command = 'MOV?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def MVR(self, AxisIDs: tuple, Distances: tuple):
            # Set Target Relative To Current Position (p. 177)
            command = 'MVR'
            for axisID, Distance in zip(AxisIDs, Distances):
                    command += ' ' + str(axisID) + ' ' + str(Distance)
            self.connection.send(command)

        def OMA(self, AxisIDs: tuple, Positions: tuple):
            # Set Open-Loop Target Position (p. 178)
            command = 'OMA'
            for axisID, Position in zip(AxisIDs, Positions):
                    command += ' ' + str(axisID) + ' ' + str(Position)
            self.connection.send(command)

        def OMA_query(self, AxisIDs: tuple = None):
            # Get Open-Loop Target Position (p. 179)
            command = 'OMA?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def OMR(self, AxisIDs: tuple, Distances: tuple):
            # Set Open-Loop Target Relative To Current Position (p.179)
            command = 'OMR'
            for axisID, Distance in zip(AxisIDs, Distances):
                    command += ' ' + str(axisID) + ' ' + str(Distance)
            self.connection.send(command)

        def ONT_query(self, AxisIDs: tuple = None):
            # Get On-Target State (p. 180)
            command = 'ONT?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def OSM(self, AxisIDs: tuple, Values: tuple):
            # Open-Loop Step Moving (p. 181)
            command = 'OSM'
            for axisID, Value in zip(AxisIDs, Values):
                    command += ' ' + str(axisID) + ' ' + str(Value)
            self.connection.send(command)

        def OSN_query(self, AxisIDs: tuple = None):
            # Read Left Steps (p. 181)
            command = 'OSN?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def POS(self, AxisIDs: tuple, Positions: tuple):
            # Set Real Position (p. 182)
            # Sets the current position of the axis (does not cause motion).
            # An axis is considered to be "referenced" when the position
            # has been set with POS (for more information, see
            # "Referencing" (p. 34)).
            command = 'OSM'
            for axisID, Position in zip(AxisIDs, Positions):
                    command += ' ' + str(axisID) + ' ' + str(Position)
            self.connection.send(command)

        def POS_query(self, AxisIDs: tuple = None):
            # Get Real Position (p. 182)
            command = 'POS?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def RBT(self):
            # Reboot System (p. 183)
            self.connection.send('RBT')

        # def RMC? List Running Macros (p. 183)

        def RON(self, AxisIDs: tuple, ReferenceOn_selections: tuple):
            # Set Reference Mode (p. 184)
            command = 'RON'
            for axisID, ReferenceOn in zip(AxisIDs, ReferenceOn_selections):
                    command += ' ' + str(axisID) + ' ' + str(ReferenceOn)
            self.connection.send(command)

        def RON_query(self, AxisIDs: tuple = None):
            # Get Reference Mode (p. 184)
            command = 'RON?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def RPA(self, ItemIDs: tuple = None, PamIDs: tuple = None):
            # Reset Volatile Memory Parameters (p. 185)
            # ItemIDs and PamIDs must have equal lengths
            command = 'RPA'
            if ItemIDs is not None:
                for ItemID, PamID in zip(ItemIDs, PamIDs):
                    command += ' ' + str(ItemID) + ' ' + str(ItemID)
            return self.connection.send(command)

        # def RTR <RecordTableRate> Set Record Table Rate (p. 186)

        # def RTR? Get Record Table Rate (p. 186)

        def SAI(self, AxisIDs: tuple, NewIdentifiers: tuple):
            # Set Current Axis Identifiers (p. 187)
            command = 'SAI'
            for AxisID, NewIdentifier in zip(AxisIDs, NewIdentifiers):
                command += ' ' + str(AxisID) + ' ' + str(NewIdentifier)
            self.connection.send(command)

        def SAI_query(self,):
            # Get List Of Current Axis Identifiers (p. 187)
            self.connection.transaction('SAI? ALL')

        # def SEP <Pswd> {<ItemID> <PamID> <PamValue>} Set Nonvolatile Memory Parameters (p. 188)

        # def SEP? [{<ItemID> <PamID>}] Get Nonvolatile Memory Parameters (p. 189)

        # def SPA {<ItemID> <PamID> <PamValue>} Set Volatile Memory Parameters (p. 190)

        # def SPA? [{<ItemID> <PamID>}] Get Volatile Memory Parameters (p. 191)

        # def SRG? {<AxisID> <RegisterID>} Query Status Register Value (p. 192)

        # def STE <AxisID> <Amplitude> Start Step And Response Measurement (p. 193)

        def STP(self,):
            # Stop All Axes (p. 194)
            self.connection.send('STP')

        def SVO(self, AxisIDs: tuple, ServoStates: tuple):
            # Set Servo Mode (p. 195)
            command = 'SVO'
            for AxisID, ServoState in zip(AxisIDs, ServoStates):
                command += ' ' + str(AxisID) + ' ' + str(ServoState)
            self.connection.send(command)

        def SVO_query(self, AxisIDs: tuple = None):
            # Get Servo Mode (p. 196)
            return self.connection.transaction('SVO?')

        # def TIO? Tell Number Of Digital I/O Lines (p. 196)

        def TMN_query(self, AxisIDs: tuple = None):
            # Get Minimum Commandable Position (p. 197)
            command = 'TMN?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        def TMX_query(self, AxisIDs: tuple = None):
            # Get Maximum Commandable Position (p. 197)
            command = 'TMX?'
            if AxisIDs is not None:
                for axisID in AxisIDs:
                    command += ' ' + str(axisID)
            return self.connection.transaction(command)

        # def TNR? Get Number Of Record Tables (p. 198)

        # def TRO {<TrigOutID> <TrigMode>} Set Trigger Output State (p. 198)

        # def TRO? [{<TrigOutID>}] Get Trigger Output State (p. 198)

        # def TRS? [{<AxisID>}] Indicate Reference Switch (p. 199)

        # def TVI? Tell Valid Character Set For Axis Identifiers (p. 200)

        # def VAR <Variable> <String> Set Variable Value (p. 200)

        # def VAR? [{<Variable>}] Get Variable Value (p. 201)

        # def VER? Get Versions Of Firmware And Drivers (p. 202)

        # def WAC <CMD?> <OP> <Value> Wait For Condition (p. 202)

        # def WPA <Pswd> [{<ItemID> <PamID>}] Save Parameters To Non-Volatile Memory (p. 203)

    # --- Base class commands --- #

    def initialize(self,):
        # Run the iControl default initilization routine
        raise NotImplementedError

    def get_instrument_id(self,):
        # Get the equivalent of *IDN?
        print('Connected to {:s}'.format(
            self.nat_cmds.IDN_query()))

    def reboot(self,):
        # Effectively like power-cycling the device
        raise NotImplementedError

    def load_defaults(self,):
        # Load/Restore manufacturer default parameters
        raise NotImplementedError

    def query_error_code(self):
        # Return error string
        return int(self.nat_cmds.ERR_query())

    def find_home_position(self, AxisIDs: tuple = None):
        # Locate and set the default home position
        print('Finding home')
        self.nat_cmds.FRF(AxisIDs)
        time.sleep(0.1)  # Delay for motion status update
        motion_status = self.query_motion_status()
        while int(motion_status) != 0 and motion_status != b'':
            print('...moving\r', end='')
            motion_status = self.query_motion_status()
        print('Motion complete')

    def set_home_position(self, axis=1, position=0):
        # Set the current location as the home position
        self.nat_cmds.POS(AxisIDs=(axis,), Positions=(position,))
        return int(self.nat_cmds.POS_query(AxisIDs=(axis,)))

    def query_home_position(self, axis=1):
        # Return the current home position
        return int(self.nat_cmds.POS_query(AxisIDs=(axis,)))

    def find_travel_limits(self, axis,):
        # Locate or return the travel limits
        raise NotImplementedError

    def set_travel_limits(self, axis,):
        # Set the (soft) travel limits
        raise NotImplementedError

    def query_travel_limits(self, axis,):
        # Return the current travel limits
        raise NotImplementedError

    def query_current_position(self, axis=1):
        # Return the current position
        return int(self.nat_cmds.POS_query(axisIDs=(axis,)))

    def query_target_position(self, axis=1):
        # Return the target position
        return int(self.nat_cmds.MOV_query(AxisIDs=(axis,)))

    def move_absolute(self, position: float, axis: int = 1):
        # Move to an absolute location
        print('Finding target position: {:f} um'.format(position))
        self.nat_cmds.MOV(AxisIDs=(axis,), Positions=(position,))
        motion_status = self.query_motion_status()
        while int(motion_status) != 0 and motion_status != b'':
            print('...moving\r', end='')
            motion_status = self.query_motion_status()
        print('Motion complete')
        new_position =\
            float(
                re.search(
                    r'\d=(-*\d\.\d+)\n',
                    self.nat_cmds.MOV_query(AxisIDs=(axis,))
                ).group(1)
            )
        return new_position

    def move_relative(self, distance: float, axis: int = 1):
        # Move relative to current position
        print('Moving by {:f} um'.format(distance))
        self.nat_cmds.MVR(AxisIDs=(axis,), Distances=(distance,))
        motion_status = self.query_motion_status()
        while int(motion_status) != 0 and motion_status != b'':
            print('...moving\r', end='')
            motion_status = self.query_motion_status()
        print('Motion complete')
        new_position =\
            float(
                re.search(
                    r'\d=(-*\d\.\d+)\n',
                    self.nat_cmds.MOV_query(AxisIDs=(axis,))
                ).group(1)
            )
        return new_position

    def query_motion_status(self,):
        # Determine if stage is moving
        return self.nat_cmds.num5()

    def stop_motion(self, axis=1):
        # Stop all motion
        self.nat_cmds.HLT(AxisIDs=(axis,))

    # --- Child Class Specific Commands --- #

    def initilize_Q521_14U(self,):
        # Consider initializing for specific stage
        pass


class APTController:
    def __init__(self, path_to_dll="C:\\Program Files (x86)\\Thorlabs\\APT\\APT Server\\"):
        self.path_to_dll = path_to_dll
        self.name = "APT.dll"
        self.hardware_type = c_long(31)  # 31 means
        self.aptdll = cdll.LoadLibrary(self.path_to_dll + self.name)
        self.aptdll.APTInit()
        self.hardware_serial_number = self.get_serial_number()
        self._serial_number = c_long(self.hardware_serial_number)  # formatted for passing to DLL
        if self.hardware_serial_number == 0:
            print('Check USB connection to controller')
        elif self.hardware_serial_number is not None:
            self.initialize_hardware_device()
            print('APT Controller %s initialized' % (self.hardware_serial_number))
        else:
            print('Cannot find active controller')

    def get_serial_number(self):
        HWSerialNum = c_long()
        hardware_index = c_long()
        self.aptdll.GetHWSerialNumEx(self.hardware_type, hardware_index, pointer(HWSerialNum))
        return HWSerialNum.value

    def initialize_hardware_device(self):
        self.aptdll.InitHWDevice(self._serial_number)
        return True

    def get_hardware_limit_switches(self):
        reverseLimitSwitch = c_long()
        forwardLimitSwitch = c_long()
        self.aptdll.MOT_GetHWLimSwitches(self._serial_number, pointer(reverseLimitSwitch), pointer(forwardLimitSwitch))
        hardwareLimitSwitches = [reverseLimitSwitch.value, forwardLimitSwitch.value]
        return hardwareLimitSwitches

    def get_stage_axis_info(self):
        minimum_position = c_float()
        maximum_position = c_float()
        units = c_long()
        pitch = c_float()
        self.aptdll.MOT_GetStageAxisInfo(self._serial_number, pointer(minimum_position), pointer(maximum_position), pointer(units), pointer(pitch))
        stage_axis_info = [minimum_position.value, maximum_position.value, units.value, pitch.value]
        return stage_axis_info

    def set_stage_axis_info(self, minimum_position=0, maximum_position=25, units=1, pitch=0.5):
        minimum_position = c_float(minimum_position)
        maximum_position = c_float(maximum_position)
        units = c_long(units)  # units of [mm]
        pitch = c_float(pitch)  # for Z725B screw pitch = 0.5 mm (see https://www.thorlabs.com/drawings/51127b32d9ea09a8-1609D25A-F3B4-46AB-39BF35368E80A608/Z725B-Manual.pdf)
        self.aptdll.MOT_SetStageAxisInfo(self._serial_number, minimum_position, maximum_position, units, pitch)
        return True

    def get_position(self):
        position = c_float()
        self.aptdll.MOT_GetPosition(self._serial_number, pointer(position))
        return position.value

    def move_to_target_position(self, absPosition):
        absolutePosition = c_float(absPosition)
        self.aptdll.MOT_MoveAbsoluteEx(self._serial_number, absolutePosition, True)
        return True

    def find_home_position(self):
        self.aptdll.MOT_MoveHome(self._serial_number)
        return True

    def run_calibration_sequence(self):
        self.find_home_position()


class KinesisController:
    def __init__(self, serialNumber=None, HomeStage=False, stageName=None, stageType='linear', path_kinesis_install=r"C:\Program Files\Thorlabs\Kinesis"):

        os.chdir(path_kinesis_install)
        self.name = "Thorlabs.MotionControl.KCube.DCServo.dll"
        self.stageName = stageName
        self.lib = cdll.LoadLibrary(self.name)

        # Build device list
        self.lib.TLI_BuildDeviceList()

        self.serialNumber = serialNumber
        self.stepsPerRev = 512
        self.gearBoxRatio = 67
        if stageType == 'linear':
            self.pitch = 1
        elif stageType == 'rotational':
            self.pitch = 17.87
        else:
            print('Stage type undefined')

        self.moveTimeout = 60.0

        # Setting up stage
        print(f"Initializing {self.stageName}")
        self.initialize_device()

        # Adjusting stage parameters
        print(f"Adjusting {self.stageName} settings")
        self.set_up_device()

        # Homing stages
        if HomeStage == True:
            print(print(f"Homing {self.stageName}"))
            self.home_device()


    def initialize_device(self):
        # set up device
        self.lib.CC_Open(self.serialNumber)
        self.lib.CC_StartPolling(self.serialNumber, c_int(200))
        # might need to enable the channel:
        # lib.CC_EnableChannel(serialNumber)

        time.sleep(3)
        self.lib.CC_ClearMessageQueue(self.serialNumber)


    def clean_up_device(self):
        # clean up and exit
        self.lib.CC_ClearMessageQueue(self.serialNumber)
        # print(lib.CC_GetPosition())
        self.lib.CC_StopPolling(self.serialNumber)
        self.lib.CC_Close(self.serialNumber)


    def home_device(self):
        homeStartTime = time.time()
        self.lib.CC_Home(self.serialNumber)

        self.messageType = c_ushort()
        self.messageID = c_ushort()
        self.messageData = c_ulong()

        homed = False
        while (homed == False):
            self.lib.CC_GetNextMessage(self.serialNumber, byref(self.messageType), byref(self.messageID), byref(self.messageData))
            if ((self.messageID.value == 0 and self.messageType.value == 2) or (time.time() - homeStartTime) > self.moveTimeout):
                homed = True
        self.lib.CC_ClearMessageQueue(self.serialNumber)


    def set_up_device(self):
        # Set up to convert physical units to units on the device
        self.lib.CC_SetMotorParamsExt(self.serialNumber, c_double(self.stepsPerRev), c_double(self.gearBoxRatio), c_double(self.pitch))

        deviceUnit = c_int()
        self.deviceUnit = deviceUnit


    def move_device(self, position):
        deviceUnit = c_int()

        realUnit = c_double(position)

        self.lib.CC_GetDeviceUnitFromRealValue(self.serialNumber, realUnit, byref(deviceUnit), 0)

        moveStartTime = time.time()
        self.lib.CC_MoveToPosition(self.serialNumber, deviceUnit)

        moved = False
        messageType = c_ushort()
        messageID = c_ushort()
        messageData = c_ulong()
        while (moved == False):
            self.lib.CC_GetNextMessage(self.serialNumber, byref(messageType), byref(messageID), byref(messageData))

            if ((messageID.value == 1 and messageType.value == 2) or (time.time() - moveStartTime) > self.moveTimeout):
                moved = True

    def set_rel_efield(self, rel_efield):
        angle = np.arccos(np.sqrt(rel_efield)) * 180 / math.pi
        self.move_device(position=angle)


    def rotate_stage(self, angle):
        self.move_device(position=angle)