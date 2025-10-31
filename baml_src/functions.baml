// functions.baml
// Defines BAML functions for the multi-stage summarization pipeline

// Function 1: Summarize a single chunk with context from previous summary
function SummarizeChunk(
  previous_summary: string,
  chunk_text: string
) -> SummarySchema {
  client Haiku
  prompt #"
    You are an expert summarizer performing incremental document analysis.

    Your task is to analyze the current chunk of text and integrate it with the previous summary.

    ## PREVIOUS SUMMARY:
    {{ previous_summary }}

    ## CURRENT CHUNK:
    {{ chunk_text }}

    ## INSTRUCTIONS:
    1. Read the current chunk carefully
    2. Extract key entities, facts, relationships, and themes
    3. Integrate new information with the previous summary
    4. Identify any uncertainties or ambiguities
    5. Create an updated summary that combines both contexts

    ## OUTPUT REQUIREMENTS:
    - summary: 2-4 sentences covering both previous and current content
    - entities: Extract all mentioned entities with types and descriptions
    - key_facts: List important facts with importance levels
    - relationships: Identify connections between entities
    - uncertainties: Note any unclear or ambiguous points
    - themes: High-level topics covered

    Be precise, factual, and avoid speculation beyond what's stated.

    {{ ctx.output_format }}
  "#
}

// Function 2: Merge multiple summaries hierarchically
function MergeSummaries(
  summaries: SummarySchema[]
) -> SummarySchema {
  client Haiku
  prompt #"
    You are an expert at synthesizing multiple summaries into a coherent whole.

    You have received {{ summaries.length }} summaries to merge.

    ## SUMMARIES TO MERGE:
    {% for summary in summaries %}
    ### Summary {{ loop.index }}:
    {{ summary.summary }}

    Entities: {{ summary.entities | length }}
    Key Facts: {{ summary.key_facts | length }}
    Themes: {{ summary.themes | join(", ") }}
    ---
    {% endfor %}

    ## INSTRUCTIONS:
    1. Consolidate all summaries into a single coherent summary
    2. Merge entity lists, removing duplicates and consolidating descriptions
    3. Combine key facts, preserving the most important ones
    4. Merge relationships, avoiding redundancy
    5. Consolidate uncertainties
    6. Identify overarching themes that span multiple summaries

    ## OUTPUT REQUIREMENTS:
    - summary: A unified 3-5 sentence summary covering all content
    - entities: Merged list with no duplicates
    - key_facts: Combined list, prioritize by importance
    - relationships: Merged relationships
    - uncertainties: Consolidated uncertainties
    - themes: High-level themes across all summaries

    Maintain factual accuracy and avoid introducing new information not present in the summaries.

    {{ ctx.output_format }}
  "#
}

// Function 3: Final analysis with large-context model
function AnalyzeSummary(
  final_summary: SummarySchema,
  original_metadata: string
) -> AnalysisReport {
  client Sonnet
  prompt #"
    You are a senior analyst tasked with producing a comprehensive analysis report.

    You have received a consolidated summary of a large document that was processed in chunks.

    ## CONSOLIDATED SUMMARY:
    {{ final_summary.summary }}

    ## ENTITIES ({{ final_summary.entities | length }}):
    {% for entity in final_summary.entities %}
    - {{ entity.name }} ({{ entity.type }}): {{ entity.description }}
    {% endfor %}

    ## KEY FACTS ({{ final_summary.key_facts | length }}):
    {% for fact in final_summary.key_facts %}
    - [{{ fact.importance }}] {{ fact.fact }} ({{ fact.category }})
    {% endfor %}

    ## RELATIONSHIPS:
    {% for rel in final_summary.relationships %}
    - {{ rel.subject }} → {{ rel.predicate }} → {{ rel.object }} ({{ rel.context }})
    {% endfor %}

    ## THEMES:
    {{ final_summary.themes | join(", ") }}

    ## UNCERTAINTIES:
    {% for unc in final_summary.uncertainties %}
    - {{ unc.statement }} (Reason: {{ unc.reason }})
    {% endfor %}

    ## ORIGINAL DOCUMENT METADATA:
    {{ original_metadata }}

    ## YOUR TASK:
    Produce a comprehensive analysis report that includes:

    1. **Executive Summary**: A high-level overview (3-5 sentences) that captures the essence of the entire document

    2. **Main Conclusions**: The primary takeaways or conclusions drawn from the content

    3. **Key Insights**: Novel or particularly important insights that emerged from the analysis

    4. **Entities Summary**: The most important entities, consolidated and refined

    5. **Critical Facts**: The most critical facts that a reader must know

    6. **Knowledge Gaps**: Areas where information is incomplete, contradictory, or uncertain

    7. **Recommendations**: If applicable, suggest actionable next steps or areas for further investigation

    8. **Confidence Level**: Assess your overall confidence in this analysis (high/medium/low) and explain why

    9. **Metadata**: Include processing information

    Be analytical, precise, and add value beyond simple summarization. Look for patterns, implications, and non-obvious connections.

    {{ ctx.output_format }}
  "#
}

// Alternative version that uses GPT-4o-mini for chunk summarization
function SummarizeChunkGPT(
  previous_summary: string,
  chunk_text: string
) -> SummarySchema {
  client GPT4oMini
  prompt #"
    You are an expert summarizer performing incremental document analysis.

    Your task is to analyze the current chunk of text and integrate it with the previous summary.

    ## PREVIOUS SUMMARY:
    {{ previous_summary }}

    ## CURRENT CHUNK:
    {{ chunk_text }}

    ## INSTRUCTIONS:
    1. Read the current chunk carefully
    2. Extract key entities, facts, relationships, and themes
    3. Integrate new information with the previous summary
    4. Identify any uncertainties or ambiguities
    5. Create an updated summary that combines both contexts

    ## OUTPUT REQUIREMENTS:
    - summary: 2-4 sentences covering both previous and current content
    - entities: Extract all mentioned entities with types and descriptions
    - key_facts: List important facts with importance levels
    - relationships: Identify connections between entities
    - uncertainties: Note any unclear or ambiguous points
    - themes: High-level topics covered

    Be precise, factual, and avoid speculation beyond what's stated.

    {{ ctx.output_format }}
  "#
}

// Test function for validating BAML setup
function TestSummarization(
  text: string
) -> SummarySchema {
  client Haiku
  prompt #"
    Analyze the following text and extract structured information:

    {{ text }}

    Provide a summary with entities, facts, and themes.

    {{ ctx.output_format }}
  "#
}
