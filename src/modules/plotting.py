import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QStyleOption
from PySide6.QtCore import QTimer, Qt, QRectF

import numpy as np
import random

from pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem
from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox
from pyqtgraph.graphicsItems.AxisItem import AxisItem
from PySide6.QtGui import QPainter


class _CustomAxis(pg.AxisItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tick_sign_before = False
        self.tick_sign = ""

        self.angle = 0
        self.x_transform = 0
        self.y_transform = 0

    def set_sign(self, value: str):
        self.tick_sign = value

    def set_sign_before(self, value: bool = True):
        """sets the position of the sign for a the value
        Default: False is after
        """

        self.tick_sign_before = value

    def tickStrings(self, values: list[float], scale: float, spacing: float):

        if self.tick_sign_before:
            return [f"{self.tick_sign}{v:.0f}" for v in values]

        else:
            return [f"{v:.0f}{self.tick_sign}" for v in values]

    def set_angle(self, angle: int):
        self.angle = angle

    def set_transform(self, x, y):
        self.x_transform = x
        self.y_transform = y

    def drawPicture(
        self, p: QPainter, axisSpec: tuple, tickSpecs: list, textSpecs: list
    ):

        print(type(textSpecs))

        # axisSpec: (pen, p1, p2)
        axis_pen, axis_p1, axis_p2 = axisSpec
        p.setPen(axis_pen)
        p.drawLine(axis_p1, axis_p2)  # <-- draw baseline

        # Draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)

        # Draw rotated labels
        p.setPen(self.pen())
        for rect, flags, text in textSpecs:
            p.save()
            # move to center of label rect
            p.translate(rect.center().x(), rect.center().y())
            p.translate(self.x_transform, self.y_transform)

            p.rotate(self.angle)
            # draw text roughly centered
            p.drawText(-rect.width() / 2, rect.height() / 2, text)
            p.restore()


class Plot:

    def __init__(self):

        self._root = pg.PlotWidget()

        self._plot_item: PlotItem = self._get_plot_item()
        self._view_box: ViewBox = self._get_view_box()
        self._legend: pg.LegendItem = self._get_created_legend()

        self._curves: list[PlotDataItem] = []

        self._setup_legend()

        self.add_curve()

        self.x_axis = _XAxes(self)
        self.y_axis = _YAxes(self)

        self.data = _Data(self)

        self._init_settings()

        self.set_title("None")

        self.set_plot_color("#ffffff")

    def add_curve(self):

        new_curve: PlotDataItem = self._plot_item.plot()

        self._curves.append(new_curve)

        self._legend_add_value()

    def _get_plot_item(self):

        plot_item = self._root.getPlotItem()

        if not isinstance(plot_item, PlotItem):
            raise TypeError

        return plot_item

    def _get_view_box(self):

        view_box = self._get_plot_item().getViewBox()

        return view_box

    def _get_created_legend(self):

        legend = self._plot_item.addLegend()

        return legend

    def _setup_legend(self):

        self._legend.mouseDragEvent = (
            lambda *args, **kwargs: None
        )  # Disables drag event

        self._legend.setOffset(0)

    def _legend_add_value(self):  ###################

        self._legend.addItem(self._curves[-1], "Test")

    def _init_settings(self):
        pg.setConfigOptions(antialias=True)

        self._plot_item.setMenuEnabled(False)
        self._plot_item.hideButtons()

        self._view_box.setMouseEnabled(False, False)

    def set_title(self, title: str):

        self._plot_item.setTitle(title)

    def set_plot_color(self, color: str, curve: int = 0):

        self._curves[curve].setPen(color)

    def widget(self):
        return self._root

    def show(self):

        self._root.show()


class _Axes:

    def __init__(self, root: Plot) -> None:

        self._root = root
        self._setup()

    def _setup(self):  # implement
        self._axis: _CustomAxis

    def set_max_range(self, max_range: int | float | None = None):  # implement
        pass

    def invert(self, x: bool):  # implement
        pass

    def set_label(self, label: str):

        self._axis.setLabel(label)

    def set_tick_lable_angle(self, angle):
        self._axis.set_angle(angle)

    def set_tick_lable_transform(self, x: int, y: int):
        self._axis.set_transform(x, y)

    def set_sign(self, sign: str):

        self._axis.set_sign(sign)

    def set_ticks(self):

        ticks: list[tuple[float, str]] = [(i, f"{i}:00") for i in range(24)]

        self._axis.setTicks([ticks])


class _XAxes(_Axes):

    def _setup(self):

        self._axis = _CustomAxis(orientation="bottom")
        self._root._plot_item.setAxisItems({"bottom": self._axis})

        self.set_max_range()
        self.set_label("X-Axis")

    def set_max_range(self, max_range: int | float | None = None):
        if max_range is None:
            self._root._view_box.enableAutoRange(axis="x")

        else:
            self._root._view_box.setXRange(
                0, max_range, 0
            )  # padding 0 so point 0 is at exact edge

            # self._root._max_x = int(self._root._view_box.viewRange()[0][1])

    def invert(self, x: bool):

        self._root._view_box.invertX(x)


class _YAxes(_Axes):

    def _setup(self):

        self._axis = _CustomAxis(orientation="left")
        self._root._plot_item.setAxisItems({"left": self._axis})

        self.set_max_range()
        self.set_label("Y-Axis")

    def set_max_range(self, max_range: int | float | None = None):
        if max_range is None:
            self._root._view_box.enableAutoRange(axis="y")
        else:
            self._root._view_box.setYRange(max_range, 0)

    def invert(self, x: bool):

        self._root._view_box.invertY(x)


class _Data:

    def __init__(self, root: Plot) -> None:

        self._root = root
        self._setup_data()
        self._setup_frame_timer()

    def _setup_data(self):
        self._max_data_points = 100

        self._data: dict[int, list] = {}
        """{curve: [data]}"""

    def _setup_frame_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_frame)
        self._loop_count = 0
        self._cur_curve = 0

        self._animation_frames = 100
        self._frame_time = 10

    def set_max_data_points(self, x: int | None = None):
        """Sets total values that can be stored.
        If `add_data_point` oldest will be deleated.

        None = inf
        """

        self._max_data_points = x

    def add_data_point(self, value: int | float, curve: int = 0):
        """Adds a data point to a specified curve"""

        self._data[curve].insert(0, value)

        if self._max_data_points is not None:

            self._root.x_axis.set_max_range(self._max_data_points)

            if len(self._data[curve]) > self._max_data_points:
                self._data[curve].pop()

        self._root._curves[curve].setData(self._data[curve])

    def set_data(self, data: list, curve: int = 0):
        """Sets the data of specified curve"""

        self._data[curve] = data

        self._max_data_points = len(self._data[curve])
        self._root.x_axis.set_max_range(self._max_data_points)

        self._root._curves[curve].setData(self._data[curve])

    def interpolate_data(self, data: list, curve: int = 0):
        """Smooth animation from old data to new data."""

        self._start_data = np.array(self._data[curve])
        self._new_data = np.array(data)

        self._cur_curve = curve
        self._loop_count = 0

        # Set new data before frames, so current data is acurate
        self._data[self._cur_curve] = self._new_data.tolist()

        self._timer.start(self._frame_time)

    def _update_frame(self):

        if self._loop_count >= self._animation_frames:
            self._timer.stop()

            # Makes sure final frame is acurate
            self._root._curves[self._cur_curve].setData(self._data[self._cur_curve])
            return

        self._loop_count += 1

        time = self._loop_count / self._animation_frames

        # Interpolation slows as it reaches the end
        time_eased = time * (2.0 - time)

        # Interpolate over frames
        current_frame_data = (
            1.0 - time_eased
        ) * self._start_data + time_eased * self._new_data

        self._root._curves[self._cur_curve].setData(current_frame_data)

    def clear(self):
        """Deleats all data"""

        self._data.clear()


def main():
    app = QApplication([])

    window = Plot()

    window.y_axis.set_max_range(100)

    window.y_axis.set_sign("°F")
    window.x_axis.set_sign("min")

    window.x_axis.set_ticks()

    window.x_axis.set_tick_lable_angle(-45)
    window.x_axis.set_tick_lable_transform(-10, 5)

    data = [random.randint(0, 100) for _ in range(24)]
    # data2 = [random.randint(0, 100) for _ in range(32)]

    # data = [40, 44, 52, 60, 52, 48, 46]
    # data2 = [42, 56, 70, 80, 99, 43, 13]

    window.data.set_data(data)

    window.show()

    app.exec()


if __name__ == "__main__":
    main()
