// clients.baml
// Defines LLM client configurations for summarization and analysis

// Small-context, fast model for iterative chunk summarization
client<llm> Haiku {
  provider anthropic
  options {
    model claude-3-haiku-20240307
    api_key env.ANTHROPIC_API_KEY
    max_tokens 2000
    temperature 0.3
  }
}

// Alternative small-context model (OpenAI)
client<llm> GPT4oMini {
  provider openai
  options {
    model gpt-4o-mini
    api_key env.OPENAI_API_KEY
    max_tokens 2000
    temperature 0.3
  }
}

// Large-context model for final analysis
client<llm> Sonnet {
  provider anthropic
  options {
    model claude-3-5-sonnet-20241022
    api_key env.ANTHROPIC_API_KEY
    max_tokens 4000
    temperature 0.2
  }
}

// Alternative large-context model (OpenAI)
client<llm> GPT4o {
  provider openai
  options {
    model gpt-4o
    api_key env.OPENAI_API_KEY
    max_tokens 4000
    temperature 0.2
  }
}

// Retry strategy for all functions
retry_policy StandardRetry {
  max_retries 3
  strategy {
    type exponential_backoff
    delay_ms 1000
    multiplier 2
  }
}
