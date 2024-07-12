# 用于扩展板BCM IO映射至CPU IO
# 系统中默认开启一路i2c和一路pwm，如需要其他接口请按需配置/boot/config.txt
# 扩展板上数字IO 2~27
#        模拟IO A0~A7
#        I2C sda/scl 2/3
#        pwm 
#        spi 不启用

# Version: 1.0.1

import periphery
import time

pin_map = {

    2: 73,
    3: 74,
    4: 89,

    17: 83,
    27: 85,
    22: 84,

    10: 40,
    9: 39,
    11: 41,

    0: 71,
    5: 126,
    6: 125,
    13: 150,
    19: 121,
    26: 149,




    14: 81,
    15: 80,
    18: 120,

    23: 86,
    24: 87,

    25: 124,
    8: 42,
    7: 6,
    1: 72,

    12:146,

    16: 82,
    20: 123,
    21: 127,
}

class GPIO:
    def __new__(cls, pin, *args, **kargs):
        if pin == 2 or pin == 3:
            print('warning: please not use i2c pin')

        return periphery.GPIO(pin_map[pin], *args, **kargs)

class LED:
    def __init__(self, pin):
        self.GPIO = GPIO(pin, 'out')
    
    def on(self):
        self.GPIO.write(True)
    
    def off(self):
        self.GPIO.write(False)


class ADC:
    def __init__(self, pin):
        self.i2c = periphery.I2C("/dev/i2c-6")
        self.pin = pin

    def read(self):
        msgs = [periphery.I2C.Message([0x10+self.pin]), periphery.I2C.Message([0x00, 0x00], read=True)]
        self.i2c.transfer(0x24, msgs)
        return (msgs[1].data[1] << 8) + msgs[1].data[0]

class RC522:
    def __init__(self):
        # 参考代码：https://github.com/cpranzl/mfrc522_i2c/tree/main/examples
        from mfrc522_i2c import MFRC522
        i2cBus = 6
        i2cAddress = 0x28
        self.MFRC522Reader = MFRC522(i2cBus, i2cAddress)

    def scan(self):
        (status, backData, tagType) = self.MFRC522Reader.scan()
        if status == self.MFRC522Reader.MIFARE_OK:
            print(f'Card detected, Type: {tagType}')

            # Get UID of the card
            (status, uid, backBits) = self.MFRC522Reader.identify()
            if status == self.MFRC522Reader.MIFARE_OK:
                return (tagType, uid)
            else:
                return (tagType, None)
        
        return (None, None)

    def read (self, uid, blockAddr):
        # Select the scanned card
        (status, backData, backBits) = self.MFRC522Reader.select(uid)
        if status == self.MFRC522Reader.MIFARE_OK:
            # Authenticate
            (status, backData, backBits) = self.MFRC522Reader.authenticate(
                self.MFRC522Reader.MIFARE_AUTHKEY1,
                blockAddr,
                self.MFRC522Reader.MIFARE_KEY,
                uid)
            if (status == self.MFRC522Reader.MIFARE_OK):
                # Read data from card
                (status, backData, backBits) =self.MFRC522Reader.read(
                    blockAddr)
                if (status == self.MFRC522Reader.MIFARE_OK):
                    return backData
                else:
                    print("read: read error")
                    return None
                self.MFRC522Reader.deauthenticate()
            else:
                print("read: Authenticate error")
        else:
            print("read: card miss")

