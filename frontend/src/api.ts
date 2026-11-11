import type {
  CoffeeProfileDraft,
  EquipmentItem,
  PersonalisedRecipe,
  RecipeGenerateRequest,
  EvidencePackage,
  RecipeSearchRequest
} from './types';

const API_BASE = '/api/v1';

export async function scanCoffeeBag(file: File): Promise<CoffeeProfileDraft> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Scan failed with status ${res.status}`);
  }

  return res.json();
}

export async function getProfile(profileId: string): Promise<CoffeeProfileDraft> {
  const res = await fetch(`${API_BASE}/profiles/${profileId}`);
  if (!res.ok) {
    throw new Error(`Failed to load coffee profile (${res.status})`);
  }
  return res.json();
}

export async function updateProfile(profileId: string, updates: Partial<Record<string, string>>): Promise<CoffeeProfileDraft> {
  const res = await fetch(`${API_BASE}/profiles/${profileId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    throw new Error(`Failed to update profile (${res.status})`);
  }
  return res.json();
}

export async function getDrippers(): Promise<EquipmentItem[]> {
  const res = await fetch(`${API_BASE}/equipment/drippers`);
  if (!res.ok) throw new Error('Failed to fetch drippers');
  return res.json();
}

export async function getGrinders(): Promise<EquipmentItem[]> {
  const res = await fetch(`${API_BASE}/equipment/grinders`);
  if (!res.ok) throw new Error('Failed to fetch grinders');
  return res.json();
}

export async function generateRecipe(request: RecipeGenerateRequest): Promise<PersonalisedRecipe> {
  const res = await fetch(`${API_BASE}/recipes/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to generate recipe');
  }
  return res.json();
}

export async function getRecipe(recipeId: string): Promise<PersonalisedRecipe> {
  const res = await fetch(`${API_BASE}/recipes/${recipeId}`);
  if (!res.ok) {
    throw new Error(`Failed to load recipe (${res.status})`);
  }
  return res.json();
}

export async function searchRecipes(request: RecipeSearchRequest): Promise<EvidencePackage> {
  const res = await fetch(`${API_BASE}/recipes/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to search recipe knowledge base');
  }
  return res.json();
}

