// Render one page of a PDF to PNG (poppler's pdftoppm is not installed here).
// Uses PDFPage.thumbnail, which honours the page's /Rotate.
// usage: swift pdfpage.swift <in.pdf> <page 1-based> <out.png> [scale]
import Foundation
import PDFKit
import AppKit

let a = CommandLine.arguments
guard a.count >= 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])),
      let n = Int(a[2]), let page = doc.page(at: n - 1) else {
    print("usage: pdfpage.swift in.pdf page out.png [scale]"); exit(2)
}
let scale = a.count > 4 ? CGFloat(Double(a[4]) ?? 4.0) : 4.0
var box = page.bounds(for: .mediaBox)
if page.rotation % 180 != 0 { box = CGRect(x: 0, y: 0, width: box.height, height: box.width) }
let img = page.thumbnail(of: NSSize(width: box.width * scale, height: box.height * scale), for: .mediaBox)
guard let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
      let png = rep.representation(using: .png, properties: [:]) else { print("render failed"); exit(1) }
try! png.write(to: URL(fileURLWithPath: a[3]))
print("pages=\(doc.pageCount) rotation=\(page.rotation) wrote \(a[3]) \(rep.pixelsWide)x\(rep.pixelsHigh)")
