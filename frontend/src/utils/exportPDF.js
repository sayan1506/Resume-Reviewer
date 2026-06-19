import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * Captures the element with id `elementId` and exports it as a PDF.
 * @param {string} elementId - The DOM id of the container to capture.
 * @param {string} filename  - Output filename (e.g. "review-report.pdf")
 */
export async function exportToPDF(elementId, filename = 'report.pdf') {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`exportToPDF: element #${elementId} not found`);
    return;
  }

  const canvas = await html2canvas(element, {
    scale: 2,           // retina-quality
    useCORS: true,
    backgroundColor: '#0a0e1a',   // match the app's dark background
  });

  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'px',
    format: [canvas.width / 2, canvas.height / 2],
  });

  pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2);
  pdf.save(filename);
}

/**
 * Exports plain text as a clean, selectable, multi-page A4 PDF (white background,
 * black text) — suitable for a submittable cover letter. Unlike exportToPDF this
 * does not rasterize the DOM, so the result is real text, not an image.
 * @param {string} text     - The text content to render.
 * @param {string} filename - Output filename (e.g. "cover-letter.pdf")
 */
export function exportTextToPDF(text, filename = 'cover-letter.pdf') {
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
  const margin = 56;
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const maxWidth = pageWidth - margin * 2;
  const lineHeight = 16;

  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(11);

  let y = margin;
  const paragraphs = (text || '').split('\n');

  paragraphs.forEach((para) => {
    const lines = para.length ? pdf.splitTextToSize(para, maxWidth) : [''];
    lines.forEach((line) => {
      if (y > pageHeight - margin) {
        pdf.addPage();
        y = margin;
      }
      pdf.text(line, margin, y);
      y += lineHeight;
    });
  });

  pdf.save(filename);
}
