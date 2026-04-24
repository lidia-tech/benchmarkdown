# Benchmarkdown: An Open-Source Toolkit for Comparing Document-to-Markdown Extraction Services

## The deceptively hard problem

At Lidia, our enterprise legal intelligence platform, lawyers upload documents every day. Contracts, court rulings, notarial acts, regulatory filings — the system needs to ingest them all. The first step in our document processing pipeline is extracting clean, structured markdown from these files, so that downstream AI features (semantic chunking, summarization, legal search) can work with the content. On paper, this sounds straightforward: take a PDF, get text out. In practice, it turned out to be one of the hardest problems we faced.

The challenge is document diversity. Our clients upload anything from digitally born, clean contracts to scanned handwritten testaments, dog vaccination certificates, and faded photocopies of decades-old legal acts. A reasonable PDF parser with default settings handles about 90% of documents well enough. Getting to 95% requires tuning the parser and introducing OCR. Reaching 98% is genuinely hard. The last two percent? R&D spent literal weeks on those cases, and a stubborn 0.2% still resists all attempts.

This is the logarithmic curve of problem-solving: each additional percentage point of coverage requires exponentially more effort than the last. We needed a systematic way to evaluate and compare extraction services — not just eyeballing outputs, but measuring them.

## Introducing Benchmarkdown

Benchmarkdown is an open-source web application for comparing document-to-markdown extraction technologies. It wraps multiple extraction services behind a unified interface, allowing users to configure each service, run extractions on the same set of documents, and evaluate the results both qualitatively (side-by-side visual comparison) and quantitatively (automated metric computation against ground truth).

The application is built around two plugin systems. Extraction plugins wrap different PDF-to-markdown services, each discoverable at runtime — adding a new extractor requires creating a directory with three files and no changes to the core application. Metric plugins evaluate extraction quality against ground truth references, following the same pattern.

### The workflow

A typical session looks like this: you upload a set of documents, select one or more extraction configurations from your saved profiles, queue them as tasks, and hit "Run". The application extracts all documents with all selected configurations in parallel, then presents the results in a comparison view — either tabbed or side-by-side — where you can inspect the rendered markdown and the raw output. If you have ground truth references, you upload those and the system computes all available metrics, displaying them in a color-coded table.

Configuration profiles are saved as JSON files and persist across sessions, so you can build up a library of configurations for different document types ("scanned Italian contracts", "clean English PDFs", "handwritten notes") and quickly re-run comparisons when you upgrade a service or try a new one.

## Supported extractors

Benchmarkdown ships with six extraction plugins, covering a range of approaches from local open-source tools to cloud AI services.

**Docling** is IBM's open-source document conversion library, and the only fully local option. It supports multiple OCR engines (EasyOCR, Tesseract, RapidOCR, macOS native OCR) and provides table structure extraction in both fast and accurate modes. Running locally means zero API costs and no data leaving your machine — important when dealing with confidential legal documents.

**Azure Document Intelligence** is Microsoft's cloud document analysis service. It stands out for producing markdown output natively, without the post-processing conversion step that most other services require. The "prebuilt-layout" model handles text, tables, and structural elements, with optional locale hints for multilingual documents.

**AWS Textract** is Amazon's document extraction service, accessed through the `textractor` library. It supports handwriting recognition and form field extraction (key-value pairs), and documents are staged through an S3 bucket, which adds a setup step but integrates naturally into AWS-native workflows.

**LiteLLM Vision** takes a fundamentally different approach: it renders each PDF page as an image and sends it to a vision-capable language model. Through the LiteLLM framework, it supports any vision LLM provider — OpenAI, Anthropic, AWS Bedrock, Google, or a local model via Ollama. The extraction prompt is fully customizable. This approach trades speed for flexibility: the model "reads" the document the way a human would, which makes it particularly effective for cases where traditional OCR struggles — handwritten text, unusual layouts, mixed-language documents, or heavily degraded scans.

