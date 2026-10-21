import { jsPDF } from 'jspdf'

export function downloadTxt(filename, content) {
  const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: filename })
  a.click(); URL.revokeObjectURL(url)
}

export function downloadPdf(filename, { original, rephrased, style, similarity }) {
  const doc = new jsPDF()
  let y = 20
  const write = (text, size = 11, bold = false) => {
    doc.setFont('helvetica', bold ? 'bold' : 'normal'); doc.setFontSize(size)
    doc.splitTextToSize(text, 175).forEach((line) => { if (y > 280) { doc.addPage(); y = 20 } doc.text(line, 17, y); y += size * 0.5 + 2 })
    y += 3
  }
  write('RePhraseAI - Rephrased Text', 16, true)
  write(`Style: ${style}   |   Semantic similarity: ${(similarity * 100).toFixed(1)}%`, 10)
  write('Original', 12, true); write(original)
  write('Rephrased', 12, true); write(rephrased)
  doc.save(filename)
}
