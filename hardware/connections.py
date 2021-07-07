'''
Helper methods for connecting to instruments over various
communication protocols.

Note: Seems better to let the user encode/decode to utf-8, incase
    data sent/retured to the instument should be in bytes.
'''
from __future__ import print_function 
import serial
import serial.tools.list_ports 
import chardet
import time
import vxi11
import visa
import socket


def select_connection(connection_type: str, **connection_kwargs):
        """Select and instantiate the requisite Connection class.

        Parameters
        ----------
        connection_type : str
            Communication protocol e.g. 'serial', 'ethernet'.
        **connection_kwargs
            Keyword arguments passed to the __init__ of the requiste

        Returns
        -------
        Connection instance
            A connection to an instrument via the connection protocol
            specified by connection_type. An instance of one of the
            ___Connection classes in this module.

        """
        # Switch-case dict for selecting the proper connection
        connection_class = {
            'test': TestClass,
            'serial': SerialConnection,
            'ethernet': EthernetConnection
        }
        return connection_class[connection_type](**connection_kwargs)


class TestClass:
    def __init__(self, **connection_kwargs):
        if 'test_var' in connection_kwargs:
            self.test_var = connection_kwargs['test_var']

    def test_method(self):
        print(self.test_var)


class SerialConnection():
    """A serial connection to an instrument.

    Shares the common send/read/write methods of all connections
    classes.

    Attributes
    ----------
    connected : bool
        Status of connection
    connection : Serial instance
        Connection to the instrument.
    get_instrument_id : bool, optional, default: False
        Query the instrument ID; equivalent of *IDN?
    IDN : str
        Instrument identity.
    terminating_char : str
        string that indicates the end of a command/command-sequence.

    """

    def __init__(
        self,
        get_instrument_id=False,
        terminating_char='\n',
        **serial_kwargs
    ):
        """SerialConnection constructor.

        Parameters
        ----------
        get_instrument_id : bool, optional, default: False
            Select whether the instrument ID is read.
        terminating_char : str, optional, default: '\n'
            Indicates the end of a command/command-sequence.
        **serial_kwargs
            pySerial keyword arguments

        """
        self.get_instrument_id = get_instrument_id
        self.terminating_char = terminating_char
        self.IDN = ''
        self.open_connection(**serial_kwargs)

    def open_connection(self, **serial_kwargs):
        """Open a pySerial connection.

        Parameters
        ----------
        **serial_kwargs
            pySerial keyword arguments

        """
        try:
            self.connection = serial.Serial(**serial_kwargs)
            self.connected = True
        except ValueError:
            print('ValueError in SerialConnection.open_connection:\n')
            print('Parameter(s) are out of range, e.g. baud rate, data bits.')
        except serial.SerialException:
            print('SerialException in SerialConnection.open_connection:\n')
            print('Device can not be found or can not be configured.')
        else:
            if self.get_instrument_id and self.connected:
                self.connection.write('*IDN?\n'.encode())
                time.sleep(0.1)
                self.IDN = self.connection.read_all().decode()
                if self.IDN != '':
                    print('Connected to: %s' % self.IDN)
                else:
                    print('Cannot read instrument IDN')

    def close_connection(self):
        """Close serial connection."""
        self.connection.close()
        self.connected = False
        print("%s disconnected" % self.IDN)

    def send(self, command, raw_bytes=False):
        """Send command via serial."""
        if raw_bytes is True:
            self.connection.write(command)
        else:  # Use utf-8 encoding and add terminating char
            self.connection.write(
                (command + self.terminating_char).encode())

    def read_until(self, raw_bytes=False):
        """Read until terminating_char is found."""
        if raw_bytes is True:
            return self.connection.read_until(
                expected=self.terminating_char)
        else:  # Decode as utf-8
            return self.connection.read_until(
                expected=self.terminating_char).decode()

    def read_all(self, raw_bytes=False):
        """Read until buffer is empty."""
        if raw_bytes is True:
            return self.connection.read_all()
        else:  # Decode as utf-8
            return self.connection.read_all().decode()

    def transaction(self, command, delay=0.05, raw_bytes=False):
        """Send a command and read response until buffer is empty."""
        if raw_bytes is True:
            self.send(command, raw_bytes=True)
            time.sleep(delay)  # Wait for response
            return self.read_all(raw_bytes=True)
        else:  # Encode/decode communication in utf-8
            self.send(command, raw_bytes=False)
            time.sleep(delay)  # Wait for response
            return self.read_all(raw_bytes=False)


