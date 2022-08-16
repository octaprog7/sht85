# micropython
# MIT License
# Copyright (c) 2022 Roman Shevchik   goctaprog@gmail.com

"""Sensirion SHT85 micropython module"""

import micropython
import ustruct
import array

from sensor_pack import bus_service
from sensor_pack.base_sensor import BaseSensor, Iterator


class Sht85(BaseSensor, Iterator):
    """Class for work with Sensirion SHT85 sensor"""

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x44):
        super().__init__(adapter, address)

    def get_id(self):
        pass

    def soft_reset(self):
        pass

    def __next__(self):
        raise NotImplementedError
