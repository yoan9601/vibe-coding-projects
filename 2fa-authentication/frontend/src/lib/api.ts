// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface ApiError {
  detail: string;
}

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });
    } catch (error) {
      // Network error - backend is not reachable
      console.error('Network error:', error);
      throw new Error(
        'Unable to connect to the server. Please check if the backend is running and CORS is configured correctly.'
      );
    }

    if (!response.ok) {
      if (response.status === 401) {
  // Don't redirect if already on login page
  if (!endpoint.includes('/auth/login')) {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
  throw new Error('Invalid username or password');
}
      if (response.status === 403) {
        throw new Error('Access denied. You do not have permission to perform this action.');
      }
      const error: ApiError = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || 'An error occurred');
    }

    if (response.status === 204) {
      return {} as T;
    }
    return response.json();
  }

  // Auth endpoints
  // Auth endpoints
  async login(username: string, password: string) {
    return this.request<{ access_token: string; token_type: string; requires_2fa: boolean }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async verify2FA(code: string, tempToken: string) {
    return this.request<{ access_token: string; token_type: string }>('/auth/verify-2fa', {
      method: 'POST',
      headers: { Authorization: `Bearer ${tempToken}` },
      body: JSON.stringify({ code }),
    });
  }

  async register(username: string, email: string, password: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async getCurrentUser() {
    return this.request<User>('/auth/me');
  }

  async enable2FA(telegram_chat_id: string) {
    return this.request<{ message: string }>('/auth/enable-2fa', {
      method: 'POST',
      body: JSON.stringify({ telegram_chat_id }),
    });
  }

  async disable2FA() {
    return this.request<{ message: string }>('/auth/disable-2fa', {
      method: 'POST',
    });
  }

  async test2FA() {
    return this.request<{ message: string }>('/auth/test-2fa', {
      method: 'POST',
    });
  }

  async changePassword(currentPassword: string, newPassword: string) {
    return this.request<{ message: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  // Tools endpoints
  async getTools(params: {
    skip?: number;
    limit?: number;
    category?: string;
    status?: string;
    search?: string;
  } = {}) {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params.category) searchParams.append('category', params.category);
    if (params.status) searchParams.append('status', params.status);
    if (params.search) searchParams.append('search', params.search);
    
    return this.request<{ tools: Tool[]; total: number }>(`/tools?${searchParams}`);
  }

  async getTool(id: number) {
    return this.request<Tool>(`/tools/${id}`);
  }

  async createTool(data: CreateToolData) {
    return this.request<Tool>('/tools', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTool(id: number, data: Partial<CreateToolData>) {
    return this.request<Tool>(`/tools/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTool(id: number) {
    return this.request<{ message: string }>(`/tools/${id}`, {
      method: 'DELETE',
    });
  }

  async getMyTools() {
    return this.request<Tool[]>('/tools/my');
  }

  async rateTool(id: number, rating: number) {
    return this.request<{ message: string; average_rating: number }>(`/tools/${id}/rate`, {
      method: 'POST',
      body: JSON.stringify({ rating }),
    });
  }

  async getUserRating(toolId: number) {
    return this.request<{ rating: number | null }>(`/tools/${toolId}/my-rating`);
  }

  // Comments endpoints
  async getComments(toolId: number, skip = 0, limit = 10) {
    return this.request<{ comments: Comment[]; total: number }>(
      `/tools/${toolId}/comments?skip=${skip}&limit=${limit}`
    );
  }

  async addComment(toolId: number, content: string) {
    return this.request<Comment>(`/tools/${toolId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  async updateComment(toolId: number, commentId: number, content: string) {
    return this.request<Comment>(`/tools/${toolId}/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteComment(toolId: number, commentId: number) {
    return this.request<{ message: string }>(`/tools/${toolId}/comments/${commentId}`, {
      method: 'DELETE',
    });
  }

  async voteComment(toolId: number, commentId: number, vote: 'up' | 'down') {
    return this.request<{ upvotes: number; downvotes: number }>(`/tools/${toolId}/comments/${commentId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ vote }),
    });
  }

  // Admin endpoints
  async getPendingTools() {
    return this.request<Tool[]>('/admin/tools/pending');
  }

  async approveTool(id: number) {
    return this.request<Tool>(`/admin/tools/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved: true }),
    });
  }

  async rejectTool(id: number, reason: string) {
    return this.request<Tool>(`/admin/tools/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved: false, reason }),
    });
  }

  async getAllUsers() {
    return this.request<User[]>('/admin/users');
  }

  async updateUserRole(userId: number, role: string) {
    return this.request<User>(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async getStatistics() {
    return this.request<Statistics>('/admin/statistics');
  }
}

export const api = new ApiService();

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'user' | 'moderator' | 'admin';
  is_2fa_enabled: boolean;
  telegram_chat_id?: string;
  created_at: string;
}

export interface Tool {
  id: number;
  name: string;
  description: string;
  category: 'development' | 'design' | 'productivity' | 'communication' | 'analytics' | 'other';
  url: string;
  status: 'pending' | 'approved' | 'rejected';
  rejection_reason?: string;
  average_rating: number;
  total_ratings: number;
  rating_distribution?: { [key: number]: number };
  created_by: string;
  created_by_id: number;
  created_at: string;
}

export interface CreateToolData {
  name: string;
  description: string;
  category: string;
  url: string;
}

export interface Comment {
  id: number;
  content: string;
  username: string;
  user_id: number;
  upvotes: number;
  downvotes: number;
  user_vote?: 'up' | 'down' | null;
  created_at: string;
  updated_at?: string;
}

export interface Statistics {
  users_by_role: { role: string; count: number }[];
  tools_by_status: { status: string; count: number }[];
  tools_by_category: { category: string; count: number }[];
  recent_activity: { action: string; description: string; timestamp: string }[];
}
