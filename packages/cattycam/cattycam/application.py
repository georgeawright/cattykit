from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import panel as pn

from .canvases import BrowserHistoryBridge
from .charts import _object_attribute_charts, _run_overview
from .details import (
    _codelet_history,
    _coderack_badges,
    _slipnet_activation_list,
    _slipnet_canvas,
    _workspace_canvas,
)
from .views import _problem_overview, _run_group_table


def create_app(database: str | Path) -> pn.Column:
    """Create a run picker which opens a tabbed, run-specific database view."""
    from cattycam.database import (
        run_overview_series,
        table_names,
        table_rows,
    )

    database_path = Path(database)
    if not database_path.is_file():
        return pn.Column(
            "# Cattycam",
            pn.pane.Alert(f"Database not found: {database_path}", alert_type="danger"),
        )

    tables = table_names(database_path)
    if "runs" not in tables:
        return pn.Column(
            "# Cattycam",
            pn.pane.Alert(
                "This database has no Cattycam runs table. Generate a new history "
                "database with the current SQLiteLogger.",
                alert_type="warning",
            ),
        )
    content = pn.Column(sizing_mode="stretch_width")
    active_run = pn.widgets.IntInput(value=0, visible=False)
    active_object = pn.widgets.TextInput(value="", visible=False)
    if pn.state.location:
        # This is a standalone Panel application. Reloading after a URL change
        # gives browser Back/Forward a fresh session whose selected run is read
        # from the query string.
        pn.state.location.reload = True
        pn.state.location.sync(active_run, {"value": "run_id"})
        pn.state.location.sync(active_object, {"value": "object_id"})

    def show_run(run_id: int) -> None:
        columns, rows = table_rows(database_path, "runs", run_id=run_id)
        if not rows:
            content.objects = [
                pn.pane.Alert(f"Run {run_id} was not found.", alert_type="warning")
            ]
            return
        run = dict(zip(columns, rows[0], strict=True))
        model = run["model"]
        problem = run["problem"]
        solution = run["solution"]
        codelets_run = run["number_of_codelets_run"]
        final_temperature = run["final_temperature"]
        selected_time = pn.widgets.IntInput(
            value=int(codelets_run or 0), visible=False
        )
        if pn.state.location:
            pn.state.location.sync(selected_time, {"value": "time"})
        codelet_time = pn.widgets.EditableIntSlider(
            name="Time",
            start=0,
            end=int(codelets_run or 0),
            value=selected_time.value,
            sizing_mode="stretch_width",
        )
        codelet_time.param.watch(
            lambda event: setattr(selected_time, "value", event.new),
            "value_throttled",
        )
        overview = _run_overview(
            run_overview_series(database_path, run_id), codelet_time
        )
        coderack_panel = pn.bind(
            _coderack_badges,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        codelet_history_panel = pn.bind(
            _codelet_history,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        workspace_panel = pn.bind(
            _workspace_canvas,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        slipnet_panel = pn.bind(
            _slipnet_canvas,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        slipnet_activations = pn.bind(
            _slipnet_activation_list,
            database_path,
            run_id,
            codelet_time.param.value_throttled,
        )
        detail_panels = pn.Row(
            pn.Column(
                "### Coderack",
                coderack_panel,
                "### Codelet history",
                codelet_history_panel,
                sizing_mode="stretch_width",
                styles={"flex": "1"},
            ),
            pn.Column(
                "### Workspace",
                workspace_panel,
                "### Slipnet",
                pn.Row(
                    slipnet_panel,
                    slipnet_activations,
                    sizing_mode="stretch_width",
                ),
                sizing_mode="stretch_width",
                styles={"flex": "2"},
            ),
            sizing_mode="stretch_width",
        )
        problem_and_solution = (
            problem if solution is None else str(problem).replace("?", str(solution))
        )
        content.objects = [
            pn.Row(
                pn.pane.Markdown(
                    f"## Run {run_id} of {model} {problem_and_solution}"
                    f" Codelets run: {codelets_run}"
                    f" final temperature: {final_temperature}"
                )
            ),
            overview,
            codelet_time,
            detail_panels,
        ]

    def show_object(run_id: int, object_id: str) -> None:
        from cattycam.database import (
            codelet_run_times,
            object_display_reprs,
            object_history,
        )

        history = object_history(database_path, run_id, object_id)
        if history is None:
            content.objects = [
                pn.pane.HTML(f'<p><a href="?run_id={run_id}">← Run {run_id}</a></p>'),
                pn.pane.Alert(
                    f"Object {object_id!r} was not found in run {run_id}.",
                    alert_type="warning",
                ),
            ]
            return
        representations = object_display_reprs(database_path, run_id)
        run_times = codelet_run_times(database_path, run_id)
        slipnode_ids = {
            identifier.removeprefix("slipnode:"): identifier
            for identifier in representations
            if identifier.startswith("slipnode:")
        }

        def object_link(item: str) -> str:
            label = representations.get(item, item)
            return (
                f'<a href="?{urlencode({"run_id": run_id, "object_id": item})}">'
                f"{html.escape(label)}</a>"
            )

        def attribute_value_html(attribute: str, value: object) -> str:
            if isinstance(value, str):
                if attribute == "parent_codelet" and value in run_times:
                    label = representations.get(value, value)
                    return (
                        f'<a href="?{urlencode({"run_id": run_id, "time": run_times[value]})}">'
                        f"{html.escape(label)}</a>"
                    )
                target = value if value in representations else slipnode_ids.get(value)
                if target and not target.startswith("codelet:"):
                    return object_link(target)
                if value in representations:
                    return html.escape(representations[value])
                return html.escape(json.dumps(value))
            if isinstance(value, list):
                return "[" + ", ".join(
                    attribute_value_html(attribute, item) for item in value
                ) + "]"
            if isinstance(value, dict):
                return "{" + ", ".join(
                    f"{html.escape(str(key))}: {attribute_value_html(attribute, item)}"
                    for key, item in value.items()
                ) + "}"
            return html.escape(json.dumps(value, sort_keys=True, default=str))

        charts, attributes = _object_attribute_charts(history, attribute_value_html)
        proposed_not_created = (
            history["proposal_time"] is not None
            and history["creation_time"] is None
        )
        def object_links(ids: list[str]) -> pn.pane.HTML:
            items = "".join(
                f"<li>{object_link(item)}</li>"
                for item in ids
            ) or "<li>None</li>"
            return pn.pane.HTML(f"<ul>{items}</ul>", sizing_mode="stretch_width")

        group_sections = []
        if history["group_members"] or history["group_bonds"]:
            group_sections = [
                "### Group members",
                object_links(history["group_members"]),
                "### Group bonds",
                object_links(history["group_bonds"]),
            ]
        mapping_sections = []
        if history["table"] == "correspondences":
            headers = ["ID", "Source facet", "Target facet", "Source descriptor", "Target descriptor", "Label"]
            rows = "".join(
                "<tr>"
                + "".join(
                    f"<td>{html.escape('' if mapping[key] is None else str(mapping[key]))}</td>"
                    for key in (
                        "id",
                        "source_facet",
                        "target_facet",
                        "source_descriptor",
                        "target_descriptor",
                        "label",
                    )
                )
                + "</tr>"
                for mapping in history["concept_mappings"]
            )
            mapping_content = (
                "<table><thead><tr>"
                + "".join(f"<th>{header}</th>" for header in headers)
                + f"</tr></thead><tbody>{rows}</tbody></table>"
                if rows
                else "<p><em>No concept mappings were logged.</em></p>"
            )
            mapping_sections = [
                "### Concept mappings",
                pn.pane.HTML(
                    mapping_content,
                    sizing_mode="stretch_width",
                ),
            ]
        slipnode_link_sections = []
        if history["table"] == "slipnodes":
            collection_labels = {
                "category_links": "Category links",
                "instance_links": "Instance links",
                "has_property_links": "Has-property links",
                "lateral_sliplinks": "Lateral sliplinks",
                "lateral_non_sliplinks": "Lateral non-sliplinks",
                "incoming_links": "Incoming links",
            }

            def slipnode_link_part(name: str | None) -> str:
                return "—" if name is None else object_link(f"slipnode:{name}")

            def slipnode_link_repr(link: dict[str, object]) -> str:
                source = slipnode_link_part(str(link["source"]))
                target = slipnode_link_part(str(link["target"]))
                label = link["label"]
                if label is None:
                    return f"{source} ~~~~&gt; {target}"
                return f"{source} ~~ {slipnode_link_part(str(label))} ~~&gt; {target}"

            links_by_collection: dict[str, list[dict[str, object]]] = {}
            for link in history["slipnode_link_arguments"]:
                links_by_collection.setdefault(str(link["collection"]), []).append(link)
            link_content = "".join(
                f"<h4>{html.escape(collection_labels[collection])}</h4><ul>"
                + "".join(
                    f"<li>{slipnode_link_repr(link)}</li>" for link in links
                )
                + "</ul>"
                for collection, links in links_by_collection.items()
            ) or "<p><em>No link arguments were logged.</em></p>"
            slipnode_link_sections = [
                "### Link arguments",
                pn.pane.HTML(link_content, sizing_mode="stretch_width"),
            ]
        content.objects = [
            pn.pane.HTML(f'<p><a href="?run_id={run_id}">← Run {run_id}</a></p>'),
            pn.pane.Markdown(f"## {object_id}"),
            *(
                [pn.pane.Markdown("This object was proposed but not created.")]
                if proposed_not_created
                else [charts]
            ),
            "### Attributes",
            attributes,
            *group_sections,
            *mapping_sections,
            *slipnode_link_sections,
        ]

    def show_runs(_: object | None = None) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        groups = []
        for (model, problem), grouped_runs in runs.groupby(
            ["model", "problem"], dropna=False, sort=True
        ):
            groups.extend(
                (
                    pn.pane.HTML(
                        "<h3>"
                        f"{html.escape(str(model))} — {html.escape(str(problem))}"
                        f" <a href=\"?{urlencode({'model': model, 'problem': problem})}\">Overview</a>"
                        "</h3>"
                    ),
                    _run_group_table(grouped_runs, columns),
                )
            )
        content.objects = [
            "## Runs",
            pn.pane.Markdown("Click a run ID to inspect that run."),
            *groups,
        ]

    def show_problem(model: str, problem: str) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        problem_runs = runs[(runs["model"] == model) & (runs["problem"] == problem)]
        if problem_runs.empty:
            content.objects = [
                pn.pane.Alert(
                    "No runs were found for this model and problem.",
                    alert_type="warning",
                )
            ]
            return
        content.objects = [
            pn.pane.HTML('<p><a href="?">← All runs</a></p>'),
            _problem_overview(model, problem, problem_runs),
        ]

    def update_view(event: Any | None = None) -> None:
        run_id = active_run.value
        if run_id:
            if active_object.value:
                show_object(run_id, active_object.value)
            else:
                show_run(run_id)
        elif (
            pn.state.location
            and {"model", "problem"} <= pn.state.location.query_params.keys()
        ):
            show_problem(
                pn.state.location.query_params["model"],
                pn.state.location.query_params["problem"],
            )
        else:
            show_runs()

    active_run.param.watch(update_view, "value")
    active_object.param.watch(update_view, "value")
    update_view()
    return pn.Column(
        content,
        BrowserHistoryBridge(),
        sizing_mode="stretch_width",
    )
