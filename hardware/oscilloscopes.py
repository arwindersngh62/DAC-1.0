import numpy as np
import struct
from . import connections
import importlib
import h5py
from datetime import datetime
importlib.reload(connections)


class Oscilloscopes(connections.VISAConnection):

    def __init__(self, instrument_ip_address):
        self.instrument_ip_address = instrument_ip_address
        self.resource_name = "TCPIP0::%s::INSTR" % self.instrument_ip_address
        super().__init__(self.resource_name)


class Tektronix_DPO4102B(Oscilloscopes):

    def __init__(self, instrument_ip_address='192.168.1.4'):
        super().__init__(instrument_ip_address)

    def set_byte_number(self, num_bytes=2, silent=True):
        cmd = 'WFMO:BYT_Nr %i' % num_bytes
        self.send(cmd)
        if not silent:
            self.query_byte_number()

    def query_byte_number(self):
        print(f"Number of bytes per data point: \
                {self.transaction('WFMO:BYT_Nr?')}")

    def set_data_encoding(self, encoding, silent=False):
        cmd = 'DATA:ENC %s' % encoding
        self.send(cmd)
        if not silent:
            self.query_data_encoding()

    def set_data_source(self, channel, silent=False):
        cmd = 'DAT:SOU CH%s' % channel
        self.send(cmd)
        if not silent:
            self.query_data_source()

    def set_data_start(self, start, silent=False):
        cmd = 'DAT:STAR %s' % start
        self.send(cmd)
        if not silent:
            self.query_data_start()

    def set_data_stop(self, stop, silent=False):
        if stop == -1:
            # Take full wave-form data
            stop = self.get_horizontal_record_length()
        cmd = 'DAT:STOP %s' % stop
        self.send(cmd)
        if not silent:
            self.query_data_stop()

    def set_verbose(self, status=1, silent=True):
        self.connection.write('VERBOSE %s' % status)
        if not silent:
            self.query_verbose()

    def set_header(self, status=1, silent=True):
        self.connection.write('HEAD %s' % status)
        if not silent:
            self.query_header()

    def set_acquisition_mode(self, mode, silent=True):
        """ Possible modes: SAM | PEAK | HIR | AVE | ENV """
        self.connection.write('ACQ:MOD %s' % mode)
        if not silent:
            self.query_acquisition_mode()

    def set_runstop(self, silent=True):
        self.connection.write('ACQ:STOPA RUNST')
        if not silent:
            self.query_stopafter()

    def set_acquire_sequence(self, silent=True):
        self.connection.write('ACQ:STOPA SEQ')
        if not silent:
            self.query_stopafter()

    def set_number_averages(self, averages=8, silent=True):
        self.connection.write('ACQ:NUMAV %i' % averages)
        if not silent:
            self.query_number_averages()

    def set_acquisition_state(self, state):
        """ Possible states: OFF | STOP | ON | RUN """
        self.connection.write('ACQ:STATE %s' % state)

    def query_stopafter(self):
        print(self.transaction('ACQ:STOPA?'))

    def query_number_averages(self):
        print(self.transaction('ACQ:NUMAV?'))

    def query_verbose(self):
        print(self.transaction('VERBOSE?'))

    def query_header(self):
        print(self.transaction('HEAD?'))

    def query_data_start(self):
        print(f"Tranfer data from point: {self.transaction('DAT:STAR?')}")

    def query_data_stop(self):
        print(f"Transfer data to point: {self.transaction('DAT:STOP?')}")

    def query_data_source(self):
        print(f"Data source: {self.transaction('DAT:SOU?')}")

    def query_data_encoding(self):
        print(f"Data encoding: {self.transaction('DATA:ENC?')}")

    def query_acquisition_mode(self):
        print(f"Acquisition mode: {self.transaction('ACQ:MOD?')}")

    def query_all_acquisition(self):
        return(self.transaction('ACQ?'))

    def query_busy(self, silent=False):
        reply = self.transaction('BUSY?')
        if not silent:
            if reply == 0:
                print('Yes')
            if reply == 1:
                print('No')
        return reply

    def get_horizontal_record_length(self):
        return int(self.transaction('HOR:RECO?'))

    def get_x_axis_unit(self):
        return self.transaction('WFMO:XUN?').strip('""')

    def get_x_axis_increment(self, silent=False):
        """ Returns the horizontal spacing of outgoing waveform """
        reply = float(self.transaction('WFMO:XINC?'))
        if not silent:
            print(f"X-axis increment: {reply} {self.get_x_axis_unit()}")
        return reply

    def get_x_axis_zero(self):
        return float(self.transaction('WFMO:XZE?'))

    def get_y_axis_multiplier(self):
        return float(self.transaction('WFMO:YMU?'))

    def get_y_axis_offset(self):
        return float(self.transaction('WFMO:YOF?'))

    def get_y_axis_zero(self):
        return float(self.transaction('WFMO:YZE?'))

    def get_y_axis_unit(self, silent=False):
        return self.transaction('WFMO:YUN?').strip('""')

    def get_data(self,
                 channel='2',
                 encoding='RPB',
                 start=1,
                 stop=-1,
                 silent=True,
                 num_bytes=1):
        """ Returns the correctly scaled x- and y-axis scope data
        (e.g. in units of [s] and [V]) over a specified range
        (defaults to full waveform) from specified channel
        (default to 1).
        WARNING! This method will currently not be robust to changes in
        the encoding due to byte ordering swaps. """
        self.set_header(status=0)  # Turn off the header
        # If encoding is set to 'binary', rather than 'ascii', take care of
        # additional header of the form '#head_length,data_length'.
        self.set_data_encoding(encoding, silent=silent)
        self.set_data_source(channel, silent=silent)
        self.set_data_start(start, silent=silent)
        self.set_data_stop(stop, silent=silent)
        self.set_byte_number(num_bytes, silent=True)
        self.send('CURVE?')
        self.raw_data = self.connection.read_raw()
        # Remove the additional header for Binary data - TODO! Implement check
        # for ASCII format
        if self.transaction('DAT:ENC?') == 'RPBINARY' or 'RPB':
            # This is because the second element of binary data is num bits of
            # data length, e.g. 3 for data of length 100 points
            bin_header_length = 2 + int(self.raw_data[1:2].decode('utf-8'))
            self.header = self.raw_data[:bin_header_length]
            self.raw_data_no_header = self.raw_data[bin_header_length:-1]
            # TODO! Implement how to read as 2 bytes per data point, i.e. total
            # of 32 bits for higher precision
            self.decoded_data = np.array(struct.unpack('%sB' % len(
                self.raw_data_no_header), self.raw_data_no_header), )
        else:
            raise NotImplemented
        y_offset = self.get_y_axis_offset()
        y_multiplier = self.get_y_axis_multiplier()
        y_zero = self.get_y_axis_zero()

        ydata_in_units = y_zero + \
            ((self.decoded_data - y_offset) * y_multiplier)

        x_increment = self.get_x_axis_increment(silent=silent)
        num_points = len(ydata_in_units)
        x_zero = self.get_x_axis_zero()
        time_base = x_zero + x_increment * np.arange(0,num_points)

        return time_base, ydata_in_units

    def create_h5_archive(self, data):
        """ TODO! FIX """
        self.filename = datetime.now().strftime('%Y_%m_%d_%H_%M_%S.h5')
        self.h5f = h5py.File(self.filename)
        # TODO! Add group of osc params to .h5 file
        self.h5f.ydata = self.h5f.create_dataset(
            'ydata',
            shape=(1, len(data)),
            dtype='f8',
            compression=9,
            maxshape=(None, len(data)))
        self.h5f.time_base = self.h5f.create_dataset(
            'time_base',
            shape=(1, len(data)),
            maxshape=(None, len(data)),
            dtype='f8',
            compression=9)

    def save_data_to_h5f(self, time_base, ydata, new_archive=False):
        """ TODO! FIX! Saves data to .h5 archive in working directory.
        Default to appending to existing archive file. """
        if new_archive:
            self.create_h5_archive(ydata)
        try:
            if not self.h5f:
                self.create_h5_archive(ydata)
        except AttributeError:
            self.create_h5_archive(ydata)
        self.h5f.ydata.resize(
            (self.h5f.ydata.shape[0] + 1, self.h5f.ydata.shape[1]))
        self.h5f.time_base.resize(
            (self.h5f.time_base.shape[0] + 1, self.h5f.time_base.shape[1]))
        self.h5f.ydata[-1, :] = ydata
        self.h5f.time_base[-1, :] = time_base


class Tektronix_MDO4104C(Tektronix_DPO4102B):

    def __init__(self, instrument_ip_address='192.168.1.5'):
        super().__init__(instrument_ip_address)


if __name__ == "__main__":
    osc = Tektronix_DPO4102B()
