"""
Built-In Devices
================

This example demonstrates some input devices built into AxoPy for testing as
well as other hardware devices. Pass the following options to try out different
devices:

rainbow
    Basic use of an NoiseGenerator to show lots of colorful random data.
bar
    Basic use of an NoiseGenerator to show a bar plot using filtered data.
polar
    Basic use of an NoiseGenerator to show a polar plot using filtered data.
keyboard
    Basic use of a Keyboard to show roughly-timed keyboard inputs.
keystick
    Neat use of a filter to get joystick-like inputs from a keyboard.
emgsim
    A silly EMG simulator that uses smoothed 'wasd' key presses to modulate the
    amplitude of Gaussian noise -- they kinda look like EMG signals!
mouse
    Basic use of a Mouse for velocity input.
trignoemg
    Delsys Trigno system EMG channels. Requires ``pytrigno``.
trignoacc
    Delsys Trigno system ACC channels. Requires ``pytrigno``.
myoemg
    Myo armband EMG channels. Requires ``myo-python`` and ``pydaqs``.
myoimu
    Myo armband IMU channels. Requires ``myo-python`` and ``pydaqs``.
nidaq
    NIDAQ device. Requires ``nidaqmx`` and ``pydaqs``.
blackrock
    Blackrock Neuroport device. Requires ``cbpy`` and ``pydaqs``.
cyberglove
    Cyberglove Systems data glove. Requires ``cyberglove``.
"""

import sys
import argparse
import numpy as np
from axopy.task import Oscilloscope, BarPlotter, PolarPlotter
from axopy.experiment import Experiment
from axopy.daq import NoiseGenerator, RandomWalkGenerator, Keyboard, Mouse
from axopy.pipeline import Pipeline, Callable, Windower, Filter, Ensure2D
from axopy.gui.main import get_qtapp

from axopy.pipeline import Block


def rainbow():
    num_channels = 16
    dev = NoiseGenerator(rate=2000, num_channels=num_channels, read_size=200)
    channel_names = ['Ch ' + str(i) for i in range(1, num_channels+1)]
    run(dev, channel_names=channel_names)


def bar():
    num_channels = 10
    channel_names = ['Ch ' + str(i) for i in range(1, num_channels+1)]
    dev = NoiseGenerator(rate=200, num_channels=num_channels, read_size=20)
    pipeline = Pipeline([
        Windower(100),
        Callable(lambda x: 3 * np.mean(x, axis=1, keepdims=True))])
    Experiment(daq=dev, subject='test').run(BarPlotter(
        pipeline, channel_names=channel_names, group_colors=[[255, 204, 204]],
        yrange=(-0.5, 0.5)))


def polar():
    num_channels = 5
    dev = RandomWalkGenerator(rate=60, num_channels=num_channels,
                              amplitude=0.03, read_size=1)
    # Polar plot can only show non-negative values
    pipeline = Pipeline([
        Callable(lambda x: np.abs(x))])
    Experiment(daq=dev, subject='test').run(PolarPlotter(
        pipeline, color=[0, 128, 255], fill=True, n_circles=10, max_value=5.))


def keyboard():
    keys = list('wasd')
    dev = Keyboard(keys=keys)
    # need a windower to show something interesting in the oscilloscope
    pipeline = Pipeline([Windower(10)])
    run(dev, pipeline, channel_names=keys)


def keystick():
    keys = list('wasd')
    dev = Keyboard(rate=20, keys=keys)
    pipeline = Pipeline([
        # window to average over
        Windower(10),
        # mean along rows
        Callable(lambda x: np.mean(x, axis=1, keepdims=True)),
        # window to show in the oscilloscope
        Windower(60)
    ])
    run(dev, pipeline, channel_names=keys)


def emgsim():
    keys = list('wasd')
    # sampling rate of the simulated EMG data
    fs = 2000
    # update rate of the generated data
    update_rate = 20
    # gain to use in noise generation
    gain = 0.25
    # number of seconds of data the oscilloscope shows
    osc_view_time = 5

    samp_per_input = int(fs / update_rate)

    pipeline = Pipeline([
        # get keyboard inputs of past second
        Windower(update_rate),
        # take mean over last second and apply a gain
        Callable(lambda x: np.mean(x, axis=1, keepdims=True)),
        # generate noise with amplitude of previous output
        Callable(lambda x, k: gain * x * np.random.randn(x.shape[0], k),
                 func_args=(samp_per_input,)),
        # window for pretty display in oscilloscope
        Windower(osc_view_time * update_rate * samp_per_input),
    ])

    dev = Keyboard(rate=update_rate, keys=keys)
    run(dev, pipeline, channel_names=keys)

