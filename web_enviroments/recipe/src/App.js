// import React, { useState, useEffect } from 'react';
// import Select from 'react-select';
// import {
//   FaSearch,
//   FaListUl,
//   FaClipboardList,
//   FaUtensils,
//   FaFacebookF,
//   FaTwitter,
//   FaInstagram
// } from 'react-icons/fa';
// import './App.css';

// const home_url = 'http://98.80.38.242:1220/';

// const ingredientsOptions = [
//   { value: "Bread", label: "Bread" },
//   { value: "Egg", label: "Egg" },
//   { value: "Apple", label: "Apple" },
//   { value: "Lettuce", label: "Lettuce" },
//   { value: "Potato", label: "Potato" },
//   { value: "Tomato", label: "Tomato" }
// ];


// const equipmentOptions = [
//   { value: "Bowl", label: "Bowl" },
//   { value: "Pan", label: "Pan" },
//   { value: "Knife", label: "Knife" },
//   { value: "Toaster", label: "Toaster" },
//   { value: "StoveBurner", label: "StoveBurner" },
//   { value: "Microwave", label: "Microwave" },
//   { value: "Plate", label: "Plate" }
// ];

// const dietOptions = [
//   { value: '', label: 'All Diet Types' },
//   { value: 'vegetarian', label: 'Vegetarian' },
//   { value: 'non-vegetarian', label: 'Non-Vegetarian' }
// ];

// const difficultyOptions = [
//   { value: '', label: 'All Difficulties' },
//   { value: 'novice', label: 'Novice' },
//   { value: 'simple', label: 'Simple' },
//   { value: 'intermediate', label: 'Intermediate' },
//   { value: 'hard', label: 'Hard' }
// ];

// function TopBar() {
//   return (
//     <div className="bg-white shadow-md">
//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
//         <div className="flex justify-between items-center py-3">
//           <div className="flex items-center space-x-4">

//             <a href={home_url} style={{
//               textDecoration: "none",
//               color: "black",
//               margin: "0 1rem",
//               display: "flex",
//               alignItems: "center",
//             }}>
//               <h3 style={{ color: "black", margin: "0", border: "2px solid black", padding: "0.5rem", borderRadius: "5px" }}>🏠 Home </h3>
//             </a>

//             <FaSearch className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//             <FaListUl className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//             <FaClipboardList className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//             <FaUtensils className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//           </div>
//           <div className="flex items-center space-x-4">
//             <FaFacebookF className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//             <FaTwitter className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//             <FaInstagram className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

// function Carousel({ recipes, getRecipeImageUrl, onSelectRecipe }) {
//   return (
//     <div className="mb-12">
//       <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Popular Recipes</h2>
//       <div className="flex space-x-6 overflow-x-auto pb-4">
//         {recipes.map((recipe) => (
//           <div
//             key={recipe.id}
//             onClick={() => onSelectRecipe(recipe)}
//             className="w-50 h-50 flex-shrink-0 bg-white rounded-lg shadow-xl p-6 cursor-pointer transform transition hover:scale-105 flex flex-col items-center"
//           >
//             <img
//               src={getRecipeImageUrl(recipe)}
//               alt={recipe.name}
//               className="w-48 h-48 object-cover rounded-md mb-4"
//             />
//             <h3 className="text-lg font-semibold text-gray-700 text-center flex items-center gap-2">
//               <FaUtensils className="text-indigo-500" /> {recipe.name}
//             </h3>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }

// function FeaturedCategories() {
//   const categories = [
//     { id: 1, name: 'Breakfast', image: 'imgs/Apple and Egg Breakfast Bowl/Apple_Egg_Cheese_Bake1Logo-1.jpg' },
//     { id: 2, name: 'Lunch', image: 'imgs/Veggie Medley Plate/0B88C201-D67F-4FC4-9F3F-978F52FB2FE2.jpg' },
//     { id: 3, name: 'Dinner', image: 'imgs/Simple Apple and Potato Mash/96d793ce15728203d9521a6f763c0edc.jpg' },
//     { id: 4, name: 'Desserts', image: 'imgs/Sautéed Apple and Tomato Salad/5456742.jpg' },
//   ];

