// Search and filter functionality for recipes
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
      const response = await fetch('http://localhost:8000/api/recipes/');
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
      arr.findIndex(x => x.code === c.code) === i
    ).sort((a, b) => a.name.localeCompare(b.name));

    const countrySelect = document.getElementById('countryFilter');
    // Clear existing options except the first "All countries" option
    while (countrySelect.options.length > 1) {
      countrySelect.remove(1);
    }

    uniqueCountries.forEach(country => {
      const option = document.createElement('option');
      option.value = country.code;
      option.textContent = country.name;
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
      if (this.currentCountry && recipe.country_code !== this.currentCountry) {
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
    const flags = {
      'UA': '🇺🇦', 'RU': '🇷🇺', 'US': '🇺🇸', 'IT': '🇮🇹',
      'FR': '🇫🇷', 'JP': '🇯🇵', 'CN': '🇨🇳', 'MX': '🇲🇽',
      'IN': '🇮🇳', 'TH': '🇹🇭', 'DE': '🇩🇪', 'ES': '🇪🇸',
      'GR': '🇬🇷', 'PL': '🇵🇱', 'HU': '🇭🇺', 'CZ': '🇨🇿'
    };
    return flags[countryCode] || '🌍';
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
          <div class="no-results-icon">😢</div>
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

      col.innerHTML = `
        <a href="${recipe.link}" class="text-decoration-none">
          <div class="card recipe-card h-100">
            <div class="recipe-image-container">
              <img src="${recipe.image}" class="card-img-top recipe-card-img" alt="${recipe.title}">
              <div class="recipe-overlay">
                <span class="recipe-category">${recipe.category}</span>
              </div>
            </div>
            <div class="card-body">
              <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span class="country-flag" title="${recipe.country_origin}" style="font-size: 1.3rem;">
                  ${countryFlag}
                </span>
                <h5 class="card-title text-dark" style="margin: 0; flex: 1;">${recipe.title}</h5>
              </div>
              <p class="card-text text-muted small">${recipe.description}</p>
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
}

// Initialize search when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
  const search = new RecipeSearch();
  await search.init();
  // Store global reference for resetFilters function
  window.search = search;
});

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
