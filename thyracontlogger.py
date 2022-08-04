# -*- coding: utf-8 -*-

import argparse
import serial
import numpy as np
from datetime import datetime, timezone
from matplotlib.dates import num2date
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
#%matplotlib qt

from thyracont import ThyracontReader


DEFAULT_COMPORT = 'COM4'
DEFAULT_BAUDRATE = 115200
DEFAULT_INTERVAL = 1

# https://stackoverflow.com/a/39079819
LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


def main():
    parser = argparse.ArgumentParser(
        description="Read, log and plot Thyracont pressure gauge values")
    parser.add_argument('COMPORT', type=str, nargs='?', default=DEFAULT_COMPORT)
    parser.add_argument('--baudrate', type=int,
                        dest='baudrate', default=DEFAULT_BAUDRATE)
    parser.add_argument('--interval', type=float,
                        dest='interval', default=DEFAULT_INTERVAL)
    args = parser.parse_args()

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
    bautoupdate = Button(plt.axes([0.8, 0.9, 0.2, 0.075]), 'Fit view')
    bautoupdate.on_clicked(autoupdate)

    while True:
        timing.append(datetime.now(tz=LOCAL_TIMEZONE))
        pressure.append(sensor.read_measurement())
        line.set_data(timing, pressure)
        # update upper xlim if current upper xlim > old data
        low, up = ax.get_xlim()
        if len(timing) <= 2:
            ax.set_xlim(timing[0], timing[-1])
        else:
            if num2date(up) >= timing[-2]:
                up = timing[-1]
                ax.set_xlim(num2date(low), timing[-1])
        plt.tight_layout()
        plt.pause(args.interval)
        if not plt.fignum_exists(fig.number):
            break
    
    sensor.close()


if __name__ == '__main__':
    main()
