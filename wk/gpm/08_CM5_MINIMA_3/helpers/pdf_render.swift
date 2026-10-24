// Render pages of a PDF to PNG with PDFKit (no poppler on this Mac).
// usage: swift pdf_render.swift in.pdf outprefix firstPage lastPage scale
import Foundation
import PDFKit
import AppKit
let a = CommandLine.arguments
let doc = PDFDocument(url: URL(fileURLWithPath: a[1]))!
let first = Int(a[3])!, last = min(Int(a[4])!, doc.pageCount)
let scale = CGFloat(Double(a[5]) ?? 3.0)
print("pages:", doc.pageCount)
for i in first...last {
  let page = doc.page(at: i-1)!
  let box = page.bounds(for: .mediaBox)
  let w = Int(box.width*scale), h = Int(box.height*scale)
  let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
  NSGraphicsContext.saveGraphicsState()
  let ctx = NSGraphicsContext(bitmapImageRep: rep)!
  NSGraphicsContext.current = ctx
  ctx.cgContext.setFillColor(NSColor.white.cgColor)
  ctx.cgContext.fill(CGRect(x:0,y:0,width:w,height:h))
  ctx.cgContext.scaleBy(x: scale, y: scale)
  page.draw(with: .mediaBox, to: ctx.cgContext)
  NSGraphicsContext.restoreGraphicsState()
  let png = rep.representation(using: .png, properties: [:])!
  try! png.write(to: URL(fileURLWithPath: "\(a[2])-\(i).png"))
  if let t = page.string { try! t.write(toFile: "\(a[2])-\(i).txt", atomically: true, encoding: .utf8) }
}