class RGB:
    def __init__(self):
        self.type='ws2812_rgb'
        self.lenth = 16
        self.frame_start = [0xDD, 0x55, 0xEE]
        self.frame_group_addr = [0x00, 0x00]
        self.frame_device_addr = [0x00, 0x01]
        self.frame_port = [0x00]
        self.frame_function = [0x99]
        self.frame_type = [0x01]  # ws2812_rgb
        self.frame_reserved = [0x00, 0x00]
        # user define：color data lenth
        # self.frame_data_lenth = [0x00, 0x03]
        self.frame_extend_times = [0x00, 0x01]
        # user define： color
        # self.frame_color_red = [0xFF, 0x00, 0x00]
        self.frame_end = [0xAA, 0xBB]

        self.uart = periphery.Serial("/dev/ttyS4", 115200)
        self.uart.flush()
        # wait uart ready
        time.sleep(0.1)

    def set(self, colors):
        ''' color: [(r, g, b), (r2, g2, b2), ...]
        '''
        frame_colors = []
        for index, color in enumerate(colors):
            # print(color)
            (r,g,b) = color
            frame_colors += [r, g, b]

        self.send_frame(frame_colors)

    def send_frame(self, colors):
        frame = []
        frame += self.frame_start
        frame += self.frame_group_addr
        frame += self.frame_device_addr
        frame += self.frame_port
        frame += self.frame_function
        frame += self.frame_type
        frame += self.frame_reserved
        frame += [len(colors)//0xff, len(colors)%0xff]
        frame += self.frame_extend_times
        frame += colors
        frame += self.frame_end
        self.uart.write(frame)
        self.uart.flush()

class Ultrasound:
    '''
    最大测距理论值小于343
    '''
    def __init__(self, trigger_pin=4, echo_pin=5, max_cm=None, timeout=1):
        #set GPIO Pins
        self.trigger = GPIO(trigger_pin, 'out')
        self.echo = GPIO(echo_pin, 'in')
        self.max_cm = max_cm
        self.timeout = timeout  # 超时时间（秒）

    def read(self):
        # set Trigger to HIGH
        # GPIO.output(GPIO_TRIGGER, True)
        self.trigger.write(True)
    
        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        # GPIO.output(GPIO_TRIGGER, False)
        self.trigger.write(False)
    
        StartTime = time.time()
        StopTime = time.time()
    
        # save StartTime
        start_time = time.time()  # 记录开始时间
        while self.echo.read() == 0:
            StartTime = time.time()
            if time.time() - start_time > self.timeout:  # 检查是否超时
                return 0
        # save time of arrival
        while self.echo.read() == 1:
            StopTime = time.time()
            if self.max_cm is not None:
                if StopTime - StartTime > self.max_cm * 2 / 34300:
                    return self.max_cm
            if time.time() - start_time > self.timeout:  # 检查是否超时
                return 0

        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2
    
        return distance

class SoundSensor:
    def __init__(self, analog_pin=0, digital_pin=22):

        self.gpio = GPIO(digital_pin, 'in') 
        self.adc = ADC(analog_pin)
    
    def read(self):
        signal = self.gpio.read()
        value = self.adc.read()

        return (not signal, value)

class PhotosensitiveSensor:
    def __init__(self, analog_pin=4):
        self.adc = ADC(analog_pin)
    
    def read(self):
        return self.adc.read()

class SoilMoistureSensor:
    def __init__(self, analog_pin=5):
        self.adc = ADC(analog_pin)
    
    def read(self):
        return self.adc.read()

class WaterDepthSensor:
    def __init__(self, analog_pin=7):
        self.adc = ADC(analog_pin)
    
    def read(self):
        return self.adc.read()

class FlameSensor:
    def __init__(self, analog_pin=2, digital_pin=24):

        self.gpio = GPIO(digital_pin, 'in') 
        self.adc = ADC(analog_pin)
    
    def read(self):
        signal = self.gpio.read()
        value = self.adc.read()

        return (not signal, value)

class RotaryPotentionmeter:
    def __init__(self, analog_pin=6):
        self.adc = ADC(analog_pin)
    
    def read(self):
        return self.adc.read()

class MQGasSensor:
    def __init__(self, analog_pin=1, digital_pin=23):

        self.gpio = GPIO(digital_pin, 'in') 
        self.adc = ADC(analog_pin)
    
    def read(self):
        signal = self.gpio.read()
        value = self.adc.read()

        return (not signal, value)

class Servo:
    def __init__(self, chip=0, channel=0):
        self.pwm = periphery.PWM(chip, channel)
        self.pwm.frequency =  50

        self.high_duration(1.5)
        self.pwm.enable()

    def high_duration(self, ms):
        T_ms = 1 / self.pwm.frequency * 1000
        # print("T:", T_ms)
        # print(ms)
        self.pwm.duty_cycle = 1 - (ms/T_ms)

    def update(self, degree):
        if degree > 90:
            degree = 90
        if degree < -90:
            degree = -90
        # -90 ~ 90 map to 0.5 ~ 2.5
        ms = (degree - (-90)) * (2.5 - 0.5) / (90 - (-90)) + 0.5
        self.high_duration(ms)

class Servos:
    def __init__(self):
        self.servo_x = Servo(chip=0)
        self.servo_y = Servo(chip=1)

    def update_x(self, degree):
        self.servo_x.update(degree)

    def update_y(self, degree):
        # y 限位 0-90
        if degree > 90:
            degree = 90
        if degree < 0:
            degree = 0

        # 舵机反向安装，所以需要加负数
        self.servo_y.update(-degree)
