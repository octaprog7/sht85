# micropython
# mail: goctaprog@gmail.com
# MIT license


# Please read this before use!:
from machine import I2C, Pin
import sht85sen
from sensor_pack.bus_service import I2cAdapter
import time

if __name__ == '__main__':
    # пожалуйста установите выводы scl и sda в конструкторе для вашей платы, иначе ничего не заработает!
    # please set scl and sda pins for your board, otherwise nothing will work!
    # https://docs.micropython.org/en/latest/library/machine.I2C.html#machine-i2c
    # i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=400_000) № для примера
    # bus =  I2C(scl=Pin(4), sda=Pin(5), freq=100000)   # на esp8266    !
    i2c = I2C(id=0, scl=Pin(13), sda=Pin(12), freq=400000)  # on Arduino Nano RP2040 Connect tested
    adaptor = I2cAdapter(i2c)
    # ps - humidity sensor
    hum_sen = sht85sen.Sht85(adaptor, 0x44, True)

    # если у вас посыпались исключения, чего у меня на макетной плате с али и проводами МГТФ не наблюдается,
    # то проверьте все соединения.
    hs_id = hum_sen.get_id()
    print(f"Sensor ID: {hex(hs_id)}")
    print(f"Status register:", hex(hum_sen.get_status()))
    hum_sen.start_single_meas(repeatability=0)
    delay = hum_sen.get_conversion_cycle_time()
    time.sleep_us(delay)    # не забывай вызывать ожидание результата, или что-то делай и измеряй время!
    t, h = hum_sen.read_temp_hum_pair()
    print(f"Temperature: {t}\thumidity: {h}\tdelay: {delay}")
    print("Switch to periodic acquisition mode and use iterator + delay")
    hum_sen.set_periodic_acquisition_mode(repeatability=0, meas_per_sec=2)
    delay = hum_sen.get_conversion_cycle_time()
    time.sleep_us(delay)
    #
    for temp, hum in hum_sen:
        print(f"Temperature: {temp}\thumidity: {hum}\tdelay: {delay}")
        delay = hum_sen.get_conversion_cycle_time()
        time.sleep_us(delay)
    