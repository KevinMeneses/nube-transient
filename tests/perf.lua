-- CPU: render de 60 s sin plugin y con 10 instancias (Golpe con ataque, y el peor caso: Continuo + banda +
-- lookahead + mezcla). Escribe tests/out/perf.txt. Uso: REAPER -nonewinst tests/perf.lua
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local AUDIO = os.getenv("HOME") .. "/Music/ClaudeBeats/Master/Nube baja (master X20).wav"
if not reaper.file_exists(AUDIO) then AUDIO = OUT .. "/../signals/lib_loop.wav" end
local f = io.open(OUT .. "/perf.txt", "w")
local PREV = reaper.EnumProjects(-1)   -- pestaña activa de antes (puede ser de otra sesión): se restaura al final
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemTake_Source(take, reaper.PCM_Source_CreateFromFile(AUDIO))
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", 60)
reaper.SetMediaItemInfo_Value(item, "B_LOOPSRC", 1)
local function render(name, nfx, setup)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  for k = 1, nfx do local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Transient/nube_transient.jsfx", false, -1); setup(fx) end
  os.remove(OUT .. "/" .. name .. ".wav")
  reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true); reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true); reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
  local t0 = reaper.time_precise(); reaper.Main_OnCommand(42230, 0); return reaper.time_precise() - t0
end
local t_empty = render("perf_vacio", 0, function() end)
-- slider N = parámetro N-1
local t_golpe = render("perf_golpe", 10, function(fx)
  for p, v in pairs({[0] = 6, [1] = -10, [7] = 2}) do reaper.TrackFX_SetParam(tr, fx, p, v) end
end)
local t_full = render("perf_todo", 10, function(fx)
  for p, v in pairs({[0] = 5, [1] = -6, [2] = 1, [7] = 5, [8] = 1, [11] = 80}) do reaper.TrackFX_SetParam(tr, fx, p, v) end
end)
local function pct(t) return (t - t_empty) / 10 / 60 * 100 end
f:write(string.format("sin plugin %.2f s | 10 x Golpe %.2f s (%.2f %% c/u) | 10 x peor caso %.2f s (%.2f %% c/u) (60 s de audio)\n",
  t_empty, t_golpe, pct(t_golpe), t_full, pct(t_full)))
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_perf.rpp", 0); reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_perf.rpp"); reaper.Main_OnCommand(40860, 0)
if PREV and reaper.ValidatePtr(PREV, "ReaProject*") then reaper.SelectProjectInstance(PREV) end
f:write("done\n"); f:close()
