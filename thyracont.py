# -*- coding: utf-8 -*-

import time
import numpy as np
from typing import Union


class MalformedPackageException(Exception):
    pass


class CommunicationException(Exception):
    """No answer or only malformed answers were received from the device."""
    pass


class ProtocolErrorMessage(Exception):
    """Error messages received from device."""
    pass


class ThyracontReader:
    """Reads pressure from Thyracont gauges via serial port.
    Uses communication protocol version 2.1 for Thyracont Smartline Devices."""

    def __init__(self, serial, timeout=1, address=1):
        self.serial = serial
        self.address = address
        if timeout is not None and serial != 'dummy':
            serial.timeout = timeout

    def clear(self):
        self.serial.write(b'\r')
        self.serial.write(b'\r')
        self.flush()
        time.sleep(0.5)
        self.serial.reset_input_buffer()

    def close(self):
        self.serial.close()

    @staticmethod
    def _calc_checksum(msg: str):
        """Calculate checksum;
        `msg` should contain ADR AC CMD LEN [DATA]"""
        s = sum(ord(ch) for ch in msg)
        return chr(s % 64 + 64)

    @staticmethod
    def _build_package(address:int, cmd:str, data:str='', access_code:int=0):
        msg = f'{address:03d}{access_code:d}{cmd}{len(data):02d}{data}'
        cs = ThyracontReader._calc_checksum(msg)
        pkg = (msg + cs + '\r').encode('ascii')
        return pkg

    @staticmethod
    def _parse_package(pkg:Union[bytes, bytearray]):
        assert pkg.endswith(b'\r')
        if len(pkg) < 10:
            raise MalformedPackageException("Package too short.")
        cs = chr(pkg[-2])
        msg = pkg[:-2].decode('ascii')
        if ThyracontReader._calc_checksum(msg) != cs:
            raise MalformedPackageException("Checksum failed.")
        l = int(msg[6:8])
        assert len(msg) == l + 8
        return {
            'ADR':  int(msg[0:3]),
            'AC':   int(msg[3:4]),
            'CMD':  msg[4:6],
            'DATA': msg[8:8+l]
        }
    
    def _send(self, pkg):
        assert pkg.endswith(b'\r')
        #print('>', pkg)
        self.serial.write(pkg)
        
    def _read(self):
        pkg = self.serial.read_until(b'\r')
        #print('<', pkg)
        if not pkg.endswith(b'\r'):
            raise TimeoutError
        return pkg
    
    def _communicate(self, cmd:str, data:str='', access_code:int=0, retries=3):
        pkg = ThyracontReader._build_package(self.address, cmd, data, access_code)
        for i in range(retries):
            self._send(pkg)
            try:
                pkg = self._read()
                ret = ThyracontReader._parse_package(pkg)
                if ret['ADR'] != self.address:
                    continue
                if ret['AC'] == 7:
                    raise ProtocolErrorMessage(ret['DATA'])
                if ret['AC'] != access_code + 1:
                    raise CommunicationException("Unexpected access code.")
                return ret
            except MalformedPackageException as e:
                raise e
        raise CommunicationException

    def read_measurement(self):
        """Pressure in mbar."""
        if self.serial == 'dummy':
            return np.random.uniform(1e-5, 1e3)

        ret = self._communicate('MV')
        if ret['DATA'] == 'OR' or ret['DATA'] == 'UR':
            return np.nan
        else:
            return float(ret['DATA'])
    
    def read_measurement_range(self):
        """Lower and upper limit in mbar."""
        data = self._communicate('MR')['DATA']
        print(data)
        # Return data is in format 'H[float]L[float]'
        assert data.startswith('H')
        low, high = data.split('L')
        return float(low), float(high)


if __name__ == '__main__':
    import serial
    ser = serial.Serial('COM4', 115200, timeout=2)
    sensor = ThyracontReader(ser)
    sensor.read_measurement()
    sensor.close()
