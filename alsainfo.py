#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from collections import namedtuple
from ctypes import c_char_p, c_int, c_uint, c_ulong, c_void_p, byref, cdll, create_string_buffer
from enum import IntEnum
from textwrap import indent


log = logging.getLogger(__name__)


class LibAsoundError(Exception):
    pass


class SndPcmStream(IntEnum):
    PLAYBACK = 0
    CAPTURE = 1


class SndPcmFormat(IntEnum):
    # Signed 8 bit
    S8 = 0
    # Unsigned 8 bit
    U8 = 1
    # Signed 16 bit Little Endian
    S16_LE = 2
    # Signed 16 bit Big Endian
    S16_BE = 3
    # Unsigned 16 bit Little Endian
    U16_LE = 4
    # Unsigned 16 bit Big Endian
    U16_BE = 5
    # Signed 24 bit Little Endian using low three bytes in 32-bit word
    S24_LE = 6
    # Signed 24 bit Big Endian using low three bytes in 32-bit word
    S24_BE = 7
    # Unsigned 24 bit Little Endian using low three bytes in 32-bit word
    U24_LE = 8
    # Unsigned 24 bit Big Endian using low three bytes in 32-bit word
    U24_BE = 9
    # Signed 32 bit Little Endian
    S32_LE = 10
    # Signed 32 bit Big Endian
    S32_BE = 11
    # Unsigned 32 bit Little Endian
    U32_LE = 12
    # Unsigned 32 bit Big Endian
    U32_BE = 13
    # Float 32 bit Little Endian, Range -1.0 to 1.0
    FLOAT_LE = 14
    # Float 32 bit Big Endian, Range -1.0 to 1.0
    FLOAT_BE = 15
    # Float 64 bit Little Endian, Range -1.0 to 1.0
    FLOAT64_LE = 16
    # Float 64 bit Big Endian, Range -1.0 to 1.0
    FLOAT64_BE = 17
    # IEC-958 Little Endian
    IEC958_SUBFRAME_LE = 18
    # IEC-958 Big Endian
    IEC958_SUBFRAME_BE = 19
    # Mu-Law
    MU_LAW = 20
    # A-Law
    A_LAW = 21
    # Ima-ADPCM
    IMA_ADPCM = 22
    # MPEG
    MPEG = 23
    # GSM
    GSM = 24
    # Signed 20bit Little Endian in 4bytes format, LSB justified
    S20_LE = 25
    # Signed 20bit Big Endian in 4bytes format, LSB justified
    S20_BE = 26
    # Unsigned 20bit Little Endian in 4bytes format, LSB justified
    U20_LE = 27
    # Unsigned 20bit Big Endian in 4bytes format, LSB justified
    U20_BE = 28
    # Special
    SPECIAL = 31
    # Signed 24bit Little Endian in 3bytes format
    S24_3LE = 32
    # Signed 24bit Big Endian in 3bytes format
    S24_3BE = 33
    # Unsigned 24bit Little Endian in 3bytes format
    U24_3LE = 34
    # Unsigned 24bit Big Endian in 3bytes format
    U24_3BE = 35
    # Signed 20bit Little Endian in 3bytes format
    S20_3LE = 36
    # Signed 20bit Big Endian in 3bytes format
    S20_3BE = 37
    # Unsigned 20bit Little Endian in 3bytes format
    U20_3LE = 38
    # Unsigned 20bit Big Endian in 3bytes format
    U20_3BE = 39
    # Signed 18bit Little Endian in 3bytes format
    S18_3LE = 40
    # Signed 18bit Big Endian in 3bytes format
    S18_3BE = 41
    # Unsigned 18bit Little Endian in 3bytes format
    U18_3LE = 42
    # Unsigned 18bit Big Endian in 3bytes format
    U18_3BE = 43
    # G.723 (ADPCM) 24 kbit/s, 8 samples in 3 bytes
    G723_24 = 44
    # G.723 (ADPCM) 24 kbit/s, 1 sample in 1 byte
    G723_24_1B = 45
    # G.723 (ADPCM) 40 kbit/s, 8 samples in 3 bytes
    G723_40 = 46
    # G.723 (ADPCM) 40 kbit/s, 1 sample in 1 byte
    G723_40_1B = 47
    # Direct Stream Digital (DSD) in 1-byte samples (x8)
    DSD_U8 = 48
    # Direct Stream Digital (DSD) in 2-byte samples (x16)
    DSD_U16_LE = 49
    # Direct Stream Digital (DSD) in 4-byte samples (x32)
    DSD_U32_LE = 50
    # Direct Stream Digital (DSD) in 2-byte samples (x16)
    DSD_U16_BE = 51
    # Direct Stream Digital (DSD) in 4-byte samples (x32)
    DSD_U32_BE = 52

    if sys.byteorder == 'little':
        # Signed 16 bit CPU endian
        S16 = S16_LE
        # Unsigned 16 bit CPU endian
        U16 = U16_LE
        # Signed 24 bit CPU endian
        S24 = S24_LE
        # Unsigned 24 bit CPU endian
        U24 = U24_LE
        # Signed 32 bit CPU endian
        S32 = S32_LE
        # Unsigned 32 bit CPU endian
        U32 = U32_LE
        # Float 32 bit CPU endian
        FLOAT = FLOAT_LE
        # Float 64 bit CPU endian
        FLOAT64 = FLOAT64_LE
        # IEC-958 CPU Endian
        IEC958_SUBFRAME = IEC958_SUBFRAME_LE
        # Signed 20bit in 4bytes format, LSB justified, CPU Endian
        S20 = S20_LE
        # Unsigned 20bit in 4bytes format, LSB justified, CPU Endian
        U20 = U20_LE
    elif sys.byteorder == 'big':
        # Signed 16 bit CPU endian
        S16 = S16_BE
        # Unsigned 16 bit CPU endian
        U16 = U16_BE
        # Signed 24 bit CPU endian
        S24 = S24_BE
        # Unsigned 24 bit CPU endian
        U24 = U24_BE
        # Signed 32 bit CPU endian
        S32 = S32_BE
        # Unsigned 32 bit CPU endian
        U32 = U32_BE
        # Float 32 bit CPU endian
        FLOAT = FLOAT_BE
        # Float 64 bit CPU endian
        FLOAT64 = FLOAT64_BE
        # IEC-958 CPU Endian
        IEC958_SUBFRAME = IEC958_SUBFRAME_BE
        # Signed 20bit in 4bytes format, LSB justified, CPU Endian
        S20 = S20_BE
        # Unsigned 20bit in 4bytes format, LSB justified, CPU Endian
        U20 = U20_BE


