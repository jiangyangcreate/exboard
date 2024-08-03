import Jetson.GPIO as JetsonGPIO
import serial
import serial.tools.list_ports
from smbus import SMBus
import time
import smbus
import smbus2

JetsonGPIO.setwarnings(False)

class MFRC522:
    # Define register values from datasheet
    COMMANDREG = 0x01  # Start and stops command execution
    COMIENREG = 0x02  # Enable and disable interrupt request control bits
    COMIRQREG = 0x04  # Interrupt request bits
    DIVIRQREG = 0x05  # Interrupt request bits
    ERRORREG = 0x06  # Error bits showing the error status of the last command
    STATUS2REG = 0x08  # Receiver and transmitter status bits
    FIFODATAREG = 0x09  # Input and output of 64 byte FIFO buffer
    FIFOLEVELREG = 0x0A  # Number of bytes stored in the FIFO buffer
    CONTROLREG = 0x0C  # Miscellaneous control register
    BITFRAMINGREG = 0x0D  # Adjustments for bit-oriented frames
    MODEREG = 0x11  # Defines general modes for transmitting and receiving
    TXCONTROLREG = 0x14  # Controls the logical behavior of the antenna pins
    TXASKREG = 0x15  # Controls the setting of the transmission modulation
    CRCRESULTREGMSB = 0x21  # Shows the MSB of the CRC calculation
    CRCRESULTREGLSB = 0x22  # Shows the LSB of the CRC calculation
    TMODEREG = 0x2A  # Defines settings for the internal timer
    TPRESCALERREG = 0x2B  # Defines settings for internal timer
    TRELOADREGH = 0x2C  # Defines 16-bit timer reload value
    TRELOADREGL = 0x2D  # Defines 16-bit timer reload value
    VERSIONREG = 0x37  # Shows the software version

    # MFRC522 Commands
    MFRC522_IDLE = 0x00  # No actions, cancels current command execution
    MFRC522_CALCCRC = 0x03  # Activates the CRC coprocessor and performs
    # a self test
    MFRC522_TRANSCEIVE = 0x0C  # Transmits data from FIFO buffer to
    # anntenna and automatically activates the receiver after
    # transmission
    MFRC522_MFAUTHENT = 0x0E  # Performs the MIFARE standard authentication
    # as a reader
    MFRC522_SOFTRESET = 0x0F  # Resets the MFRC522

    # MIFARE Classic Commands
    MIFARE_REQUEST = [0x26]
    MIFARE_WAKEUP = [0x52]
    MIFARE_ANTICOLCL1 = [0x93, 0x20]
    MIFARE_SELECTCL1 = [0x93, 0x70]
    MIFARE_ANTICOLCL2 = [0x95, 0x20]
    MIFARE_SELECTCL2 = [0x95, 0x70]
    MIFARE_HALT = [0x50, 0x00]
    MIFARE_AUTHKEY1 = [0x60]
    MIFARE_AUTHKEY2 = [0x61]
    MIFARE_READ = [0x30]
    MIFARE_WRITE = [0xA0]
    MIFARE_DECREMENT = [0xC0]
    MIFARE_INCREMENT = [0xC1]
    MIFARE_RESTORE = [0xC2]
    MIFARE_TRANSFER = [0xB0]

    # Mifare 1K EEPROM is arranged of 16 sectors. Each sector has 4 blocks and
    # each block has 16-byte. Block 0 is a special read-only data block that
    # keeps the manufacturer data and the UID of the tag. The sector trailer
    # block, the last block of the sector, holds the access conditions and two
    # of the authentication keys for that particular sector
    MIFARE_1K_MANUFAKTURERBLOCK = [0]
    MIFARE_1K_SECTORTRAILER = [3, 7, 11, 15, 19, 23, 27, 31, 35,
                               39, 43, 47, 51, 55, 59, 63]
    MIFARE_1K_DATABLOCK = [1, 2, 4, 5, 6, 8, 9, 10, 12, 13,
                           14, 16, 17, 18, 20, 21, 22,  24,  25,  26,
                           28, 29, 30, 32, 33, 34, 36,  37,  38,  40,
                           41, 42, 44, 45, 46, 48, 49,  50,  52,  53,
                           54, 56, 57, 58, 60, 61, 62]

    # Mifare 4K EEPROM is arranged of 40 sectors. From sector 0 to 31, memory
    # organization is similar to Mifare 1K, each sector has 4 blocks. From
    # sector 32 to 39, each sector has 16 blocks
    MIFARE_4K_MANUFAKTURERBLOCK = [0]
    MIFARE_4K_SECTORTRAILER = [3, 7, 11, 15, 19, 23, 27, 31, 35, 39,
                               43, 47, 51, 55, 59, 63, 67, 71, 75, 79,
                               83, 87, 91, 95, 99, 103, 107, 111, 115, 119,
                               123, 127, 143, 159, 175, 191, 207, 223, 239,
                               255]
    MIFARE_4K_DATABLOCK = [1,  2, 4, 5, 6, 8, 9, 10, 12, 13,
                           14, 16, 17, 18, 20, 21, 22, 24, 25, 26,
                           28, 29, 30, 32, 33, 34, 36, 37, 38, 40,
                           41, 42, 44, 45, 46, 48, 49, 50, 52, 53,
                           54, 56, 57, 58, 60, 61, 62, 64, 65, 66,
                           68, 69, 70, 72, 73, 74, 76, 77, 78, 80,
                           81, 82, 84, 85, 86, 88, 89, 90, 92, 93,
                           94, 96, 97, 98, 100, 101, 102, 104, 105, 106,
                           108, 109, 110, 112, 113, 114, 116, 117, 118, 120,
                           121, 122, 124, 125, 126, 128, 129, 130, 131, 132,
                           133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
                           144, 145, 146, 147, 148, 149, 150, 151, 152, 153,
                           154, 155, 156, 157, 158, 160, 161, 162, 163, 164,
                           165, 166, 167, 168, 169, 170, 171, 172, 173, 174,
                           176, 177, 178, 179, 180, 181, 182, 183, 184, 185,
                           186, 187, 188, 189, 190, 192, 193, 194, 195, 196,
                           197, 198, 199, 200, 201, 202, 203, 204, 205, 206,
                           208, 209, 210, 211, 212, 213, 214, 215, 216, 217,
                           218, 219, 220, 221, 222, 224, 225, 226, 227, 228,
                           229, 230, 231, 232, 233, 234, 235, 236, 237, 238,
                           240, 241, 242, 243, 244, 245, 246, 247, 248, 249,
                           250, 251, 252, 253, 254]

    MIFARE_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

    MIFARE_OK = 0
    MIFARE_NOTAGERR = 1
    MIFARE_ERR = 2

    MAX_LEN = 16

    def __init__(self, Bus, Address):
        self.i2cBus = SMBus(Bus)
        self.i2cAddress = Address
        self.__MFRC522_init()

    def getReaderVersion(self):
        version = None

        # Retrieve version from VERSIONREG
        version = self.__MFRC522_read(self.VERSIONREG)
        if (version == 0x91):
            version = 'v1.0'
        if (version == 0x92):
            version = 'v2.0'

        return (version)

    def scan(self):
        """ Scans for a card and returns the UID"""
        status = None
        backData = []
        backBits = None

        # None bits of the last byte
        self.__MFRC522_write(self.BITFRAMINGREG, 0x07)

        buffer = []
        buffer.extend(self.MIFARE_REQUEST)

        (status, backData, backBits) = self.__transceiveCard(buffer)

        if ((status != self.MIFARE_OK) | (backBits != 0x10)):
            status = self.MIFARE_ERR

        return (status, backData, backBits)

    def __serialNumberValid(self, serialNumber):
        """ Checks if the serial number is valid """
        i = 0
        serialCheck = 0

        while (i < (len(serialNumber) - 1)):
            serialCheck = serialCheck ^ serialNumber[i]
            i = i + 1
        if (serialCheck != serialNumber[i]):
            return False
        else:
            return True

    def identify(self):
        """ Receives the serial number of the card"""
        status = None
        backData = []
        backBits = None

        # All bits of the last byte
        self.__MFRC522_write(self.BITFRAMINGREG, 0x00)

        buffer = []
        buffer.extend(self.MIFARE_ANTICOLCL1)

        (status, backData, backBits) = self.__transceiveCard(buffer)

        if (status == self.MIFARE_OK):
            if (self.__serialNumberValid(backData)):
                status = self.MIFARE_OK
            else:
                status = self.MIFARE_ERR

        return (status, backData, backBits)

    def __transceiveCard(self, data):
        """ Transceives data trough the reader/writer from and to the card """
        status = None
        backData = []
        backBits = None

        IRqInv = 0x80  # Signal on pin IRQ is inverted
        TxIEn = 0x40  # Allow the transmitter to interrupt requests
        RxIEn = 0x20  # Allow the receiver to interrupt requests
        IdleIEn = 0x10  # Allow the idle interrupt request
        LoAlertIEn = 0x04  # Allow the low Alert interrupt request
        ErrIEn = 0x02  # Allow the error interrupt request
        TimerIEn = 0x01  # Allow the timer interrupt request
        self.__MFRC522_write(self.COMIENREG, (IRqInv |
                                              TxIEn |
                                              RxIEn |
                                              IdleIEn |
                                              LoAlertIEn |
                                              ErrIEn |
                                              TimerIEn))

        # Indicates that the bits in the ComIrqReg register are set
        Set1 = 0x80
        self.__MFRC522_clearBitMask(self.COMIRQREG, Set1)

        # Immediatly clears the internal FIFO buffer's read and write pointer
        # and ErrorReg register's BufferOvfl bit
        FlushBuffer = 0x80
        self.__MFRC522_setBitMask(self.FIFOLEVELREG, FlushBuffer)

        # Cancel running commands
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_IDLE)

        # Write data in FIFO register
        for i in range(0, len(data)):
            self.__MFRC522_write(self.FIFODATAREG, data[i])

        # Countinously repeat the transmission of data from the FIFO buffer and
        # the reception of data from the RF field.
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_TRANSCEIVE)

        # Starts the transmission of data, only valid in combination with the
        # Transceive command
        StartSend = 0x80
        self.__MFRC522_setBitMask(self.BITFRAMINGREG, StartSend)

        # The timer has decrement the value in TCounterValReg register to zero
        TimerIRq = 0x01
        # The receiver has detected the end of a valid data stream
        RxIRq = 0x20
        # A command was terminated or unknown command is started
        IdleIRq = 0x10

        # Wait for an interrupt
        i = 2000
        while True:
            comIRqReg = self.__MFRC522_read(self.COMIRQREG)
            if (comIRqReg & TimerIRq):
                # Timeout
                break
            if (comIRqReg & RxIRq):
                # Valid data available in FIFO
                break
            if (comIRqReg & IdleIRq):
                # Command terminate
                break
            if (i == 0):
                # Watchdog expired
                break
            i -= 1

        # Clear the StartSend bit in BitFramingReg register
        self.__MFRC522_clearBitMask(self.BITFRAMINGREG, StartSend)

        # Retrieve data from FIFODATAREG
        if (i != 0):
            # The host or a MFRC522's internal state machine tries to write
            # data to the FIFO buffer even though it is already full
            BufferOvfl = 0x10
            # A bit collision is detected
            ColErr = 0x08
            # Parity check failed
            ParityErr = 0x02
            # Set to logic 1 if the SOF is incorrect
            ProtocolErr = 0x01

            errorTest = (BufferOvfl | ColErr | ParityErr | ProtocolErr)
            errorReg = self.__MFRC522_read(self.ERRORREG)

            # Test if any of the errors above happend
            if (~(errorReg & errorTest)):
                status = self.MIFARE_OK

                # Indicates any error bit in thr ErrorReg register is set
                ErrIRq = 0x02

                # Test if the timer expired and an error occured
                if (comIRqReg & TimerIRq & ErrIRq):
                    status = self.MIFARE_NOTAGERR

                fifoLevelReg = self.__MFRC522_read(self.FIFOLEVELREG)

                # Edge cases
                if fifoLevelReg == 0:
                    fifoLevelReg = 1
                if fifoLevelReg > self.MAX_LEN:
                    fifoLevelReg = self.MAX_LEN

                # Indicates the number of valid bits in the last received byte
                RxLastBits = 0x08

                lastBits = self.__MFRC522_read(self.CONTROLREG) & RxLastBits

                if (lastBits != 0):
                    backBits = (fifoLevelReg - 1) * 8 + lastBits
                else:
                    backBits = fifoLevelReg * 8

                # Read data from FIFO register
                for i in range(0, fifoLevelReg):
                    backData.append(self.__MFRC522_read(self.FIFODATAREG))

            else:
                status.MIFARE_ERR

        return (status, backData, backBits)

    def __calculateCRC(self, data):
        """ Uses the reader/writer to calculate CRC """
        # Clear the bit that indicates taht the CalcCRC command is active
        # and all data is processed
        CRCIRq = 0x04
        self.__MFRC522_clearBitMask(self.DIVIRQREG, CRCIRq)

        # Immedialty clears the internal FIFO buffer's read and write pointer
        # and ErrorReg register's BufferOvfl bit
        FlushBuffer = 0x80
        self.__MFRC522_setBitMask(self.FIFOLEVELREG, FlushBuffer)

        # Write data to FIFO
        i = 0
        while (i < len(data)):
            self.__MFRC522_write(self.FIFODATAREG, data[i])
            i = i + 1

        # Execute CRC calculation
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_CALCCRC)
        i = 255
        while True:
            divirqreg = self.__MFRC522_read(self.DIVIRQREG)
            i = i - 1
            if (i == 0):
                # Watchdog expired
                break
            if (divirqreg & CRCIRq):
                # CRC is calculated
                break

        # Retrieve CRC from CRCRESULTREG
        crc = []
        crc.append(self.__MFRC522_read(self.CRCRESULTREGLSB))
        crc.append(self.__MFRC522_read(self.CRCRESULTREGMSB))

        return (crc)

    def select(self, serialNumber):
        """ Selects a card with a given serial number """
        status = None
        backData = []
        backBits = None

        buffer = []
        buffer.extend(self.MIFARE_SELECTCL1)

        i = 0
        while (i < 5):
            buffer.append(serialNumber[i])
            i = i + 1

        crc = self.__calculateCRC(buffer)
        buffer.extend(crc)

        (status, backData, backBits) = self.__transceiveCard(buffer)

        return (status, backData, backBits)

    def authenticate(self, mode, blockAddr, key, serialNumber):
        """ Authenticates the card """
        status = None
        backData = []
        backBits = None

        buffer = []
        buffer.extend(mode)
        buffer.append(blockAddr)
        buffer.extend(key)

        i = 0
        while (i < 4):
            buffer.append(serialNumber[i])
            i = i + 1

        (status, backData, backBits) = self.__authenticateCard(buffer)

        return (status, backData, backBits)

    def deauthenticate(self):
        """ Deauthenticates the card """
        # Indicates that the MIFARE Crypto1 unit is switched on and
        # therfore all data communication with the card is encrypted
        # Can ONLY be set to logic 1 by a successfull execution of
        # the MFAuthent command
        MFCrypto1On = 0x08
        self.__MFRC522_clearBitMask(self.STATUS2REG, MFCrypto1On)

    def __authenticateCard(self, data):
        status = None
        backData = []
        backBits = None

        IRqInv = 0x80  # Signal on pin IRQ is inverted
        IdleIEn = 0x10  # Allow the idle interrupt request
        ErrIEn = 0x02  # Allow the error interrupt request
        self.__MFRC522_write(self.COMIENREG, (IRqInv | IdleIEn | ErrIEn))

        # Indicates that the bits in the ComIrqReg register are set
        Set1 = 0x80
        self.__MFRC522_clearBitMask(self.COMIRQREG, Set1)

        # Immedialty clears the interl FIFO buffer's read and write pointer
        # and ErrorReg register's BufferOvfl bit
        FlushBuffer = 0x80
        self.__MFRC522_setBitMask(self.FIFOLEVELREG, FlushBuffer)

        # Cancel running commands
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_IDLE)

        # Write data in FIFO register
        i = 0
        while (i < len(data)):
            self.__MFRC522_write(self.FIFODATAREG, data[i])
            i = i + 1

        # This command manages MIFARE authentication to anable a secure
        # communication to any MIFARE card
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_MFAUTHENT)

        # The timer has decrement the value in TCounterValReg register to zero
        TimerIRq = 0x01
        # The receiver has detected the end of a valid data stream
        RxIRq = 0x20
        # A command was terminated or unknown command is started
        IdleIRq = 0x10

        # Wait for an interrupt
        i = 2000
        while True:
            comIRqReg = self.__MFRC522_read(self.COMIRQREG)
            if (comIRqReg & TimerIRq):
                # Timeout
                break
            if (comIRqReg & RxIRq):
                # Valid data available in FIFO
                break
            if (comIRqReg & IdleIRq):
                # Command terminate
                break
            if (i == 0):
                # Watchdog expired
                break
            i -= 1

        # Clear the StartSend bit in BitFramingReg register
        StartSend = 0x80
        self.__MFRC522_clearBitMask(self.BITFRAMINGREG, StartSend)

        # Retrieve data from FIFODATAREG
        if (i != 0):
            # The host or a MFRC522's internal state machine tries to write
            # data to the FIFO buffer even though it is already full
            BufferOvfl = 0x10
            # A bit collision is detected
            ColErr = 0x08
            # Parity check failed
            ParityErr = 0x02
            # Set to logic 1 if the SOF is incorrect
            ProtocolErr = 0x01

            errorTest = (BufferOvfl | ColErr | ParityErr | ProtocolErr)
            errorReg = self.__MFRC522_read(self.ERRORREG)

            # Test if any of the errors above happend
            if (~(errorReg & errorTest)):
                status = self.MIFARE_OK

                # Indicates any error bit in thr ErrorReg register is set
                ErrIRq = 0x02

                # Test if the timer expired and an error occured
                if (comIRqReg & TimerIRq & ErrIRq):
                    status = self.MIFARE_NOTAGERR

            else:
                status = self.MIFARE_ERR

        return (status, backData, backBits)

    def read(self, blockAddr):
        """ Reads data from the card """
        status = None
        backData = []
        backBits = None

        buffer = []
        buffer.extend(self.MIFARE_READ)
        buffer.append(blockAddr)

        crc = self.__calculateCRC(buffer)
        buffer.extend(crc)

        (status, backData, backBits) = self.__transceiveCard(buffer)

        return (status, backData, backBits)

    def write(self, blockAddr, data):
        """ Writes data to the card """
        status = None
        backData = []
        backBits = None

        buffer = []
        buffer.extend(self.MIFARE_WRITE)
        buffer.append(blockAddr)

        crc = self.__calculateCRC(buffer)
        buffer.extend(crc)

        (status, backData, backBits) = self.__transceiveCard(buffer)

        if (status == self.MIFARE_OK):

            buffer.clear()
            buffer.extend(data)

            crc = self.__calculateCRC(buffer)
            buffer.extend(crc)

            (status, backData, backBits) = self.__transceiveCard(buffer)

        return (status, backData, backBits)

    def __MFRC522_antennaOn(self):
        """ Activates the reader/writer antenna """
        value = self.__MFRC522_read(self.TXCONTROLREG)
        if (~(value & 0x03)):
            self.__MFRC522_setBitMask(self.TXCONTROLREG, 0x03)

    def __MFRC522_antennaOff(self):
        """ Deactivates the reader/writer antenna """
        self.__MFRC522_clearBitMask(self.TXCONTROLREG, 0x03)

    def __MFRC522_reset(self):
        """ Resets the reader/writer """
        self.__MFRC522_write(self.COMMANDREG, self.MFRC522_SOFTRESET)

    def __MFRC522_init(self):
        """ Initialization sequence"""
        self.__MFRC522_reset()

        # Timer starts automatically at the end of the transmission in all
        # communication modes and speeds
        TAuto = 0x80
        # Defines the higher 4 bits of the TPrescaler value
        TPrescaler_Hi = 0x0D
        # Defines the lower 4 bits of the TPrescaler value
        TPrescaler_Lo = 0x3E
        self.__MFRC522_write(self.TMODEREG, (TAuto | TPrescaler_Hi))
        self.__MFRC522_write(self.TPRESCALERREG, TPrescaler_Lo)

        # Defines the higher 8 bits of the timer reload value
        TReloadVal_Hi = 0x1E
        # Defines the lower 8 bits of the timer reload value
        TReloadVal_Lo = 0x00
        self.__MFRC522_write(self.TRELOADREGH, TReloadVal_Hi)
        self.__MFRC522_write(self.TRELOADREGL, TReloadVal_Lo)

        Force100ASK = 0x40  # Forces a 100% ASK modulation
        self.__MFRC522_write(self.TXASKREG, Force100ASK)

        # Moderegister reset value
        ResetVal = 0x3F
        # Moderegister feature mask
        FeatureMask = 0x14
        # Transmitter can only be started if RF field is generated
        TxWaitRF = 0x20
        # Defines polarity of pin MFIN, polarity of pin is active HIGH
        PolMFin = 0x08
        # Defines the preset value for the CRC coprocessor for the CalcCRC
        # command
        CRCPreset = 0x01
        self.__MFRC522_write(self.MODEREG, ((ResetVal &
                                             FeatureMask) |
                                            TxWaitRF |
                                            PolMFin |
                                            CRCPreset))

        # Activate antenna
        self.__MFRC522_antennaOn()

    def __MFRC522_read(self, address):
        """ Read data from an address on the i2c bus """
        value = self.i2cBus.read_byte_data(self.i2cAddress, address)
        return value

    def __MFRC522_write(self, address, value):
        """ Write data on an address on the i2c bus """
        self.i2cBus.write_byte_data(self.i2cAddress, address, value)

    def __MFRC522_setBitMask(self, address, mask):
        """ Set bits according to a mask on a address on the i2c bus """
        value = self.__MFRC522_read(address)
        self.__MFRC522_write(address, value | mask)

    def __MFRC522_clearBitMask(self, address, mask):
        """ Resets bits according to a mask on a address on the i2c bus """
        value = self.__MFRC522_read(address)
        self.__MFRC522_write(address, value & (~mask))