//   return (
//     <div className="mb-12">
//       <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Categories</h2>
//       <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
//         {categories.map((category) => (
//           <div key={category.id} className="bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer transform transition hover:scale-105">
//             <img
//               src={`${process.env.PUBLIC_URL}/${category.image}`}
//               alt={category.name}
//               className="w-full h-32 object-cover"
//             />
//             <div className="p-4 text-center">
//               <h3 className="text-xl font-semibold text-gray-700">{category.name}</h3>
//             </div>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }

// function LatestArticles() {
//   const articles = [
//     { id: 1, title: '5 Quick Breakfast Ideas', excerpt: 'Start your day right with these quick and healthy breakfast recipes.' },
//     { id: 2, title: 'Meal Prep 101', excerpt: 'Learn the basics of meal prepping to save time during your busy week.' },
//     { id: 3, title: 'Decadent Desserts', excerpt: 'Indulge in our favorite dessert recipes for a sweet ending to any meal.' },
//   ];

//   return (
//     <div className="mb-12">
//       <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Latest Articles</h2>
//       <div className="space-y-6">
//         {articles.map((article) => (
//           <div key={article.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-2xl transition">
//             <h3 className="text-2xl font-semibold text-gray-800 mb-2">{article.title}</h3>
//             <p className="text-gray-600">{article.excerpt}</p>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }

// function Footer() {
//   return (
//     <footer className="bg-gray-800 py-6 mt-12">
//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
//         <div className="flex justify-center space-x-6 mb-4">
//           <a href="https://www.facebook.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
//             <FaFacebookF size={20} />
//           </a>
//           <a href="https://www.twitter.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
//             <FaTwitter size={20} />
//           </a>
//           <a href="https://www.instagram.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
//             <FaInstagram size={20} />
//           </a>
//         </div>
//         <p className="text-gray-400">&copy; 2025 Recipes.</p>
//       </div>
//     </footer>
//   );
// }

// function App() {
//   const [recipes, setRecipes] = useState([]);
//   const [searchQuery, setSearchQuery] = useState('');
//   const [dietFilter, setDietFilter] = useState('');
//   const [difficultyFilter, setDifficultyFilter] = useState('');
//   const [selectedIngredients, setSelectedIngredients] = useState([]);
//   const [selectedEquipments, setSelectedEquipments] = useState([]);
//   const [filteredRecipes, setFilteredRecipes] = useState([]);
//   const [selectedRecipe, setSelectedRecipe] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const [stepIndex, setStepIndex] = useState(0);

//   useEffect(() => {
//     const fetchRecipes = async () => {
//       try {
//         const response = await fetch('recipes.json');
//         const data = await response.json();
//         setRecipes(data);
//         setLoading(false);
//       } catch (error) {
//         console.error('Error fetching recipes:', error);
//         setLoading(false);
//       }
//     };

//     fetchRecipes();
//   }, []);

//   useEffect(() => {
//     setStepIndex(0);
//   }, [selectedRecipe]);

//   useEffect(() => {
//     // deep copy recipes to filtered
//     let filtered = JSON.parse(JSON.stringify(recipes));

//     const trimmedSearchQuery = searchQuery.trim().toLowerCase();

//     if (trimmedSearchQuery !== '') {
//       filtered = filtered.filter(recipe =>
//         recipe.name.toLowerCase().includes(trimmedSearchQuery)
//       );
//     }  

//     if (dietFilter !== '') {
//       filtered = filtered.filter(recipe =>
//         recipe.diet_type && recipe.diet_type.toLowerCase() === dietFilter.toLowerCase()
//       );
//     }
//     if (difficultyFilter !== '') {
//       filtered = filtered.filter(recipe =>
//         recipe.difficulty && recipe.difficulty.toLowerCase() === difficultyFilter.toLowerCase()
//       );
//     }

//     if (selectedIngredients.length > 0) {
//       const ingredientValues = selectedIngredients.map(item => item.value);
//       filtered = filtered.filter(recipe =>
//         ingredientValues.every(ing => recipe.ingredients.includes(ing))
//       );
//     }

//     if (selectedEquipments.length > 0) {
//       const equipmentValues = selectedEquipments.map(item => item.value);
//       filtered = filtered.filter(recipe =>
//         equipmentValues.every(eq => recipe.equipment.includes(eq))
//       );
//     }

//     setFilteredRecipes(filtered);
//     window.scrollTo(0, 0);
//   }, [recipes, searchQuery, dietFilter, difficultyFilter, selectedIngredients, selectedEquipments]);

