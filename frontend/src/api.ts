import type {
  CoffeeProfileDraft,
  EquipmentItem,
  PersonalisedRecipe,
  RecipeGenerateRequest,
  EvidencePackage,
  RecipeSearchRequest,
  User,
  AuthResponse,
  UserEquipmentProfile,
  UserEquipmentProfileCreate,
  BrewLog,
  BrewLogCreate,
  BrewLogFeedbackUpdate
} from './types';

const API_BASE = `${import.meta.env.VITE_API_URL || ''}/api/v1`;

// Token storage helpers
const TOKEN_KEY = 'brewwise_jwt_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Authentication
export async function register(email: string, password: string, displayName: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed');
  }
  const data: AuthResponse = await res.json();
  setToken(data.token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  const data: AuthResponse = await res.json();
  setToken(data.token);
  return data;
}

export async function getMe(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    clearToken();
    return null;
  }
  return res.json();
}

// Equipment Profiles
export async function getEquipmentProfiles(): Promise<UserEquipmentProfile[]> {
  const res = await fetch(`${API_BASE}/equipment/profiles`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch equipment profiles');
  return res.json();
}

export async function createEquipmentProfile(profile: UserEquipmentProfileCreate): Promise<UserEquipmentProfile> {
  const res = await fetch(`${API_BASE}/equipment/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create profile');
  }
  return res.json();
}

export async function deleteEquipmentProfile(profileId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/equipment/profiles/${profileId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete profile');
}

export async function setDefaultProfile(profileId: string): Promise<UserEquipmentProfile> {
  const res = await fetch(`${API_BASE}/equipment/profiles/${profileId}/default`, {
    method: 'PUT',
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to set default profile');
  return res.json();
}

// Brew Logging & Feedback
export async function logBrew(brewData: BrewLogCreate): Promise<BrewLog> {
  const res = await fetch(`${API_BASE}/brews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(brewData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to log brew');
  }
  return res.json();
}

export async function getBrews(coffeeProfileId?: string): Promise<BrewLog[]> {
  let url = `${API_BASE}/brews?limit=50`;
  if (coffeeProfileId) {
    url += `&coffee_profile_id=${encodeURIComponent(coffeeProfileId)}`;
  }
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch brews');
  return res.json();
}

export async function getBrew(brewId: string): Promise<BrewLog> {
  const res = await fetch(`${API_BASE}/brews/${brewId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch brew details');
  return res.json();
}

export async function updateBrewFeedback(brewId: string, feedback: BrewLogFeedbackUpdate): Promise<BrewLog> {
  const res = await fetch(`${API_BASE}/brews/${brewId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(feedback),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update feedback');
  }
  return res.json();
}

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

