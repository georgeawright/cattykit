from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import urlencode

import panel as pn

from .canvases import SlipnetCanvas, WorkspaceCanvas


def _coderack_badges(database: Path, run_id: int, time: int) -> pn.Column:
    """Render active codelets as urgency-bin rows of compact type badges."""
    from cattycam.database import coderack_codelets

    codelets = coderack_codelets(database, run_id, time)
    if not codelets:
        return pn.pane.Markdown(
            "_No codelets on the coderack._", height=390, sizing_mode="stretch_width"
        )
    rows: dict[int, list[str]] = {}
    for urgency_bin, codelet_type, codelet_id in codelets:
        rows.setdefault(urgency_bin, []).append(
            f"{codelet_type} {codelet_id.removeprefix('codelet:')}"
        )
    bin_rows = []
    for urgency_bin, codelet_types in rows.items():
        lightness = max(72, 98 - min(urgency_bin, 7) * 3.5)
        if bin_rows:
            bin_rows.append(
                pn.pane.HTML(
                    "<hr style='width:100%; margin:6px 0; border:0; "
                    "border-top:1px solid #d0d0d0;'>",
                    sizing_mode="stretch_width",
                )
            )
        bin_rows.append(
            pn.Row(
                pn.pane.Markdown(str(urgency_bin), width=55),
                pn.FlexBox(
                    *[
                        pn.pane.HTML(
                            f'<span style="display:inline-block; padding:3px 7px; '
                            f"border-radius:10px; background:hsl(265 55% {lightness}%); "
                            f'border:1px solid hsl(265 35% {max(42, lightness - 22)}%);">'
                            f"{html.escape(codelet_type)}</span>"
                        )
                        for codelet_type in codelet_types
                    ],
                    flex_wrap="wrap",
                    sizing_mode="stretch_width",
                ),
                sizing_mode="stretch_width",
            )
        )
    return pn.Column(
        pn.Row(pn.pane.Markdown("**Urgency**", width=55)),
        *bin_rows,
        height=390,
        scroll=True,
        sizing_mode="stretch_width",
    )


class CoderackView:
    """Keep coderack rows alive while the selected time changes.

    Replacing the output of a bound function makes Panel remove and recreate the
    complete component.  Keeping the rows here lets a playback tick change only
    the urgency bins whose codelets changed.
    """

    def __init__(self, database: Path, run_id: int, time: int) -> None:
        self.database = database
        self.run_id = run_id
        self._rows: dict[int, pn.Row] = {}
        self._codelets: dict[int, list[str]] = {}
        self._bin_rows = pn.Column(sizing_mode="stretch_width")
        self._header = pn.Row(pn.pane.Markdown("**Urgency**", width=55))
        self._empty = pn.pane.Markdown(
            "_No codelets on the coderack._", sizing_mode="stretch_width"
        )
        self.view = pn.Column(
            self._header,
            self._empty,
            self._bin_rows,
            height=390,
            scroll=True,
            sizing_mode="stretch_width",
        )
        self.update(time)

    def _codelets_at(self, time: int) -> dict[int, list[str]]:
        from cattycam.database import coderack_codelets

        codelets: dict[int, list[str]] = {}
        for urgency_bin, codelet_type, codelet_id in coderack_codelets(
            self.database, self.run_id, time
        ):
            codelets.setdefault(urgency_bin, []).append(
                f"{codelet_type} {codelet_id.removeprefix('codelet:')}"
            )
        return codelets

    def _row(self, urgency_bin: int, codelet_types: list[str]) -> pn.Row:
        lightness = max(72, 98 - min(urgency_bin, 7) * 3.5)
        return pn.Row(
            pn.pane.Markdown(str(urgency_bin), width=55),
            pn.FlexBox(
                *[
                    pn.pane.HTML(
                        f'<span style="display:inline-block; padding:3px 7px; '
                        f"border-radius:10px; background:hsl(265 55% {lightness}%); "
                        f'border:1px solid hsl(265 35% {max(42, lightness - 22)}%);">'
                        f"{html.escape(codelet_type)}</span>"
                    )
                    for codelet_type in codelet_types
                ],
                flex_wrap="wrap",
                sizing_mode="stretch_width",
            ),
            sizing_mode="stretch_width",
        )

    def update(self, time: int) -> None:
        codelets = self._codelets_at(time)
        for urgency_bin, codelet_types in codelets.items():
            if self._codelets.get(urgency_bin) != codelet_types:
                self._rows[urgency_bin] = self._row(urgency_bin, codelet_types)
        for urgency_bin in set(self._rows) - set(codelets):
            del self._rows[urgency_bin]
        self._codelets = codelets
        # Panel retains unchanged Row models when only their ordering changes.
        bins = sorted(self._rows, reverse=True)
        for index, urgency_bin in enumerate(bins):
            self._rows[urgency_bin].styles = (
                {}
                if index == 0
                else {
                    "border-top": "1px solid #d0d0d0",
                    "margin-top": "6px",
                    "padding-top": "6px",
                }
            )
        self._bin_rows.objects = [self._rows[bin] for bin in bins]
        self._header.visible = bool(codelets)
        self._bin_rows.visible = bool(codelets)
        self._empty.visible = not codelets


