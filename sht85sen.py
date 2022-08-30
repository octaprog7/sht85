# micropython
# MIT license
# Copyright (c) 2022 Roman Shevchik   goctaprog@gmail.com

"""Sensirion SHT85 micropython module"""

import micropython

from sensor_pack import bus_service, crc_mod
from sensor_pack.base_sensor import BaseSensor, Iterator, check_value
import time


class Sht85(BaseSensor, Iterator):
    """Class for work with Sensirion SHT85 sensor"""

    @staticmethod
    def _check_rep(repeatability) -> int:
        """
        repeatability       description
        0                   low
        1                   medium
        2                   high.

        Три режима повторяемости различаются продолжительностью измерения,
        уровнем шума и потреблением энергии."""
        return check_value(repeatability, range(0, 3), f"Invalid value repeatability: {repeatability}")

    def _send_cmd(self, iterable):
        self._write(bytearray(iterable))

    @micropython.native
    def get_conversion_cycle_time(self, min_value: bool = True) -> int:
        """Return conversion cycle time in [us].
        Pls see table 2.2 Timing Specifications.
        repeatability       description
        0                   low
        1                   medium
        2                   high.

        Три режима повторяемости различаются продолжительностью измерения,
        уровнем шума и потреблением энергии.

        Если min_value == Истина, то возвращает минимальное время, иначе максимальное в микросекундах !!!"""
        if 0 == self.mode:  # single shot mode
            r = Sht85._check_rep(self.repeatability)
            min_val = 2500, 4500, 12500
            max_val = 4500, 6500, 15500
            if min_value:
                return min_val[r]
            return max_val[r]

        if 1 == self.mode:  # periodic acquisition mode
            d = 2, 1, .5, .25, .1
            return int(1_000_000 * d[self.meas_per_sec])     # in us !!!

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x44, check_crc=True):
        super().__init__(adapter, address, False)
        self.mode = -1      # 0 - single shot acquisition mode; 1 - periodic acquisition mode
        self.repeatability = -1     # повторяемость
        self.meas_per_sec = -1      # кол-во измерений в секунду
        self.check_crc = check_crc       # проверка считанных значений

    @staticmethod
    def check_data(buf: bytes):
        """Проверка данных в последовательности на правильность, путем сравнения контрольной
        суммы из последовательности с вычисленной контрольной суммой"""
        if not len(buf) in (3, 6):
            raise ValueError("Invalid buffer length!")
        if 3 == len(buf):
            offsets = (0,)
        else:
            offsets = 0, 3
        for ofs in offsets:
            crc = crc_mod.crc8(buf[ofs:ofs + 2], 0x31, 0xFF)
            val = buf[ofs + 2]
            if crc != val:
                raise IOError(f"Input data broken! Bad CRC! Calculated crc8: {hex(crc)} != {hex(val)}")

    def _read_register(self, reg_addr, bytes_count=2) -> bytes:
        """считывает из регистра датчика значение.
        bytes_count - размер значения в байтах"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write(self, buf: bytes):
        return self.adapter.write(self.address, buf)

    def start_single_meas(self, repeatability: int):
        """In single shot mode different measurement commands can be selected.
        They differ with respect to repeatability (low, medium and high).
        repeatability       description
        0                   low
        1                   medium
        2                   high.

        Запускает однократное измерение. После вызова этого метода нужно подождать
        время, возвращаемое методом get_conversion_cycle_time и только потом считать результат"""
        Sht85._check_rep(repeatability)
        x = 0x16, 0x0B, 0x00
        t = 0x24, x[repeatability]
        self._send_cmd(t)
        self.repeatability = repeatability
        self.mode = 0  # single shot mode

    def read_temp_hum_pair(self) -> tuple:
        """Считывает из датчика пару сырых значений температура-относит. влажность и
        преобразует их в градусы Цельсия и проценты.
        Внимание! После запуска однократного измерения или запуска периодических измерений
        нужно ПОДОЖДАТЬ их результатов!!!
        Сколько ждать микросекунд(!) возвращает функция get_conversion_cycle_time !"""
        if 1 == self.mode:
            t = 0xE0, 0x00
            self._send_cmd(t)   # FETCH (Table 10: Fetch Data command)

        b = self._read_register(0x00, 6)
        if self.check_crc:
            Sht85.check_data(b)
        raw_temp, raw_rel_hum = (b[0] << 8) | b[1], (b[3] << 8) | b[4]
        #
        return 2.670328832E-3 * raw_temp - 45, 1.52590219E-3 * raw_rel_hum

    def set_periodic_acquisition_mode(self, repeatability: int, meas_per_sec: int):
        """Запускает процесс периодических измерений температуры и влажности датчиком.
        repeatability - повторяемость
        repeatability       Описание
        0                   low
        1                   medium
        2                   high.

        meas_per_sec - измерений в секунду
        meas_per_sec    измерений в секунду
        0               0.5
        1               1
        2               2
        3               4
        4               10
        """
        Sht85._check_rep(repeatability)
        check_value(meas_per_sec, range(0, 5), f"Invalid value measurements per second: {meas_per_sec}")
        msb = 0x20, 0x21, 0x22, 0x23, 0x27
        lsb = (0x32, 0x24, 0x2F), (0x30, 0x26, 0x2D), (0x36, 0x20, 0x2B), (0x34, 0x22, 0x29), (0x37, 0x21, 0x2A)
        t = msb[meas_per_sec], lsb[meas_per_sec][repeatability]
        self._send_cmd(t)
        self.repeatability = repeatability
        self.mode = 1  # periodic acquisition mode
        self.meas_per_sec = meas_per_sec

    def get_id(self) -> int:
        t = (0x36, 0x82)
        self._send_cmd(t)
        time.sleep_us(500)
        b = self._read_register(0x00, 6)
        if self.check_crc:
            Sht85.check_data(b)
        return b[0] << 24 | b[1] << 16 | b[3] << 8 | b[4]

    def soft_reset(self):
        """When the system is in idle state the soft reset command can be sent to the SHT85.
        This triggers the sensor to reset its system controller and reloads calibration data from the memory."""
        t = (0x30, 0xA2)
        self._send_cmd(t)

    def set_heater(self, on: bool):
        """The SHT85 is equipped with an internal heater, which is meant for plausibility checking only.
        The temperature increase achieved by the heater depends on various parameters and lies in the range of a
        few degrees centigrade. It can be switched on and off.
        After a reset the heater is disabled (default condition)."""
        t = (0x30, 0x6D if on else 0x66)
        self._send_cmd(t)

    def send_break(self):
        """The periodic data acquisition mode can be stopped using the break command.
        It is recommended to stop the periodic data acquisition prior to sending another command.
        Upon reception of the break command the sensor will abort the ongoing measurement and enter
        the single shot mode. This takes 1ms."""
        t = (0x30, 0x93)
        self._send_cmd(t)

    def get_status(self) -> int:
        """The status register contains information on the operational status of the heater,
        the alert mode and on the execution status of the last command and the last write sequence."""
        t = (0xF3, 0x2D)
        self._send_cmd(t)
        time.sleep_us(500)
        b = self._read_register(0x00, 3)
        if self.check_crc:
            Sht85.check_data(b)
        return b[0] << 8 | b[1]

    def __next__(self):
        if 1 == self.mode:  # periodic acquisition mode
            return self.read_temp_hum_pair()
