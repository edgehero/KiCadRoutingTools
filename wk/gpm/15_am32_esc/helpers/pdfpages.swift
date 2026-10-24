// pdfpages.swift -- render PDF pages to PNG and dump their text with Apple's PDFKit.
// Why: the skill (SKILL.md 3.5) reads datasheets with pdftotext/pdftoppm (poppler),
// and the Read tool renders PDFs through pdftoppm too; neither is installed here.
// Usage: swift pdfpages.swift <pdf> <out_prefix> <first> <last> [dpi]
//   writes <out_prefix>-<N>.png and <out_prefix>-<N>.txt for pages first..last (1-based)
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 5, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: pdfpages <pdf> <prefix> <first> <last> [dpi]\n".data(using: .utf8)!)
    exit(2)
}
let prefix = a[2]
let first = Int(a[3]) ?? 1
let last = min(Int(a[4]) ?? doc.pageCount, doc.pageCount)
let dpi = a.count > 5 ? (Double(a[5]) ?? 150) : 150
print("pages: \(doc.pageCount)")
for n in first...last {
    guard let page = doc.page(at: n - 1) else { continue }
    let txt = page.string ?? ""
    try? txt.write(toFile: "\(prefix)-\(n).txt", atomically: true, encoding: .utf8)
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72.0
    let w = Int(box.width * scale), h = Int(box.height * scale)
    guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                                     bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                     isPlanar: false, colorSpaceName: .deviceRGB,
                                     bytesPerRow: 0, bitsPerPixel: 0) else { continue }
    NSGraphicsContext.saveGraphicsState()
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.current = ctx
    let cg = ctx.cgContext
    cg.setFillColor(NSColor.white.cgColor)
    cg.fill(CGRect(x: 0, y: 0, width: w, height: h))
    cg.scaleBy(x: scale, y: scale)
    cg.translateBy(x: -box.origin.x, y: -box.origin.y)
    page.draw(with: .mediaBox, to: cg)
    NSGraphicsContext.restoreGraphicsState()
    if let png = rep.representation(using: .png, properties: [:]) {
        try? png.write(to: URL(fileURLWithPath: "\(prefix)-\(n).png"))
    }
    print("page \(n): \(txt.count) chars")
}