class RC522:
    def __init__(self):
        i2cBus = 7
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

    def read (self, uid:list, blockAddr:int):
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

    def write(self, blockAddr:int, data:list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]):
        """
        blockAddr: 1-15
        data:list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        """
        return self.MFRC522Reader.write(blockAddr, data)

class RGB:

    def __init__(self):
        pass

    def set(self,data):
        '''
        data: list
         [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
         or 
         [255, 0, 0, 0, 255, 0, 0, 0, 255]
        '''
        flattened_list = []
        for tup in data:
            try:
                flattened_list.extend(tup)
            except:
                flattened_list.append(tup)
        flattened_list = flattened_list + [0]*(24*3 - len(flattened_list))
        with smbus2.SMBus(7) as bus:
            msg = smbus2.i2c_msg.write(0x24, [200]+flattened_list+[99])
            bus.i2c_rdwr(msg)

    def close(self):
        with smbus2.SMBus(7) as bus:
            msg = smbus2.i2c_msg.write(0x24, [200]+[0,0,0]*24+[99])
            bus.i2c_rdwr(msg)

class ADC:
    """
    此类用于处理模拟到数字转换器（ADC）。它接收一个引脚编号，并创建一个 I2C 对象来读取 ADC 的值。
    """
    
    SUBLINE = 7      # 固定的总线编号
    SUBPIN = 0x24    # 固定的设备地址
    BASE_ADDR = 0x10 # 基地址
    DEFAULT_FUNCTION = 1  # 默认的功能码 (读取 ADC 原始数据)

    def __init__(self, channel, function=DEFAULT_FUNCTION):
        """
        初始化 ADC。

        :param channel: 引脚序号 (0 表示 A0, 1 表示 A1, ... 7 表示 A7)
        :param function: 功能码 (默认是 1 表示读取 ADC 原始数据, 可选值: 1 表示读取 ADC 原始数据, 2 表示读取输入电压, 3 表示读取输入输出电压比)
        """
        self.adcpin = (ADC.BASE_ADDR + channel)+ (function-1)*16
        self.bus = smbus.SMBus(ADC.SUBLINE)

    def read(self):
        """
        读取 ADC 的当前值。

        :return: ADC 当前值
        """
        value = self.bus.read_word_data(ADC.SUBPIN, self.adcpin)
        return value

