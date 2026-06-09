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
