# AI Sliding Context Summarizer

A BoundaryML BAML-based pipeline for multi-stage document summarization using small-context LLMs with iterative processing and hierarchical merging.

## Overview

This project solves the problem of summarizing large documents that exceed the context window of smaller, faster LLMs. It implements a sliding-window approach where:

1. **Document Chunking**: Large documents are split into overlapping chunks
2. **Iterative Summarization**: Each chunk is summarized using a small-context model (Claude Haiku / GPT-4o-mini), with an evolving summary passed between iterations
3. **Hierarchical Merging**: Intermediate summaries are merged hierarchically to avoid context limits
4. **Final Analysis**: A large-context model (Claude Sonnet / GPT-4o) performs deep analysis on the consolidated summary

## Features

- **Structured Output**: All LLM responses are validated against BAML schemas
- **Modular Design**: Easy to swap models, adjust chunk sizes, and configure behavior
- **Transparent Logging**: All intermediate summaries saved to disk for inspection
- **Configurable**: Chunk size, overlap, and models controlled via `config.json`
- **Retry Logic**: Built-in exponential backoff for API failures
- **Token-Aware**: Uses tiktoken for accurate token counting

## Project Structure

```
ai-sliding-context-summarizer/
├── baml/
│   ├── schemas.baml        # Structured output schemas (SummarySchema, AnalysisReport)
│   ├── clients.baml        # LLM client configurations (Haiku, Sonnet, GPT variants)
│   └── functions.baml      # BAML functions (SummarizeChunk, MergeSummaries, AnalyzeSummary)
├── src/
│   └── orchestrator.py     # Main Python orchestration script
├── summaries/              # Output directory for intermediate summaries (auto-created)
├── logs/                   # Session logs (auto-created)
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.9+
- BoundaryML BAML installed (`npm install -g @boundaryml/baml`)
- API keys for Anthropic and/or OpenAI

### Setup

1. **Clone or create the project**:
   ```bash
   cd ai-sliding-context-summarizer
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Generate BAML client code**:
   ```bash
   baml-cli generate --from ./baml_src
   ```

   This generates Python client code in `baml_client/` that the orchestrator imports.

5. **Verify configuration**:
   Edit `config.json` to adjust chunk size, overlap, and other parameters.

## Usage

### Basic Usage

```bash
python src/orchestrator.py <input_file> [output_file]
```

**Example**:
```bash
python src/orchestrator.py research_paper.txt analysis_report.md
```

This will:
1. Read `research_paper.txt`
2. Chunk it according to `config.json` settings
3. Iteratively summarize each chunk
4. Merge summaries hierarchically
5. Generate a final analysis with a large-context model
6. Output a markdown report to `analysis_report.md`

### Configuration

Edit `config.json` to customize behavior:

```json
{
  "chunk_size": 2000,        // Tokens per chunk
  "overlap": 200,            // Overlapping tokens between chunks
  "merge_batch_size": 4,     // How many summaries to merge at once
  "models": {
    "summarizer": "claude-3-haiku-20240307",
    "analyzer": "claude-3-5-sonnet-20241022"
  }
}
```

### Switching Models

To use GPT models instead of Claude:

1. Edit `baml_src/functions.baml`:
   - Change `client Haiku` to `client GPT4oMini` in `SummarizeChunk`
   - Change `client Sonnet` to `client GPT4o` in `AnalyzeSummary`

2. Regenerate BAML client:
   ```bash
   baml-cli generate --from ./baml_src
   ```

3. Ensure `OPENAI_API_KEY` is set in `.env`

## Output

### Markdown Report

The final output is a polished markdown report (`final_report.md` by default) containing:

- Executive Summary
- Main Conclusions
- Key Insights
- Key Entities (people, organizations, concepts)
- Critical Facts
- Knowledge Gaps & Uncertainties
- Recommendations (if applicable)
- Analysis Metadata

### Intermediate Summaries

All intermediate summaries are saved to `summaries/<session_id>/`:

- `chunk_0000.json`, `chunk_0001.json`, ... (individual chunk summaries)
- `merge_level1_0000.json`, ... (hierarchical merge results)
- `final_analysis.json` (complete analysis output)

