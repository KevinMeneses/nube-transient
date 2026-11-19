-- Escribe los parámetros del Nube Transient de la pestaña de demo (la busca por nombre) en tests/out/dump.txt:
-- "índice|nombre|valor formateado|valor crudo" por línea.
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local f = io.open(OUT .. "/dump.txt", "w")
local i, P = 0, nil
while true do
  local p, fn = reaper.EnumProjects(i, "")
  if not p then break end
  if fn == OUT .. "/_tab_demo.rpp" then P = p end
  i = i + 1
end
if P then
  local tr = reaper.GetTrack(P, 0)
  for p = 0, reaper.TrackFX_GetNumParams(tr, 0) - 1 do
    local _, n = reaper.TrackFX_GetParamName(tr, 0, p, ""); local _, v = reaper.TrackFX_GetFormattedParamValue(tr, 0, p, "")
    f:write(p, "|", n, "|", v, "|", reaper.TrackFX_GetParam(tr, 0, p), "\n")
  end
end
f:write("done\n"); f:close()
