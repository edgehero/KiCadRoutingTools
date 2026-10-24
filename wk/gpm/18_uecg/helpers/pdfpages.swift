// pdfpages.swift -- render or text-dump PDF pages with macOS PDFKit (poppler is not installed).
// usage: swift pdfpages.swift text <pdf> <first> <last>
//        swift pdfpages.swift png <pdf> <page> <out.png> [scale]
//        swift pdfpages.swift count <pdf>
import Foundation
import PDFKit
import AppKit
let a = CommandLine.arguments
guard a.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: a[2])) else { print("bad args or pdf"); exit(2) }
switch a[1] {
case "count": print(doc.pageCount)
case "text":
  let f = Int(a[3])!, l = Int(a[4])!
  for i in f...l { if let p = doc.page(at: i-1) { print("=== PAGE \(i) ==="); print(p.string ?? "") } }
case "find":
  let needle = a[3].lowercased()
  for i in 0..<doc.pageCount { if let s = doc.page(at: i)?.string?.lowercased(), s.contains(needle) { print(i+1) } }
case "png":
  let n = Int(a[3])!, out = a[4]; let scale = a.count > 5 ? Double(a[5])! : 3.0
  guard let p = doc.page(at: n-1) else { exit(3) }
  let b = p.bounds(for: .mediaBox)
  let w = Int(b.width*scale), h = Int(b.height*scale)
  let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
  NSGraphicsContext.saveGraphicsState()
  let ctx = NSGraphicsContext(bitmapImageRep: rep)!
  NSGraphicsContext.current = ctx
  let cg = ctx.cgContext
  cg.setFillColor(NSColor.white.cgColor); cg.fill(CGRect(x:0,y:0,width:w,height:h))
  cg.scaleBy(x: scale, y: scale)
  p.draw(with: .mediaBox, to: cg)
  NSGraphicsContext.restoreGraphicsState()
  try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
  print("wrote \(out) \(w)x\(h)")
default: print("unknown mode")
}
