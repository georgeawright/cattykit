import panel as pn
from bokeh.models import Span

from cattycam.charts import _line_chart


def test_time_marker_follows_programmatic_slider_changes() -> None:
    time = pn.widgets.EditableIntSlider(start=0, end=2, value=0)
    chart = _line_chart("Test", [(0, 1), (2, 3)], "Value", time, [])
    marker = next(item for item in chart.select(type=Span) if item.line_color == "red")

    time.value = 2

    assert marker.location == 2