PCM_RATES = (
    5512,
    8000,
    11025,
    16000,
    22050,
    32000,
    44100,
    48000,
    64000,
    88200,
    96000,
    176400,
    192000
)
PCM_BUFFER_SIZES = (
    32,
    64,
    128,
    256,
    512,
    1024,
    2048,
    4096
)
SND_PCM_NONBLOCK = 1

_lib = cdll.LoadLibrary("libasound.so.2")
_lib.snd_ctl_card_info_get_id.restype = c_char_p
_lib.snd_ctl_card_info_get_name.restype = c_char_p
_lib.snd_pcm_hw_params_get_format_mask.restype = None
_lib.snd_pcm_info_get_id.restype = c_char_p
_lib.snd_pcm_info_get_name.restype = c_char_p
_lib.snd_pcm_info_get_subdevice_name.restype = c_char_p
_lib.snd_pcm_format_name.restype = c_char_p
_lib.snd_strerror.restype = c_char_p


def decode_format_mask(fmask):
    return ((fmt, _lib.snd_pcm_format_name(c_int(fmt)).decode())
            for fmt in SndPcmFormat
            if _lib.snd_pcm_format_mask_test(fmask, c_int(fmt)) > 0)


def check_call(fn, args, msg="{errmsg}", **kwargs):
    err = fn(*args)
    if fn.restype is not None and err < 0:
        if '{errmsg}' not in msg:
            msg += ' {errmsg}'
        errmsg = _lib.snd_strerror(err).decode('utf-8')
        raise LibAsoundError(msg.format(errmsg=errmsg, **kwargs))


