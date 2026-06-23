# Context Scope Design

## Goal

Add an explicit current-content scope control to the MarginNote web panel so the user can choose automatic context, selected text/node only, or full-document retrieval.

## User Experience

The current content box exposes a segmented control: Auto, Selection, Full Text. Auto prefers the current PDF selection or MN node, but falls back to full-document retrieval when no selection exists or the prompt clearly asks for the whole document. Selection uses only the current PDF selection and selected MN node. Full Text ignores accidental selections and retrieves relevant chunks from the current PDF.

## Backend Behavior

Every web request includes `contextScope` with one of `auto`, `selection`, or `document`. The Companion normalizes aliases and chooses the effective scope for the request. Document scope resolves the current PDF from `pdfPath`, `documentPath`, the existing PDF cache, the MN database, or known paths. It extracts PDF text with PyMuPDF once, stores a JSON text cache keyed by book id and PDF hash, chunks the text by page, and retrieves the most relevant chunks for the prompt.

## Error Handling

If the user chooses Full Text and no PDF path/cache is readable, the model input includes a clear full-text-read failure instead of pretending the full document was visible. Selection mode never tries to read the PDF file. Auto mode falls back to the same clear failure only when it actually needs document context.

## Tests

Tests cover context-scope normalization, selection-vs-document routing, document retrieval inclusion in model input, UI controls, payload propagation, and JavaScript syntax.