//   const getRecipeImageUrl = (recipe) => {
//     return `${process.env.PUBLIC_URL}/imgs/${recipe.name}/${recipe.image}`;
//   };

//   return (
//     <div className="min-h-screen bg-gray-50 flex flex-col">
//       <TopBar />

//       <header className="bg-gradient-to-r from-violet-400 to-red-600 py-8 shadow-lg">
//         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
//           <h1 className="text-4xl font-extrabold text-white"> Recipes</h1>
//           <p className="mt-2 text-lg text-indigo-100">
//             Discover and cook your next favorite meal
//           </p>
//         </div>
//       </header>

//       <main className="flex-grow max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
//         <div className="mb-8 space-y-4">
//           <div className="flex flex-wrap gap-4 items-center">
//             <input
//               type="text"
//               placeholder="Search recipes..."
//               value={searchQuery}
//               onChange={(e) => setSearchQuery(e.target.value)}
//               className="w-full px-4 py-2 border rounded-md"
//             />
//           </div>

//           <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
//             <div>
//               <Select
//                 name="diet type"
//                 options={dietOptions}
//                 className="basic-single"
//                 classNamePrefix="select"
//                 placeholder="Filter by Diet"
//                 value={dietOptions.find(option => option.value === dietFilter)}
//                 onChange={(option) => setDietFilter(option.value)}
//               />
//             </div>
//             <div>
//               <Select
//                 name="difficulty"
//                 options={difficultyOptions}
//                 className="basic-single"
//                 classNamePrefix="select"
//                 placeholder="Filter by Difficulty"
//                 value={difficultyOptions.find(option => option.value === difficultyFilter)}
//                 onChange={(option) => setDifficultyFilter(option.value)}
//               />
//             </div>
//             <div>
//               <Select
//                 isMulti
//                 name="ingredients"
//                 options={ingredientsOptions}
//                 className="basic-multi-select"
//                 classNamePrefix="select"
//                 placeholder="Filter by Ingredients"
//                 value={selectedIngredients}
//                 onChange={setSelectedIngredients}
//               />
//             </div>
//             <div>
//               <Select
//                 isMulti
//                 name="equipments"
//                 options={equipmentOptions}
//                 className="basic-multi-select"
//                 classNamePrefix="select"
//                 placeholder="Filter by Equipments"
//                 value={selectedEquipments}
//                 onChange={setSelectedEquipments}
//               />
//             </div>
//           </div>

//         </div>

//         {searchQuery.trim() === '' &&
//           dietFilter === '' &&
//           difficultyFilter === '' &&
//           selectedIngredients.length === 0 &&
//           selectedEquipments.length === 0 &&
//           !loading && recipes.length > 0 && (
//             <>
//               <Carousel
//                 recipes={recipes}
//                 getRecipeImageUrl={getRecipeImageUrl}
//                 onSelectRecipe={setSelectedRecipe}
//               />
//               <FeaturedCategories />
//               <LatestArticles />
//             </>
//           )}

//         {/* When filters or search query applied */}
//         {(searchQuery.trim() !== '' ||
//           dietFilter !== '' ||
//           difficultyFilter !== '' ||
//           selectedIngredients.length > 0 ||
//           selectedEquipments.length > 0) && (
//             <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
//               <div className="bg-white rounded-lg shadow-lg p-6">
//                 <h2 className="text-2xl font-bold text-gray-800 border-b pb-2 mb-4">
//                   Search Results
//                 </h2>
//                 {filteredRecipes.length > 0 ? (
//                   <ul className="divide-y divide-gray-200">
//                     {filteredRecipes.map((recipe) => (
//                       <li
//                         key={recipe.id}
//                         className={`py-3 flex items-center gap-4 transition-transform transform hover:scale-105 ${selectedRecipe?.id === recipe.id ? 'bg-indigo-50 rounded-md' : ''
//                           }`}
//                       >
//                         <img
//                           src={getRecipeImageUrl(recipe)}
//                           alt={recipe.name}
//                           className="w-20 h-20 object-cover rounded-md shadow-sm"
//                         />
//                         <button
//                           onClick={() => setSelectedRecipe(recipe)}
//                           className={`text-lg flex-1 text-left focus:outline-none ${selectedRecipe?.id === recipe.id
//                             ? 'text-indigo-700 font-semibold'
//                             : 'text-gray-700 hover:text-indigo-600'
//                             }`}
//                         >
//                           {recipe.name}
//                         </button>
//                       </li>
//                     ))}
//                   </ul>
//                 ) : (
//                   <p className="text-center text-gray-500">No recipes found.</p>
//                 )}
//               </div>

