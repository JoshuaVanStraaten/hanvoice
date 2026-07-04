/** API types mirroring the backend's Pydantic response models. */

export interface Plan {
  id: "free" | "founder" | "premium";
  name: string;
  price_usd_cents: number;
  billing_period: "none" | "monthly" | "lifetime";
  daily_pronunciation_limit: number;
  daily_conversation_turn_limit: number;
  daily_llm_token_limit: number;
  daily_handwriting_limit: number;
}

export interface Profile {
  id: string;
  display_name: string;
  native_language: string;
  onboarding_completed: boolean;
  created_at: string;
}

export interface Me {
  profile: Profile;
  plan: Plan;
  has_founder_pass: boolean;
}

export interface UsageCounters {
  usage_date: string;
  pronunciation_attempts: number;
  conversation_turns: number;
  llm_tokens_in: number;
  llm_tokens_out: number;
  tts_seconds: number;
  handwriting_checks: number;
}

export interface UsageToday {
  usage: UsageCounters;
  plan: Plan;
}

export interface LessonSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  sort_order: number;
  phrase_count: number;
}

export interface LessonPhrase {
  id: number;
  hangul: string;
  romanized: string;
  english: string;
  audio_url: string | null;
  sort_order: number;
}

export interface LessonDetail {
  id: number;
  slug: string;
  title: string;
  description: string;
  phrases: LessonPhrase[];
}

export interface ScenarioSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  difficulty: number;
  completion_goals: string[];
  sort_order: number;
}

export interface PronunciationScores {
  accuracy: number;
  fluency: number;
  completeness: number;
  overall: number;
  recognized_text: string;
  words: Array<Record<string, unknown>>;
}

export interface PronunciationAttempt {
  attempt_id: number;
  target_text: string;
  scores: PronunciationScores;
}

export interface ConversationMessage {
  id: number;
  role: "user" | "assistant";
  hangul: string;
  romanized: string | null;
  english: string | null;
  contextual_correction: string | null;
  created_at: string;
}

export interface ConversationSession {
  id: number;
  scenario_id: number;
  status: "active" | "completed" | "abandoned";
  goals_completed: string[];
  started_at: string;
  ended_at: string | null;
}

export interface ConversationDetail {
  session: ConversationSession;
  messages: ConversationMessage[];
}

export interface StartConversationResponse {
  session: ConversationSession;
  opening_message: ConversationMessage;
  audio_base64: string | null;
}

export interface TurnResponse {
  user_message: ConversationMessage;
  assistant_message: ConversationMessage;
  goals_completed: string[];
  scenario_completed: boolean;
  audio_base64: string | null;
}

export interface HandwritingScores {
  proportion_score: number;
  stroke_score: number;
  legibility_score: number;
  overall_score: number;
  feedback: string;
}

export interface HandwritingAttempt {
  attempt_id: number;
  target_text: string;
  scores: HandwritingScores;
  model_version: string;
}

export interface LessonProgressItem {
  lesson_id: number;
  lesson_slug: string;
  lesson_title: string;
  status: "in_progress" | "completed";
  phrases_completed: number;
  phrase_count: number;
  best_pronunciation_score: number | null;
}

export interface ScenarioProgressItem {
  scenario_id: number;
  scenario_slug: string;
  scenario_title: string;
  status: "in_progress" | "completed";
  times_completed: number;
  last_session_id: number | null;
}

export interface Progress {
  lessons: LessonProgressItem[];
  scenarios: ScenarioProgressItem[];
}