class AlsaCard(namedtuple('AlsaCard', ('cardno', 'id', 'name', 'devices'))):
    __slots__ = ()

    def __repr__(self):
        s = 'AlsaCard(cardno={c.cardno}, id={c.id!r}, name={c.name!r} devices=['.format(c=self)
        if self.devices:
            s += '\n' + indent(',\n'.join(repr(d) for d in self.devices), ' ' * 4)
            s += '\n'

        s += '])'
        return s


class AlsaDevice(namedtuple('AlsaDevice', ('devno', 'id', 'name', 'stream', 'buffer_sizes',
                                           'periods', 'channels', 'rates', 'formats',
                                           'subdevices'))):
    __slots__ = ()

    def __repr__(self):
        s = 'AlsaDevice(\n'
        for name, value in self._asdict().items():
            if name == 'stream':
                value = str(value)
            elif name == 'formats' and value is not None:
                value = tuple(f[1] for f in value)

            s += '    {}: {},\n'.format(name, value)

        s += ')'
        return s


def get_cards(stream=SndPcmStream.PLAYBACK):
    if stream not in SndPcmStream:
        raise Exception("Unknown stream type: {}".format(stream))

    cards = []
    c_card = c_int(-1)
    c_dev = c_int(-1)
    c_dir = c_int(0)
    c_min = c_uint()
    c_max = c_uint()
    c_min_long = c_ulong()
    c_max_long = c_ulong()
    c_handle_p = c_void_p()
    c_pcm_p = c_void_p()
    c_info_p = c_void_p()
    c_pcminfo_p = c_void_p()
    c_fmask_p = c_void_p()
    c_params_p = c_void_p()

    s_stream = 'playback' if stream == SndPcmStream.PLAYBACK else 'capture'

    # card enumeration
    while True:
        _lib.snd_card_next(byref(c_card))
        if c_card.value < 0:
            log.debug("End of card enumeration list reached.")
            break

        hwdev = "hw:{}".format(c_card.value)
        b_hwdev = create_string_buffer(hwdev.encode())

        err = _lib.snd_ctl_open(byref(c_handle_p), b_hwdev, c_card)
        if err < 0:
            _lib.snd_ctl_close(c_handle_p)
            continue

        check_call(_lib.snd_ctl_card_info_malloc, (byref(c_info_p),),
                   "Could not allocate memory for snd_ctl_card_info_t.")
        _lib.snd_ctl_card_info(c_handle_p, c_info_p)

        devices = []
        card = AlsaCard(
            cardno=c_card.value,
            id=_lib.snd_ctl_card_info_get_id(c_info_p).decode(),
            name=_lib.snd_ctl_card_info_get_name(c_info_p).decode(),
            devices=devices
        )
        log.debug('Discovered card #%i "%s" ("%s").', card.cardno, card.id, card.name)
        cards.append(card)

        # device enumeration
        while True:
            _lib.snd_ctl_pcm_next_device(c_handle_p, byref(c_dev))
            if c_dev.value < 0:
                log.debug("End of device enumeration list reached.")
                break

            check_call(_lib.snd_pcm_info_malloc, (byref(c_pcminfo_p),),
                       "Could not allocate memory for snd_pcm_info_t.")
            _lib.snd_pcm_info_set_device(c_pcminfo_p, c_dev)
            _lib.snd_pcm_info_set_subdevice(c_pcminfo_p, 0)
            _lib.snd_pcm_info_set_stream(c_pcminfo_p, c_int(stream))

            err = _lib.snd_ctl_pcm_info(c_handle_p, c_pcminfo_p)
            if err < 0:
                errmsg = _lib.snd_strerror(err).decode('utf-8')
                log.debug("Could not get info for PCM %s device #%i. %s",
                          s_stream, c_dev.value, errmsg)
                continue

            device_id = bytes.decode(_lib.snd_pcm_info_get_id(c_pcminfo_p))
            device_name = bytes.decode(_lib.snd_pcm_info_get_name(c_pcminfo_p))
            log.debug('Discovered %s device #%i "%s" ("%s").', s_stream, c_dev.value, device_id,
                      device_name)

            # count subdevices
            nsubd = _lib.snd_pcm_info_get_subdevices_count(c_pcminfo_p)
            log.debug("Device has %i subdevice(s).", nsubd)

            subdevices = []
            # open sound device
            hwdev = "hw:{},{}".format(card.id, c_dev.value)
            b_hwdev = create_string_buffer(hwdev.encode('ascii'))
            buffer_sizes = periods = channels = rates = formats = None

            try:
                check_call(_lib.snd_pcm_open,
                           (byref(c_pcm_p), b_hwdev, c_int(stream), SND_PCM_NONBLOCK),
                           "Could not open PCM {stream} device '{dev}'.",
                           stream=s_stream, dev=hwdev)
                check_call(_lib.snd_pcm_nonblock, (c_pcm_p, 1),
                           "Nonblock setting error: ")
            except LibAsoundError as exc:
                log.warning(str(exc))
            else:
                try:
                    # Get hardware parameter space
                    check_call(_lib.snd_pcm_hw_params_malloc, (byref(c_params_p),),
                               "Could not allocate memory for snd_pcm_hw_params_t.")
                    check_call(_lib.snd_pcm_hw_params_any, (c_pcm_p, c_params_p),
                               "Could not get params for {stream} device '{dev}'.",
                               stream=s_stream, dev=hwdev)

                    # Get supported channel counts
                    check_call(_lib.snd_pcm_hw_params_get_channels_min, (c_params_p, byref(c_min)),
                               "Could not get minimum channels count.")

                    check_call(_lib.snd_pcm_hw_params_get_channels_max, (c_params_p, byref(c_max)),
                               "Could not get maximum channels count.")

                    log.debug("Min/max channels: %i, %i", c_min.value, c_max.value)
                    channels = tuple(
                        ch for ch in range(c_min.value, c_max.value + 1)
                        if _lib.snd_pcm_hw_params_test_channels(c_pcm_p, c_params_p, ch) == 0
                    )

                    # Get supported sample rates
                    check_call(_lib.snd_pcm_hw_params_get_rate_min,
                               (c_params_p, byref(c_min), byref(c_dir)),
                               "Could not get minimum sample rate.")

                    check_call(_lib.snd_pcm_hw_params_get_rate_max,
                               (c_params_p, byref(c_max), byref(c_dir)),
                               "Could not get maximum sample rate.")

                    log.debug("Min/max sample rate: %i, %i", c_min.value, c_max.value)
                    rates = tuple(
                        rate for rate in PCM_RATES
                        if c_min.value <= rate <= c_max.value and
                        _lib.snd_pcm_hw_params_test_rate(c_pcm_p, c_params_p, rate, 0) == 0
                    )

                    # Get supported sample formats
                    check_call(_lib.snd_pcm_format_mask_malloc, (byref(c_fmask_p),),
                               "Could not allocate memory for snd_pcm_format_mask_t.")
                    try:
                        check_call(_lib.snd_pcm_hw_params_get_format_mask, (c_params_p, c_fmask_p),
                                   "Could not get sample formats.")

                    except LibAsoundError as exc:
                        log.error(str(exc))
                    else:
                        formats = tuple(decode_format_mask(c_fmask_p))
                        log.debug("Sample formats: %s", ",".join(f[1] for f in formats))
                    finally:
                        _lib.snd_pcm_format_mask_free(c_fmask_p)

                    # Get supported period times
                    check_call(_lib.snd_pcm_hw_params_get_periods_min,
                               (c_params_p, byref(c_min), byref(c_dir)),
                               "Could not get minimum periods count.")

                    check_call(_lib.snd_pcm_hw_params_get_periods_max,
                               (c_params_p, byref(c_max), byref(c_dir)),
                               "Could not get minimum periods count.")

                    log.debug("Min/max periods count: (%i, %i)", c_min.value, c_max.value)
                    periods = (c_min.value, c_max.value)

                    # Get supported buffer sizes
                    check_call(_lib.snd_pcm_hw_params_get_buffer_size_min,
                               (c_params_p, byref(c_min_long)),
                               "Could not get minimum buffer time.")

                    check_call(_lib.snd_pcm_hw_params_get_buffer_size_max,
                               (c_params_p, byref(c_max_long)),
                               "Could not get minimum buffer time.")

                    log.debug("Min/max buffer time: (%i, %i) us", c_min_long.value,
                              c_max_long.value)
                    buffer_sizes = tuple(
                        size for size in PCM_BUFFER_SIZES
                        if c_min_long.value <= size <= c_max_long.value and
                        _lib.snd_pcm_hw_params_test_buffer_size(c_pcm_p, c_params_p, size) == 0
                    )

                    # List subdevices
                    for subd in range(0, nsubd):
                        _lib.snd_pcm_info_set_subdevice(c_pcminfo_p, c_int(subd))
                        sub_name = _lib.snd_pcm_info_get_subdevice_name(c_pcminfo_p).decode()
                        log.debug('Discovered subdevice: "%s"', sub_name)
                        subdevices.append(sub_name)
                except LibAsoundError as exc:
                    log.warning(exc)
                finally:
                    _lib.snd_pcm_close(c_pcm_p)
                    _lib.snd_pcm_hw_params_free(c_params_p)
                    _lib.snd_pcm_info_free(c_pcminfo_p)

            devices.append(
                AlsaDevice(
                    devno=c_dev.value,
                    id=device_id,
                    name=device_name,
                    stream=stream,
                    buffer_sizes=buffer_sizes,
                    periods=periods,
                    channels=channels,
                    rates=rates,
                    formats=formats,
                    subdevices=subdevices
                )
            )

        _lib.snd_ctl_close(c_handle_p)
        _lib.snd_ctl_card_info_free(c_info_p)

    return cards


