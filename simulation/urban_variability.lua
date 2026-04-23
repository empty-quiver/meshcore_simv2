-- urban_variability.lua
-- Driver script for the SNR-variability dynamic-topology A/B scenario.
-- Usage: orchestrator --lua simulation/urban_variability.lua simulation/urban_variability_test.json
--
-- At each tick, picks one mutable link and applies one of three realistic
-- propagation events:
--   small drift (60%) - persistent +/-3 dB shift on the link mean
--   shadow      (30%) - -8 dB for 60-120s, then restores
--   deep fade   (10%) - -20 dB for 30-90s (link effectively dead)
--
-- Called from JSON commands: init_variability at t=0, apply_variability every 20s.

local BASE_SNR  = 4.0
local BASE_RSSI = -115.0

local links = {
    {from='alice', to='R1'}, {from='alice', to='R2'},
    {from='R1', to='R3'}, {from='R3', to='R5'}, {from='R5', to='R7'},
    {from='R2', to='R4'}, {from='R4', to='R6'}, {from='R6', to='R8'},
    {from='R3', to='R4'}, {from='R5', to='R6'},
    {from='R7', to='bob'}, {from='R8', to='bob'},
}

local current_snr = {}
local current_rssi = {}
local events = {}   -- key = link index, value = {end_ms}
local event_count = {drift=0, shadow=0, fade=0}

function init_variability()
    -- math.randomseed uses Lua's RNG; we want reproducibility but also
    -- seed-variance across runs, so use sim-provided time as seed mix.
    math.randomseed(os.time() + sim:time())
    -- burn a few - Lua's LCG is weak on the first few calls
    for i = 1, 5 do math.random() end
    for i, l in ipairs(links) do
        current_snr[i] = BASE_SNR
        current_rssi[i] = BASE_RSSI
    end
    log("[variability] init done, " .. #links .. " mutable links")
end

function apply_variability()
    local now = sim:time()

    -- Expire any events past their end time
    for i, e in pairs(events) do
        if now >= e.end_ms then
            sim:set_link(links[i].from, links[i].to, current_snr[i], current_rssi[i])
            events[i] = nil
        end
    end

    -- Pick a link not currently inside an event
    local candidates = {}
    for i = 1, #links do
        if not events[i] then table.insert(candidates, i) end
    end
    if #candidates == 0 then return end
    local i = candidates[math.random(#candidates)]
    local l = links[i]
    local r = math.random()

    if r < 0.6 then
        -- Persistent small drift (+/-3 dB)
        local drift = (math.random() - 0.5) * 6
        current_snr[i] = math.max(-2, math.min(12, current_snr[i] + drift))
        current_rssi[i] = current_rssi[i] + drift
        sim:set_link(l.from, l.to, current_snr[i], current_rssi[i])
        event_count.drift = event_count.drift + 1
    elseif r < 0.9 then
        -- Shadow: -10 dB for 60-120s (drops a 4 dB link to -6, near threshold)
        local dur = 60000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 10, current_rssi[i] - 10)
        events[i] = {end_ms = now + dur}
        event_count.shadow = event_count.shadow + 1
    else
        -- Deep fade: -22 dB for 30-90s (link effectively dead at SF10 sensitivity)
        local dur = 30000 + math.random(60000)
        sim:set_link(l.from, l.to, current_snr[i] - 22, current_rssi[i] - 22)
        events[i] = {end_ms = now + dur}
        event_count.fade = event_count.fade + 1
    end
end

-- ===== Main loop =====
sim:initialize()
while not sim:finished() do
    sim:step(1000)
end

log(string.format("[variability] events fired: drift=%d shadow=%d fade=%d",
    event_count.drift, event_count.shadow, event_count.fade))

local ok = sim:finalize()
if not ok then os.exit(1) end
