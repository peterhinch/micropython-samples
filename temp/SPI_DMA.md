# A nonblocking SPI master for RP2

The module `spi_dma` provides a class `RP2_SPI_DMA_MASTER` which uses DMA to
perform fast SPI output. A typical use case is to transfer the contents of a
frame buffer to a display as a background task.

## Constructor

This takes the following args:
* `sm_num` State machine no. (0..7 on RP2040, 0..11 on RP2350)
* `freq` SPI clock frequency in Hz.
* `sck` A `Pin` instance for `sck`. Pins are arbitrary.
* `mosi` A `Pin` instance for `mosi`.
* `callback` A callback to run when DMA is complete. This is run in a hard IRQ
context. Typical use is to set a `ThreadSafeFlag`. Note that the DMA completes
before transmission ends due to bytes stored in the SM FIFO. This is unlikely to
have practical consequences because of MicroPython latency: in particular
response to a `ThreadSafeFlag` typically takes >200μs.

## Methods

* `write(data : bytes)` arg a `bytes` or `bytearray` of data to transmit. Return
is rapid with transmission running in the background. Returns `None`.
* `deinit()` Disables the DMA and the SM. Returns `None`.

## CS/

The application should assert CS/ (set to 0) prior to transmission and deassert
it after transmission is complete.

## Test script and performance

The file `spi_dma_test.py` illustrates usage with `asyncio`. The module has
been tested at 30MHz, but higher frequencies may be practical with care
given to wiring.
