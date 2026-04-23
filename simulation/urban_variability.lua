-- Urban multipath SNR-variability simulator.
--
-- Runs alongside an A/B sim run. At each tick, picks one mutable link and
-- applies one of three realistic propagation events:
--   small drift  (60%) - mean SNR shifts by +/-3 dB; persists indefinitely
--   shadow      (30%) - SNR drops 8 dB for 60-120s, then restores
--   deep fade   (10%) - SNR drops 20 dB for 30-90s (link effectively dead)
--
-- Persistent drifts accumulate over the run; shadow and deep-fade events
-- self-expire. A link already inside an active shadow/fade is skipped
-- until its event resolves.

-- Mutable links: every edge in the urban_variability topology (bidirectional).
-- Baseline SNR/RSSI from build_urban_scenario.py.
local BASE_SNR  = 8.0
local BASE_RSSI = -105.0

local links = {
    {from='alice', to='R1'}, {from='alice', to='R2'},
    {from='R1', to='R3'}, {from='R3', to='R5'}, {from='R5', to='R7'},
    {from='R2', to='R4'}, {from='R4', to='R6'}, {from='R6', to='R8'},
    {from='R1', to='R2'}, {from='R3', to='R4'}, {from='R5', to='R6'}, {from='R7', to='R8'},
    {from='R7', to='bob'}, {from='R8', to='bob'},
    {from='R1', to='R4'}, {from='R5', to='R8'},
}

-- Per-link current mean (starts at baseline, accumulates drift)
local current_snr = {}
local current_rssi = {}
-- Active shadow/fade events: keyed by link index, value = end_ms
local events = {}

local function key(i) return i end

function init_variability()
    math.randomseed(42)  -- stable RNG; real seed variance comes from sim:seed
    for i, l in ipairs(links) do
        current_snr[i] = BASE_SNR
        current_rssi[i] = BASE_RSSI
    end
    sim:log('[variability] initialized ' .. #links .. ' mutable links')
end

function apply_variability()
    local now = sim:time()

    -- Step 1: expire events whose time is up; restore base mean
    for i, e in pairs(events) do
        if now >= e.end_ms then
            sim:set_link(links[i].from, links[i].to, current_snr[i], current_rssi[i])
            events[i] = nil
        end
    end

    -- Step 2: pick a link not currently in an event
    local candidates = {}
    for i = 1, #links do
        if not events[i] then table.insert(candidates, i) end
    end
    if #candidates == 0 then return end
    local i = candidates[math.random(#candidates)]
    local l = links[i]
    local r = math.random()

    if r < 0.6 then
        -- Small drift: persistent +/-3 dB, at most +/-1 per event
        local drift = (math.random() - 0.5) * 6
        current_snr[i] = math.max(-4, math.min(15, current_snr[i] + drift))
        current_rssi[i] = current_rssi[i] + drift  -- rssi correlates
        sim:set_link(l.from, l.to, current_snr[i], current_rssi[i])
    elseif r < 0.9 then
        -- Shadow: -8 dB for 60-120s
        local dur = 60000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 8, current_rssi[i] - 8)
        events[i] = {end_ms = now + dur}
    else
        -- Deep fade: -20 dB for 30-90s (link effectively broken)
        local dur = 30000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 20, current_rssi[i] - 20)
        events[i] = {end_ms = now + dur}
    end
end
