// Render PDF pages to PNG and/or dump their text with macOS PDFKit.
// Why: poppler (pdftotext/pdftoppm) is not installed on this machine, so the
// skill's §3.5 recipe and the Read tool's PDF `pages` both fail.
// usage: swift pdf_render.swift <pdf> text <first> <last>
//        swift pdf_render.swift <pdf> png <first> <last> <out_prefix> [dpi]
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 5, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    print("usage: pdf_render.swift <pdf> text|png <first> <last> [prefix] [dpi]"); exit(2)
}
let mode = a[2]
let first = max(1, Int(a[3]) ?? 1)
let last = min(doc.pageCount, Int(a[4]) ?? doc.pageCount)
print("pages: \(doc.pageCount)")
for i in first...last {
    guard let page = doc.page(at: i - 1) else { continue }
    if mode == "text" {
        print("===== page \(i) =====")
        print(page.string ?? "")
    } else {
        let prefix = a.count > 5 ? a[5] : "page"
        let dpi = a.count > 6 ? (Double(a[6]) ?? 200) : 200
        let box = page.bounds(for: .mediaBox)
        let scale = dpi / 72.0
        let w = Int(box.width * scale), h = Int(box.height * scale)
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
        cg.scaleBy(x: scale, y: scale)
        page.draw(with: .mediaBox, to: cg)
        NSGraphicsContext.restoreGraphicsState()
        let out = "\(prefix)-\(i).png"
        try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
        print("wrote \(out)")
    }
}
