import time
import sys
from pathlib import Path

import multiprocessing
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

def main(in_file: str, out_file: str) -> None:
     pdf_options = PdfPipelineOptions(
         do_ocr=False,
         do_table_structure=True,
         accelerator_options=AcceleratorOptions(
             num_threads=multiprocessing.cpu_count(),
         )
     )

     pdf_options.table_structure_options.mode = TableFormerMode.FAST

     converter = DocumentConverter(format_options={
         InputFormat.PDF: PdfFormatOption(
             pipeline_options=pdf_options,
             backend=PyPdfiumDocumentBackend
         )
     })

     start = time.perf_counter()
     result = converter.convert(str(in_file))
     text = result.document.export_to_markdown()
     end = time.perf_counter()
     print(f"Docling converter took {end - start:.2f} seconds")
     Path(out_file).write_text(text)


if __name__ == "__main__":
    if sys.argv and len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Please provide an input PDF file path and an output markdown file path as a command-line argument.")
        sys.exit(1)