class CodeletHistoryView:
    """Incrementally prepend codelet cards during forward playback."""

    def __init__(self, database: Path, run_id: int, time: int) -> None:
        self.database = database
        self.run_id = run_id
        self._time: int | None = None
        self._card_ids: list[str] = []
        self._cards = pn.Column(sizing_mode="stretch_width")
        self._empty = pn.pane.Markdown(
            "_No codelets have run yet._", sizing_mode="stretch_width"
        )
        self.view = pn.Column(
            self._empty,
            self._cards,
            height=430,
            scroll=True,
            sizing_mode="stretch_width",
        )
        self.update(time)

    def update(self, time: int, *, force: bool = False) -> None:
        cards = _codelet_history_cards(self.database, self.run_id, time)
        card_ids = [codelet_id for codelet_id, _ in cards]
        new_card_count = len(card_ids) - len(self._card_ids)
        if (
            not force
            and self._time is not None
            and time > self._time
            and new_card_count >= 0
            and card_ids[new_card_count:] == self._card_ids
        ):
            # Playback retains every existing card and prepends its whole batch.
            if new_card_count:
                self._cards.objects = [
                    pn.pane.HTML(card, sizing_mode="stretch_width")
                    for _, card in cards[:new_card_count]
                ] + self._cards.objects
        elif force or card_ids != self._card_ids:
            # Slider jumps and backwards navigation need a different history.
            self._cards.objects = [
                pn.pane.HTML(card, sizing_mode="stretch_width") for _, card in cards
            ]
        self._empty.visible = not card_ids
        self._card_ids = card_ids
        self._time = time


def _workspace_canvas(database: Path, run_id: int, time: int) -> WorkspaceCanvas:
    """Render the workspace state for the selected run and codelet time."""
    from cattycam.database import workspace_snapshot

    return WorkspaceCanvas(
        snapshot=workspace_snapshot(database, run_id, time), sizing_mode="stretch_width"
    )


def _slipnet_canvas(database: Path, run_id: int, time: int) -> SlipnetCanvas:
    """Render the Slipnet state for the selected run and codelet time."""
    from cattycam.database import slipnet_snapshot

    return SlipnetCanvas(
        snapshot=slipnet_snapshot(database, run_id, time), sizing_mode="stretch_width"
    )


def _slipnet_activation_list(database: Path, run_id: int, time: int) -> pn.Column:
    """Render the Slipnet's nodes ordered by activation beside its graph."""
    from cattycam.database import slipnet_snapshot

    nodes = sorted(
        slipnet_snapshot(database, run_id, time)["nodes"],
        key=lambda node: (-float(node["activation"]), node["name"]),
    )
    rows = "".join(
        "<tr><td>"
        f"{html.escape(node['name'])}</td><td>{float(node['activation']):.2f}</td></tr>"
        for node in nodes
    )
    return pn.Column(
        "#### Activation",
        pn.pane.HTML(
            "<table style='width:100%; font-size:12px'><tbody>"
            f"{rows}</tbody></table>",
            sizing_mode="stretch_width",
        ),
        width=210,
        height=430,
        scroll=True,
    )


