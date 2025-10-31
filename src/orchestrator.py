#!/usr/bin/env python3
"""
Multi-Stage Document Summarization Orchestrator

This script orchestrates the sliding-context summarization pipeline:
1. Chunks large documents with overlap
2. Iteratively summarizes each chunk using a small-context model
3. Hierarchically merges intermediate summaries
4. Produces final analysis with a large-context model
"""

import json
import os
import sys
import tiktoken
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from baml_client import b
from baml_client.types import SummarySchema, AnalysisReport


class DocumentChunker:
    """Handles document chunking with overlap."""

    def __init__(self, chunk_size: int = 2000, overlap: int = 200, model: str = "cl100k_base"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        tokens = self.encoding.encode(text)
        chunks = []

        i = 0
        while i < len(tokens):
            # Extract chunk
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move pointer forward by (chunk_size - overlap)
            i += self.chunk_size - self.overlap

        return chunks


class SummarizationPipeline:
    """Orchestrates the multi-stage summarization process."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chunker = DocumentChunker(
            chunk_size=config["chunk_size"],
            overlap=config["overlap"]
        )
        self.summaries_dir = Path("summaries")
        self.logs_dir = Path("logs")
        self.summaries_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Session ID for this run
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.summaries_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)

    def log(self, message: str):
        """Log message to console and file."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        log_file = self.logs_dir / f"{self.session_id}.log"
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")

    def save_summary(self, summary: SummarySchema, stage: str, index: int = 0):
        """Save intermediate summary to disk."""
        filename = self.session_dir / f"{stage}_{index:04d}.json"
        with open(filename, "w") as f:
            json.dump(summary.model_dump(), f, indent=2)
        self.log(f"Saved {stage} summary #{index} to {filename}")

    def save_analysis(self, analysis: AnalysisReport):
        """Save final analysis report."""
        filename = self.session_dir / "final_analysis.json"
        with open(filename, "w") as f:
            json.dump(analysis.model_dump(), f, indent=2)
        self.log(f"Saved final analysis to {filename}")

    def summarize_chunks_iteratively(self, chunks: List[str]) -> SummarySchema:
        """
        Iteratively summarize chunks, passing evolving summary forward.

        Returns the final consolidated summary after processing all chunks.
        """
        self.log(f"Starting iterative summarization of {len(chunks)} chunks...")

        previous_summary = "No previous context. This is the first chunk."

        for i, chunk in enumerate(chunks):
            self.log(f"Processing chunk {i+1}/{len(chunks)} ({self.chunker.count_tokens(chunk)} tokens)...")

            try:
                # Call BAML function
                summary = b.SummarizeChunk(
                    previous_summary=previous_summary,
                    chunk_text=chunk
                )

                # Save intermediate result
                self.save_summary(summary, "chunk", i)

                # Update previous summary for next iteration
                previous_summary = self._format_summary_for_context(summary)

                self.log(f"✓ Chunk {i+1} summarized: {len(summary.entities)} entities, "
                        f"{len(summary.key_facts)} facts, {len(summary.themes)} themes")

            except Exception as e:
                self.log(f"✗ Error processing chunk {i+1}: {e}")
                raise

        # Return the final summary from last iteration
        return summary

    def _format_summary_for_context(self, summary: SummarySchema) -> str:
        """Format a summary into a compact string for passing as context."""
        entities_str = "; ".join([f"{e.name} ({e.type})" for e in summary.entities[:10]])
        facts_str = "; ".join([f.fact for f in summary.key_facts[:10]])

        return f"""
SUMMARY: {summary.summary}
KEY ENTITIES: {entities_str}
KEY FACTS: {facts_str}
THEMES: {", ".join(summary.themes)}
""".strip()

    def merge_summaries_hierarchically(self, summaries: List[SummarySchema]) -> SummarySchema:
        """
        Hierarchically merge summaries using a tree structure.

        If we have many summaries, merge them in batches to avoid context limits.
        """
        if len(summaries) == 1:
            return summaries[0]

        self.log(f"Hierarchically merging {len(summaries)} summaries...")

        batch_size = self.config.get("merge_batch_size", 4)
        level = 0
        current_summaries = summaries

        while len(current_summaries) > 1:
            level += 1
            next_summaries = []

            for i in range(0, len(current_summaries), batch_size):
                batch = current_summaries[i:i + batch_size]
                self.log(f"Level {level}: Merging batch {i//batch_size + 1} "
                        f"({len(batch)} summaries)...")

                try:
                    merged = b.MergeSummaries(summaries=batch)
                    self.save_summary(merged, f"merge_level{level}", i // batch_size)
                    next_summaries.append(merged)
                    self.log(f"✓ Batch merged: {len(merged.entities)} entities, "
                            f"{len(merged.key_facts)} facts")
                except Exception as e:
                    self.log(f"✗ Error merging batch: {e}")
                    raise

            current_summaries = next_summaries

        self.log(f"Hierarchical merge complete. Final summary has "
                f"{len(current_summaries[0].entities)} entities.")
        return current_summaries[0]

    def analyze_final_summary(self, summary: SummarySchema, metadata: Dict[str, Any]) -> AnalysisReport:
        """Send final summary to large-context model for analysis."""
        self.log("Performing final analysis with large-context model...")

        metadata_str = json.dumps(metadata, indent=2)

        try:
            analysis = b.AnalyzeSummary(
                final_summary=summary,
                original_metadata=metadata_str
            )
            self.save_analysis(analysis)
            self.log(f"✓ Analysis complete: {len(analysis.main_conclusions)} conclusions, "
                    f"{len(analysis.key_insights)} insights")
            return analysis
        except Exception as e:
            self.log(f"✗ Error during analysis: {e}")
            raise

    def generate_markdown_report(self, analysis: AnalysisReport, output_path: Path):
        """Generate a human-readable markdown report."""
        self.log(f"Generating markdown report at {output_path}...")

        with open(output_path, "w") as f:
            f.write(f"# Document Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Session ID:** {self.session_id}\n\n")
            f.write(f"---\n\n")

            f.write(f"## Executive Summary\n\n")
            f.write(f"{analysis.executive_summary}\n\n")

            f.write(f"## Main Conclusions\n\n")
            for i, conclusion in enumerate(analysis.main_conclusions, 1):
                f.write(f"{i}. {conclusion}\n")
            f.write(f"\n")

            f.write(f"## Key Insights\n\n")
            for i, insight in enumerate(analysis.key_insights, 1):
                f.write(f"{i}. {insight}\n")
            f.write(f"\n")

            f.write(f"## Key Entities\n\n")
            for entity in analysis.entities_summary[:20]:  # Top 20
                f.write(f"- **{entity.name}** ({entity.type}): {entity.description}\n")
            f.write(f"\n")

            f.write(f"## Critical Facts\n\n")
            for fact in analysis.critical_facts[:15]:  # Top 15
                f.write(f"- [{fact.importance}] **{fact.category}**: {fact.fact}\n")
            f.write(f"\n")

            if analysis.knowledge_gaps:
                f.write(f"## Knowledge Gaps & Uncertainties\n\n")
                for gap in analysis.knowledge_gaps:
                    f.write(f"- {gap.statement}\n")
                    f.write(f"  - *Reason:* {gap.reason}\n")
                f.write(f"\n")

            if analysis.recommendations:
                f.write(f"## Recommendations\n\n")
                for i, rec in enumerate(analysis.recommendations, 1):
                    f.write(f"{i}. {rec}\n")
                f.write(f"\n")

            f.write(f"## Analysis Metadata\n\n")
            f.write(f"- **Chunks Processed:** {analysis.metadata.total_chunks_processed}\n")
            f.write(f"- **Model Used:** {analysis.metadata.model_used}\n")
            f.write(f"- **Confidence Level:** {analysis.confidence_level}\n")
            f.write(f"- **Estimated Word Count:** {analysis.metadata.word_count_estimate:,}\n")
            f.write(f"\n")

            f.write(f"---\n\n")
            f.write(f"*Generated by AI Sliding Context Summarizer*\n")

        self.log(f"✓ Markdown report saved to {output_path}")

    def process_document(self, input_path: Path, output_path: Path = None):
        """Main orchestration function."""
        if output_path is None:
            output_path = Path("final_report.md")

        self.log(f"=" * 60)
        self.log(f"Starting document processing pipeline")
        self.log(f"Input: {input_path}")
        self.log(f"Output: {output_path}")
        self.log(f"=" * 60)

        # Step 1: Read document
        self.log("Step 1: Reading document...")
        with open(input_path, "r", encoding="utf-8") as f:
            document = f.read()

        word_count = len(document.split())
        token_count = self.chunker.count_tokens(document)
        self.log(f"Document loaded: {word_count:,} words, {token_count:,} tokens")

        # Step 2: Chunk document
        self.log("Step 2: Chunking document...")
        chunks = self.chunker.chunk_text(document)
        self.log(f"Created {len(chunks)} chunks (size={self.config['chunk_size']}, "
                f"overlap={self.config['overlap']})")

        # Step 3: Iteratively summarize chunks
        self.log("Step 3: Iteratively summarizing chunks...")
        final_summary = self.summarize_chunks_iteratively(chunks)

        # Step 4: Analyze with large-context model
        self.log("Step 4: Analyzing with large-context model...")
        metadata = {
            "total_chunks": len(chunks),
            "original_word_count": word_count,
            "original_token_count": token_count,
            "chunk_size": self.config["chunk_size"],
            "overlap": self.config["overlap"],
            "session_id": self.session_id
        }

        analysis = self.analyze_final_summary(final_summary, metadata)

        # Step 5: Generate final report
        self.log("Step 5: Generating final markdown report...")
        self.generate_markdown_report(analysis, output_path)

        self.log("=" * 60)
        self.log("✓ Pipeline complete!")
        self.log(f"Final report: {output_path}")
        self.log(f"Intermediate summaries: {self.session_dir}")
        self.log("=" * 60)


def main():
    """Main entry point."""
    # Load configuration
    config_path = Path("config.json")
    if not config_path.exists():
        print(f"Error: {config_path} not found")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <input_file> [output_file]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("final_report.md")

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found")
        sys.exit(1)

    # Run pipeline
    pipeline = SummarizationPipeline(config)
    try:
        pipeline.process_document(input_path, output_path)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