class GPIO:
    """
    此类用于处理通用输入/输出（GPIO）引脚。它接收一个引脚编号和其他参数 'out' 或 'in'，
    并返回一个 GPIO 对象。GPIO 可进行的操作有：

    write(value)：写入一个布尔值
    read()：读取当前引脚的值
    cleanup()：清理引脚
    """
    
    def __init__(self, channel, direction, initial=None):
        """
        初始化 GPIO 引脚。

        :param channel: GPIO 引脚编号
        :param direction: 'out' 或 'in'
        :param initial: 初始值 (仅适用于输出引脚)
        """
        self.channel = channel
        self.direction = JetsonGPIO.OUT if direction == 'out' else JetsonGPIO.IN
        JetsonGPIO.setmode(JetsonGPIO.BCM)  # 默认使用 BOARD 模式
        if initial is not None and self.direction == JetsonGPIO.OUT:
            JetsonGPIO.setup(self.channel, self.direction, initial=initial)
        else:
            JetsonGPIO.setup(self.channel, self.direction)

    def write(self, value):
        """
        写入一个布尔值到 GPIO 引脚 (仅适用于输出引脚)。

        :param value: 布尔值 (True 或 False)
        """
        if self.direction == JetsonGPIO.OUT:
            JetsonGPIO.output(self.channel, JetsonGPIO.HIGH if value else JetsonGPIO.LOW)
        else:
            raise ValueError("Can't write to an input GPIO")

    def read(self):
        """
        读取当前 GPIO 引脚的值。

        :return: 布尔值 (True 或 False)
        """
        return JetsonGPIO.input(self.channel) == JetsonGPIO.HIGH

    def cleanup(self):
        """
        清理 GPIO 引脚。
        """
        JetsonGPIO.cleanup(self.channel)

