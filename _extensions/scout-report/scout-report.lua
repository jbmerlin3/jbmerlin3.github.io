-- Renders a scouting report from the `scout:` block in a page's YAML header.
-- Usage in the page body: {{< scout-report pdf="Report.pdf" image="report.jpg" >}}
-- Lua, not R, because the site's GitHub build installs only Quarto.

local str = pandoc.utils.stringify

local function warn(page, msg)
  local text = "[scout-report] " .. page .. ": " .. msg
  if quarto and quarto.log and quarto.log.warning then
    quarto.log.warning(text)
  else
    io.stderr:write("WARNING " .. text .. "\n")
  end
end

local function s(x)
  if x == nil then return "" end
  local out = str(x)
  return (out:gsub("^%s+", ""):gsub("%s+$", ""))
end

-- Long YAML strings arrive as blocks; keep their markdown by re-writing them.
local function md_text(x)
  if x == nil then return "" end
  if pandoc.utils.type(x) == "Blocks" then
    return pandoc.write(pandoc.Pandoc(x), "markdown"):gsub("%s+$", "")
  end
  return s(x)
end

local function list(x)
  if x == nil then return {} end
  if pandoc.utils.type(x) == "List" then return x end
  return { x }
end

local function cell(text)
  return (text:gsub("\n", " "):gsub("|", "\\|"))
end

local function tags_text(tags)
  local out = {}
  for _, t in ipairs(list(tags)) do table.insert(out, s(t)) end
  return table.concat(out, " · ")
end

-- "40/50" -> 40, 50. Blank or partial grades return nil so the check can flag them.
local function parse_grade(g)
  local p, f = s(g):match("^(%d+)%s*/%s*(%d+)$")
  return tonumber(p), tonumber(f)
end

local function check_entry(page, kind, name, entry, needs_grade)
  if needs_grade then
    local p, f = parse_grade(entry.grade)
    if not p then
      warn(page, kind .. " '" .. name .. "' has no present/future grade (write it as 40/50)")
    elseif f < p then
      warn(page, kind .. " '" .. name .. "' future grade is below present")
    end
  end
  if md_text(entry.notes) == "" then
    warn(page, kind .. " '" .. name .. "' has no explanation sentences")
  end
end

local function spin_text(x)
  local raw = s(x):gsub(",", "")
  local n = tonumber(raw)
  if not n then return s(x) end
  local r = math.floor(n / 100 + 0.5) * 100
  return tostring(r):reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")
end

local function has_any(entries, field)
  for _, e in ipairs(entries) do
    if s(e[field]) ~= "" then return true end
  end
  return false
end

