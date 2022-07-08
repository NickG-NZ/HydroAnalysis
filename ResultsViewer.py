"""
Basic visualization tool for Results
"""
import sys
from PyQt5.QtWidgets import QApplication
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from PlotWindow import PlotWindow


class ResultsViewer:

    def __init__(self, results):
        self._app = QApplication(sys.argv)
        self._results = results
        self._plot_window = PlotWindow("ResultsViewer")

    def compare_channels(self, x_channel, y_channel, sort_by=None):
        """
        Plot the two requested channels against one-another
        Channels should be specified as GroupName.ChannelName

        'sort_by' can be used to specify another channel to group the data points by
                 For instance, if the data contains sweeps of values against foil angle-of-attack,
                 the data can be plotted with a separate line colour for each angle-of-attack
        """
        x_channel_tokens = x_channel.split('.')
        x_group_name = ''.join(x_channel_tokens[:-1])
        x_channel_name = x_channel_tokens[-1]
        x_data = self._results.get_channel_log(x_group_name, x_channel_name)

        y_channel_tokens = y_channel.split('.')
        y_group_name = ''.join(y_channel_tokens[:-1])
        y_channel_name = y_channel_tokens[-1]
        y_data = self._results.get_channel_log(y_group_name, y_channel_name)

        # Create the initial plot
        fig, ax = plt.subplots()
        x_name = x_group_name + "." + x_channel_name
        y_name = y_group_name + "." + y_channel_name
        title = f"{y_name} vs. {x_name}"
        ax.set(xlabel=x_name, ylabel=y_name)

        # Create a separate line on the plot for each unique point in the 'sort_by' group
        if sort_by:
            sort_tokens = sort_by.split('.')
            sort_group = ''.join(sort_tokens[:-1])
            sort_channel = sort_tokens[-1]
            sort_data = self._results.get_channel_log(sort_group, sort_channel)

            unique_points = np.unique(sort_data)
            df = pd.DataFrame.from_dict({'x_data' : x_data, 'y_data': y_data, 'sort_data': sort_data})
            for point in unique_points:
                subset = df.loc[abs(df.sort_data - point) < 1e-8]
                ax.plot(subset.x_data, subset.y_data, label=f"{point:.3f}")
            ax.legend()
            ax.text(0.9 * np.amax(x_data), np.amax(y_data), "Sorted By: " + sort_by)
        else:
            ax.scatter(x_data, y_data)

        self._plot_window.add_plot(title, fig)

    def run(self):
        """
        Call this after all channel comparisons have been initialized
        """
        self._app.exec_()

