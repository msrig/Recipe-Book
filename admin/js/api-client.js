/**
 * API Client for Recipe Book Admin
 * Handles all communication with the FastAPI backend
 */

class RecipeAPI {
  constructor(baseURL = "http://localhost:8000") {
    this.baseURL = baseURL;
    this.token = localStorage.getItem("access_token");
  }

  // Set token after login
  setToken(token) {
    this.token = token;
    localStorage.setItem("access_token", token);
  }

  // Clear token on logout
  clearToken() {
    this.token = null;
    localStorage.removeItem("access_token");
  }

  // Get authorization headers
  getHeaders() {
    const headers = {
      "Content-Type": "application/json"
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    return headers;
  }

  // Generic fetch method
  async request(method, endpoint, data = null) {
    const url = `${this.baseURL}${endpoint}`;
    const options = {
      method,
      headers: this.getHeaders()
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);

      if (response.status === 401) {
        // Token expired or invalid
        this.clearToken();
        window.location.href = "/admin/login.html";
        return null;
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error: ${endpoint}`, error);
      throw error;
    }
  }

  // Auth endpoints
  async login(username, password) {
    return this.request("POST", "/api/auth/login", { username, password });
  }

  async verifyToken() {
    return this.request("GET", "/api/auth/verify");
  }

  // Recipe endpoints
  async getRecipes(category = null, country = null) {
    let endpoint = "/api/recipes/";
    const params = new URLSearchParams();

    if (category) params.append("category", category);
    if (country) params.append("country", country);

    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }

    return this.request("GET", endpoint);
  }

  async getRecipe(recipeId) {
    return this.request("GET", `/api/recipes/${recipeId}`);
  }

  async createRecipe(recipeData) {
    return this.request("POST", "/api/recipes/", recipeData);
  }

  async polishRecipe(recipeData) {
    return this.request("POST", "/api/recipes/ai/polish", recipeData);
  }

  async updateRecipe(recipeId, recipeData) {
    return this.request("PUT", `/api/recipes/${recipeId}`, recipeData);
  }

  async deleteRecipe(recipeId) {
    return this.request("DELETE", `/api/recipes/${recipeId}`);
  }

  // Image upload
  async uploadImage(recipeId, file) {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseURL}/api/recipes/${recipeId}/image`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.token}`
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Image upload failed");
    }

    return await response.json();
  }

  // Category endpoints
  async getCategories() {
    return this.request("GET", "/api/recipes/categories/list");
  }

  async addCategory(category) {
    return this.request("POST", "/api/recipes/categories/", { category });
  }

  // Country endpoints
  async getCountries() {
    return this.request("GET", "/api/recipes/countries/list");
  }
}

// Create global API instance
const api = new RecipeAPI();
