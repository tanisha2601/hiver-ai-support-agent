export interface AgentRequest {
  message: string;
  context?: string;
}

export interface RetrievedExample {
  historical_tweet_id?: string;
  historical_customer_text?: string;
  historical_brand_response?: string;
  similarity_score: number;
  retrieval_method?: string;
}

export interface AgentResult {
  customer_message: string;
  intent: string;
  intent_confidence: number;
  retrieved_examples: RetrievedExample[];
  grounding_status: string;
  grounding_score: number;
  response: string;
  decision: string;
  decision_reason: string;
}

export interface EvaluationSummary {
  intent_metrics: any;
  majority_metrics?: any;
  tfidf_metrics?: any;
  retrieval_metrics?: any;
  escalation_metrics: any;
  reply_quality: any;
  intent_distribution: {name: string, value: number}[];
  true_intent_distribution: {name: string, value: number}[];
  decision_distribution: {name: string, value: number}[];
  grounding_distribution: {name: string, value: number}[];
  confidence_distribution: {name: string, value: number}[];
  failure_distribution: {name: string, value: number}[];
}

export interface FailureMode {
  'Failure name': string;
  'Number of affected examples': number;
  Example: string;
  'Why the system failed': string;
  'Proposed improvement': string;
}

export interface HealthStatus {
  status: string;
  agent: string;
  retrieval: string;
  generation: string;
  evaluation_data: string;
  dataset: string;
  retrieval_type: string;
  embedding_model: string;
}
