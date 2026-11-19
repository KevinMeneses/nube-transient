-- Abre una pestaña de demo: pista con el loop de batería de prueba (fader en -inf, no suena), Nube Transient con un
-- preset, ventana del FX flotante y reproducción en loop. Cerrar con tests/ui_close.lua.
-- Opciones en tests/out/demo_opts.txt: "preset [audio]" (REAPER no hereda el entorno).
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local of = io.open(ROOT .. "/out/demo_opts.txt"); local OPT = of and of:read("*l") or ""; if of then of:close() end
local PRESET = tonumber(OPT:match("^(%S+)") or "22")
local AUDIO = OPT:match("^%S+%s+(.+)$") or (ROOT .. "/signals/lib_loop.wav")
if not reaper.file_exists(AUDIO) then AUDIO = ROOT .. "/signals/hits.wav" end
reaper.Main_OnCommand(40859, 0)
local TAB = ROOT .. "/out/_tab_demo.rpp"; reaper.Main_SaveProjectEx(0, TAB, 0); reaper.Main_openProject("noprompt:" .. TAB)
local P = reaper.EnumProjects(-1)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(P, 0)
reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "Nube Transient demo", true)
reaper.SetMediaTrackInfo_Value(tr, "D_VOL", 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(AUDIO); reaper.SetMediaItemTake_Source(take, src)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", reaper.GetMediaSourceLength(src))
reaper.UpdateArrange()
local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Transient/nube_transient.jsfx", false, -1)
reaper.TrackFX_SetParam(tr, fx, 13, PRESET)
reaper.TrackFX_Show(tr, fx, 3)
reaper.GetSet_LoopTimeRange2(P, true, true, 0, reaper.GetMediaSourceLength(src), false)
reaper.GetSetRepeat(1)
reaper.OnPlayButtonEx(P)
reaper.Main_SaveProject(P, false)
local f = io.open(ROOT .. "/out/ui.txt", "w"); f:write("done\n"); f:close()