//               <div className="bg-white rounded-lg shadow-lg p-6">
//                 {selectedRecipe ? (
//                   <>
//                     <h2 className="text-3xl font-bold text-gray-800 mb-6">Recipe Details</h2>
//                     <img
//                       src={getRecipeImageUrl(selectedRecipe)}
//                       alt={selectedRecipe.name}
//                       className="w-full h-72 object-cover rounded-md shadow-md mb-6"
//                     />
//                     <h3 className="text-2xl font-semibold text-gray-700 mb-3">
//                       {selectedRecipe.name}
//                     </h3>

//                     {/* Ingredients Section */}
//                     <div className="mb-4">
//                       <h4 className="flex items-center text-xl font-semibold text-gray-600 mb-2">
//                         <FaListUl className="mr-2 text-indigo-500" /> Ingredients
//                       </h4>
//                       <ul className="list-disc pl-5 space-y-1 text-gray-700">
//                         {selectedRecipe.ingredients.map((ingredient, index) => (
//                           <li key={index}>{ingredient}</li>
//                         ))}
//                       </ul>
//                     </div>

//                     {/* Step-by-step Recipe Instructions */}
//                     <div>
//                       <h4 className="flex items-center text-xl font-semibold text-gray-600 mb-2">
//                         <FaClipboardList className="mr-2 text-indigo-500 inline" /> Recipe Steps
//                       </h4>
//                       <p className="text-gray-700 mb-4">
//                         {selectedRecipe.recipe[stepIndex]}
//                       </p>
//                       <div className="flex justify-between items-center">
//                         <button
//                           onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
//                           disabled={stepIndex === 0}
//                           className="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300"
//                         >
//                           Previous
//                         </button>
//                         <span className="text-sm text-gray-500">
//                           Step {stepIndex + 1} of {selectedRecipe.recipe.length}
//                         </span>
//                         <button
//                           onClick={() =>
//                             setStepIndex((i) => Math.min(selectedRecipe.recipe.length - 1, i + 1))
//                           }
//                           disabled={stepIndex === selectedRecipe.recipe.length - 1}
//                           className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600"
//                         >
//                           Next
//                         </button>
//                       </div>
//                     </div>
//                   </>
//                 ) : (
//                   <div className="h-full flex items-center justify-center">
//                     <p className="text-gray-500">Select a recipe to see details.</p>
//                   </div>
//                 )}
//               </div>
//             </div>
//           )}

//         {loading && <p className="text-center text-gray-600">Loading recipes...</p>}
//       </main>

//       <Footer />
//     </div>
//   );
// }

// export default App;


import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import {
  FaSearch,
  FaListUl,
  FaClipboardList,
  FaUtensils,
  FaFacebookF,
  FaTwitter,
  FaInstagram
} from 'react-icons/fa';
import './App.css';

const home_url = 'http://98.80.38.242:1220/';

const ingredientsOptions = [
  { value: "Bread", label: "Bread" },
  { value: "Egg", label: "Egg" },
  { value: "Apple", label: "Apple" },
  { value: "Lettuce", label: "Lettuce" },
  { value: "Potato", label: "Potato" },
  { value: "Tomato", label: "Tomato" }
];

const equipmentOptions = [
  { value: "Bowl", label: "Bowl" },
  { value: "Pan", label: "Pan" },
  { value: "Knife", label: "Knife" },
  { value: "Toaster", label: "Toaster" },
  { value: "StoveBurner", label: "StoveBurner" },
  { value: "Microwave", label: "Microwave" },
  { value: "Plate", label: "Plate" }
];

const dietOptions = [
  { value: '', label: 'All Diet Types' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'non-vegetarian', label: 'Non-Vegetarian' }
];

const difficultyOptions = [
  { value: '', label: 'All Difficulties' },
  { value: 'novice', label: 'Novice' },
  { value: 'simple', label: 'Simple' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'hard', label: 'Hard' }
];

