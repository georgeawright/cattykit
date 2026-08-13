"""Panel application for browsing a Cattycam SQLite database.

Run with ``panel serve cattycam/app.py --show --args path/to/history.sqlite``.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any

import param
import pandas as pd
import panel as pn
from bokeh.models import Label, Span
from bokeh.plotting import figure

# Panel executes a served file as a script, rather than as a package module.
# Add the source-package root so this works with ``panel serve cattycam/app.py``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

pn.extension("tabulator")


class WorkspaceCanvas(pn.reactive.ReactiveHTML):
    """Canvas rendering of the Copycat workspace at one codelet time."""

    snapshot = param.Dict(default={})

    _template = """
    <div id="container" style="width:100%; overflow:hidden; border:1px solid #d0d0d0;">
      <canvas id="canvas" style="display:block; width:100%; height:390px;"></canvas>
    </div>
    """

    _scripts = {
        "snapshot": "if (state.draw) state.draw()",
    }

    _scripts["draw"] = """
    const width = Math.max(container.clientWidth, 620)
    const height = 390
    const scale = window.devicePixelRatio || 1
    canvas.width = width * scale
    canvas.height = height * scale
    const ctx = canvas.getContext('2d')
    ctx.setTransform(scale, 0, 0, scale, 0, 0)
    ctx.clearRect(0, 0, width, height)
    ctx.font = '14px sans-serif'
    ctx.fillStyle = '#20242a'
    const layout = {
      initial: [20, 54, width / 2 - 35, 110],
      modified: [width / 2 + 15, 54, width / 2 - 35, 110],
      target: [20, 245, width / 2 - 35, 110],
      answer: [width / 2 + 15, 245, width / 2 - 35, 110],
    }
    const points = new Map()
    const hits = []
    const lettersByString = {}
    for (const letter of (data.snapshot.letters || [])) {
      ;(lettersByString[letter.string] ||= []).push(letter)
    }
    for (const [role, box] of Object.entries(layout)) {
      ctx.fillStyle = '#4b5563'
      ctx.font = '12px sans-serif'
      ctx.fillText(role, box[0], box[1] - 18)
      const letters = (lettersByString[role] || []).sort((a, b) => a.position - b.position)
      const step = box[2] / Math.max(letters.length + 1, 2)
      letters.forEach((letter, index) => {
        const point = {x: box[0] + step * (index + 1), y: box[1] + box[3] / 2}
        points.set(letter.id, point)
        hits.push({type: 'letter', id: letter.id, x: point.x, y: point.y, descriptions: data.snapshot.descriptions[letter.id] || []})
      })
    }
    function strokeStyle(proposed, color = '#334e68') {
      ctx.setLineDash(proposed ? [5, 4] : [])
      ctx.strokeStyle = proposed ? '#8a6d3b' : color
      ctx.lineWidth = 1.6
    }
    function arrow(from, to, bend, proposed, color) {
      if (!from || !to) return
      const mx = (from.x + to.x) / 2
      const my = (from.y + to.y) / 2 + bend
      const clearance = 20
      const sourceDistance = Math.max(Math.hypot(mx - from.x, my - from.y), 1)
      const targetDistance = Math.max(Math.hypot(to.x - mx, to.y - my), 1)
      const start = {
        x: from.x + clearance * (mx - from.x) / sourceDistance,
        y: from.y + clearance * (my - from.y) / sourceDistance,
      }
      const end = {
        x: to.x - clearance * (to.x - mx) / targetDistance,
        y: to.y - clearance * (to.y - my) / targetDistance,
      }
      strokeStyle(proposed, color)
      ctx.beginPath(); ctx.moveTo(start.x, start.y); ctx.quadraticCurveTo(mx, my, end.x, end.y); ctx.stroke()
      const angle = Math.atan2(end.y - my, end.x - mx)
      ctx.setLineDash([]); ctx.fillStyle = ctx.strokeStyle
      ctx.beginPath(); ctx.moveTo(end.x, end.y)
      ctx.lineTo(end.x - 8 * Math.cos(angle - 0.45), end.y - 8 * Math.sin(angle - 0.45))
      ctx.lineTo(end.x - 8 * Math.cos(angle + 0.45), end.y - 8 * Math.sin(angle + 0.45))
      ctx.closePath(); ctx.fill()
      return {from: start, to: end, mx, my}
    }
    const connections = [
      ...(data.snapshot.bonds || []).map(connection => ({...connection, type: 'bond'})),
      ...(data.snapshot.correspondences || []).map(connection => ({...connection, type: 'correspondence'})),
      ...(data.snapshot.replacements || []).map(connection => ({...connection, type: 'replacement'})),
    ]
    const connectionsByPair = {}
    for (const connection of connections) {
      const pair = [connection.source, connection.target].sort().join('|')
      ;(connectionsByPair[pair] ||= []).push(connection)
    }
    for (const pairConnections of Object.values(connectionsByPair)) {
      pairConnections.forEach((connection, index) => {
        const from = points.get(connection.source), to = points.get(connection.target)
        if (!from || !to) return
        const baseBend = from.y === to.y ? -36 : (from.x < to.x ? -30 : 30)
        const laneOffset = (index - (pairConnections.length - 1) / 2) * 24
        const curve = arrow(
          from,
          to,
          baseBend + laneOffset,
          connection.proposed,
          connection.type === 'replacement' ? '#7c3aed' : undefined,
        )
        if (connection.type === 'bond' && curve) {
          hits.push({type: 'bond', id: connection.id, ...curve, facet: connection.facet, category: connection.category, direction: connection.direction})
        } else if (connection.type === 'correspondence' && curve) {
          hits.push({type: 'correspondence', ...curve, id: connection.id, mappings: connection.mappings || []})
        }
      })
    }
    for (const group of (data.snapshot.groups || [])) {
      const box = layout[group.string]
      if (!box) continue
      const letters = (lettersByString[group.string] || []).sort((a, b) => a.position - b.position)
      const selected = letters.filter(letter => letter.position >= group.left && letter.position <= group.right)
      if (!selected.length) continue
      const ps = selected.map(letter => points.get(letter.id))
      const left = Math.min(...ps.map(point => point.x)) - 20
      const right = Math.max(...ps.map(point => point.x)) + 20
      strokeStyle(group.proposed)
      ctx.strokeRect(left, box[1] + 24, right - left, 62)
      hits.push({type: 'group', id: group.id, x: left, y: box[1] + 24, width: right - left, height: 62, descriptions: data.snapshot.descriptions[group.id] || []})
    }
    ctx.setLineDash([])
    for (const [role, letters] of Object.entries(lettersByString)) {
      for (const letter of letters) {
        const point = points.get(letter.id)
        if (!point) continue
        ctx.fillStyle = '#111827'; ctx.font = '22px serif'
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.fillText(letter.value, point.x, point.y)
      }
    }
    if (state.selection) {
      const selection = state.selection
      const descriptionLines = (selection.descriptions || []).map(description => `${description.facet || '—'}: ${description.descriptor || '—'}`)
      const lines = selection.type === 'bond'
        ? [`facet: ${selection.facet || '—'}`, `bond category: ${selection.category || '—'}`, `direction category: ${selection.direction || '—'}`]
        : selection.type === 'correspondence'
          ? (selection.mappings || []).map(mapping => `${mapping.source_type || '—'} → ${mapping.target_type || '—'}`)
        : [...new Set(descriptionLines)]
      const title = selection.id
      const cardX = Math.min(width - 190, Math.max(8, selection.cardX + 16))
      const cardY = Math.min(height - 70, Math.max(8, selection.cardY - 12))
      ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.font = '12px sans-serif'
      const cardWidth = Math.max(145, ctx.measureText(title).width + 20, ...lines.map(line => ctx.measureText(line).width + 20))
      const cardHeight = 27 + Math.max(lines.length, 1) * 18
      ctx.fillStyle = 'white'; ctx.strokeStyle = '#111827'; ctx.lineWidth = 1
      ctx.fillRect(cardX, cardY, cardWidth, cardHeight); ctx.strokeRect(cardX, cardY, cardWidth, cardHeight)
      ctx.fillStyle = '#111827'; ctx.font = '600 12px sans-serif'; ctx.fillText(title, cardX + 8, cardY + 17)
      ctx.font = '12px sans-serif'
      if (lines.length) lines.forEach((line, index) => ctx.fillText(line, cardX + 8, cardY + 37 + index * 18))
      else ctx.fillText(selection.type === 'correspondence' ? 'No concept mappings' : 'No descriptions', cardX + 8, cardY + 37)
    }
    state.hits = hits
    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic'
    """
    _scripts["render"] = """
    state.draw = () => {""" + _scripts["draw"] + """}
    state.point = event => {
      const bounds = canvas.getBoundingClientRect()
      return {x: event.clientX - bounds.left, y: event.clientY - bounds.top}
    }
    state.hitAt = point => {
      const hits = state.hits || []
      for (const type of ['letter', 'correspondence', 'bond', 'group']) {
        const hit = hits.slice().reverse().find(hit => {
          if (hit.type !== type) return false
      if (hit.type === 'letter') return Math.hypot(hit.x - point.x, hit.y - point.y) < 18
      if (hit.type === 'group') return point.x >= hit.x && point.x <= hit.x + hit.width && point.y >= hit.y && point.y <= hit.y + hit.height
      if (hit.type === 'bond' || hit.type === 'correspondence') {
        let previous = hit.from
        for (let step = 1; step <= 20; step++) {
          const t = step / 20, next = {x: (1-t)*(1-t)*hit.from.x + 2*(1-t)*t*hit.mx + t*t*hit.to.x, y: (1-t)*(1-t)*hit.from.y + 2*(1-t)*t*hit.my + t*t*hit.to.y}
          const length = Math.hypot(next.x - previous.x, next.y - previous.y)
          const distance = length ? Math.abs((next.x-previous.x)*(previous.y-point.y) - (previous.x-point.x)*(next.y-previous.y)) / length : Infinity
          const tolerance = hit.type === 'correspondence' ? 11 : 7
          if (distance < tolerance && point.x >= Math.min(previous.x,next.x)-tolerance && point.x <= Math.max(previous.x,next.x)+tolerance && point.y >= Math.min(previous.y,next.y)-tolerance && point.y <= Math.max(previous.y,next.y)+tolerance) return true
          previous = next
        }
      }
      return false
        })
        if (hit) return hit
      }
      return null
    }
    canvas.addEventListener('click', event => {
      const selection = state.hitAt(state.point(event))
      state.selection = selection ? {...selection, cardX: selection.x || selection.from.x, cardY: selection.y || selection.from.y} : null
      state.draw()
    })
    state.resizeObserver = new ResizeObserver(() => {
      window.clearTimeout(state.resizeTimer)
      state.resizeTimer = window.setTimeout(() => state.draw(), 50)
    })
    state.resizeObserver.observe(container)
    state.draw()
    """
    del _scripts["draw"]


class SlipnetCanvas(pn.reactive.ReactiveHTML):
    """Canvas graph of the Slipnet at one codelet time."""

    snapshot = param.Dict(default={})

    _template = """
    <div id="container" style="width:100%; overflow:hidden; border:1px solid #d0d0d0;">
      <canvas id="canvas" style="display:block; width:100%; height:430px;"></canvas>
    </div>
    """
    _scripts = {"snapshot": "if (state.draw) state.draw()"}
    _scripts["draw"] = """
    const width = Math.max(container.clientWidth, 620)
    const height = 430
    const scale = window.devicePixelRatio || 1
    canvas.width = width * scale; canvas.height = height * scale
    const ctx = canvas.getContext('2d')
    ctx.setTransform(scale, 0, 0, scale, 0, 0)
    ctx.clearRect(0, 0, width, height)
    const snapshotNodes = data.snapshot.nodes || []
    const names = snapshotNodes.map(node => node.name)
    const positionsMatch = state.nodes && state.nodes.length === names.length &&
      state.nodes.every(node => names.includes(node.name))
    if (!positionsMatch) {
      const orbit = Math.min(width, height) * 0.36
      state.nodes = snapshotNodes.map((node, index) => {
        const angle = (2 * Math.PI * index) / snapshotNodes.length - Math.PI / 2
        return {...node, index, x: width / 2 + orbit * Math.cos(angle), y: height / 2 + orbit * Math.sin(angle)}
      })
    } else {
      const activationByName = new Map(snapshotNodes.map(node => [node.name, node.activation]))
      state.nodes.forEach((node, index) => { node.index = index; node.activation = activationByName.get(node.name) || 0 })
      if (state.width && state.width !== width) {
        const horizontalScale = width / state.width
        state.nodes.forEach(node => { node.x *= horizontalScale })
      }
    }
    const nodes = state.nodes
    state.width = width
    if (nodes.length && (!state.selected || !nodes.some(node => node.name === state.selected))) {
      state.selected = nodes.reduce(
        (mostActive, node) => Number(node.activation || 0) > Number(mostActive.activation || 0)
          ? node : mostActive,
        nodes[0],
      ).name
    }
    const links = (data.snapshot.links || []).filter(link =>
      nodes.some(node => node.name === link.source) && nodes.some(node => node.name === link.target)
    )
    if (!nodes.length) {
      ctx.fillStyle = '#4b5563'; ctx.font = '14px sans-serif'
      ctx.fillText('No Slipnet data recorded for this run.', 16, 28)
      return
    }
    const byName = new Map(nodes.map(node => [node.name, node]))
    const padding = 26
    for (let iteration = 0; iteration < (state.dragged ? 0 : 100); iteration++) {
      const forces = nodes.map(() => ({x: 0, y: 0}))
      for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y
        const distance = Math.max(Math.hypot(dx, dy), 1)
        const force = 1100 / (distance * distance)
        const x = force * dx / distance, y = force * dy / distance
        forces[i].x -= x; forces[i].y -= y; forces[j].x += x; forces[j].y += y
      }
      for (const link of links) {
        const source = byName.get(link.source), target = byName.get(link.target)
        const dx = target.x - source.x, dy = target.y - source.y
        const distance = Math.max(Math.hypot(dx, dy), 1)
        const desired = 34 + 78 * Math.min(Math.max(Number(link.fixed_length) || 0.5, 0), 1)
        const force = (distance - desired) * 0.025
        const x = force * dx / distance, y = force * dy / distance
        forces[source.index].x += x; forces[source.index].y += y
        forces[target.index].x -= x; forces[target.index].y -= y
      }
      nodes.forEach((node, index) => {
        node.x = Math.min(width - padding, Math.max(padding, node.x + forces[index].x))
        node.y = Math.min(height - padding, Math.max(padding, node.y + forces[index].y))
      })
    }
    ctx.font = '10px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    for (const link of links) {
      const source = byName.get(link.source), target = byName.get(link.target)
      ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(source.x, source.y); ctx.lineTo(target.x, target.y); ctx.stroke()
      if (link.label) {
        const x = (source.x + target.x) / 2, y = (source.y + target.y) / 2
        const text = link.label, textWidth = ctx.measureText(text).width
        ctx.fillStyle = 'rgba(255, 255, 255, 0.88)'
        ctx.fillRect(x - textWidth / 2 - 3, y - 7, textWidth + 6, 14)
        ctx.fillStyle = '#475569'; ctx.fillText(text, x, y)
      }
    }
    for (const node of nodes) {
      const activation = Math.min(Math.max(Number(node.activation) || 0, 0), 1)
      const radius = 7 + activation * 16
      ctx.beginPath(); ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(37, 99, 235, ${0.22 + activation * 0.7})`; ctx.fill()
      ctx.strokeStyle = '#1d4ed8'; ctx.lineWidth = 1.2; ctx.stroke()
      ctx.fillStyle = '#111827'; ctx.font = '11px sans-serif'
      ctx.textAlign = 'left'; ctx.fillText(node.name, node.x + radius + 3, node.y)
      if (state.selected === node.name) {
        ctx.beginPath(); ctx.arc(node.x, node.y, radius + 4, 0, Math.PI * 2)
        ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 2.5; ctx.stroke()
      }
    }
    if (state.selected) {
      const node = byName.get(state.selected)
      if (node) {
        const text = `${node.name} — activation ${Number(node.activation || 0).toFixed(2)}`
        ctx.font = '13px sans-serif'; const textWidth = ctx.measureText(text).width
        ctx.fillStyle = 'white'; ctx.strokeStyle = '#111827'; ctx.lineWidth = 1
        ctx.fillRect(12, 12, textWidth + 18, 27); ctx.strokeRect(12, 12, textWidth + 18, 27)
        ctx.fillStyle = '#111827'; ctx.textAlign = 'left'; ctx.fillText(text, 21, 26)
      }
    }
    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic'
    """
    _scripts["render"] = """
    state.draw = () => {""" + _scripts["draw"] + """}
    state.point = event => {
      const bounds = canvas.getBoundingClientRect()
      return {x: event.clientX - bounds.left, y: event.clientY - bounds.top}
    }
    state.nodeAt = point => (state.nodes || []).find(node => {
      const radius = 10 + Math.min(Math.max(Number(node.activation) || 0, 0), 1) * 16
      return Math.hypot(node.x - point.x, node.y - point.y) <= radius
    })
    canvas.addEventListener('mousedown', event => {
      const node = state.nodeAt(state.point(event))
      if (node) { state.dragged = node; state.selected = node.name; canvas.style.cursor = 'grabbing'; state.draw() }
    })
    canvas.addEventListener('mousemove', event => {
      const point = state.point(event)
      if (state.dragged) {
        state.dragged.x = point.x; state.dragged.y = point.y; state.draw()
      } else {
        canvas.style.cursor = state.nodeAt(point) ? 'grab' : 'default'
      }
    })
    const release = () => { if (state.dragged) { state.dragged = null; canvas.style.cursor = 'default'; state.draw() } }
    canvas.addEventListener('mouseup', release)
    canvas.addEventListener('mouseleave', release)
    state.resizeObserver = new ResizeObserver(() => {
      window.clearTimeout(state.resizeTimer)
      state.resizeTimer = window.setTimeout(() => state.draw(), 50)
    })
    state.resizeObserver.observe(container)
    state.draw()
    """
    del _scripts["draw"]


class BrowserHistoryBridge(pn.reactive.ReactiveHTML):
    """Reload the standalone app after browser Back or Forward navigation."""

    _template = "<div></div>"
    _scripts = {
        "render": """
            if (!state.popstate_listener) {
                state.popstate_listener = () => window.location.reload()
                window.addEventListener("popstate", state.popstate_listener)
            }
        """
    }


def create_app(database: str | Path) -> pn.Column:
    """Create a run picker which opens a tabbed, run-specific database view."""
    from cattycam.database import (
        coderack_codelets,
        run_overview_series,
        table_documentation,
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
    if pn.state.location:
        # This is a standalone Panel application. Reloading after a URL change
        # gives browser Back/Forward a fresh session whose selected run is read
        # from the query string.
        pn.state.location.reload = True
        pn.state.location.sync(active_run, {"value": "run_id"})

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
        codelet_time = pn.widgets.EditableIntSlider(
            name="Codelets run",
            start=0,
            end=int(codelets_run or 0),
            value=int(codelets_run or 0),
            sizing_mode="stretch_width",
        )
        overview = _run_overview(
            run_overview_series(database_path, run_id), codelet_time
        )
        visible_tables = [table for table in tables if table != "attribute_values"]
        table_content = pn.Column(sizing_mode="stretch_width")
        table_links = pn.Row(sizing_mode="stretch_width")

        def show_table(table: str) -> None:
            table_content.objects = [
                pn.pane.HTML(
                    table_documentation(database_path, table, run_id=run_id),
                    sizing_mode="stretch_width",
                )
            ]

        for table in visible_tables:
            link = pn.widgets.Button(name=table, button_type="light")
            link.on_click(lambda _, table=table: show_table(table))
            table_links.append(link)
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
            table_links,
            table_content,
        ]

    def show_runs(_: object | None = None) -> None:
        columns, rows = table_rows(database_path, "runs")
        runs = pd.DataFrame(rows, columns=columns)
        grid = pn.widgets.Tabulator(
            runs,
            selectable=1,
            show_index=False,
            sizing_mode="stretch_width",
        )

        def open_run(event: Any) -> None:
            row_index = event.row
            active_run.value = int(runs.iloc[row_index]["id"])

        grid.on_click(open_run)
        content.objects = [
            "## Runs",
            pn.pane.Markdown("Click a row to inspect that run."),
            grid,
        ]

    def update_view(event: Any | None = None) -> None:
        run_id = active_run.value if event is None else event.new
        if run_id:
            show_run(run_id)
        else:
            show_runs()

    active_run.param.watch(update_view, "value")
    update_view()
    return pn.Column(
        content,
        BrowserHistoryBridge(),
        sizing_mode="stretch_width",
    )


def _run_overview(
    series: dict[str, list[tuple]], codelet_time: pn.widgets.EditableIntSlider
) -> pn.Column:
    """Build charts summarizing the selected run."""
    return pn.Column(
        pn.Row(
            _line_chart(
                "Codelets on coderack",
                series["coderack"],
                "Number of codelets on coderack",
                codelet_time,
            ),
            _line_chart(
                "Temperature",
                series["temperature"],
                "Temperature",
                codelet_time,
                value_formatter=lambda value: f"{float(value):.2f}",
            ),
            _workspace_chart(series["workspace"], codelet_time),
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )


def _line_chart(
    title: str,
    values: list[tuple],
    y_axis_label: str,
    codelet_time: pn.widgets.EditableIntSlider,
    value_formatter=str,
) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert(f"No {title.lower()} data was logged.", alert_type="info")
    chart = figure(
        title=title,
        x_axis_label="Codelets run",
        y_axis_label=y_axis_label,
        height=260,
        width=380,
        toolbar_location=None,
    )
    chart.line(*zip(*values), line_width=2)
    _add_time_marker(chart, codelet_time, values, value_formatter)
    return chart


def _workspace_chart(
    values: list[tuple], codelet_time: pn.widgets.EditableIntSlider
) -> pn.viewable.Viewable:
    if not values:
        return pn.pane.Alert("No workspace data was logged.", alert_type="info")
    times, totals = zip(*values)
    chart = figure(
        title="Workspace objects and structures",
        x_axis_label="Codelets run",
        y_axis_label="Total count",
        height=260,
        width=380,
        toolbar_location=None,
    )
    chart.line(times, totals, line_width=2, color="#1f77b4")
    _add_time_marker(chart, codelet_time, values, str)
    return chart


def _add_time_marker(
    chart,
    codelet_time: pn.widgets.EditableIntSlider,
    values: list[tuple],
    value_formatter,
) -> None:
    """Add a vertical marker and value label that follow the selected time."""
    value = _value_at_time(values, codelet_time.value_throttled)
    marker = Span(
        location=codelet_time.value_throttled,
        dimension="height",
        line_color="red",
        line_width=2,
    )
    chart.add_layout(marker)
    label = Label(
        x=codelet_time.value_throttled,
        # The plot frame is shorter than the figure because of its title and axes.
        # Keep the screen-positioned label inside that frame.
        y=175,
        y_units="screen",
        text=value_formatter(value),
        background_fill_color="white",
        background_fill_alpha=0.9,
        border_line_color="black",
        padding=6,
        text_color="black",
    )
    chart.add_layout(label)

    def update_marker(event: Any) -> None:
        marker.location = event.new
        label.x = event.new
        label.text = value_formatter(_value_at_time(values, event.new))

    codelet_time.param.watch(update_marker, "value_throttled")


def _value_at_time(values: list[tuple], time: int) -> object:
    """Return the latest series value known at a selected codelet time."""
    return next(
        (value for value_time, value in reversed(values) if value_time <= time),
        values[0][1],
    )


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

    cards = "".join(
        "<div style='display:flex; gap:6px; min-height:76px; margin-bottom:8px;'>"
        f"<div style='width:42px; flex:0 0 42px; font-weight:600;'>{run_time}</div>"
        "<div style='box-sizing:border-box; flex:1; border:1px solid #8296b4; "
        "border-radius:5px; padding:6px;'>"
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


database_argument = sys.argv[1] if len(sys.argv) > 1 else "cattycam.sqlite"
create_app(database_argument).servable(title="Cattycam")
