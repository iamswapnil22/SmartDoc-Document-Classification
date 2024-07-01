import { GlobalWorkerOptions } from 'pdfjs-dist/build/pdf';

// Set the workerSrc property to point to the PDF.js worker file
GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/4.3.136/pdf.worker.min.js`;
