# Task list

## Implement litellm based multi-modal LLM engine

1. Save each page of the PDF into a separate PNG file:

```python
import fitz  # PyMuPDF

# Open the PDF file
doc = fitz.open("../data/input/lidia-internal/EDPB Opinion 12-2018.pdf")

# Choose the page (0-based index)
page_number = 0
page = doc.load_page(page_number)

# Render the page to a pixmap (image)
pix = page.get_pixmap(dpi=300)  # use higher dpi for better quality

# Save the pixmap as an image
pix.save("page_screenshot.png")
```

The dpi should be configurable.

2. Call an LLM model with an appropiate prompt ("Extract all text literally from the page" or something similar; experiment with it). Use litellm framework: https://docs.litellm.ai/docs/completion/vision

## Implement Aspose extractor engine

https://docs.aspose.com/pdf/python-cpp/extract-text/


## Implement extracted markdown evaluation metrics

Create a framework for extracted markdown evaluation. The evaluation compares the extracted text from different models with a "ground truth" (GT) markdown uploaded by the user. Let's reason if it is better to ask the GT from the user at the moment when they're uploading the PDF files, or after the extraction step, as a new "validation" step.

The GT is compared to the markdown results of each extraction task based on different metrics. The metrics are also pluggable, and reside in a new metrics/ folder. As a test and dummy metrics, implement a simple metrics that compares the percentual difference of word/character count of the extracted markdown and the GT.

### Clarifications

1. **When to collect GT**: Implement as a separate validation step after extraction (not during PDF upload):
   - More flexible - users may not have GT ready upfront
   - Users can extract first, review results, then validate what matters
   - Optional workflow - not all users need validation

2. **GT scope**: One GT markdown file per source document, compared against all extractor results for that document

3. **Metrics display**: Show results in a table comparing all extractors against GT for each selected metric

4. **Metrics architecture**: Follow the same plugin pattern as extractors for consistency and extensibility

### Thoughts, proposed solution

**Architecture Design:**

1. **Metrics Plugin System** (mirrors extractor architecture):
   - `benchmarkdown/metrics/` base directory
   - `benchmarkdown/metrics/base.py` - Protocol definition
   - `benchmarkdown/metrics/__init__.py` - MetricRegistry for discovery
   - Each metric in `benchmarkdown/metrics/{name}/` with standard structure

2. **Metric Protocol**:
   ```python
   class Metric(Protocol):
       async def compute(self, ground_truth: str, extracted: str) -> MetricResult
   ```

   MetricResult dataclass contains: score/value, description, and optional details

3. **Initial Metrics**:
   - `word_count_diff`: Percentage difference in word count
   - `char_count_diff`: Percentage difference in character count
   - Both grouped as "text_stats" metric family

4. **UI Integration**:
   - New "Validation" tab/section (appears after extraction completes)
   - Upload GT markdown file(s) - one per document
   - Select documents + extractors to validate
   - Select metrics to apply
   - Display results in comparison table

5. **Data Flow**:
   - User uploads GT markdown → stored in memory/temp
   - User selects extraction results to validate
   - System applies all selected metrics
   - Results shown in table: Document | Extractor | Metric | Score

**Implementation Plan:**
1. Create metrics base protocol and registry
2. Implement word_count_diff and char_count_diff metrics
3. Add validation UI section to app_builder.py
4. Test with sample documents
5. Document in implementation notes

### What was implemented

(To be filled after implementation)

## Implement price per page estimation

TBD
