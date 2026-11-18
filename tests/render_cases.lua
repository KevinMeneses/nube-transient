-- Carga Nube Transient en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
-- tests/out/only.txt (opcional): lista de nombres separados por coma; solo esos casos.
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
local SIG = ROOT .. "/signals/"
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- slider N (1..14) = parámetro N-1. Los sliders con forma :log=mid van normalizados 0..1
local LOGP = {[5] = {1, 100, 10}, [7] = {5, 2000, 150}, [10] = {30, 12000, 600}}
local function to_norm(s, v)
  local mn, mx, mid = table.unpack(LOGP[s])
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
local function lib(name) local f = SIG .. "lib_" .. name .. ".wav"; return reaper.file_exists(f) and ("lib_" .. name .. ".wav") or "hits.wav" end

local CASES = {
  -- iguales al claude_cola_corta original (sus 4 sliders) con el preset equivalente
  {"orig_def_hits",  "hits.wav",       {40, 60, -12, 6}, "orig"},
  {"p3_hits",        "hits.wav",       {[14] = 3}},
  {"orig_def_snare", lib("snare"),     {40, 60, -12, 6}, "orig"},
  {"p3_snare",       lib("snare"),     {[14] = 3}},
  {"orig_def_808",   lib("b808"),      {40, 60, -12, 6}, "orig"},
  {"p3_808",         lib("b808"),      {[14] = 3}},
  {"orig_nb_snare",  lib("snare"),     {70, 130, -4, 6}, "orig"},
  {"p1_snare",       lib("snare"),     {[14] = 1}},
  {"orig_nb_clap",   lib("clap"),      {60, 100, -8, 6}, "orig"},
  {"p2_clap",        lib("clap"),      {[14] = 2}},
  {"orig_nb_kick",   lib("kick"),      {70, 130, -4, 6}, "orig"},
  {"p1_kick",        lib("kick"),      {[14] = 1}},
  -- contra el prototipo numpy (tests/proto.py)
  {"pr_g_at",        "hits.wav",       {[1] = 6, [8] = 2}},
  {"pr_g_mix",       "hits.wav",       {[1] = -6, [2] = -10, [12] = 50, [13] = 3}},
  {"pr_c",           "hits.wav",       {[3] = 1, [1] = 6, [2] = -10, [7] = 200}},
  {"pr_band_lo",     "bands.wav",      {[9] = 1, [10] = 200, [2] = -20}},
  {"pr_band_hi",     "bands.wav",      {[9] = 2, [10] = 200, [2] = -20}},
  {"pr_listen1",     "bands.wav",      {[9] = 1, [10] = 200, [2] = -20, [11] = 1}},
  {"pr_listen2",     "hits.wav",       {[2] = -12, [11] = 2}},
  {"pr_kick_c",      lib("kick"),      {[3] = 1, [1] = 5, [2] = -6, [7] = 300, [8] = 1.5}},
  {"pr_808_g",       lib("b808"),      {[1] = 4, [2] = -10, [5] = 25, [6] = 150, [7] = 200, [8] = 1}},
  -- teoría
  {"neutral",        "hits.wav",       {}},
  {"neutral_c",      "hits.wav",       {[3] = 1}},
  {"lvl_g0",         "hits.wav",       {[1] = 6, [2] = -12, [8] = 1}},
  {"lvl_g30",        "hits_m30.wav",   {[1] = 6, [2] = -12, [8] = 1}},
  {"lvl_c0",         "hits.wav",       {[3] = 1, [1] = 6, [2] = -12, [7] = 200}},
  {"lvl_c30",        "hits_m30.wav",   {[3] = 1, [1] = 6, [2] = -12, [7] = 200}},
  {"la_off",         "hits.wav",       {[1] = 6, [5] = 10}},
  {"la_3",           "hits.wav",       {[1] = 6, [5] = 10, [8] = 3}},
  {"tail_g",         "hits.wav",       {[2] = -12, [6] = 40, [7] = 60}},
  {"s45_c",          "sine45.wav",     {[3] = 1, [1] = 6, [2] = -6}},
  {"s45_g",          "sine45.wav",     {[1] = 6, [2] = -6}},
  {"band_flat",      "sine1k.wav",     {[9] = 1, [10] = 1000}},
  {"mix50",          "hits.wav",       {[2] = -12, [12] = 50}},
  {"gain6",          "sine1k.wav",     {[13] = 6}},
}
-- independencia del nivel con samples reales (0 dB y -30 dB)
for _, s in ipairs({"kick", "snare", "b808", "clap"}) do
  if reaper.file_exists(SIG .. "lib_" .. s .. ".wav") then
    for _, m in ipairs({{"g", {[1] = 5, [2] = -10, [8] = 1}}, {"c", {[3] = 1, [1] = 5, [2] = -10, [7] = 300}}}) do
      CASES[#CASES + 1] = {"lvl_" .. s .. "_" .. m[1] .. "0", "lib_" .. s .. ".wav", m[2]}
      CASES[#CASES + 1] = {"lvl_" .. s .. "_" .. m[1] .. "30", "lib_" .. s .. "_m30.wav", m[2]}
    end
  end
end
-- 808 ligado (sin salto de nivel en la 2a nota): solo se informa, es el límite de detectar por nivel
if reaper.file_exists(SIG .. "lib_d808_ligado.wav") then
  CASES[#CASES + 1] = {"leg_d808_p14", "lib_d808_ligado.wav", {[14] = 14}}
  CASES[#CASES + 1] = {"leg_b808_p14", "lib_b808_ligado.wav", {[14] = 14}}
end
-- presets sobre el sonido para el que están hechos (sin la librería: los golpes sintéticos)
local PSIG = {"snare", "clap", "snare", "kick", "kick", "kick", "kick", "snare", "snare", "snare", "clap", "clap",
              "b808", "d808", "b808", "hat", "hat", "loop", "loop", "loop", "rsnare", "dsnare", "-", "-"}
for p = 1, 24 do
  CASES[#CASES + 1] = {"preset" .. p, PSIG[p] == "-" and "hits.wav" or lib(PSIG[p]), {[14] = p}}
end

local only = nil
local of = io.open(OUT .. "/only.txt")
if of then only = {} for n in of:read("*a"):gmatch("[^,%s]+") do only[#only + 1] = n end of:close() end
local function wanted(name)
  if not only then return true end
  for _, n in ipairs(only) do if name:find(n, 1, true) then return true end end
  return false
end

local PREV = reaper.EnumProjects(-1)   -- pestaña activa de antes (puede ser de otra sesión): se restaura al final
reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 0)
reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN_AUTO", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN_AUTO", 0)

for _, c in ipairs(CASES) do
  local name, src, params, extra = c[1], c[2], c[3], c[4]
  if wanted(name) then
    local s = reaper.PCM_Source_CreateFromFile(SIG .. src)
    reaper.SetMediaItemTake_Source(take, s)
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", (reaper.GetMediaSourceLength(s)))
    reaper.UpdateItemInProject(item)
    while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
    local fx
    if extra == "orig" then
      fx = reaper.TrackFX_AddByName(tr, "JS:Claude/claude_cola_corta.jsfx", false, -1)
      if fx < 0 then log("ERROR no cargó claude_cola_corta") break end
      for i, v in ipairs(params) do reaper.TrackFX_SetParam(tr, fx, i - 1, v) end
    else
      fx = reaper.TrackFX_AddByName(tr, "JS:Nube Transient/nube_transient.jsfx", false, -1)
      if fx < 0 then log("ERROR no cargó el FX") break end
      if params[14] then reaper.TrackFX_SetParam(tr, fx, 13, params[14]) end
      for s_, v in pairs(params) do
        if s_ ~= 14 then
          if LOGP[s_] then reaper.TrackFX_SetParamNormalized(tr, fx, s_ - 1, to_norm(s_, v))
          else reaper.TrackFX_SetParam(tr, fx, s_ - 1, v) end
        end
      end
    end
    local file = OUT .. "/" .. name .. ".wav"
    os.remove(file)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT", "ZXZhdyAAAQ==", true) -- WAV 32 bits float
    reaper.Main_OnCommand(42230, 0)
    local vals = {}
    for k = 1, (extra == "orig" and 4 or 13) do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, k - 1, ""); vals[#vals + 1] = v end
    log("caso", name, src, table.concat(vals, " | "))
  end
end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp")
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
if PREV and reaper.ValidatePtr(PREV, "ReaProject*") then reaper.SelectProjectInstance(PREV) end
log("done")
logf:close()
