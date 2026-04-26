// Search and filter functionality for recipes
const API_BASE = (() => {
  const params = new URLSearchParams(window.location.search);
  const urlApiBase = params.get('api_base');
  if (urlApiBase) {
    return urlApiBase.replace(/\/$/, '');
  }

  const savedApiBase = localStorage.getItem('recipe_api_base');
  if (savedApiBase) {
    return savedApiBase.replace(/\/$/, '');
  }

  if (window.RECIPE_API_BASE) {
    return String(window.RECIPE_API_BASE).replace(/\/$/, '');
  }

  const localStaticPorts = new Set(['5173', '5174', '5500', '5501']);
  if (
    window.location.hostname === 'localhost' &&
    localStaticPorts.has(window.location.port)
  ) {
    return 'http://127.0.0.1:8000';
  }

  return '';
})();

class RecipeSearch {
  constructor(recipes = []) {
    this.recipes = recipes;
    this.originalRecipes = [...recipes];
    this.searchInput = null;
    this.recipeGrid = null;
    this.categoryFilter = null;
    this.countryFilter = null;
    this.userFilter = null;
    this.currentCategory = null;
    this.currentCountry = null;
    this.currentUser = null;
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
    this.userFilter = document.getElementById('userFilter');

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

    if (this.userFilter) {
      this.userFilter.addEventListener('change', (e) => this.handleUserFilter(e));
      this.loadUsers();
    }

    this.applyUrlFilters();
    window.addEventListener('recipe-language-change', () => {
      this.loadCategories();
      this.loadCountries();
      this.applyFilters();
    });

    // Render recipes after initialization
    this.applyFilters();
  }

  // Load categories from recipes
  loadCategories() {
    const categories = [...new Set(this.originalRecipes.map(r => r.category))]
      .sort((a, b) => this.categoryLabel(a).localeCompare(this.categoryLabel(b)));

    const categorySelect = document.getElementById('categoryFilter');
    // Clear existing options except the first "All categories" option
    while (categorySelect.options.length > 1) {
      categorySelect.remove(1);
    }

    categories.forEach(cat => {
      const option = document.createElement('option');
      option.value = cat;
      option.textContent = this.categoryLabel(cat);
      categorySelect.appendChild(option);
    });

    categorySelect.value = this.currentCategory || '';
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
    ).sort((a, b) => this.countryLabel(a.name).localeCompare(this.countryLabel(b.name)));

    const countrySelect = document.getElementById('countryFilter');
    // Clear existing options except the first "All countries" option
    while (countrySelect.options.length > 1) {
      countrySelect.remove(1);
    }

    uniqueCountries.forEach(country => {
      const option = document.createElement('option');
      option.value = country.code || country.name;
      option.textContent = `${this.getCountryFlag(country.code)} ${this.countryLabel(country.name)}`;
      countrySelect.appendChild(option);
    });

