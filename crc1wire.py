"""реализация вычисление CRC
 8 бит
 полином 0x31 (x^8 + x^5 + x^4 + 1)
 начальное значение 0xFF
 отражение входа: нет
 отражение выхода: нет
 завершающий XOR: нет

 Примеры CRC-8:
    Входная последовательность: 0x01 0x02 0x03
    CRC-8: 0x87
    Входная последовательность: 0 1 2 3 4 5 6 7 8 9
    CRC-8: 0x52"""


def crc8(sequence, init_value: int, polynomial=0x31):
    mask = 0xFF
    crc = init_value & mask
    for item in sequence:
        crc = crc ^ (item & mask)
        for b in range(8):
            if crc & 0x80:
                crc = mask & ((crc << 1) ^ polynomial)
            else:
                crc = mask & (crc << 1)
    return crc