from functools import partial
from moon import DateTime, MoonPhase
from parsedatetime import Calendar  # pip install parsedatetime
from pytimeparse.timeparse import timeparse  # pip install pytimeparse
from random import randrange
from time import mktime
import argparse
import httplib


def zero():
    return 0


class FakeFile(object):
    def __init__(self, namespace):
        self.eof = False
        self.start = namespace.start
        self.stop = namespace.stop
        self.step = namespace.step
        self.nanoseconds = partial(randrange, 10**9) \
                           if namespace.jitter else zero

    def read(self, blocksize):
        if self.eof:
            return ''
        moonphase = MoonPhase(self.start)
        result = "moon,phase=%s illumination=%.1f,age=%.1f %d%09d" % (
            moonphase.phase_text.replace(' ', '-'),
            moonphase.illuminated * 100,
            moonphase.age,
            self.start.gmticks(),
            self.nanoseconds()
            )
        self.start += self.step
        self.eof = self.start > self.stop
        return result

def main():
    """Calculate phases of the moon."""

    def mktime(str, _cal = Calendar()):
        return DateTime.mktime(_cal.parse(str)[0])

    def mkdelta(str):
        return DateTime.DateTimeDeltaFromSeconds(timeparse(str))

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('start', nargs='?', type=mktime,
                        default=DateTime.now())
    parser.add_argument('stop', nargs='?', type=mktime,
                        default=None)
    parser.add_argument('--step', nargs='?', type=mkdelta,
                        default=timeparse('1d'))
    parser.add_argument('--jitter', action='store_true')
    args_obj = parser.parse_args(['one year ago', 'now', '--step', '4w'])
    if args_obj.stop is None:
        args_obj.stop = args_obj.start
    data = FakeFile(args_obj)

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
        }
    responses = set()
    datablock = data.read(1024)
    while datablock:
        conn = httplib.HTTPConnection("192.168.32.131", 8086)
        conn.request("POST", "/write?db=mydb", datablock, headers)
        response = conn.getresponse()
        if (response.status, response.reason) not in responses:
            print response.status, response.reason
            responses.add((response.status, response.reason))
        datablock = data.read(1024)

if __name__ == '__main__':
    main()

