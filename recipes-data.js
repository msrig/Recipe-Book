// Recipe data structure for search and display
const recipes = [
  {
    id: 1,
    title: "Турша",
    titleEn: "Turscha",
    category: "Закуска",
    categoryEn: "Appetizer",
    image: "images/recipe1.jpg",
    link: "recipe1.html",
    description: "Ферментированная салат из стручковой фасоли с перцем, чесноком и хреном",
    ingredients: ["Фасоль", "Перец", "Чеснок", "Хрен", "Огурцы"],
    keywords: ["турша", "фасоль", "закуска", "ферментированная", "овощи"]
  },
  {
    id: 2,
    title: "Зеленый Борщ",
    titleEn: "Green Borscht",
    category: "Суп",
    categoryEn: "Soup",
    image: "images/recipe2.jpg",
    link: "recipe2.html",
    description: "Традиционный русский суп из щавеля с картофелем и яйцом",
    ingredients: ["Щавель", "Картошка", "Морковь", "Яйца", "Зелень"],
    keywords: ["борщ", "зеленый", "суп", "щавель", "традиционный"]
  },
  {
    id: 3,
    title: "Салат \"Цезарь\" с курицей",
    titleEn: "Caesar Salad with Chicken",
    category: "Салат",
    categoryEn: "Salad",
    image: "images/recipe3.jpg",
    link: "recipe3.html",
    description: "Классический салат с курицей, листьями салата, помидорами и пармезаном",
    ingredients: ["Курица", "Салат Ромэн", "Помидоры", "Сыр Пармезан", "Сухарики"],
    keywords: ["цезарь", "салат", "курица", "классический", "овощи"]
  },
  {
    id: 4,
    title: "Тонкие Блины на молоке",
    titleEn: "Thin Milk Pancakes",
    category: "Завтрак",
    categoryEn: "Breakfast",
    image: "images/recipe4.jpg",
    link: "recipe4.html",
    description: "Тонкие и нежные блины из молока, яиц и муки",
    ingredients: ["Молоко", "Яйца", "Мука", "Сахар", "Масло"],
    keywords: ["блины", "завтрак", "молоко", "тонкие", "сладкое"]
  },
  {
    id: 5,
    title: "Куриный суп с лапшой",
    titleEn: "Chicken Noodle Soup",
    category: "Суп",
    categoryEn: "Soup",
    image: "images/recipe5.jpg",
    link: "recipe5.html",
    description: "Теплый и питательный суп из курицы с лапшой и овощами",
    ingredients: ["Курица", "Картофель", "Морковь", "Лапша", "Лук"],
    keywords: ["суп", "курица", "лапша", "традиционный", "питательный"]
  },
  {
    id: 6,
    title: "Шоколадный торт \"Прага\"",
    titleEn: "Prague Chocolate Cake",
    category: "Десерт",
    categoryEn: "Dessert",
    image: "images/recipe6.jpg",
    link: "recipe6.html",
    description: "Многослойный шоколадный торт с кремом и глазурью",
    ingredients: ["Какао", "Шоколад", "Масло", "Яйца", "Сахар"],
    keywords: ["торт", "шоколад", "прага", "десерт", "сладкое"]
  }
];

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = recipes;
}