### Logs

Session logs are saved to `logs/<session_id>.log` for debugging.

## Architecture

### Pipeline Stages

```
┌─────────────────┐
│  Large Document │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunk w/Overlap│ (DocumentChunker)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Iterative       │ (SummarizeChunk × N)
│ Summarization   │ Small-context model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hierarchical    │ (MergeSummaries)
│ Merge           │ Batch merge in tree structure
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final Analysis  │ (AnalyzeSummary)
│                 │ Large-context model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Markdown Report │
└─────────────────┘
```

### Key BAML Functions

1. **SummarizeChunk(previous_summary, chunk_text) → SummarySchema**
   - Summarizes current chunk while integrating previous context
   - Extracts entities, facts, relationships, themes, uncertainties
   - Returns structured output validated against schema

2. **MergeSummaries(summaries: [SummarySchema]) → SummarySchema**
   - Consolidates multiple summaries into one
   - Deduplicates entities, prioritizes facts by importance
   - Maintains consistent structure

3. **AnalyzeSummary(final_summary, metadata) → AnalysisReport**
   - Performs deep analysis on consolidated summary
   - Generates conclusions, insights, recommendations
   - Includes confidence assessment

### Schema Validation

All outputs are validated against Pydantic models generated from BAML schemas:

- **SummarySchema**: Contains summary text, entities, facts, relationships, uncertainties, themes
- **AnalysisReport**: Executive summary, conclusions, insights, critical facts, recommendations, metadata

This ensures:
- Consistent output structure
- Reduced hallucination
- Reliable downstream processing

## Advanced Usage

### Custom Prompts

Edit `baml/functions.baml` to customize prompts for each stage. After editing, regenerate the client:

```bash
baml-cli generate --from ./baml --output ./baml_client
```

### Adding New Models

1. Add client definition in `baml/clients.baml`
2. Reference it in function definitions
3. Regenerate client code

### Programmatic Usage

```python
from pathlib import Path
from src.orchestrator import SummarizationPipeline
import json

# Load config
with open("config.json") as f:
    config = json.load(f)

# Create pipeline
pipeline = SummarizationPipeline(config)

# Process document
pipeline.process_document(
    input_path=Path("input.txt"),
    output_path=Path("output.md")
)
```

## Troubleshooting

### BAML client not found

**Error**: `ModuleNotFoundError: No module named 'baml_client'`

**Solution**: Run `baml-cli generate --from ./baml_src`

### API rate limits

**Error**: Rate limit errors from LLM providers

**Solution**: The retry policy in `baml/clients.baml` handles transient failures. For persistent rate limits, reduce chunk size or add delays between calls.

### Token limit exceeded

**Error**: Chunk summaries exceed model context window

**Solution**: Reduce `chunk_size` in `config.json`

### Schema validation failures

**Error**: BAML function returns invalid output

**Solution**: Check `logs/` for details. The retry policy will attempt to fix formatting issues. You may need to adjust prompts in `baml/functions.baml`.

## Performance

**Example**: 50,000-word document (~65,000 tokens)

- **Chunk size**: 2000 tokens, 200 overlap
- **Chunks**: ~35 chunks
- **Time**: ~5-7 minutes (depends on API latency)
- **Cost**: ~$0.50-1.00 (Haiku for chunks, Sonnet for analysis)

Optimize by:
- Increasing chunk size (fewer API calls, but needs larger context model)
- Using GPT-4o-mini instead of Haiku (slightly cheaper)
- Batching chunk summaries (modify orchestrator to process multiple chunks in parallel)

## Contributing

This is a reference implementation. Extend it by:

- Adding support for PDF/DOCX input
- Implementing parallel chunk processing
- Adding real-time streaming output
- Creating a web UI
- Supporting additional LLM providers

## License

MIT License - feel free to modify and extend.

## References

- [BoundaryML BAML Documentation](https://docs.boundaryml.com)
- [Anthropic Claude API](https://docs.anthropic.com)
- [OpenAI API](https://platform.openai.com/docs)

---

**Generated by AI Sliding Context Summarizer**