class Ultrasound:
    '''
    最大测距理论值小于343
    '''
    def __init__(self, trigger_pin=4, echo_pin=5, max_cm=None, timeout=0.1):
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
        distance = int(TimeElapsed * 34300) / 2
        time.sleep(0.01)
        return distance

class LED:
    def __init__(self, pin):
        self.GPIO = GPIO(pin, 'out')
    
    def on(self):
        self.GPIO.write(True)
    
    def off(self):
        self.GPIO.write(False)


class SoundSensor:
    def __init__(self, analog_pin=0,digital_pin=0):
        self.adc = ADC(analog_pin)
    
    def read(self):
        value = self.adc.read()
        signal = value > 200

        return (signal, value)

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
    def __init__(self, analog_pin=2, digital_pin=23):

        self.adc = ADC(analog_pin)
    
    def read(self):
        value = self.adc.read()
        signal = value < 200

        return (not signal, value)

class Servos:
    # VISCA命令集
    commands = {
        "stop": "81010601{vv}{ww}0303FF",
        "left": "81010601{vv}{ww}0103FF",
        "right": "81010601{vv}{ww}0203FF",
        "up": "81010601{vv}{ww}0301FF",
        "down": "81010601{vv}{ww}0302FF",
        "upleft": "81010601{vv}{ww}0101FF",
        "upright": "81010601{vv}{ww}0201FF",
        "downleft": "81010601{vv}{ww}0102FF",
        "downright": "81010601{vv}{ww}0202FF",
        "absolute_position": "81010602{vv}{ww}{Y}{Z}FF",
        "relative_position": "81010603{vv}{ww}{Y}{Z}FF",
        "home": "81010604FF",
        "reset": "81010605FF",
    }

    def __init__(self, device="/dev/ttyUSB0"):
        self.device = device
        self.y = 0
        self.z = 0

    def send_visca_command(self, command):
        """
        通过串口向摄像机发送VISCA命令。

        参数:
        command (str): 要发送的VISCA命令，格式为十六进制字符串。

        返回:
        response (bytes): 从摄像机接收到的响应。
        """
        try:
            ser = serial.Serial(self.device, 9600, timeout=1)  # 初始化串口
            command_bytes = bytearray.fromhex(command)  # 将命令转换为字节
            ser.write(command_bytes)  # 发送命令
            response = ser.read_all()  # 读取响应
            ser.close()  # 关闭串口
            return response
        except:
            ports_list = list(serial.tools.list_ports.comports())
            if len(ports_list) <= 0:
                print("未发现端口")
            else:
                for comport in ports_list:
                    if "USB" in str(comport):
                        print("发现USB端口：", comport.device, comport.description)

    @staticmethod
    def calculate_pan_speed_bytes(pan_speed_value):
        """
        计算轴（旋转）的位置字节。

        参数:
        pan_speed_value (int): 速度值，0-16

        返回:
        pan_step_str (str): 计算得到的平移位置字节，格式为十六进制字符串。
        """
        pan_speed_value = max(0, min(pan_speed_value, 16))  # 限制取值范围
        return f"{pan_speed_value:02X}"  # 转为2位16进制

    @staticmethod
    def calculate_pan_position_bytes(pan_pos_value, axis_type):
        """
        计算轴（旋转）的位置字节。

        参数:
        pan_pos_value (int): 位置值，
        axis_type (str): 轴的类型 ('y' or 'Y' for Y-axis, others for Z-axis)

        返回:
        pan_step_str (str): 计算得到的平移位置字节，格式为十六进制字符串。
        """
        if axis_type.lower() == "y":
            pan_pos_value = max(-177.5, min(pan_pos_value, 177.5))  # 限制取值范围
        else:
            pan_pos_value = max(-21, min(pan_pos_value, 21))  # 限制取值范围

        pan_pos_value = int(pan_pos_value * 25)  # 将角度转换为步长
        pan_direction = "-" if pan_pos_value < 0 else "+"  # 设定旋转方向
        pan_pos_value = abs(pan_pos_value)  # 取绝对值

        HEX_VALUES = [4096, 256, 16, 1]  # 定义常量
        pan_pos_ints = []
        for i, value in enumerate(HEX_VALUES):
            if pan_direction == "+":
                pan_pos_ints.append(pan_pos_value // value)
            else:  # 异或操作
                pan_pos_ints.append((pan_pos_value // value) ^ 0xF)
                if i == 3:  # 最后一个数字，取反后加1
                    pan_pos_ints[-1] = pan_pos_ints[-1] + 1
            pan_pos_value %= value

        pan_pos_strs = [f"{i:02X}" for i in pan_pos_ints]  # 转换为2位16进制字符串
        return "".join(pan_pos_strs)

    def create_command(self, command_key, vv=10, ww=10, Y=None, Z=None):
        """
        创建VISCA命令。

        参数:
        command_key (str): 命令键名。
        vv (str): 水平方向速度，取值范围为0-16
        ww (str): 垂直方向速度，取值范围为0-16
        Y (str): 控制水平旋转的位置。
        Z (str): 控制垂直旋转的位置。

        返回:
        command (str): 格式化后的VISCA命令字符串。

        异常:
        ValueError: 当命令需要Y和Z参数时，若未提供，则抛出异常。
        """
        if command_key in ["home", "reset"]:
            return self.commands[command_key]
        if command_key in ["absolute_position", "relative_position"]:
            if Y is None or Z is None:
                raise ValueError("Y和Z为位置命令,必须提供")
            return self.commands[command_key].format(
                vv=self.calculate_pan_speed_bytes(vv),
                ww=self.calculate_pan_speed_bytes(ww),
                Y=self.calculate_pan_position_bytes(Y, "y"),
                Z=self.calculate_pan_position_bytes(Z, "z"),
            )
        return self.commands[command_key].format(
            vv=self.calculate_pan_speed_bytes(vv),
            ww=self.calculate_pan_speed_bytes(ww),
        )

    # 控制函数
    def turn_stop(self, vv=0, ww=0):
        return self.send_visca_command(self.create_command("stop", vv, ww))

    def turn_left(self, vv=10, ww=10):
        return self.send_visca_command(self.create_command("left", vv, ww))

    def turn_right(self, vv=10, ww=10):
        return self.send_visca_command(self.create_command("right", vv, ww))

    def turn_up(self, vv=10, ww=10):
        return self.send_visca_command(self.create_command("up", vv, ww))

    def turn_down(self, vv=10, ww=10):
        return self.send_visca_command(self.create_command("down", vv, ww))

    def move_home(self):
        return self.send_visca_command(self.create_command("home"))

    def move_to_absolute_position(self, vv=10, ww=10, Y=0, Z=0):
        return self.send_visca_command(self.create_command("absolute_position", vv, ww, Y, Z))

    def update_x(self, degree):
        self.move_to_absolute_position(Y=degree,Z = self.z)
        self.y += degree

    def update_y(self, degree):
        self.move_to_absolute_position(Y=self.y,Z = degree)
        self.z += degree