import re
from threading import Thread, Event
from time import sleep

import pexpect
from PyQt5.QtCore import QObject, pyqtSignal

from alsainfo import SndPcmStream, get_cards


class Device:
    def __init__(self, card, card_name, card_detail, dev, dev_name,
                 dev_detail, record=False):
        self.card = card
        self.card_name = card_name
        self.card_detail = card_detail
        self.dev = dev
        self.dev_name = dev_name
        self.dev_detail = dev_detail
        self._in = record
        self.audio_proc = AudioProcess(self.cmdName, self.card_detail, self.hw)

    @classmethod
    def record(cls, *args, **kwargs):
        kwargs["record"] = True
        return cls(*args, **kwargs)

    def __str__(self):
        return self.detail

    @property
    def cmdName(self):
        # TODO: support alternative bridges, i.e. zita-ajbridge
        return "alsa_{}".format("in" if self._in else "out")

    def match_name(self, cname, dname):
        return self.card_name == cname and self.dev_name == dname

    @property
    def hw(self):
        return "hw:{},{}".format(self.card, self.dev)

    @property
    def name(self):
        return "{}: {}".format(self.card_name, self.dev_name)

    @property
    def detail(self):
        return "{}: {}".format(self.card_detail, self.dev_detail)


class DeviceList:
    def __init__(self, record=False):
        self._record = record
        self.update()

    def update(self):
        factory = Device.record if self._record else Device
        cards = get_cards(SndPcmStream.CAPTURE if self._record else SndPcmStream.PLAYBACK, capabilities=False)
        self.list = {}

        for card in cards:
            for dev in card.devices:
                self.list[dev.name] = factory(card.cardno, card.id, card.name, dev.devno, dev.id, dev.name)

    def __getitem__(self, item):
        return self.list.__getitem__(item)

    def __iter__(self):
        return self.list.values().__iter__()

    def byHW(self, card, dev):
        for d in self:
            if card == d.card and dev == d.dev:
                return d
        raise ValueError('Device hw:{},{} not in list'.format(card, dev))

    def byName(self, cname, dname):
        for d in self:
            if d.match_name(cname, dname):
                return d
        raise ValueError('Device [{}:{}] not in list'.format(cname, dname))

    def stop(self):
        for d in self.list.values():
            d.audio_proc.setActive(False)


class AudioProcess(QObject):
    NOT_EMPTY = re.compile(r"\S+", re.MULTILINE)
    CMD_PAT = '{cmd} -j "{name}" -d {hw}'
    # emitted when led-values change
    delay_changed = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(self, cmd, name, hw, parent=None):
        super(AudioProcess, self).__init__(parent)

        self._command = AudioProcess.CMD_PAT.format(cmd=cmd, name=name, hw=hw)
        self._process = pexpect.spawn('ls')
        self._active = Event()
        self._fails = 0

        process_reader = Thread(name="read daemon",
                                target=self.process_reader)
        process_reader.setDaemon(True)
        process_reader.start()

    def setActive(self, active):
        if active:
            self._active.set()
        else:
            self._active.clear()
            self._fails = 0
            self.stop()

    def start(self):
        try:
            started = self._process.isalive()
        except:
            started = False
        if not started:
            print("starting " + self._command)
            self._process = pexpect.spawn(self._command)

    def process_reader(self):
        while True:
            self._active.wait()
            self.start()
            try:
                r = self._process.expect([r"delay \= (\d+)", ".+"])
                if r == 0:
                    delay = self._process.match.groups()[0].decode()
                    self.delay_changed.emit(delay)
                else:
                    msg = self._process.match.string.decode()
                    if AudioProcess.NOT_EMPTY.search(msg):
                        self.log_message.emit(msg)

                if not self._process.isalive():
                    raise pexpect.EOF('Process died after start.')

                self._fails = 0
            except:
                self._fails += 1
                print("{} failed ({}) :(".format(self._command, self._fails))

            sleep(self.sleepTime)

    @property
    def sleepTime(self):
        ts = [0.1] * 3 + [1] * 3 + [5] * 3 + [20] * 2
        try:
            return ts[self._fails]
        except:
            return 60

    def stop(self):
        try:
            self._process.terminate(force=True)
            print("stopped " + self._command)
        except:
            pass

    def restart(self):
        self.stop()
        self.start()

    def isRunning(self):
        return self._process.isalive()