**LlamaParse** is LlamaIndex's cloud parsing service, offering an optional GPT-4o-enhanced mode for particularly difficult documents. **TensorLake** provides a cloud document ingestion API with specialized features like signature detection and figure summarization. Both are paid services with free tiers for evaluation.

## Why quantitative metrics matter

Qualitative comparison — looking at two markdown outputs side by side — is indispensable for understanding *what* went wrong, but it does not scale. When you have twenty documents, four extractors, and three configuration variants each, eyeballing 240 outputs is not practical. More importantly, qualitative assessment is subjective: two reviewers may disagree on whether a slightly garbled table is acceptable.

Quantitative metrics enable fast iteration. Change a configuration parameter, re-run the extraction, and check the numbers. If ROUGE-2 recall drops, you lost content. If precision drops, you introduced noise. This feedback loop is what makes it possible to systematically converge on a good generic configuration.

For our downstream tasks at Lidia, we care about two dimensions of extraction quality. First, *text fidelity*: the extracted text must faithfully reproduce the content of the source document. Second, *structural accuracy*: the markdown headings must align with the document's actual section structure. We break down extracted documents into semantically meaningful chunks for downstream processing — summarization, search, AI-assisted analysis — and heading boundaries are the primary signal for where one chunk ends and another begins. A perfectly transcribed document with all headings flattened to `##` level is nearly as bad as a garbled one, because the processing pipeline cannot distinguish sections from subsections.

This drove us to define metrics along both dimensions.

### Content fidelity: ROUGE-2 bigram overlap

For measuring text fidelity, we implemented a ROUGE-2 style word bigram overlap metric. The choice of bigrams over simpler alternatives was deliberate.

Single-word overlap (ROUGE-1) is too loose for our domain. Common Italian legal terms — "del", "contratto", "articolo", "comma" — appear in virtually every document and inflate scores between unrelated texts. Bigrams (consecutive word pairs) verify that content appears *in context*: "risoluzione del" and "del contratto" are distinct bigrams that only match if the extraction preserved the same word sequences.

Character-level similarity (Levenshtein distance or SequenceMatcher) is too sensitive to formatting noise — a single extra newline or a markdown bold marker tanks the score — and too slow for large documents (O(n*m) complexity). A 47K-character reference compared against a 12K extraction means ~560 million operations per pair.

The ROUGE-2 metric decomposes into three scores that tell different diagnostic stories:

- **Recall** measures content completeness: what fraction of the ground truth's bigrams appear in the extraction. Low recall means truncation or missing content.
- **Precision** measures content cleanliness: what fraction of the extraction's bigrams match the ground truth. Low precision means boilerplate, navigation artifacts, or hallucinated text.
- **F1** is the harmonic mean — a single summary score that balances both concerns.

A truncated-but-clean extraction (first 12K of a 47K document) gets high precision but low recall. A full-but-noisy extraction (content plus cookie banners and sidebar text) gets high recall but low precision. These are different problems requiring different fixes, and the metric distinguishes between them.

### Structural accuracy: heading metrics

For structural quality, Benchmarkdown provides two complementary metrics. *Heading F1* computes the F1 score between the heading structures of the ground truth and the extraction — treating headings as a set and measuring overlap. *Structure Similarity* uses a graph-based approach, building table-of-contents trees from both documents and computing their alignment score. Together, they capture whether the extractor correctly identified section boundaries and heading hierarchy.

## Benchmark results on READoc

