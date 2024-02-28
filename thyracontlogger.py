# -*- coding: utf-8 -*-

import os, time, argparse, serial
from datetime import datetime, timezone, timedelta
from matplotlib.dates import num2date
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
#%matplotlib qt

from thyracont import ThyracontReader


DEFAULT_COMPORT = 'COM4'
DEFAULT_LOGFILE = 'thyracont-log.txt'
DEFAULT_BAUDRATE = 115200
DEFAULT_INTERVAL = 1

# https://stackoverflow.com/a/39079819
LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


def main():
    parser = argparse.ArgumentParser(
        description="Read, log and plot Thyracont pressure gauge values")
    parser.add_argument('COMPORT', type=str, nargs='?', default=DEFAULT_COMPORT)
    parser.add_argument('LOGFILE', type=str, nargs='?', default=DEFAULT_LOGFILE)
    parser.add_argument('--baudrate', type=int,
                        dest='baudrate', default=DEFAULT_BAUDRATE)
    parser.add_argument('--interval', type=float,
                        dest='interval', default=DEFAULT_INTERVAL)
    args = parser.parse_args()
    
    logabspath = os.path.abspath(os.path.expanduser(args.LOGFILE))

    ser = serial.Serial(args.COMPORT, args.baudrate)
    sensor = ThyracontReader(ser)

    fig = plt.figure()
    plt.xlabel('Time')
    plt.ylabel('Pressure / mbar')
    plt.ylim(1e-5, 1.01e3)
    plt.yscale('log')
    plt.grid()
    plt.xticks(rotation=50)
    line = plt.plot([], [])[0]
    ax = plt.gca()

    timing = []
    pressure = []

    def autoupdate(event):
        ax.set_xlim(timing[0], timing[-1])
        ax.set_ylim(min(pressure)*0.95, max(pressure)*1.1)
    bautoupdate = Button(plt.axes([0.15, 0.8, 0.15, 0.075]), 'Fit view')
    bautoupdate.on_clicked(autoupdate)

    with open(logabspath, 'a+') as file:
        print("Logging to", logabspath)
        while True:
            looptime = time.time()
            t = datetime.now(tz=LOCAL_TIMEZONE)
            p = sensor.read_measurement()

            # Write to logfile
            file.write(f"{t.isoformat()}\t{p:e}\n")
            file.flush()

            # Update plot
            timing.append(t)
            pressure.append(p)
            line.set_data(timing, pressure)

            # update upper xlim if current upper xlim > old data
            low, up = ax.get_xlim()
            if len(timing) <= 2:
                ax.set_xlim(timing[0]-timedelta(seconds=args.interval),
                            timing[-1])
            else:
                if num2date(up) >= timing[-2]:
                    up = timing[-1]
                    ax.set_xlim(num2date(low), timing[-1])

            if p > 10:
                pstr = f"{p:.0f}"
            elif p > 1:
                pstr = f"{p:.2f}"
            else:
                pstr = f"{p:.2e}"
            ax.set_title(f"{args.COMPORT} Pressure: {pstr} mbar\nLog: {logabspath}")
            plt.tight_layout()

            plt.pause(max(0, args.interval - (time.time()-looptime)))
            if not plt.fignum_exists(fig.number):
                break

    sensor.close()


if __name__ == '__main__':
    main()
