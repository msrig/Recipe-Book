/**
 * API Client for Recipe Book Admin
 * Handles all communication with the FastAPI backend
 */

class RecipeAPI {
  constructor(baseURL = null) {
    this.baseURL = baseURL ?? this.resolveBaseURL();
    this.token = localStorage.getItem("access_token");
  }

  resolveBaseURL() {
    const params = new URLSearchParams(window.location.search);
    const apiBaseFromUrl = params.get("api_base");

    if (apiBaseFromUrl) {
      const normalized = apiBaseFromUrl.replace(/\/$/, "");
      localStorage.setItem("recipe_api_base", normalized);
      return normalized;
    }

    const savedApiBase = localStorage.getItem("recipe_api_base");
    if (savedApiBase) {
      return savedApiBase.replace(/\/$/, "");
    }

    if (window.RECIPE_API_BASE) {
      return String(window.RECIPE_API_BASE).replace(/\/$/, "");
    }

    if (["5500", "5501", "5173", "5174"].includes(window.location.port)) {
      return "http://127.0.0.1:8000";
    }

    return "";
  }

  // Set token after login
  setToken(token) {
    this.token = token;
    localStorage.setItem("access_token", token);
  }

  setUser(user) {
    if (user) {
      localStorage.setItem("recipe_user", JSON.stringify(user));
    }
  }

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("recipe_user") || "null");
    } catch (error) {
      return null;
    }
  }

  // Clear token on logout
  clearToken() {
    this.token = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("recipe_user");
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
      const responseText = await response.text();
      let responseData = null;

      if (responseText) {
        try {
          responseData = JSON.parse(responseText);
        } catch (error) {
          throw new Error(`Expected JSON from ${url}, got: ${responseText.slice(0, 120)}`);
        }
      }

      if (response.status === 401) {
        // Token expired or invalid
        this.clearToken();
        throw new Error(responseData?.detail || "Invalid credentials");
      }

      if (response.status === 405 && endpoint.startsWith("/api/")) {
        throw new Error(
          "HTTP 405. API-запрос попал не в FastAPI backend. Если вы используете ngrok, запустите туннель на backend-порт 8000 или откройте админку через backend/ngrok URL."
        );
      }

      if (!response.ok) {
        throw new Error(responseData?.detail || responseText || `HTTP ${response.status}`);
      }

      return responseData;
    } catch (error) {
      console.error(`API Error: ${endpoint}`, error);
      throw error;
    }
  }

  async parseResponse(response, fallbackMessage, url = "") {
    const responseText = await response.text();
    let responseData = null;

    if (responseText) {
      try {
        responseData = JSON.parse(responseText);
      } catch (error) {
        if (response.status === 413) {
          throw new Error(
            "Файл слишком большой для сервера. Нужно увеличить client_max_body_size в Nginx или выбрать фото поменьше."
          );
        }

        const textPreview = responseText
          .replace(/<[^>]*>/g, " ")
          .replace(/\s+/g, " ")
          .trim()
          .slice(0, 160);
        throw new Error(textPreview || `Сервер вернул не JSON${url ? ` от ${url}` : ""}`);
      }
    }

    if (!response.ok) {
      throw new Error(responseData?.detail || fallbackMessage || `HTTP ${response.status}`);
    }

    return responseData;
  }

  // Auth endpoints
  async login(username, password) {
    return this.request("POST", "/api/auth/login", { username, password });
  }

  async register(userData) {
    return this.request("POST", "/api/auth/register", userData);
  }

  async verifyToken() {
    return this.request("GET", "/api/auth/verify");
  }

  async getMe() {
    return this.request("GET", "/api/auth/me");
  }

  async updateMe(profileData) {
    return this.request("PATCH", "/api/auth/me", profileData);
  }

  async requestPasswordReset(email) {
    return this.request("POST", "/api/auth/password/forgot", { email });
  }

  async resetPassword(token, password) {
    return this.request("POST", "/api/auth/password/reset", { token, password });
  }

  async getAdminUsers() {
    return this.request("GET", "/api/auth/admin/users");
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

  async getMyRecipes(category = null, country = null) {
    let endpoint = "/api/recipes/mine/list";
    const params = new URLSearchParams();

    if (category) params.append("category", category);
    if (country) params.append("country", country);

    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }

    return this.request("GET", endpoint);
  }

  async getUserRecipes(username) {
    return this.request("GET", `/api/recipes/users/${encodeURIComponent(username)}`);
  }

  async getAdminUserRecipes(userId) {
    return this.request("GET", `/api/recipes/admin/users/${encodeURIComponent(userId)}/recipes`);
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

  async extractRecipeFromPhoto(file) {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseURL}/api/recipes/ai/extract-from-photo`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.token}`
      },
      body: formData
    });

    return this.parseResponse(response, "AI extraction failed", url);
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

    return this.parseResponse(response, "Image upload failed", url);
  }

  async uploadImageFromQuery(recipeId, query) {
    return this.request("POST", `/api/recipes/${recipeId}/image/from-query`, { query });
  }

  async uploadImageFromPreview(recipeId, previewPath) {
    return this.request("POST", `/api/recipes/${recipeId}/image/from-preview`, { preview_path: previewPath });
  }

  // Category endpoints
  async getCategories() {
    return this.request("GET", "/api/recipes/categories/list");
  }

  async addCategory(category) {
    return this.request("POST", "/api/recipes/categories/", { category });
  }

  async deleteCategory(category) {
    return this.request("DELETE", `/api/recipes/categories/${encodeURIComponent(category)}`);
  }

  // Country endpoints
  async getCountries() {
    return this.request("GET", "/api/recipes/countries/list");
  }
}

// Create global API instance
const api = new RecipeAPI();
