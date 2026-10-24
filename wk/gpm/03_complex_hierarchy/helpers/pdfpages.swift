// Render PDF pages to PNG and dump their text, with macOS PDFKit.
// Why: the skill's §3.5 reads a datasheet with the Read tool's `pages`,
// which needs poppler's pdftoppm; this machine has no poppler, no PyMuPDF
// and no pypdf. Usage: swift pdfpages.swift <pdf> <outprefix> <first> <last> [dpi]
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 5, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    print("usage: pdfpages <pdf> <outprefix> <first> <last> [dpi]"); exit(2)
}
let first = Int(a[3])!, last = min(Int(a[4])!, doc.pageCount)
let dpi = a.count > 5 ? Double(a[5])! : 150.0
for n in first...last {
    guard let page = doc.page(at: n - 1) else { continue }
    let box = page.bounds(for: .mediaBox)
    let s = dpi / 72.0
    let w = Int(box.width * s), h = Int(box.height * s)
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                               bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                               isPlanar: false, colorSpaceName: .deviceRGB,
                               bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.current = ctx
    let cg = ctx.cgContext
    cg.setFillColor(NSColor.white.cgColor)
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: CGFloat(s), y: CGFloat(s))
    page.draw(with: .mediaBox, to: cg)
    NSGraphicsContext.restoreGraphicsState()
    let png = rep.representation(using: .png, properties: [:])!
    try! png.write(to: URL(fileURLWithPath: "\(a[2])-\(n).png"))
    try! (page.string ?? "").write(toFile: "\(a[2])-\(n).txt", atomically: true, encoding: .utf8)
    print("page \(n): \(a[2])-\(n).png")
}
