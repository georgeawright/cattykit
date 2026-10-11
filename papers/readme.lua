local function metadata_text(value)
  if value == nil then
    return ""
  end
  return pandoc.utils.stringify(value)
end

local function bibtex_entry(metadata)
  local bibtex = metadata.bibtex
  if bibtex == nil then
    return nil
  end

  local entry_type = metadata_text(bibtex.type)
  local key = metadata_text(bibtex.key)
  if entry_type == "" or key == "" then
    error("bibtex metadata requires both type and key")
  end

  local fields = bibtex.fields or {}
  fields.author = fields.author or metadata.author
  fields.title = fields.title or metadata.title

  local names = {}
  for name, _ in pairs(fields) do
    table.insert(names, name)
  end
  table.sort(names)

  local lines = { "@" .. entry_type .. "{" .. key .. "," }
  for _, name in ipairs(names) do
    table.insert(lines, "  " .. name .. " = {" .. metadata_text(fields[name]) .. "},")
  end
  table.insert(lines, "}")
  return table.concat(lines, "\n")
end

function Pandoc(document)
  local render_readme = metadata_text(document.meta["render-readme"])
  if render_readme ~= "true" then
    return document
  end

  local title = metadata_text(document.meta.title)
  local abstract = metadata_text(document.meta.abstract)
  local citation = bibtex_entry(document.meta)

  if title == "" or abstract == "" then
    error("README rendering requires title and abstract metadata")
  end

  document.meta.title = nil
  document.meta.author = nil
  document.meta["author-meta"] = nil
  document.meta.date = nil
  document.meta.abstract = nil
  document.meta.bibliography = nil
  document.blocks = {
    pandoc.Header(1, title),
    pandoc.Header(2, "Abstract"),
    pandoc.Para(abstract),
    pandoc.Header(2, "Cite this paper"),
    pandoc.CodeBlock(citation, pandoc.Attr("", { "bibtex" }, {})),
  }
  return document
end
