// Ventana del FX de Nube Transient: imprime "id x y ancho alto" (puntos). swift tests/winid.swift
import CoreGraphics
let l = CGWindowListCopyWindowInfo(.optionAll, kCGNullWindowID) as! [[String: Any]]
for w in l {
    if let n = w[kCGWindowName as String] as? String, n.hasPrefix("JS: Nube Transient -"),
       let b = w[kCGWindowBounds as String] as? [String: Any] {
        print(w[kCGWindowNumber as String]!, b["X"]!, b["Y"]!, b["Width"]!, b["Height"]!)
    }
}
