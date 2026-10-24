// helpers/pdftool.swift -- poppler stand-in for this machine (no pdftotext / pdftoppm installed).
// usage:
//   swift pdftool.swift text <pdf> <first> <last>          print the text of pages first..last (1-based)
//   swift pdftool.swift find <pdf> <needle>                print the page numbers whose text contains needle
//   swift pdftool.swift png  <pdf> <page> <dpi> <out.png>  render one page
//   swift pdftool.swift crop <pdf> <page> <dpi> <x0> <y0> <x1> <y1> <out.png>  render a crop (fractions 0..1 of the page, y down)
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: a[2])) else {
    FileHandle.standardError.write("cannot open pdf\n".data(using: .utf8)!); exit(2)
}
func render(_ pi: Int, _ dpi: Double, _ crop: (Double, Double, Double, Double)?, _ out: String) {
    guard let page = doc.page(at: pi - 1) else { print("no page"); exit(2) }
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72.0
    var (x0, y0, x1, y1) = (0.0, 0.0, 1.0, 1.0)
    if let c = crop { (x0, y0, x1, y1) = c }
    let w = Int(box.width * scale * (x1 - x0)), h = Int(box.height * scale * (y1 - y0))
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                               samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                               colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    let cg = ctx.cgContext
    cg.setFillColor(NSColor.white.cgColor)
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: scale, y: scale)
    // PDF origin is bottom-left; crop fractions are measured from the top.
    cg.translateBy(x: -box.width * x0, y: -box.height * (1.0 - y1))
    page.draw(with: .mediaBox, to: cg)
    let data = rep.representation(using: .png, properties: [:])!
    try! data.write(to: URL(fileURLWithPath: out))
    print("wrote \(out) \(w)x\(h)")
}
switch a[1] {
case "text":
    let f = Int(a[3])!, l = Int(a[4])!
    for i in f...l { if let p = doc.page(at: i - 1) { print("=== page \(i) ==="); print(p.string ?? "") } }
case "find":
    for i in 0..<doc.pageCount { if let s = doc.page(at: i)?.string, s.localizedCaseInsensitiveContains(a[3]) { print(i + 1) } }
case "png":
    render(Int(a[3])!, Double(a[4])!, nil, a[5])
case "crop":
    render(Int(a[3])!, Double(a[4])!, (Double(a[5])!, Double(a[6])!, Double(a[7])!, Double(a[8])!), a[9])
default:
    print("unknown verb"); exit(2)
}
