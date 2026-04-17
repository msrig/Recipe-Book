// Search functionality for recipes
class RecipeSearch {
  constructor(recipes) {
    this.recipes = recipes;
    this.originalRecipes = [...recipes];
    this.searchInput = null;
    this.recipeGrid = null;
  }

  // Initialize search functionality
  init() {
    this.searchInput = document.getElementById('searchInput');
    this.recipeGrid = document.getElementById('recipeGrid');

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => this.handleSearch(e));
      this.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.searchInput.value = '';
          this.handleSearch({ target: { value: '' } });
        }
      });
    }
  }

  // Handle search input
  handleSearch(event) {
    const query = event.target.value.toLowerCase().trim();

    if (!query) {
      // Show all recipes if search is empty
      this.recipes = [...this.originalRecipes];
      this.renderRecipes();
      return;
    }

    // Filter recipes based on search query
    this.recipes = this.originalRecipes.filter(recipe => {
      const searchText = [
        recipe.title.toLowerCase(),
        recipe.titleEn.toLowerCase(),
        recipe.category.toLowerCase(),
        recipe.description.toLowerCase(),
        ...recipe.ingredients.map(ing => ing.toLowerCase()),
        ...recipe.keywords
      ].join(' ');

      // Simple substring search
      return searchText.includes(query);
    });

    this.renderRecipes();
  }

  // Render recipes based on current search results
  renderRecipes() {
    if (!this.recipeGrid) return;

    // Clear existing cards
    this.recipeGrid.innerHTML = '';

    if (this.recipes.length === 0) {
      // Show no results message
      const noResults = document.createElement('div');
      noResults.className = 'col-12 text-center py-5';
      noResults.innerHTML = '<p class="text-muted fs-5">Рецепты не найдены 😢</p>';
      this.recipeGrid.appendChild(noResults);
      return;
    }

    // Render recipe cards
    this.recipes.forEach((recipe, index) => {
      const col = document.createElement('div');
      col.className = 'col-lg-4 col-md-6';
      col.style.animationDelay = (index * 0.1) + 's';
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
              <h5 class="card-title text-dark">${recipe.title}</h5>
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
document.addEventListener('DOMContentLoaded', function() {
  if (typeof recipes !== 'undefined') {
    const search = new RecipeSearch(recipes);
    search.init();
    // Render all recipes on initial load
    search.renderRecipes();
  }
});