class AlsaInfo:
    def __init__(self, deferred=True):
        if not deferred:
            _ = self.devices  # noqa

    def _make_device_list(self, cards):
        devs = []
        for card in cards:
            if not card.devices:
                continue

            devs.append('hw:%i' % card.cardno)
            devs.append('hw:%s' % card.id)

            for dev in card.devices:
                devs.append('hw:%i,%i' % (card.cardno, dev.devno))
                devs.append('hw:%s,%i' % (card.id, dev.devno))
                devs.append('hw:%s,%s' % (card.id, dev.id))

        return devs

    @property
    def playback_devices(self):
        cards = getattr(self, '_playback', None)
        if cards is None:
            self._playback = cards = get_cards(stream=SndPcmStream.PLAYBACK)
        return self._make_device_list(cards)

    @property
    def capture_devices(self):
        cards = getattr(self, '_capture', None)
        if cards is None:
            self._capture = cards = get_cards(stream=SndPcmStream.CAPTURE)
        return self._make_device_list(cards)

    @property
    def devices(self):
        devs = set(self.playback_devices)
        return list(devs.union(self.capture_devices))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if '-v' in sys.argv[1:] else logging.INFO,
                        format="[%(name)s] %(levelname)s: %(message)s")

    ai = AlsaInfo()

    if '-r' in sys.argv:
        for card in get_cards(stream=SndPcmStream.CAPTURE):
            print(card)

        for card in ai.capture_devices:
            print(card)

        print("Capture devices")
        print("----------------\n")

    else:
        for card in get_cards(stream=SndPcmStream.PLAYBACK):
            print(card)

        print("Playback devices")
        print("----------------\n")

        for card in ai.playback_devices:
            print(card)
