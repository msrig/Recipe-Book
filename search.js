// Search and filter functionality for recipes
const API_BASE = window.location.protocol.startsWith('http') ? '' : 'http://localhost:8000';

class RecipeSearch {
  constructor(recipes = []) {
    this.recipes = recipes;
    this.originalRecipes = [...recipes];
    this.searchInput = null;
    this.recipeGrid = null;
    this.categoryFilter = null;
    this.countryFilter = null;
    this.currentCategory = null;
    this.currentCountry = null;
  }

  // Load recipes from API or fallback to static data
  async loadRecipes() {
    try {
      const response = await fetch(`${API_BASE}/api/recipes/`);
      if (!response.ok) throw new Error('API request failed');
      const data = await response.json();
      this.recipes = data.recipes || [];
      this.originalRecipes = [...this.recipes];
      console.log('Recipes loaded from API:', this.recipes.length);
    } catch (error) {
      console.warn('Failed to load from API, using static data:', error);
      // Fall back to static recipes-data.js if available
      if (typeof recipes !== 'undefined') {
        this.recipes = recipes;
        this.originalRecipes = [...recipes];
      }
    }
  }

  // Initialize search and filter functionality
  async init() {
    // Load recipes from API first
    await this.loadRecipes();

    this.searchInput = document.getElementById('searchInput');
    this.recipeGrid = document.getElementById('recipeGrid');
    this.categoryFilter = document.getElementById('categoryFilter');
    this.countryFilter = document.getElementById('countryFilter');

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => this.handleSearch(e));
      this.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.searchInput.value = '';
          this.handleSearch({ target: { value: '' } });
        }
      });
    }

    if (this.categoryFilter) {
      this.categoryFilter.addEventListener('change', (e) => this.handleCategoryFilter(e));
      this.loadCategories();
    }

    if (this.countryFilter) {
      this.countryFilter.addEventListener('change', (e) => this.handleCountryFilter(e));
      this.loadCountries();
    }

    // Render recipes after initialization
    this.renderRecipes();
  }

  // Load categories from recipes
  loadCategories() {
    const categories = [...new Set(this.originalRecipes.map(r => r.category))].sort();

    const categorySelect = document.getElementById('categoryFilter');
    // Clear existing options except the first "All categories" option
    while (categorySelect.options.length > 1) {
      categorySelect.remove(1);
    }

    categories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat;
      option.textContent = cat;
      categorySelect.appendChild(option);
    });
  }

  // Load countries from recipes
  loadCountries() {
    const countries = this.originalRecipes.map(r => ({
      name: r.country_origin,
      code: r.country_code || ''
    }));

    // Remove duplicates
    const uniqueCountries = countries.filter((c, i, arr) =>
      arr.findIndex(x => (x.code || x.name) === (c.code || c.name)) === i
    ).sort((a, b) => a.name.localeCompare(b.name));

    const countrySelect = document.getElementById('countryFilter');
    // Clear existing options except the first "All countries" option
    while (countrySelect.options.length > 1) {
      countrySelect.remove(1);
    }

    uniqueCountries.forEach(country => {
      const option = document.createElement('option');
      option.value = country.code || country.name;
      option.textContent = `${this.getCountryFlag(country.code)} ${country.name}`;
      countrySelect.appendChild(option);
    });
  }

  // Handle category filter
  handleCategoryFilter(event) {
    this.currentCategory = event.target.value;
    this.applyFilters();
  }

  // Handle country filter
  handleCountryFilter(event) {
    this.currentCountry = event.target.value;
    this.applyFilters();
  }

  // Apply all filters and search
  applyFilters() {
    const searchQuery = this.searchInput ? this.searchInput.value.toLowerCase().trim() : '';

    this.recipes = this.originalRecipes.filter(recipe => {
      // Category filter
      if (this.currentCategory && recipe.category !== this.currentCategory) {
        return false;
      }

      // Country filter
      if (
        this.currentCountry &&
        recipe.country_code !== this.currentCountry &&
        recipe.country_origin !== this.currentCountry
      ) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const searchText = [
          recipe.title.toLowerCase(),
          recipe.titleEn.toLowerCase(),
          recipe.category.toLowerCase(),
          recipe.description.toLowerCase(),
          ...recipe.ingredients.map(ing => ing.toLowerCase()),
          ...(recipe.keywords || [])
        ].join(' ');

        if (!searchText.includes(searchQuery)) {
          return false;
        }
      }

      return true;
    });

    this.renderRecipes();
  }

  // Handle search input
  handleSearch(event) {
    this.applyFilters();
  }

  // Get country flag emoji
  getCountryFlag(countryCode) {
    return flagFromCountryCode(countryCode);
  }

  // Render recipes based on current filters
  renderRecipes() {
    if (!this.recipeGrid) return;

    // Clear existing cards
    this.recipeGrid.innerHTML = '';

    if (this.recipes.length === 0) {
      // Show no results message
      const noResults = document.createElement('div');
      noResults.className = 'col-12 text-center py-5';
      noResults.innerHTML = `
        <div class="no-results">
          <div class="no-results-icon" aria-hidden="true"><i class="fas fa-magnifying-glass"></i></div>
          <p class="text-muted fs-5">Рецепты не найдены</p>
          <p class="text-muted small">Попробуйте изменить фильтры или поисковый запрос</p>
        </div>
      `;
      this.recipeGrid.appendChild(noResults);
      return;
    }

    // Render recipe cards
    this.recipes.forEach((recipe, index) => {
      const col = document.createElement('div');
      col.className = 'col-lg-4 col-md-6';
      col.style.animationDelay = (index * 0.1) + 's';

      const countryFlag = this.getCountryFlag(recipe.country_code);
      const ingredientCount = Array.isArray(recipe.ingredients) ? recipe.ingredients.length : 0;
      const title = this.escapeHtml(recipe.title);
      const country = this.escapeHtml(recipe.country_origin);
      const category = this.escapeHtml(recipe.category);
      const description = this.escapeHtml(recipe.description);
      const image = this.escapeHtml(this.getImageUrl(recipe.image, recipe.updated_at));

      col.innerHTML = `
        <a href="recipe.html?id=${encodeURIComponent(recipe.id)}" class="text-decoration-none">
          <div class="card recipe-card h-100">
            <div class="recipe-image-container">
              <img src="${image}" class="card-img-top recipe-card-img" alt="${title}">
              <div class="recipe-overlay">
                <span class="recipe-category">${category}</span>
                <span class="country-chip" title="${country}">${countryFlag} ${country}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="recipe-card-heading">
                <h5 class="card-title">${title}</h5>
              </div>
              <p class="card-text">${description}</p>
              <div class="recipe-card-footer">
                <span>${ingredientCount} ингредиентов</span>
                <span class="recipe-link-copy">Открыть <i class="fas fa-arrow-right" aria-hidden="true"></i></span>
              </div>
            </div>
          </div>
        </a>
      `;
      this.recipeGrid.appendChild(col);
    });
  }

  // Get search suggestions (for autocomplete if needed)
  getSuggestions(query) {
    const q = query.toLowerCase();
    const suggestions = new Set();

    this.originalRecipes.forEach(recipe => {
      if (recipe.title.toLowerCase().includes(q)) suggestions.add(recipe.title);
      recipe.ingredients.forEach(ing => {
        if (ing.toLowerCase().includes(q)) suggestions.add(ing);
      });
    });

    return Array.from(suggestions).slice(0, 5);
  }

  getImageUrl(imagePath, updatedAt) {
    if (!imagePath) return '';
    if (!updatedAt) return imagePath;

    const version = encodeURIComponent(String(updatedAt));
    const separator = imagePath.includes('?') ? '&' : '?';
    return `${imagePath}${separator}v=${version}`;
  }

  escapeHtml(value = '') {
    const div = document.createElement('div');
    div.textContent = String(value);
    return div.innerHTML;
  }
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
  const search = new RecipeSearch();
  await search.init();
  // Store global reference for resetFilters function
  window.search = search;
});

