from __future__ import annotations

import html
from pathlib import Path

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


def _codelet_history(database: Path, run_id: int, time: int) -> pn.viewable.Viewable:
    """Render executed codelets as reverse-chronological detail cards."""
    from cattycam.database import codelet_history, codelet_types

    codelets = codelet_history(database, run_id, time)
    if not codelets:
        return pn.pane.Markdown(
            "_No codelets have run yet._", height=430, sizing_mode="stretch_width"
        )
    children_by_parent: dict[str, list[str]] = {}
    for codelet_id, parent_id, *_ in codelets:
        if parent_id is not None:
            children_by_parent.setdefault(parent_id, []).append(codelet_id)
    types = codelet_types(database, run_id)

    def codelet_label(codelet_id: str | None) -> str:
        if codelet_id is None:
            return "—"
        return (
            f"{html.escape(types.get(codelet_id, 'unknown'))} "
            f"{codelet_id.removeprefix('codelet:')}"
        )

    def card_colors(urgency_bin: int | None, result: str | None) -> tuple[str, str]:
        """Return a pastel result colour, strengthened for higher urgency bins."""
        lightness = max(72, 98 - min(urgency_bin or 0, 7) * 3.5)
        hue = 0 if result == "fizzle" else 215
        return (
            f"hsl({hue} 65% {lightness}%)",
            f"hsl({hue} 42% {max(42, lightness - 22)}%)",
        )

    cards = "".join(
        "<div style='display:flex; gap:6px; min-height:76px; margin-bottom:8px;'>"
        f"<div style='width:42px; flex:0 0 42px; font-weight:600;'>{run_time}</div>"
        "<div style='box-sizing:border-box; flex:1; border:1px solid #8296b4; "
        f"border-radius:5px; padding:6px; background:{card_colors(urgency_bin, result)[0]}; "
        f"border-color:{card_colors(urgency_bin, result)[1]};'>"
        "<div style='display:flex; justify-content:space-between; font-weight:600;'>"
        f"<span>{html.escape(codelet_type)} {codelet_id.removeprefix('codelet:')}</span>"
        f"<span>{urgency_bin if urgency_bin is not None else ''}</span>"
        "</div><div style='margin-top:4px;'>"
        f"{html.escape(result or '')} {html.escape(fizzle_reason or '')}"
        "</div><div style='margin-top:4px; font-size:0.9em; color:#4c4c4c;'>"
        f"Parent codelet: {codelet_label(parent_id)} · "
        f"Child codelet: {', '.join(codelet_label(child) for child in children_by_parent.get(codelet_id, [])) or '—'}"
        "</div></div></div>"
        for codelet_id, parent_id, run_time, codelet_type, urgency_bin, result, fizzle_reason in codelets
    )
    return pn.pane.HTML(
        cards,
        height=430,
        sizing_mode="stretch_width",
        styles={"overflow-y": "auto"},
    )