-- One-screen layout: header strip, then a two-column grid.
-- Left column: graded tools (pitch data sits under each pitch name).
-- Right column: PBR form groups, hitter data, and the form thumbnail.
local function scout_report(args, kwargs, meta)
  local sc = meta.scout
  if sc == nil then
    warn("page", "no scout: block in the YAML header")
    return pandoc.Blocks({})
  end
  local page = s(meta.title)
  local is_pitcher = s(sc.role) == "pitcher"
  local pdf, img = s(kwargs.pdf), s(kwargs.image)
  local out = {}
  local function add(line) table.insert(out, line) end

  add("::::::: {.scout}")

  -- Header strip: bio and looks on the left, OFP on the right
  add(":::::: {.scout-head}")
  add("::::: {.scout-id}")
  local bio = {}
  for _, pair in ipairs({
    { "B/T", sc.bt }, { "Ht/Wt", sc.size }, { "Commit", sc.commit }, { "Travel team", sc.team },
  }) do
    if s(pair[2]) ~= "" then table.insert(bio, "[" .. pair[1] .. "]{.k} " .. s(pair[2])) end
  end
  if #bio > 0 then add("[" .. table.concat(bio, "[·]{.dot}") .. "]{.scout-bio}\n") end
  local looks = {}
  for _, l in ipairs(list(sc.looks)) do table.insert(looks, s(l)) end
  if #looks > 0 then
    add("[[Looks]{.k} " .. table.concat(looks, "[·]{.dot}") .. "]{.scout-looks}\n")
  end
  local summary = md_text(sc.summary)
  if summary == "" then warn(page, "summary is blank") end
  if summary ~= "" then add("[" .. summary:gsub("\n", " ") .. "]{.scout-summary}\n") end
  add(":::::")
  local ofp, follow = s(sc.ofp), s(sc.follow)
  if ofp == "" then warn(page, "OFP is blank") end
  if img ~= "" and pdf ~= "" then
    add("::::: {.scout-form}")
    add("[![](" .. img .. "){fig-alt=\"PBR evaluation form for " .. page .. "\"}](" .. pdf .. ")")
    add("[PBR form]{.form-label}")
    add(":::::")
  end
  -- One clip per player: a tile beside the form that opens the video in a pop-up.
  -- preload="none" so nothing downloads until someone clicks.
  local video, vcap = s(sc.video), s(sc.video_caption)
  if video ~= "" then
    local poster = video:gsub("[^/]+$", "poster.jpg")
    local esc = function(x) return (x:gsub("&", "&amp;"):gsub('"', "&quot;"):gsub("<", "&lt;")) end
    add("```{=html}")
    add('<div class="scout-video">')
    add('<button type="button" class="video-tile" aria-label="Play video' ..
      (vcap ~= "" and (": " .. esc(vcap)) or "") .. '" onclick="scoutVideo(this)">')
    add('<img src="' .. poster .. '" alt=""><span class="play" aria-hidden="true"></span></button>')
    add('<span class="form-label">Video</span>')
    add('<dialog class="video-modal" onclick="if(event.target===this)this.close()" onclose="this.querySelector(\'video\').pause()">')
    add('<video controls playsinline preload="none" poster="' .. poster .. '" src="' .. esc(video) .. '"></video>')
    add('<div class="video-bar"><span>' .. esc(vcap) .. '</span>' ..
      '<button type="button" class="video-close" onclick="this.closest(\'dialog\').close()" aria-label="Close video">Close</button></div>')
    add('</dialog></div>')
    add('<script>function scoutVideo(b){var d=b.parentNode.querySelector("dialog");d.showModal();d.querySelector("video").play();}</script>')
    add("```")
  end
  add("::::: {.scout-ofp}")
  add("[" .. (ofp ~= "" and ofp or "–") .. "]{.ofp-num}")
  add("[OFP]{.ofp-label}")
  if follow ~= "" then add("[" .. follow .. "]{.ofp-follow}") end
  add(":::::")
  add("::::::\n")

  add(":::::: {.scout-grid}")

  -- Left: graded tools
  add("::::: {.scout-main}")
  local tools = list(sc.tools)
  if #tools > 0 then
    add("| " .. (is_pitcher and "Pitch" or "Tool") .. " | Grade | Notes [20-80 grades, present/future]{.scout-sub} |")
    -- Pitchers need room for velo/spin/shape under the name; hitters give it to the notes
    local first_w = is_pitcher and 28 or 15
    add("|:" .. string.rep("-", first_w) .. "|:" .. string.rep("-", 7) .. "|:" .. string.rep("-", 92 - first_w) .. "|")
    for _, t in ipairs(tools) do
      local name = s(t.name)
      -- A row with no grade and no notes is an unfilled sheet row: skip it, but say so
      if s(t.grade) == "" and md_text(t.notes) == "" then
        warn(page, "Tool '" .. name .. "' is blank and was left off the page")
        goto continue
      end
      check_entry(page, "Tool", name, t, true)
      local first = "[" .. name .. "]{.tool-name}"
      if s(t.velo) ~= "" then first = first .. "[" .. s(t.velo) .. "]{.tool-data}" end
      local dat = {}
      if s(t.spin) ~= "" then table.insert(dat, spin_text(t.spin) .. " rpm") end
      if s(t.shape) ~= "" then table.insert(dat, s(t.shape)) end
      if #dat > 0 then first = first .. "[" .. table.concat(dat, " · ") .. "]{.tool-data}" end
      local notes = md_text(t.notes)
      local tags = tags_text(t.tags)
      if tags ~= "" then notes = "[" .. tags .. "]{.scout-tags}" .. notes end
      add("| " .. cell(first) .. " | [" .. cell(s(t.grade)) .. "]{.grade} | " .. cell(notes) .. " |")
      ::continue::
    end
    add("")
  end
  add(":::::")

  -- Right: PBR form groups, hitter data, form thumbnail
  add("::::: {.scout-side}")
  local traits = list(sc.traits)
  if #traits > 0 then
    add("[From the PBR form]{.scout-h}\n")
    for _, g in ipairs(traits) do
      local name = s(g.name)
      check_entry(page, "Trait group", name, g, false)
      add(":::: {.trait}")
      add("[" .. name .. "]{.trait-name}")
      local tags = tags_text(g.tags)
      if tags ~= "" then add("[" .. tags .. "]{.scout-tags}") end
      add("[" .. md_text(g.notes):gsub("\n", " ") .. "]{.trait-notes}")
      add("::::\n")
    end
  end
  local data = list(sc.data)
  if #data > 0 then
    -- Label/value rows, no table header and no source column
    add("[Data]{.scout-h}\n")
    add(":::: {.scout-data}")
    for _, d in ipairs(data) do
      add("[" .. s(d.measure) .. "]{.dk}[" .. s(d.value) .. "]{.dv}")
    end
    add("::::\n")
  end
  local links = {}
  if pdf ~= "" then table.insert(links, "[Full PBR evaluation form (PDF)](" .. pdf .. ")") end
  local url = s(sc.pbr_url)
  if url ~= "" then table.insert(links, "[Published on the PBR Scout Blog](" .. url .. ")") end
  if #links > 0 then add("[" .. table.concat(links, "[·]{.dot}") .. "]{.scout-links}\n") end
  add(":::::")

  add("::::::")
  add(":::::::")

  return pandoc.read(table.concat(out, "\n"), "markdown").blocks
end

return { ["scout-report"] = scout_report }
