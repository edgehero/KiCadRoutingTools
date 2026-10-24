// pdf_tool.swift -- poppler stand-in for this run (pdftotext / pdftoppm are not
// installed, and the Read tool's PDF pages need pdftoppm).
//   swift pdf_tool.swift text <pdf> <first> <last>        page text to stdout
//   swift pdf_tool.swift find <pdf> <needle>              pages whose text contains needle
//   swift pdf_tool.swift render <pdf> <page> <dpi> <out.png> [x0 y0 x1 y1 as fractions]
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
func die(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(2) }
if a.count < 3 { die("usage: text|find|render <pdf> ...") }
guard let doc = PDFDocument(url: URL(fileURLWithPath: a[2])) else { die("cannot open \(a[2])") }
switch a[1] {
case "text":
    let f = Int(a[3])!, l = min(Int(a[4])!, doc.pageCount)
    for i in f...l {
        print("===== page \(i)")
        print(doc.page(at: i - 1)?.string ?? "")
    }
case "find":
    let needle = a[3].lowercased()
    for i in 0..<doc.pageCount {
        if let s = doc.page(at: i)?.string?.lowercased(), s.contains(needle) { print(i + 1) }
    }
case "render":
    let pn = Int(a[3])!, dpi = Double(a[4])!, out = a[5]
    guard let page = doc.page(at: pn - 1) else { die("no page \(pn)") }
    let box = page.bounds(for: .mediaBox)
    var crop = box
    if a.count >= 10 {
        let x0 = Double(a[6])!, y0 = Double(a[7])!, x1 = Double(a[8])!, y1 = Double(a[9])!
        // fractions measured from the TOP-left of the page
        crop = CGRect(x: box.minX + box.width * x0, y: box.minY + box.height * (1 - y1),
                      width: box.width * (x1 - x0), height: box.height * (y1 - y0))
    }
    let scale = dpi / 72.0
    let w = Int(crop.width * scale), h = Int(crop.height * scale)
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                               samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                               colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    let cg = ctx.cgContext
    cg.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: scale, y: scale)
    cg.translateBy(x: -crop.minX, y: -crop.minY)
    page.draw(with: .mediaBox, to: cg)
    let data = rep.representation(using: .png, properties: [:])!
    try! data.write(to: URL(fileURLWithPath: out))
    print("wrote \(out) \(w)x\(h)")
default:
    die("unknown command \(a[1])")
}
