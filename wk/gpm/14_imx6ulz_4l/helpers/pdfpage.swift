// pdfpage.swift -- stand-in for poppler's pdftotext / pdftoppm, which this
// machine lacks (the skill's §3.5 and the Read tool's PDF pages both need them).
// usage: swift pdfpage.swift <pdf> text <first> <last>
//        swift pdfpage.swift <pdf> png <page> <dpi> <out.png> [x0 y0 x1 y1 as fractions]
//        swift pdfpage.swift <pdf> count
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("cannot open pdf\n".data(using: .utf8)!); exit(2)
}
switch a[2] {
case "count":
    print(doc.pageCount)
case "text":
    let f = Int(a[3])!, l = Int(a[4])!
    for i in f...l {
        guard let p = doc.page(at: i - 1) else { continue }
        print("===== page \(i) =====")
        print(p.string ?? "")
    }
case "png":
    let n = Int(a[3])!, dpi = Double(a[4])!, out = a[5]
    guard let p = doc.page(at: n - 1) else { exit(3) }
    let box = p.bounds(for: .mediaBox)
    var crop = CGRect(x: 0, y: 0, width: 1, height: 1)
    if a.count >= 10 {
        let x0 = Double(a[6])!, y0 = Double(a[7])!, x1 = Double(a[8])!, y1 = Double(a[9])!
        crop = CGRect(x: x0, y: y0, width: x1 - x0, height: y1 - y0)
    }
    let s = dpi / 72.0
    let w = Int(box.width * crop.width * s), h = Int(box.height * crop.height * s)
    let cs = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { exit(4) }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    // crop fractions are from the TOP-left of the page
    ctx.scaleBy(x: s, y: s)
    ctx.translateBy(x: -box.width * crop.minX, y: -box.height * (1 - crop.maxY))
    p.draw(with: .mediaBox, to: ctx)
    guard let img = ctx.makeImage() else { exit(5) }
    let rep = NSBitmapImageRep(cgImage: img)
    guard let data = rep.representation(using: .png, properties: [:]) else { exit(6) }
    try! data.write(to: URL(fileURLWithPath: out))
    print("wrote \(out) \(w)x\(h)")
default:
    exit(2)
}
