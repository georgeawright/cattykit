from __future__ import annotations

import param
import panel as pn


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

    _scripts[
        "draw"
    ] = """
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
    function strokeStyle(proposed, color = '#004D40') {
      ctx.setLineDash(proposed ? [5, 4] : [])
      ctx.strokeStyle = color
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
          connection.type === 'correspondence' ? '#D81B60'
            : connection.type === 'replacement' ? '#1E88E5' : '#004D40',
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
    const rule = data.snapshot.rule
    if (rule) {
      const secondHalf = rule.relation || rule.descriptor_2 || '—'
      const ruleText = `Replace ${rule.replaced_description_type || '—'} of ${rule.descriptor || '—'} ${rule.object_category || '—'} by ${secondHalf}`
      const modifiedBox = layout.modified
      ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      const ruleWidth = Math.min(modifiedBox[2] - 12, ctx.measureText(ruleText).width + 16)
      const ruleX = modifiedBox[0] + (modifiedBox[2] - ruleWidth) / 2
      const ruleY = modifiedBox[1] + 4
      ctx.fillStyle = 'white'; ctx.strokeStyle = 'black'; ctx.lineWidth = 1
      ctx.fillRect(ruleX, ruleY, ruleWidth, 22); ctx.strokeRect(ruleX, ruleY, ruleWidth, 22)
      ctx.fillStyle = '#111827'; ctx.fillText(ruleText, modifiedBox[0] + modifiedBox[2] / 2, ruleY + 11)
    }
    const translatedRule = data.snapshot.translated_rule
    if (translatedRule) {
      const secondHalf = translatedRule.relation || translatedRule.descriptor_2 || '—'
      const ruleText = `Replace ${translatedRule.replaced_description_type || '—'} of ${translatedRule.descriptor || '—'} ${translatedRule.object_category || '—'} by ${secondHalf}`
      const answerBox = layout.answer
      ctx.font = '12px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
      const ruleWidth = Math.min(answerBox[2] - 12, ctx.measureText(ruleText).width + 16)
      const ruleX = answerBox[0] + (answerBox[2] - ruleWidth) / 2
      const ruleY = answerBox[1] + answerBox[3] - 25
      ctx.fillStyle = 'white'; ctx.strokeStyle = 'black'; ctx.lineWidth = 1
      ctx.fillRect(ruleX, ruleY, ruleWidth, 22); ctx.strokeRect(ruleX, ruleY, ruleWidth, 22)
      ctx.fillStyle = '#111827'; ctx.fillText(ruleText, answerBox[0] + answerBox[2] / 2, ruleY + 11)
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
    _scripts["render"] = (
        """
    state.draw = () => {"""
        + _scripts["draw"]
        + """}
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
    )
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
    _scripts[
        "draw"
    ] = """
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
    _scripts["render"] = (
        """
    state.draw = () => {"""
        + _scripts["draw"]
        + """}
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
    )
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