def trignoemg():
    from pytrigno import TrignoEMG
    n_channels = 16
    dev = TrignoEMG(channels=range(1, n_channels + 1), samples_per_read=200,
                    zero_based=False, units='normalized')
    pipeline = Pipeline([Ensure2D(orientation='row'),
                         Callable(lambda x: 5*x),
                         Windower(20000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels + 1)]
    run(dev, pipeline, channel_names=channel_names)


def trignoacc():
    from pytrigno import TrignoACC
    n_channels = 2
    dev = TrignoACC(channels=range(n_channels), samples_per_read=12,
                    zero_based=True)
    pipeline = Pipeline([Windower(1200)])
    channel_names = ['Acc ' + str(i) + '_' + axis \
                     for i in range(1, n_channels+1) for axis in ['x','y','z']]
    run(dev, pipeline, channel_names=channel_names)


def myoemg():
    import myo
    from pydaqs.myo import MyoEMG
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    n_channels = 8
    dev = MyoEMG(channels=range(n_channels), samples_per_read=20)
    pipeline = Pipeline([Ensure2D(orientation='row'),
                         Callable(lambda x: 0.01*x),
                         Windower(2000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names)


def myoimu():
    import myo
    from pydaqs.myo import MyoIMU
    myo.init(sdk_path=r'C:\Users\nak142\Coding\myo-python\myo-sdk-win-0.9.0')
    dev = MyoIMU(samples_per_read=5)
    pipeline = Pipeline([Windower(500)])
    channel_names = list('wxyz')
    run(dev, pipeline, channel_names=channel_names)


def nidaq():
    from pydaqs.nidaq import Nidaq
    n_channels = 1
    dev = Nidaq(channels=range(n_channels), samples_per_read=200, rate=2000)
    pipeline = Pipeline([Ensure2D(orientation='row'), Windower(20000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names)


def blackrock():
    from pydaqs.blackrock import Blackrock
    n_channels = 1
    app = get_qtapp()
    dev = Blackrock(channels=range(1, n_channels + 1), samples_per_read=100)
    pipeline = Pipeline([Windower(5000)])
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]
    run(dev, pipeline, channel_names=channel_names)


def cyberglove():
    from cyberglove import CyberGlove
    n_df = 18
    dev = CyberGlove(n_df, 'COM3', samples_per_read=1,
                     cal_path=r"C:\Users\nak142\tmp\glove.cal")
    pipeline = Pipeline([Ensure2D('row'), Windower(1000)])
    channel_names = ['DOF ' + str(i) for i in range(1, n_df+1)]
    run(dev, pipeline, channel_names=channel_names)


def mouse():
    dev = Mouse(rate=20)
    pipeline = Pipeline([
        # just for scaling the input since it's in pixels
        Callable(lambda x: x/100),
        # window to show in the oscilloscope
        Windower(40)
    ])
    channel_names = list('xy')
    run(dev, pipeline, channel_names=channel_names)


def run(dev, pipeline=None, **kwargs):
    # run an experiment with just an oscilloscope task
    Experiment(daq=dev, subject='test').run(Oscilloscope(pipeline, **kwargs))


if __name__ == '__main__':
    functions = {
        'rainbow': rainbow,
        'bar': bar,
        'polar': polar,
        'keyboard': keyboard,
        'keystick': keystick,
        'emgsim': emgsim,
        'mouse': mouse,
        'trignoemg': trignoemg,
        'trignoacc': trignoacc,
        'myoemg': myoemg,
        'myoimu': myoimu,
        'nidaq': nidaq,
        'blackrock': blackrock,
        'cyberglove': cyberglove
    }

    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument(
        'function',
        help='Function in the example script to run.')
    args = parser.parse_args()

    if args.function not in functions:
        print("{} isn't a function in the example.".format(args.function))
        sys.exit(-1)
    else:
        functions[args.function]()