    countrySelect.value = this.currentCountry || '';
  }

  // Load recipe owners from recipes
  loadUsers() {
    const users = this.originalRecipes
      .map(recipe => recipe.owner_username)
      .filter(Boolean);
    const uniqueUsers = [...new Set(users)].sort((a, b) => a.localeCompare(b));

    const userSelect = document.getElementById('userFilter');
    while (userSelect.options.length > 1) {
      userSelect.remove(1);
    }

    uniqueUsers.forEach(username => {
      const option = document.createElement('option');
      option.value = username;
      option.textContent = username;
      userSelect.appendChild(option);
    });

    userSelect.value = this.currentUser || '';
  }

  applyUrlFilters() {
    const params = new URLSearchParams(window.location.search);
    const user = params.get('user') || params.get('owner') || params.get('u');
    const category = params.get('category');
    const country = params.get('country');

    if (user && this.userFilter) {
      this.currentUser = user;
      this.userFilter.value = user;
    }

    if (category && this.categoryFilter) {
      this.currentCategory = category;
      this.categoryFilter.value = category;
    }

    if (country && this.countryFilter) {
      this.currentCountry = country;
      this.countryFilter.value = country;
    }
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

  // Handle user filter
  handleUserFilter(event) {
    this.currentUser = event.target.value;
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

      // User filter
      if (this.currentUser && recipe.owner_username !== this.currentUser) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const searchText = [
          this.displayTitle(recipe).toLowerCase(),
          (recipe.title || '').toLowerCase(),
          (recipe.titleEn || '').toLowerCase(),
          this.categoryLabel(recipe.category).toLowerCase(),
          (recipe.category || '').toLowerCase(),
          (recipe.owner_username || '').toLowerCase(),
          this.countryLabel(recipe.country_origin).toLowerCase(),
          (recipe.country_origin || '').toLowerCase(),
          (recipe.description || '').toLowerCase(),
          ...(recipe.ingredients || []).map(ing => ing.toLowerCase()),
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

  displayTitle(recipe) {
    return typeof recipeTitle === 'function' ? recipeTitle(recipe) : (recipe.title || recipe.titleEn || '');
  }

  categoryLabel(category) {
    return typeof recipeCategoryLabel === 'function' ? recipeCategoryLabel(category) : (category || '');
  }

  countryLabel(country) {
    return typeof recipeCountryLabel === 'function' ? recipeCountryLabel(country) : (country || '');
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
          <p class="text-muted fs-5">${tRecipe('empty.title')}</p>
          <p class="text-muted small">${tRecipe('empty.copy')}</p>
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
      const title = this.escapeHtml(this.displayTitle(recipe));
      const country = this.escapeHtml(this.countryLabel(recipe.country_origin));
      const category = this.escapeHtml(this.categoryLabel(recipe.category));
      const description = this.escapeHtml(recipe.description);
      const image = this.escapeHtml(this.getImageUrl(recipe.image, recipe.updated_at));
      const owner = this.escapeHtml(recipe.owner_username || '');

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
                <span>${owner ? `${tRecipe('card.author')}: ${owner}` : `${ingredientCount} ${tRecipe('card.ingredients')}`}</span>
                <span class="recipe-link-copy">${tRecipe('card.open')} <i class="fas fa-arrow-right" aria-hidden="true"></i></span>
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
      const title = this.displayTitle(recipe);
      if (title.toLowerCase().includes(q)) suggestions.add(title);
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
  setupMobileNavAutoHide();
});

function setupMobileNavAutoHide() {
  const nav = document.querySelector('.app-nav');
  if (!nav) return;

  const mobileQuery = window.matchMedia('(max-width: 768px)');
  let lastScrollY = window.scrollY;
  let ticking = false;

  function updateNav() {
    const currentScrollY = window.scrollY;
    const scrollingDown = currentScrollY > lastScrollY;
    const nearTop = currentScrollY < 80;
    const searchFocused = document.activeElement === document.getElementById('searchInput');

    if (!mobileQuery.matches || nearTop || searchFocused) {
      nav.classList.remove('nav-hidden');
    } else {
      nav.classList.toggle('nav-hidden', scrollingDown);
    }

    lastScrollY = currentScrollY;
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(updateNav);
      ticking = true;
    }
  }, { passive: true });

  mobileQuery.addEventListener('change', () => {
    nav.classList.remove('nav-hidden');
    lastScrollY = window.scrollY;
  });
}

// Show recipe detail
function showRecipeDetail(recipeId) {
  if (!window.search) return;

  const recipe = window.search.originalRecipes.find(r => r.id === recipeId);
  if (!recipe) return;

  const countryFlag = window.search.getCountryFlag(recipe.country_code);
  const title = window.search.displayTitle(recipe);
  const country = window.search.countryLabel(recipe.country_origin);
  const category = window.search.categoryLabel(recipe.category);

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
          <h5 class="modal-title">${title}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <img src="${recipe.image}" class="img-fluid rounded mb-3" alt="${title}" style="max-height: 400px; object-fit: cover; width: 100%;">

          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <span style="font-size: 2rem;">${countryFlag}</span>
            <div>
              <h6 class="text-muted mb-0">${country}</h6>
              <p class="text-muted small mb-0">${category}</p>
            </div>
          </div>

          <p class="text-muted">${recipe.description}</p>

          <h6 class="mt-4 mb-3"><strong>${tRecipe('detail.ingredients')}:</strong></h6>
          <ul class="list-group mb-4">
            ${ingredientsList}
          </ul>

          <h6 class="mb-3"><strong>${tRecipe('detail.preparation')}:</strong></h6>
          <p style="white-space: pre-wrap; line-height: 1.6;">${recipe.preparation}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${tRecipe('detail.close')}</button>
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
  const userFilter = document.getElementById('userFilter');
  if (userFilter) userFilter.value = '';

  // Trigger filter update
  if (window.search) {
    window.search.currentCategory = null;
    window.search.currentCountry = null;
    window.search.currentUser = null;
    window.search.applyFilters();
  }
}