// Show recipe detail
function showRecipeDetail(recipeId) {
  if (!window.search) return;

  const recipe = window.search.originalRecipes.find(r => r.id === recipeId);
  if (!recipe) return;

  const countryFlag = window.search.getCountryFlag(recipe.country_code);

  let ingredientsList = '';
  recipe.ingredients.forEach(ing => {
    ingredientsList += `<li class="list-group-item">${ing}</li>`;
  });

  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.id = `modal-${recipeId}`;
  modal.setAttribute('tabindex', '-1');
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">${recipe.title}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <img src="${recipe.image}" class="img-fluid rounded mb-3" alt="${recipe.title}" style="max-height: 400px; object-fit: cover; width: 100%;">

          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">${countryFlag}</span>
            <div>
              <h6 class="text-muted mb-0">${recipe.country_origin}</h6>
              <p class="text-muted small mb-0">${recipe.category}</p>
            </div>
          </div>

          <p class="text-muted">${recipe.description}</p>

          <h6 class="mt-4 mb-3"><strong>Ингредиенты:</strong></h6>
          <ul class="list-group mb-4">
            ${ingredientsList}
          </ul>

          <h6 class="mb-3"><strong>Приготовление:</strong></h6>
          <p style="white-space: pre-wrap; line-height: 1.6;">${recipe.preparation}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  const bootstrapModal = new bootstrap.Modal(modal);
  bootstrapModal.show();

  // Clean up modal after it's hidden
  modal.addEventListener('hidden.bs.modal', () => {
    modal.remove();
  });
}

// Reset filters function
function resetFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('categoryFilter').value = '';
  document.getElementById('countryFilter').value = '';

  // Trigger filter update
  if (window.search) {
    window.search.currentCategory = null;
    window.search.currentCountry = null;
    window.search.applyFilters();
  }
}
