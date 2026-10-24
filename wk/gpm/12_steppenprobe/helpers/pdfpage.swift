// Render pages of a PDF to PNG with macOS PDFKit (poppler is not installed).
// Uses PDFPage.thumbnail so page /Rotate is honoured.
// usage: swift pdfpage.swift <pdf> <first> <last> <dpi> <outprefix>
import Foundation
import PDFKit
import AppKit
let a = CommandLine.arguments
let doc = PDFDocument(url: URL(fileURLWithPath: a[1]))!
let first = Int(a[2])!, last = min(Int(a[3])!, doc.pageCount)
let dpi = CGFloat(Double(a[4])!)
print("pages: \(doc.pageCount)")
for i in first...last {
  guard let page = doc.page(at: i-1) else { continue }
  var box = page.bounds(for: .mediaBox)
  if page.rotation % 180 != 0 { box = CGRect(x: 0, y: 0, width: box.height, height: box.width) }
  let s = dpi / 72.0
  let img = page.thumbnail(of: CGSize(width: box.width * s, height: box.height * s), for: .mediaBox)
  guard let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
        let png = rep.representation(using: .png, properties: [:]) else { continue }
  let out = "\(a[5])-\(i).png"
  try! png.write(to: URL(fileURLWithPath: out))
  print("wrote \(out) \(rep.pixelsWide)x\(rep.pixelsHigh)")
}
