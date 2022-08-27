# micropython
# MIT license
# Copyright (c) 2022 Roman Shevchik   goctaprog@gmail.com

"""Sensirion SHT85 micropython module"""

import micropython

from sensor_pack import bus_service
from sensor_pack.base_sensor import BaseSensor, Iterator
import time


@micropython.native
def _check_value(value: int, valid_range, error_msg: str) -> int:
    if value not in valid_range:
        raise ValueError(error_msg)
    return value


class Sht85(BaseSensor, Iterator):
    """Class for work with Sensirion SHT85 sensor"""

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x44):
        super().__init__(adapter, address, False)
        self.mode = -1      # 0 - single shot acquisition mode; 1 - periodic acquisition mode

    def _read(self, n_bytes: int) -> bytes:
        return self.adapter.read(self.address, n_bytes)
    
    def _read_register(self, reg_addr, bytes_count=2) -> bytes:
        """считывает из регистра датчика значение.
        bytes_count - размер значения в байтах"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write(self, buf: bytes):
        return self.adapter.write(self.address, buf)

    def get_single_meas(self, repeatability: int) -> tuple:
        """In single shot mode different measurement commands can be selected.
        They differ with respect to repeatability (low, medium and high).
        repeatability       description
        0                   low
        1                   medium
        2                   high"""
        _check_value(repeatability, range(0, 3), f"Invalid value repeatability: {repeatability}")
        x = 0x16, 0x0B, 0x00
        t = 0x24, x[repeatability]
        b = bytearray(t)
        self._write(b)
        time.sleep_us(6000)     # !!! без задержки не работает. выбрасывает исключение!
        b = self._read_register(0x00, 6)
        raw_temp, raw_rel_hum = (b[0] << 8) | b[1], (b[3] << 8) | b[4]
        #
        self.mode = 0   # single shot mode
        #
        return 2.670328832E-3*raw_temp - 45, 1.52590219E-3*raw_rel_hum - 49

    def set_periodic_acquisition_mode(self, repeatability: int, meas_per_sec: int):
        _check_value(repeatability, range(0, 3), f"Invalid value repeatability: {repeatability}")
        _check_value(meas_per_sec, range(0, 5), f"Invalid value measurements per second: {meas_per_sec}")
        msb = 0x20, 0x21, 0x22, 0x23, 0x27
        lsb = (0x32, 0x24, 0x2F), (0x30, 0x26, 0x2D), (0x36, 0x20, 0x2B), (0x34, 0x22, 0x29), (0x37, 0x21, 0x2A)
        t = msb[meas_per_sec], lsb[meas_per_sec][repeatability]
        b = bytearray(t)
        self._write(b)
        self.mode = 1  # periodic acquisition mode

    def get_id(self) -> int:
        t = (0x36, 0x82)
        self._write(bytearray(t))
        time.sleep_us(500)
        b = self._read_register(0x00, 6)
        return b[0] << 24 | b[1] << 16 | b[3] << 8 | b[4]

    def soft_reset(self):
        """When the system is in idle state the soft reset command can be sent to the SHT85.
        This triggers the sensor to reset its system controller and reloads calibration data from the memory."""
        t = (0x30, 0xA2)
        self._write(bytearray(t))

    def heater(self, on: bool):
        """The SHT85 is equipped with an internal heater, which is meant for plausibility checking only.
        The temperature increase achieved by the heater depends on various parameters and lies in the range of a
        few degrees centigrade. It can be switched on and off.
        After a reset the heater is disabled (default condition)."""
        t = (0x30, 0x6D if on else 0x66)
        self._write(bytearray(t))

    def send_break(self):
        """The periodic data acquisition mode can be stopped using the break command.
        It is recommended to stop the periodic data acquisition prior to sending another command.
        Upon reception of the break command the sensor will abort the ongoing measurement and enter
        the single shot mode. This takes 1ms."""
        t = (0x30, 0x93)
        self._write(bytearray(t))

    def get_status(self) -> int:
        """The status register contains information on the operational status of the heater,
        the alert mode and on the execution status of the last command and the last write sequence."""
        t = (0xF3, 0x2D)
        self._write(bytearray(t))
        time.sleep_us(500)
        b = self._read_register(0x00, 3)
        return b[0] << 8 | b[1]

    def __next__(self):
        raise NotImplementedError
