const COUNTRY_OPTIONS = [
  { name: "Ukraine", code: "UA", aliases: ["украина", "ukraine"] },
  { name: "Russia", code: "RU", aliases: ["россия", "russia"] },
  { name: "USA", code: "US", aliases: ["сша", "америка", "usa", "united states", "america"] },
  { name: "Italy", code: "IT", aliases: ["италия", "italy"] },
  { name: "France", code: "FR", aliases: ["франция", "france"] },
  { name: "Japan", code: "JP", aliases: ["япония", "japan"] },
  { name: "China", code: "CN", aliases: ["китай", "china"] },
  { name: "Mexico", code: "MX", aliases: ["мексика", "mexico"] },
  { name: "India", code: "IN", aliases: ["индия", "india"] },
  { name: "Thailand", code: "TH", aliases: ["таиланд", "тайланд", "thailand"] },
  { name: "Germany", code: "DE", aliases: ["германия", "germany"] },
  { name: "Spain", code: "ES", aliases: ["испания", "spain"] },
  { name: "Greece", code: "GR", aliases: ["греция", "greece"] },
  { name: "Poland", code: "PL", aliases: ["польша", "poland"] },
  { name: "Hungary", code: "HU", aliases: ["венгрия", "hungary"] },
  { name: "Czechia", code: "CZ", aliases: ["чехия", "czechia", "czech republic"] },
  { name: "South Korea", code: "KR", aliases: ["корея", "южная корея", "korea", "south korea"] },
  { name: "North Korea", code: "KP", aliases: ["северная корея", "north korea"] },
  { name: "Vietnam", code: "VN", aliases: ["вьетнам", "vietnam"] },
  { name: "Turkey", code: "TR", aliases: ["турция", "turkey"] },
  { name: "Georgia", code: "GE", aliases: ["грузия", "georgia"] },
  { name: "Armenia", code: "AM", aliases: ["армения", "armenia"] },
  { name: "Azerbaijan", code: "AZ", aliases: ["азербайджан", "azerbaijan"] },
  { name: "Uzbekistan", code: "UZ", aliases: ["узбекистан", "uzbekistan"] },
  { name: "Kazakhstan", code: "KZ", aliases: ["казахстан", "kazakhstan"] },
  { name: "Israel", code: "IL", aliases: ["израиль", "israel"] },
  { name: "Morocco", code: "MA", aliases: ["марокко", "morocco"] },
  { name: "Egypt", code: "EG", aliases: ["египет", "egypt"] },
  { name: "Brazil", code: "BR", aliases: ["бразилия", "brazil"] },
  { name: "Argentina", code: "AR", aliases: ["аргентина", "argentina"] },
  { name: "Peru", code: "PE", aliases: ["перу", "peru"] },
  { name: "Canada", code: "CA", aliases: ["канада", "canada"] },
  { name: "United Kingdom", code: "GB", aliases: ["великобритания", "англия", "uk", "great britain", "united kingdom", "england"] },
  { name: "Ireland", code: "IE", aliases: ["ирландия", "ireland"] },
  { name: "Sweden", code: "SE", aliases: ["швеция", "sweden"] },
  { name: "Norway", code: "NO", aliases: ["норвегия", "norway"] },
  { name: "Denmark", code: "DK", aliases: ["дания", "denmark"] },
  { name: "Netherlands", code: "NL", aliases: ["нидерланды", "голландия", "netherlands", "holland"] },
  { name: "Belgium", code: "BE", aliases: ["бельгия", "belgium"] },
  { name: "Switzerland", code: "CH", aliases: ["швейцария", "switzerland"] },
  { name: "Austria", code: "AT", aliases: ["австрия", "austria"] },
  { name: "Romania", code: "RO", aliases: ["румыния", "romania"] },
  { name: "Bulgaria", code: "BG", aliases: ["болгария", "bulgaria"] },
  { name: "Serbia", code: "RS", aliases: ["сербия", "serbia"] },
  { name: "Croatia", code: "HR", aliases: ["хорватия", "croatia"] },
  { name: "Australia", code: "AU", aliases: ["австралия", "australia"] },
  { name: "New Zealand", code: "NZ", aliases: ["новая зеландия", "new zealand"] }
];

function flagFromCountryCode(code) {
  if (!code || !/^[A-Za-z]{2}$/.test(code)) return "🌍";
  return code.toUpperCase().replace(/./g, char =>
    String.fromCodePoint(127397 + char.charCodeAt(0))
  );
}

function normalizeCountryName(value) {
  return (value || "").trim().toLowerCase();
}

function findCountryByName(value) {
  const normalized = normalizeCountryName(value);
  if (!normalized) return null;

  const byCode = COUNTRY_OPTIONS.find(country => country.code.toLowerCase() === normalized);
  if (byCode) return { ...byCode, flag: flagFromCountryCode(byCode.code) };

  const byName = COUNTRY_OPTIONS.find(country =>
    country.name.toLowerCase() === normalized || country.aliases.includes(normalized)
  );

  return byName ? { ...byName, flag: flagFromCountryCode(byName.code) } : null;
}

function makeCountryFromInput(value) {
  const matched = findCountryByName(value);
  if (matched) return matched;

  const name = (value || "").trim();
  return name ? { name, code: "", flag: "🌍", aliases: [] } : null;
}