def _codelet_history_cards(database: Path, run_id: int, time: int) -> list[tuple[str, str]]:
    """Return executed-codelet card markup, newest first."""
    from cattycam.database import (
        codelet_arguments,
        codelet_children,
        codelet_history,
        codelet_run_times,
        codelet_step_value_reprs,
        codelet_steps,
        codelet_types,
    )

    codelets = codelet_history(database, run_id, time)
    if not codelets:
        return []
    children_by_parent = codelet_children(database, run_id)
    types = codelet_types(database, run_id)
    run_times = codelet_run_times(database, run_id)
    arguments_by_codelet = codelet_arguments(database, run_id)
    steps_by_codelet = codelet_steps(database, run_id, time)
    step_value_reprs = codelet_step_value_reprs(database, run_id)

    def codelet_label(codelet_id: str | None) -> str:
        if codelet_id is None:
            return "—"
        label = (
            f"{html.escape(types.get(codelet_id, 'unknown'))} "
            f"{codelet_id.removeprefix('codelet:')}"
        )
        if codelet_id not in run_times:
            return label
        return (
            f'<a href="?{urlencode({"run_id": run_id, "time": run_times[codelet_id]})}">'
            f"{label}</a>"
        )

    def card_colors(urgency_bin: int | None, result: str | None) -> tuple[str, str]:
        """Return a pastel result colour, strengthened for higher urgency bins."""
        lightness = max(72, 98 - min(urgency_bin or 0, 7) * 3.5)
        hue = 0 if result == "fizzle" else 215
        return (
            f"hsl({hue} 65% {lightness}%)",
            f"hsl({hue} 42% {max(42, lightness - 22)}%)",
        )

    def duration_label(time_taken: int | None, result: str | None) -> str:
        outcome = "fizzled" if result == "fizzle" else "finished"
        return f"{outcome} after {time_taken / 1_000_000:.3f} milliseconds processing"

    def value_repr(value: object) -> str:
        if isinstance(value, str):
            if value.startswith("slipnode:"):
                return value.removeprefix("slipnode:").upper()
            return step_value_reprs.get(value, value)
        if isinstance(value, list):
            return repr([value_repr(item) for item in value])
        return repr(value)

    def value_html(value: object) -> str:
        """Render workspace-object references as links to their detail pages."""
        if isinstance(value, str) and value in step_value_reprs:
            return (
                f'<a href="?{urlencode({"run_id": run_id, "object_id": value})}">'
                f"{html.escape(value_repr(value))}</a>"
            )
        if isinstance(value, list):
            return "[" + ", ".join(value_html(item) for item in value) + "]"
        return html.escape(value_repr(value))

    def attributes_html(attributes: list[tuple[str, object]]) -> str:
        if not attributes:
            return "<div>—</div>"
        return "".join(
            "<div>"
            f"{html.escape(attribute)}: "
            f"{value_html(value)}"
            "</div>"
            for attribute, value in attributes
        )

    return [
        (codelet_id,
        "<div style='display:flex; gap:6px; min-height:76px; margin-bottom:8px;'>"
        f"<div style='width:42px; flex:0 0 42px; font-weight:600;'>{run_time}</div>"
        "<div style='box-sizing:border-box; flex:1; border:1px solid #8296b4; "
        f"border-radius:5px; padding:6px; background:{card_colors(urgency_bin, result)[0]}; "
        f"border-color:{card_colors(urgency_bin, result)[1]};'>"
        "<div style='display:flex; justify-content:space-between; font-weight:600;'>"
        f"<span>{html.escape(codelet_type)} {codelet_id.removeprefix('codelet:')}</span>"
        f"<span>{urgency_bin if urgency_bin is not None else ''}</span>"
        "</div><div style='margin-top:4px; font-size:0.9em; color:#4c4c4c;'>"
        f"Parent codelet: {codelet_label(parent_id)} · "
        f"Child codelet: {', '.join(codelet_label(child) for child in children_by_parent.get(codelet_id, [])) or '—'}"
        "</div><div style='margin-top:4px; font-size:0.9em;'>"
        "<div style='font-weight:600;'>Arguments</div>"
        f"{attributes_html(arguments_by_codelet.get(codelet_id, []))}"
        "<div style='font-weight:600; margin-top:4px;'>Run</div>"
        f"{attributes_html(steps_by_codelet.get(codelet_id, []))}"
        f"{html.escape(fizzle_reason) if result == 'fizzle' and fizzle_reason else ''}"
        "</div><div style='margin-top:4px;'>"
        f"{duration_label(time_taken, result)}"
        "</div></div></div>"
        )
        for codelet_id, parent_id, run_time, codelet_type, urgency_bin, time_taken, result, fizzle_reason in codelets
    ]


def _codelet_history(database: Path, run_id: int, time: int) -> pn.viewable.Viewable:
    """Render executed codelets as reverse-chronological detail cards."""
    cards = _codelet_history_cards(database, run_id, time)
    if not cards:
        return pn.pane.Markdown(
            "_No codelets have run yet._", height=430, sizing_mode="stretch_width"
        )
    return pn.pane.HTML(
        "".join(card for _, card in cards),
        height=430,
        sizing_mode="stretch_width",
        styles={"overflow-y": "auto"},
    )