To demonstrate the toolkit, we ran a benchmark on the [READoc](https://github.com/icip-cas/READoc) dataset, a publicly available collection of over 2,000 documents — academic papers from arXiv and README files from GitHub repositories — with human-verified ground truth markdown. Since our internal Lidia dataset contains confidential legal documents, we needed an openly available alternative, and READoc fit the bill. We used a 20-document sample — 10 from each subset — and evaluated four extractors.

### Overall results

| Extractor | ROUGE-2 F1 | Recall | Precision | Heading F1 | Avg. Time |
|-----------|-----------|--------|-----------|------------|-----------|
| AWS Textract | **83.2%** | **88.6%** | 79.0% | 84.3% | 23.2s |
| Azure Document Intelligence | 78.5% | 87.2% | 72.1% | 87.2% | 7.4s |
| Qwen3-VL-235B (via LiteLLM) | 78.7% | 77.3% | **82.7%** | **89.1%** | 237.1s |
| Docling (local, EasyOCR) | 75.8% | 73.9% | 77.9% | 86.0% | 31.2s |

Several patterns are worth noting.

**Textract leads on content fidelity**, with the highest ROUGE-2 F1 (83.2%) and the best recall (88.6%). It captures more of the source content than any other extractor in this benchmark. However, its precision (79.0%) suggests it also includes some extraneous text.

**The vision model (Qwen3-VL) produces the cleanest output** — highest precision at 82.7% — and the best heading structure (89.1% Heading F1). This makes intuitive sense: a large vision model "reads" the document holistically and tends to produce well-structured markdown. The trade-off is speed: at nearly four minutes per document on average, it is an order of magnitude slower than the traditional parsers.

**Azure Document Intelligence is the fastest cloud option** and achieves strong heading detection (87.2% Heading F1), but its lower precision (72.1%) indicates it tends to include formatting artifacts or extraneous content.

**Docling**, the only free local option, performs respectably across all metrics. Its recall is the lowest (73.9%), likely because the EasyOCR configuration we tested misses some content in complex academic layouts, but its precision is solid (77.9%).

### arXiv vs. GitHub subsets

The two subsets reveal how document complexity affects extraction quality:

| Subset | Textract | Azure DI | Qwen3-VL | Docling |
|--------|----------|----------|----------|---------|
| arXiv (ROUGE-2 F1) | 80.9% | 77.7% | 73.8% | 69.3% |
| GitHub (ROUGE-2 F1) | 85.4% | 79.2% | 83.6% | 82.3% |

All extractors perform better on GitHub READMEs than on arXiv papers. The gap is particularly pronounced for Docling (69.3% vs. 82.3%) and Qwen3-VL (73.8% vs. 83.6%). Academic papers with multi-column layouts, mathematical formulas, and complex tables are substantially harder to extract than single-column documentation pages — which aligns with the broader experience in the document AI field.

On the GitHub subset, recall scores are notably higher across the board (Textract reaches 95.1%), suggesting that simpler documents lose less content during extraction.

## Getting started

Benchmarkdown is available as an open-source project. Installation requires Python 3.11+ and `uv`:

```bash
$ git clone https://github.com/lidia-tech/benchmarkdown.git
$ cd benchmarkdown
$ uv sync --all-groups        # install all extractors
$ uv run python app.py         # launch the web UI
```

To install only specific extractors, use `uv sync --group docling` (or `textract`, `azure-document-intelligence`, etc.). Each extractor documents its own environment variables and credential setup in its README under `benchmarkdown/extractors/{name}/`.

Adding a new extractor requires creating a directory with three files (`__init__.py`, `config.py`, `extractor.py`) following the existing plugin pattern — no changes to the core application needed. The same applies to metrics.

## Conclusion

We are pleased to open-source Benchmarkdown for anyone who needs to select a document-to-markdown extraction service. The toolkit grew out of a real need at Lidia, where document diversity pushed us beyond what any single service could handle out of the box. We hope it contributes to a healthy competition between extraction service providers — and ultimately better results for their users.

The READoc benchmark results presented here are a starting point. They represent a specific configuration of each extractor on a specific dataset. Different configurations, different document types, and different languages will produce different rankings. That is precisely the point: Benchmarkdown makes it easy to run your own comparisons on your own documents, with your own ground truth.

The project is actively developed. We are working on expanding the metric suite, improving the profile system, and adding more extractors as the document AI landscape evolves. Contributions — whether new extractors, new metrics, or bug reports — are welcome on [GitHub](https://github.com/lidia-tech/benchmarkdown).
