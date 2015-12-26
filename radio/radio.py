'''
Simple class for a two way half duplex radio link. One end of the link is the master device,
meaning the only end which sends unsolicited messages. The slave only transmits in response to
such a message. Modify RadioSetup to match your hardware, channel and payload size (in bytes, 1-32).
master = TwoWayRadio(True, **RadioSetup)
slave = TwoWayRadio(False, **RadioSetup)
'''
import pyb
from nrf24l01 import NRF24L01, POWER_3, SPEED_250K

RadioSetup = { "channel": 100, "payload_size": 8, "spi_no": 1, "csn_pin": 'X5', "ce_pin": 'Y11'}

class TwoWayRadio(NRF24L01):
    pipes           = (b'\xf0\xf0\xf0\xf0\xe1', b'\xf0\xf0\xf0\xf0\xd2')
    def __init__(self, master, channel, payload_size, spi_no, csn_pin, ce_pin):
        super().__init__(pyb.SPI(spi_no), pyb.Pin(csn_pin), pyb.Pin(ce_pin),channel = channel,payload_size = payload_size)
        if master:
            self.open_tx_pipe(TwoWayRadio.pipes[0])
            self.open_rx_pipe(1, TwoWayRadio.pipes[1])
        else:
            self.open_tx_pipe(TwoWayRadio.pipes[1])
            self.open_rx_pipe(1, TwoWayRadio.pipes[0])
        self.set_power_speed(POWER_3, SPEED_250K) # Best range for point to point links
        self.start_listening()

    def start_listening(self):
        super().start_listening()
        pyb.delay(1) # Seems to improve reliability
