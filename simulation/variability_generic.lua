-- variability_generic.lua
-- Region-agnostic SNR-variability driver. Reads its mutable link list from
-- a --lua-var 'links_json' parameter (JSON-encoded array of {from, to, snr, rssi}).
-- Same event model as urban_variability.lua but works on any topology.
--
-- Usage:
--   orchestrator --lua variability_generic.lua --lua-var links_json='[...]' config.json

-- Minimal JSON parser for our schema:
--   [{"from":"...","to":"...","snr":N,"rssi":N}, ...]
local function parse_json(s)
    local t = {}
    for entry in s:gmatch('%{[^}]+%}') do
        local e = {}
        e.from = entry:match('"from"%s*:%s*"([^"]+)"')
        e.to   = entry:match('"to"%s*:%s*"([^"]+)"')
        e.snr  = tonumber(entry:match('"snr"%s*:%s*(-?[%d%.]+)'))
        e.rssi = tonumber(entry:match('"rssi"%s*:%s*(-?[%d%.]+)'))
        table.insert(t, e)
    end
    return t
end

local links_json = vars.links_json or '[]'
local links = parse_json(links_json)

local current_snr = {}
local current_rssi = {}
local base_snr = {}
local base_rssi = {}
local events = {}
local event_count = {drift = 0, shadow = 0, fade = 0}

function init_variability()
    math.randomseed(os.time() + sim:time())
    for i = 1, 5 do math.random() end
    for i, l in ipairs(links) do
        base_snr[i] = l.snr
        base_rssi[i] = l.rssi
        current_snr[i] = l.snr
        current_rssi[i] = l.rssi
    end
    log('[variability] init: ' .. #links .. ' mutable links')
end

function apply_variability()
    local now = sim:time()

    for i, e in pairs(events) do
        if now >= e.end_ms then
            sim:set_link(links[i].from, links[i].to, current_snr[i], current_rssi[i])
            events[i] = nil
        end
    end

    local candidates = {}
    for i = 1, #links do
        if not events[i] then table.insert(candidates, i) end
    end
    if #candidates == 0 then return end
    local i = candidates[math.random(#candidates)]
    local l = links[i]
    local r = math.random()

    if r < 0.6 then
        local drift = (math.random() - 0.5) * 6
        -- Clamp to a reasonable range around the baseline
        current_snr[i] = math.max(base_snr[i] - 8, math.min(base_snr[i] + 8, current_snr[i] + drift))
        current_rssi[i] = current_rssi[i] + drift
        sim:set_link(l.from, l.to, current_snr[i], current_rssi[i])
        event_count.drift = event_count.drift + 1
    elseif r < 0.9 then
        local dur = 60000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 10, current_rssi[i] - 10)
        events[i] = {end_ms = now + dur}
        event_count.shadow = event_count.shadow + 1
    else
        local dur = 30000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 22, current_rssi[i] - 22)
        events[i] = {end_ms = now + dur}
        event_count.fade = event_count.fade + 1
    end
end

sim:initialize()
while not sim:finished() do
    sim:step(1000)
end
log(string.format('[variability] events fired: drift=%d shadow=%d fade=%d',
    event_count.drift, event_count.shadow, event_count.fade))
local ok = sim:finalize()
if not ok then os.exit(1) end