class VISAConnection:
    """VISA connection over ethernet."""

    def __init__(self, resource_name):
        self.resource_name = resource_name
        self.resource_manager = visa.ResourceManager()
        self.connection = self.resource_manager.open_resource(self.resource_name)
        try:
            self.connection.write('*IDN?')
            print('Connected to: %s' % self.connection.read_raw().decode())
        except:
            print('Cannot connect to instrument')

    def send(self, command, raw_bytes=False):
        self.connection.write(command)

    def read_until(self, raw_bytes=False):
        raise NotImplementedError

    def read_all(self, raw_bytes=False):
        raise NotImplementedError

    def transaction(self, command, raw_bytes=False):
        self.send(command)
        return self.connection.read_raw().decode().rstrip()


class EthernetConnection:
    def __init__(
        self,
        ip_addr='10.4.101.23',
        port=23,
        timeout=3,
        buffersize=1024,
        terminating_char='\n'
    ):
        self.buffersize = buffersize
        self.terminating_char = terminating_char
        self.ip_addr = ip_addr
        self.port = port
        self.timeout = timeout
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.settimeout(self.timeout)
        self.connection.connect((self.ip_addr, self.port))
        self.connection.recv(self.buffersize)
        self.get_instrument_id()

    def send(self, command, raw_bytes=False):
        raise NotImplementedError

    def read_until(self, raw_bytes=False):
        raise NotImplementedError

    def read_all(self, raw_bytes=False):
        raise NotImplementedError

    def transaction(self, command, raw_bytes=False):
        raise NotImplementedError


class GPIBConnection:
    def __init__(
        self,
        gpib_address,
        host_ip_address='10.4.101.21',
        get_instrument_id=False
    ):
        self.gpib_address = gpib_address
        self.host_ip_address = host_ip_address
        self.connection = vxi11.Instrument(host=host_ip_address, name='gpib0,%i' % (gpib_address))
        self.get_instrument_id = get_instrument_id

        if self.get_instrument_id:
            try:
                self.connection.write('*IDN?')
                print('Connected to: %s' % self.connection.read_raw().decode())
            except:
                print('Cannot connect to instrument')

    def send(self, command):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        self.connection.write(command)

    def read_until(self, raw_bytes=False):
        raise NotImplementedError

    def read_all(self, raw_bytes=False):
        raise NotImplementedError

    def read_raw(self):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        return self.connection.read_raw()

    def transaction(self, command):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        self.send(command)
        return self.connection.read_raw()


class GPIBtoSerialConnection:
    """Creates an generic interface to the Prologix GPIB-USB controller for talking to legacy instruments."""

    def __init__(
        self,
        instr_gpib_addr=1,
        terminating_char='\n',
        timeout=1,
        delay=0.1,
        get_instrument_id=False
    ):
        self.terminating_char = terminating_char
        self.delay = delay
        self.timeout = timeout
        self.instr_gpib_addr = instr_gpib_addr
        self.ports_list = list(serial.tools.list_ports.comports())[0]
        self.get_instrument_id = get_instrument_id
        # print(self.ports_list)
        for port in self.ports_list:
            # print(port)
            if "USB Serial Port" in port:
                port_bits = [int(x) for x in port if x.isdigit()]
                if len(port_bits) > 1:
                    self.port_num = '%i%i' % (port_bits[0], port_bits[1])
                else:
                    self.port_num = port_bits[0]
                self.com_port = 'COM%s' % self.port_num
                self.open_connection()

    def open_connection(self):
        self.connected = True
        self.connection = serial.Serial(self.com_port, timeout=self.timeout)
        # Reset the controller and set in controller mode
        self.send("++rst")  # process takes around 5 s 
        time.sleep(6)
        self.send('++mode 1')  # 
        self.send('++auto 1')  # Address the instrument to talk (0 to listen)
        self.send('++addr %i' % self.instr_gpib_addr)

        if self.get_instrument_id:
            try:
                self.idn = self.transaction('*IDN?') 
                encoding_dict = chardet.detect(self.idn)
                self.idn = self.idn.decode(encoding_dict['encoding'])  # Not sure if this encoding is general, check on other platforms using chardet (  i.e. chardet.detect(self.idn)  )
                print("%s connected at GPIB: %i" % (self.idn.split(',')[0] + ' ' + self.idn.split(',')[1], self.instr_gpib_addr))     
            except:
                print('Can\'t get instrument ID')

    def close_connection(self):
        self.connection.close()
        self.connected = False
        print("%s disconnected" % (self.idn.split(',')[0] + ' ' + self.idn.split(',')[1])) 

    def send(self, command):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        self.connection.flushInput()
        self.connection.flushOutput()
        message = command + self.terminating_char
        self.connection.write(message.encode())  # Use encode to cast from str to bytes object for Py3
        time.sleep(self.delay)

    def read_until(self):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        return self.connection.read_until(expected=self.terminating_char)

    def read_all(self):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        return self.connection.readlines()[0]

    def transaction(self, command):
        '''UPDATE TO CONFORM WITH THE STANDARD.'''
        self.send(command)
        return self.connection.readlines()