function TopBar() {
  return (
    <div className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-3">
          <div className="flex items-center space-x-4">
            <a href={home_url} style={{
              textDecoration: "none",
              color: "black",
              margin: "0 1rem",
              display: "flex",
              alignItems: "center",
            }}>
              <h3 style={{ color: "black", margin: "0", border: "2px solid black", padding: "0.5rem", borderRadius: "5px" }}>🏠 Home </h3>
            </a>
            <FaSearch className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
            <FaListUl className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
            <FaClipboardList className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
            <FaUtensils className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
          </div>
          <div className="flex items-center space-x-4">
            <FaFacebookF className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
            <FaTwitter className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
            <FaInstagram className="text-gray-600 hover:text-indigo-500 cursor-pointer" size={20} />
          </div>
        </div>
      </div>
    </div>
  );
}

function Carousel({ recipes, getRecipeImageUrl, onSelectRecipe }) {
  return (
    <div className="mb-12">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Popular Recipes</h2>
      <div className="flex space-x-6 overflow-x-auto pb-4">
        {recipes.map((recipe) => (
          <div
            key={recipe.id}
            onClick={() => onSelectRecipe(recipe)}
            className="w-50 h-50 flex-shrink-0 bg-white rounded-lg shadow-xl p-6 cursor-pointer transform transition hover:scale-105 flex flex-col items-center"
          >
            <img
              src={getRecipeImageUrl(recipe)}
              alt={recipe.name}
              className="w-48 h-48 object-cover rounded-md mb-4"
            />
            <h3 className="text-lg font-semibold text-gray-700 text-center flex items-center gap-2">
              <FaUtensils className="text-indigo-500" /> {recipe.name}
            </h3>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeaturedCategories() {
  const categories = [
    { id: 1, name: 'Breakfast', image: 'imgs/Apple and Egg Breakfast Bowl/Apple_Egg_Cheese_Bake1Logo-1.jpg' },
    { id: 2, name: 'Lunch', image: 'imgs/Veggie Medley Plate/0B88C201-D67F-4FC4-9F3F-978F52FB2FE2.jpg' },
    { id: 3, name: 'Dinner', image: 'imgs/Simple Apple and Potato Mash/96d793ce15728203d9521a6f763c0edc.jpg' },
    { id: 4, name: 'Desserts', image: 'imgs/Sautéed Apple and Tomato Salad/5456742.jpg' },
  ];

  return (
    <div className="mb-12">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Categories</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {categories.map((category) => (
          <div key={category.id} className="bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer transform transition hover:scale-105">
            <img
              src={`${process.env.PUBLIC_URL}/${category.image}`}
              alt={category.name}
              className="w-full h-32 object-cover"
            />
            <div className="p-4 text-center">
              <h3 className="text-xl font-semibold text-gray-700">{category.name}</h3>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LatestArticles() {
  const articles = [
    { id: 1, title: '5 Quick Breakfast Ideas', excerpt: 'Start your day right with these quick and healthy breakfast recipes.' },
    { id: 2, title: 'Meal Prep 101', excerpt: 'Learn the basics of meal prepping to save time during your busy week.' },
    { id: 3, title: 'Decadent Desserts', excerpt: 'Indulge in our favorite dessert recipes for a sweet ending to any meal.' },
  ];

  return (
    <div className="mb-12">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Latest Articles</h2>
      <div className="space-y-6">
        {articles.map((article) => (
          <div key={article.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-2xl transition">
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">{article.title}</h3>
            <p className="text-gray-600">{article.excerpt}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Footer() {
  return (
    <footer className="bg-gray-800 py-6 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="flex justify-center space-x-6 mb-4">
          <a href="https://www.facebook.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
            <FaFacebookF size={20} />
          </a>
          <a href="https://www.twitter.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
            <FaTwitter size={20} />
          </a>
          <a href="https://www.instagram.com" target="_blank" rel="noreferrer" className="text-white hover:text-indigo-500">
            <FaInstagram size={20} />
          </a>
        </div>
        <p className="text-gray-400">&copy; 2025 Recipes.</p>
      </div>
    </footer>
  );
}

function App() {
  const [recipes, setRecipes] = useState([]);
  const [inputValue, setInputValue] = useState(''); // For the input field's immediate value
  const [searchQuery, setSearchQuery] = useState(''); // For the debounced search query
  const [dietFilter, setDietFilter] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [selectedIngredients, setSelectedIngredients] = useState([]);
  const [selectedEquipments, setSelectedEquipments] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const response = await fetch('recipes.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setRecipes(data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching recipes:', error);
        setLoading(false);
      }
    };

    fetchRecipes();
  }, []);

  // Debounce effect for search query
  useEffect(() => {
    const timerId = setTimeout(() => {
      setSearchQuery(inputValue);
    }, 500); // Adjust delay as needed (e.g., 300-500ms)

    return () => {
      clearTimeout(timerId);
    };
  }, [inputValue]);


  useEffect(() => {
    setStepIndex(0);
  }, [selectedRecipe]);

  useEffect(() => {
    let filtered = recipes;

    // Use the debounced searchQuery, then trim and lowercase for actual filtering
    const trimmedSearchQuery = searchQuery.trim().toLowerCase();

    if (trimmedSearchQuery !== '') {
      filtered = filtered.filter(recipe =>
        recipe.name.toLowerCase().includes(trimmedSearchQuery)
      );
    }

    if (dietFilter !== '') {
      filtered = filtered.filter(recipe =>
        recipe.diet_type && recipe.diet_type.toLowerCase() === dietFilter.toLowerCase()
      );
    }
    if (difficultyFilter !== '') {
      filtered = filtered.filter(recipe =>
        recipe.difficulty && recipe.difficulty.toLowerCase() === difficultyFilter.toLowerCase()
      );
    }

    if (selectedIngredients.length > 0) {
      const selectedIngredientValues = selectedIngredients.map(item => item.value.toLowerCase());
      filtered = filtered.filter(recipe => {
        const recipeIngredientsLower = recipe.ingredients.map(ing => ing.toLowerCase());
        return selectedIngredientValues.every(selectedIng => recipeIngredientsLower.includes(selectedIng));
      });
    }

    if (selectedEquipments.length > 0) {
      const selectedEquipmentValues = selectedEquipments.map(item => item.value.toLowerCase());
      filtered = filtered.filter(recipe => {
        const recipeEquipmentLower = recipe.equipment.map(eq => eq.toLowerCase());
        return selectedEquipmentValues.every(selectedEq => recipeEquipmentLower.includes(selectedEq));
      });
    }

    setFilteredRecipes(filtered);
  }, [recipes, searchQuery, dietFilter, difficultyFilter, selectedIngredients, selectedEquipments]);

  const getRecipeImageUrl = (recipe) => {
    if (!recipe || !recipe.name || !recipe.image) {
        // Return a placeholder or default image URL if data is missing
        return `${process.env.PUBLIC_URL}/imgs/placeholder.jpg`;
    }
    return `${process.env.PUBLIC_URL}/imgs/${recipe.name}/${recipe.image}`;
  };

  // Condition to show homepage content (carousel, categories, articles)
  const showHomepageContent =
    searchQuery.trim() === '' &&
    inputValue.trim() === '' && // Also check inputValue for immediate feedback
    dietFilter === '' &&
    difficultyFilter === '' &&
    selectedIngredients.length === 0 &&
    selectedEquipments.length === 0 &&
    !loading && recipes.length > 0;


  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <TopBar />

      <header className="bg-gradient-to-r from-violet-400 to-red-600 py-8 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl font-extrabold text-white"> Recipes</h1>
          <p className="mt-2 text-lg text-indigo-100">
            Discover and cook your next favorite meal
          </p>
        </div>
      </header>

      <main className="flex-grow max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
        <div className="mb-8 space-y-4">
          <div className="flex flex-wrap gap-4 items-center">
            <input
              type="text"
              placeholder="Search recipes..."
              value={inputValue} // Controlled by inputValue
              onChange={(e) => setInputValue(e.target.value)} // Updates inputValue immediately
              className="w-full px-4 py-2 border rounded-md"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
            <div>
              <Select
                name="diet type"
                options={dietOptions}
                className="basic-single"
                classNamePrefix="select"
                placeholder="Filter by Diet"
                value={dietOptions.find(option => option.value === dietFilter)}
                onChange={(option) => setDietFilter(option ? option.value : '')}
                isClearable
              />
            </div>
            <div>
              <Select
                name="difficulty"
                options={difficultyOptions}
                className="basic-single"
                classNamePrefix="select"
                placeholder="Filter by Difficulty"
                value={difficultyOptions.find(option => option.value === difficultyFilter)}
                onChange={(option) => setDifficultyFilter(option ? option.value : '')}
                isClearable
              />
            </div>
            <div>
              <Select
                isMulti
                name="ingredients"
                options={ingredientsOptions}
                className="basic-multi-select"
                classNamePrefix="select"
                placeholder="Filter by Ingredients"
                value={selectedIngredients}
                onChange={setSelectedIngredients}
              />
            </div>
            <div>
              <Select
                isMulti
                name="equipments"
                options={equipmentOptions}
                className="basic-multi-select"
                classNamePrefix="select"
                placeholder="Filter by Equipments"
                value={selectedEquipments}
                onChange={setSelectedEquipments}
              />
            </div>
          </div>
        </div>

        {showHomepageContent ? (
            <>
              <Carousel
                recipes={recipes} // Show all recipes initially in carousel before filtering
                getRecipeImageUrl={getRecipeImageUrl}
                onSelectRecipe={setSelectedRecipe}
              />
              <FeaturedCategories />
              <LatestArticles />
            </>
          ) : !loading && ( // When filters or search query applied or if loading is done
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-800 border-b pb-2 mb-4">
                  Search Results
                </h2>
                {filteredRecipes.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {filteredRecipes.map((recipe) => (
                      <li
                        key={recipe.id}
                        className={`py-3 flex items-center gap-4 transition-transform transform hover:scale-105 ${selectedRecipe?.id === recipe.id ? 'bg-indigo-50 rounded-md' : ''
                          }`}
                      >
                        <img
                          src={getRecipeImageUrl(recipe)}
                          alt={recipe.name}
                          className="w-20 h-20 object-cover rounded-md shadow-sm"
                        />
                        <button
                          onClick={() => setSelectedRecipe(recipe)}
                          className={`text-lg flex-1 text-left focus:outline-none ${selectedRecipe?.id === recipe.id
                            ? 'text-indigo-700 font-semibold'
                            : 'text-gray-700 hover:text-indigo-600'
                            }`}
                        >
                          {recipe.name}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-center text-gray-500">No recipes found matching your criteria.</p>
                )}
              </div>

              <div className="bg-white rounded-lg shadow-lg p-6">
                {selectedRecipe ? (
                  <>
                    <h2 className="text-3xl font-bold text-gray-800 mb-6">Recipe Details</h2>
                    <img
                      src={getRecipeImageUrl(selectedRecipe)}
                      alt={selectedRecipe.name}
                      className="w-full h-72 object-cover rounded-md shadow-md mb-6"
                    />
                    <h3 className="text-2xl font-semibold text-gray-700 mb-3">
                      {selectedRecipe.name}
                    </h3>

                    <div className="mb-4">
                      <h4 className="flex items-center text-xl font-semibold text-gray-600 mb-2">
                        <FaListUl className="mr-2 text-indigo-500" /> Ingredients
                      </h4>
                      <ul className="list-disc pl-5 space-y-1 text-gray-700">
                        {selectedRecipe.ingredients.map((ingredient, index) => (
                          <li key={index}>{ingredient}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="mb-4">
                      <h4 className="flex items-center text-xl font-semibold text-gray-600 mb-2">
                        <FaListUl className="mr-2 text-indigo-500" /> Equipment
                      </h4>
                      <ul className="list-disc pl-5 space-y-1 text-gray-700">
                        {selectedRecipe.equipment.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    </div>


                    <div>
                      <h4 className="flex items-center text-xl font-semibold text-gray-600 mb-2">
                        <FaClipboardList className="mr-2 text-indigo-500 inline" /> Recipe Steps
                      </h4>
                      <p className="text-gray-700 mb-4 whitespace-pre-line">
                        {selectedRecipe.recipe[stepIndex]}
                      </p>
                      <div className="flex justify-between items-center">
                        <button
                          onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
                          disabled={stepIndex === 0}
                          className="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
                        >
                          Previous
                        </button>
                        <span className="text-sm text-gray-500">
                          Step {stepIndex + 1} of {selectedRecipe.recipe.length}
                        </span>
                        <button
                          onClick={() =>
                            setStepIndex((i) => Math.min(selectedRecipe.recipe.length - 1, i + 1))
                          }
                          disabled={stepIndex === selectedRecipe.recipe.length - 1}
                          className="px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 disabled:opacity-50"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-500">Select a recipe to see details.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        {loading && <p className="text-center text-gray-600 py-8">Loading recipes...</p>}
      </main>
      <Footer />
    </div>
  );
}


export default App;
