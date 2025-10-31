// schemas.baml
// Defines structured output schemas for the summarization pipeline

class Entity {
  name string @description("The name of the entity (person, organization, concept, etc.)")
  type string @description("Type of entity: person, organization, location, concept, event, etc.")
  description string @description("Brief description of the entity's role or significance")
}

class Relationship {
  subject string @description("The first entity in the relationship")
  predicate string @description("The nature of the relationship")
  object string @description("The second entity in the relationship")
  context string @description("Additional context about this relationship")
}

class KeyFact {
  fact string @description("A single, verifiable statement from the text")
  importance string @description("Why this fact is significant: critical, high, medium, low")
  category string @description("Category: data, finding, claim, methodology, result, etc.")
}

class Uncertainty {
  statement string @description("A claim or statement that lacks certainty")
  reason string @description("Why this is uncertain: missing data, conflicting info, speculation, etc.")
}

class SummarySchema {
  summary string @description("A concise prose summary of the content (2-4 sentences)")
  entities Entity[] @description("List of key entities mentioned")
  key_facts KeyFact[] @description("List of important facts extracted")
  relationships Relationship[] @description("List of relationships between entities")
  uncertainties Uncertainty[] @description("List of uncertain or ambiguous points")
  themes string[] @description("High-level themes or topics covered")
}

class AnalysisReport {
  executive_summary string @description("High-level summary of the entire document (3-5 sentences)")
  main_conclusions string[] @description("List of primary conclusions or takeaways")
  key_insights string[] @description("Novel or important insights derived from the analysis")
  entities_summary Entity[] @description("Consolidated list of the most important entities")
  critical_facts KeyFact[] @description("The most critical facts from the entire document")
  knowledge_gaps Uncertainty[] @description("Areas where information is incomplete or uncertain")
  recommendations string[] @description("Actionable recommendations or next steps (if applicable)")
  confidence_level string @description("Overall confidence in the analysis: high, medium, low")
  metadata AnalysisMetadata @description("Metadata about the analysis process")
}

class AnalysisMetadata {
  total_chunks_processed int @description("Total number of chunks processed")
  model_used string @description("The model used for final analysis")
  timestamp string @description("When the analysis was completed")
  word_count_estimate int @description("Estimated word count of original document")
}
