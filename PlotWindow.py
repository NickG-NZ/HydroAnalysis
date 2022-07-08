import matplotlib
matplotlib.use('qt5agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout
import sys


class PlotWindowApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)

    def run(self):
        """
        Call this afer creating all desired PlotWindows (eg. at end of main function)
        """
        sys.exit(self.app.exec_())


class PlotWindow:
    def __init__(self, title="plot window"):
        self.MainWindow = QMainWindow()
        self.MainWindow.__init__()
        self.MainWindow.setWindowTitle(title)
        self.canvases = []
        self.figure_handles = []
        self.toolbar_handles = []
        self.tab_handles = []
        self.tabs = QTabWidget()
        self.MainWindow.setCentralWidget(self.tabs)
        self.MainWindow.resize(1280, 900)
        self.MainWindow.show()

    def add_plot(self, title, figure):
        new_tab = QWidget()
        layout = QVBoxLayout()
        new_tab.setLayout(layout)

        figure.subplots_adjust(left=0.05, right=0.99, bottom=0.05, top=0.91, wspace=0.2, hspace=0.2)
        new_canvas = FigureCanvas(figure)
        new_toolbar = NavigationToolbar(new_canvas, new_tab)

        layout.addWidget(new_canvas)
        layout.addWidget(new_toolbar)
        self.tabs.addTab(new_tab, title)

        self.toolbar_handles.append(new_toolbar)
        self.canvases.append(new_canvas)
        self.figure_handles.append(figure)
        self.tab_handles.append(new_tab)

    def create_and_add_plot(self, x_data, y_data, x_label, y_label, title):
        fig, ax = plt.subplots()
        ax.plot(x_data, y_data)
        ax.set(xlabel=x_label, ylabel=y_label)
        ax.grid(True)
        self.add_plot(title, fig)

    def create_and_add_scatter(self, x_data, y_data, x_label, y_label, title):
        fig, ax = plt.subplots()
        ax.scatter(x_data, y_data)
        ax.set(xlabel=x_label, ylabel=y_label)
        ax.grid(True)
        self.add_plot(title, fig)

