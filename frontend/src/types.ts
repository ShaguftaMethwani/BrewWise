export interface ExtractedField {
  value: string | null;
  confidence: number;
  source: 'bag_text' | 'inferred' | 'unknown' | 'user_override';
  raw_text?: string | null;
}

export interface CoffeeProfileDraft {
  id: string;
  brand: ExtractedField;
  product_name: ExtractedField;
  estate: ExtractedField;
  country: ExtractedField;
  region: ExtractedField;
  varietal: ExtractedField;
  process: ExtractedField;
  roast_level: ExtractedField;
  roast_date: ExtractedField;
  tasting_notes: ExtractedField;
  altitude: ExtractedField;
  dose_recommendation?: ExtractedField | null;
  additional_info: ExtractedField[];
  image_id?: string | null;
  image_url?: string | null;
  extraction_model: string;
  is_coffee_bag: boolean;
  rejection_reason?: string | null;
}

export interface EquipmentItem {
  id: string;
  category: 'dripper' | 'grinder';
  brand: string;
  model: string;
  geometry?: string | null;
  description?: string | null;
  default_ratio?: string;
}

export interface PourStep {
  step_number: number;
  water_g: number;
  cumulative_water_g: number;
  start_time_seconds: number;
  duration_seconds: number;
  technique: string;
  notes?: string | null;
}

export interface RecipeExplanation {
  reasoning_summary: string;
  parameter_rationale: Record<string, string>;
  assumptions: string[];
}

export interface TroubleshootingTip {
  symptom: string;
  likely_cause: string;
  adjustment: string;
}

export interface SourceReference {
  source_name: string;
  url?: string | null;
  similarity_score?: number | null;
}

export interface Adaptation {
  parameter: string;
  original_value: string;
  adapted_value: string;
  rationale: string;
}

export interface PersonalisedRecipe {
  id?: string;
  recipe_id: string;
  coffee_profile_id: string;
  source_type: 'exact_match' | 'adapted_from_related' | 'ai_generated' | 'curated_baseline' | string;
  source_recipes?: SourceReference[];
  adaptations?: Adaptation[];
  generation_model?: string | null;
  dripper: string;
  grinder?: string | null;
  filter_type?: string | null;
  dose_g: number;
  water_g: number;
  ratio: string;
  water_temperature_c: number;
  grind_description: string;
  grind_setting?: string | null;
  filter_prep?: string | null;
  bloom_water_g: number;
  bloom_time_seconds: number;
  pour_schedule: PourStep[];
  target_brew_time_seconds: number;
  step_by_step_instructions: string[];
  expected_flavour: string;
  flavour_is_prediction: boolean;
  explanation: RecipeExplanation;
  troubleshooting: TroubleshootingTip[];
  limitations: string[];
  confidence: number;
  created_at: string;
}

export interface RecipeGenerateRequest {
  coffee_profile_id: string;
  dripper?: string;
  grinder?: string;
  dose_preference_g?: number;
  target_strength?: 'light' | 'balanced' | 'strong';
}

export type MatchType = 'exact' | 'strong' | 'related' | 'analogous' | 'general';

export interface ScoredMatch {
  source_id: string;
  url: string;
  title: string;
  author?: string | null;
  site_name?: string | null;
  match_type: MatchType;
  relevance_score: number;
  coffee_metadata: Record<string, any>;
  extracted_recipe: Record<string, any>;
  match_reasons: string[];
  is_live_discovered?: boolean;
}

export interface ParameterConflict {
  parameter: string;
  difference: string;
  sources_involved: string[];
  resolution_guidance: string;
}

export interface EvidencePackage {
  match_outcome: 'A' | 'B' | 'C';
  matched_recipes: ScoredMatch[];
  conflicts: ParameterConflict[];
  coverage_summary: string;
  compact_context: string;
  discovery_status?: 'skipped_sufficient_kb' | 'success' | 'partial' | 'failed' | 'disabled' | string;
  discovery_message?: string | null;
  urls_searched?: number;
  recipes_discovered?: number;
}

export interface RecipeSearchRequest {
  coffee_profile_id: string;
  dripper?: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface UserEquipmentProfile {
  id: string;
  name: string;
  dripper: string;
  grinder?: string | null;
  filter_type?: string | null;
  default_dose_g: number;
  default_ratio: string;
  is_default: boolean;
  created_at: string;
}

export interface UserEquipmentProfileCreate {
  name: string;
  dripper: string;
  grinder?: string | null;
  filter_type?: string | null;
  default_dose_g?: number;
  default_ratio?: string;
  is_default?: boolean;
}

export interface AdjustmentRecommendation {
  diagnosis: string;
  primary_adjustment: string;
  secondary_adjustment?: string | null;
  suggested_parameters: Record<string, any>;
  rationale: string;
}

export interface BrewLog {
  id: string;
  user_id?: string | null;
  recipe_id?: string | null;
  coffee_profile_id?: string | null;
  brewed_at: string;
  dripper: string;
  grinder?: string | null;
  actual_dose_g: number;
  actual_water_g: number;
  actual_grind_setting?: string | null;
  actual_temp_c: number;
  actual_brew_time_seconds: number;
  sourness: number;
  bitterness: number;
  sweetness: number;
  body: number;
  overall_satisfaction: number;
  drawdown_speed: 'fast' | 'normal' | 'slow' | 'stalled';
  flavour_notes?: string | null;
  adjustments?: AdjustmentRecommendation | null;
  created_at: string;
}

export interface BrewLogCreate {
  recipe_id?: string | null;
  coffee_profile_id?: string | null;
  dripper: string;
  grinder?: string | null;
  actual_dose_g: number;
  actual_water_g: number;
  actual_grind_setting?: string | null;
  actual_temp_c: number;
  actual_brew_time_seconds: number;
  sourness: number;
  bitterness: number;
  sweetness: number;
  body: number;
  overall_satisfaction: number;
  drawdown_speed: 'fast' | 'normal' | 'slow' | 'stalled';
  flavour_notes?: string | null;
}

export interface BrewLogFeedbackUpdate {
  sourness?: number;
  bitterness?: number;
  sweetness?: number;
  body?: number;
  overall_satisfaction?: number;
  drawdown_speed?: 'fast' | 'normal' | 'slow' | 'stalled';
  flavour_notes?: string;
}
