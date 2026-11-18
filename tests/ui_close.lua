-- Detiene y cierra SOLO la pestaña de demo (la busca por su nombre de archivo) y vuelve a la que estaba activa.
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local TAB = OUT .. "/_tab_demo.rpp"
local prev = reaper.EnumProjects(-1)
local i = 0
while true do
  local p, fn = reaper.EnumProjects(i, "")
  if not p then break end
  if fn == TAB then
    reaper.SelectProjectInstance(p)
    reaper.OnStopButtonEx(p)
    reaper.Main_SaveProject(p, false)
    reaper.Main_OnCommand(40860, 0)
    break
  end
  i = i + 1
end
if prev and reaper.ValidatePtr(prev, "ReaProject*") then reaper.SelectProjectInstance(prev) end
local f = io.open(OUT .. "/ui.txt", "w"); f:write("closed\n"); f:close()
