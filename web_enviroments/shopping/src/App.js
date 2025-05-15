import React, { useState, useEffect } from "react";
import {
  FaSearch,
  FaMapMarkerAlt,
  FaStar,
  FaStarHalfAlt,
  FaRegStar,
  FaShoppingCart,
  FaTimes
} from "react-icons/fa";
import "./App.css";

const home_url = 'http://98.80.38.242:1220/';

const stores = [
  { id: 1, name: "Target", location: "Uptown", lat: 40.752179, lon: -73.991226 },
  { id: 2, name: "Whole Foods", location: "Centertown", lat: 40.735892, lon: -73.993567 },
  { id: 3, name: "Costco", location: "Downtown", lat: 40.7951238, lon: -73.9306786 },
  { id: 4, name: "CVS", location: "Midtown", lat: 40.731866, lon: -73.982422 },
];

const products = [
  {
    id: 18,
    name: "Bacon",
    description: "Crispy bacon perfect for breakfast or adding flavor to any dish.",
    image:
      "https://plus.unsplash.com/premium_photo-1725899528811-7c893698d113?q=80&w=2938&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 5.09 },
      { storeId: 2, price: 6.19 },
      { storeId: 3, price: 6.89 },
      { storeId: 4, price: 5.99 },
    ],
    rating: 4.5,
    colors: [],
    sizes: ["100g", "200g", "500g"]
  },
  {
    id: 19,
    name: "Cheese",
    description: "A selection of fine cheeses to enhance your meals.",
    image:
      "https://images.unsplash.com/photo-1552767059-ce182ead6c1b?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 4.99 },
      { storeId: 2, price: 4.19 },
      { storeId: 3, price: 4.89 },
      { storeId: 4, price: 4.99 },
    ],
    rating: 4.6,
    colors: [],
    sizes: ["200g", "500g", "1kg"]
  },
  {
    id: 20,
    name: "Butter",
    description: "Creamy butter made from fresh cream.",
    image:
      "https://images.unsplash.com/photo-1603596310923-dbb12732f9c7?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 3.49 },
      { storeId: 2, price: 3.19 },
      { storeId: 3, price: 3.09 },
      { storeId: 4, price: 3.49 },
    ],
    rating: 4.5,
    colors: [],
    sizes: ["250g", "500g", "1kg"]
  },
  {
    id: 21,
    name: "Peanut Butter",
    description: "Creamy peanut butter perfect for spreads and recipes.",
    image:
      "https://images.unsplash.com/photo-1624684244440-1130c3b65783?q=80&w=3085&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 2.99 },
      { storeId: 2, price: 3.09 },
      { storeId: 3, price: 2.89 },
      { storeId: 4, price: 2.19 },
    ],
    rating: 4.7,
    colors: [],
    sizes: ["200g", "500g", "1kg"]
  },
  {
    id: 22,
    name: "Chicken",
    description: "Fresh whole chicken, perfect for a family meal.",
    image:
      "https://images.unsplash.com/photo-1629966207968-16b1027bed09?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 7.79 },
      { storeId: 2, price: 8.09 },
      { storeId: 3, price: 7.89 },
      { storeId: 4, price: 7.99 },
    ],
    rating: 4.4,
    colors: [],
    sizes: ["Whole", "Half"]
  },
  {
    id: 23,
    name: "Avocado",
    description: "Creamy and delicious avocado, perfect for salads and toast.",
    image:
      "https://images.unsplash.com/photo-1671624749229-7d37826013b5?q=80&w=3135&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 1.49 },
      { storeId: 2, price: 1.29 },
      { storeId: 3, price: 1.39 },
      { storeId: 4, price: 1.49 },
    ],
    rating: 4.5,
    colors: [],
    sizes: ["Each", "Pack of 2"]
  },
  {
    id: 24,
    name: "Chicken Breast",
    description: "Boneless chicken breast, lean and perfect for healthy meals.",
    image:
      "https://images.unsplash.com/photo-1604503468506-a8da13d82791?q=80&w=3087&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 4.99 },
      { storeId: 2, price: 5.09 },
      { storeId: 3, price: 4.89 },
      { storeId: 4, price: 4.99 },
    ],
    rating: 4.6,
    colors: [],
    sizes: ["Per piece", "Pack of 4"]
  },
  {
    id: 13,
    name: "Tomatoes",
    description: "Fresh, ripe tomatoes perfect for salads and cooking.",
    image:
      "https://images.unsplash.com/photo-1561136594-7f68413baa99?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 2.99 },
      { storeId: 2, price: 3.19 },
      { storeId: 3, price: 2.89 },
      { storeId: 4, price: 2.79 },
    ],
    rating: 4.5,
    colors: [],
    sizes: ["1 lb", "2 lb", "5 lb"]
  },
  {
    id: 14,
    name: "Basil",
    description: "Fresh basil leaves to enhance your favorite dishes.",
    image:
      "https://images.unsplash.com/photo-1610970884954-4d376ecba53f?q=80&w=3018&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 1.79 },
      { storeId: 2, price: 2.09 },
      { storeId: 3, price: 1.89 },
      { storeId: 4, price: 1.99 },
    ],
    rating: 4.7,
    colors: [],
    sizes: ["Bunch", "Pack"]
  },
  {
    id: 15,
    name: "Olive Oil",
    description: "Extra virgin olive oil for a rich, authentic flavor.",
    image:
      "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?q=80&w=2848&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 9.99 },
      { storeId: 2, price: 8.99 },
      { storeId: 3, price: 9.49 },
      { storeId: 4, price: 9.99 },
    ],
    rating: 4.8,
    colors: [],
    sizes: ["250 ml", "500 ml", "1 L"]
  },
  {
    id: 16,
    name: "Garlic",
    description: "Fresh garlic bulbs for robust flavor and health benefits.",
    image:
      "https://images.unsplash.com/photo-1540148426945-6cf22a6b2383?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 1.49 },
      { storeId: 2, price: 1.59 },
      { storeId: 3, price: 1.39 },
      { storeId: 4, price: 1.49 },
    ],
    rating: 4.6,
    colors: [],
    sizes: ["Per bulb", "Pack of 3"]
  },
  {
    id: 17,
    name: "Lemons",
    description: "Juicy lemons for cooking, baking, and refreshing drinks.",
    image:
      "https://images.unsplash.com/photo-1528632735386-3bb3ead106f3?q=80&w=3174&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 0.99 },
      { storeId: 2, price: 1.09 },
      { storeId: 3, price: 0.89 },
      { storeId: 4, price: 0.85 },
    ],
    rating: 4.4,
    colors: [],
    sizes: ["Per lemon", "Pack of 6"]
  },
  {
    id: 1,
    name: "Sofa",
    description: "Comfortable sofa with pink cushions.",
    image:
      "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 93.99 },
      { storeId: 2, price: 104.99 },
      { storeId: 3, price: 98.99 },
      { storeId: 4, price: 95.99 },
    ],
    rating: 4.5,
    colors: ["Pink", "Grey", "Blue"],
    sizes: ["Small", "Medium", "Large"]
  },
  {
    id: 2,
    name: "Computer",
    description: "High-performance computer for coding.",
    image:
      "https://images.unsplash.com/photo-1498050108023-c5249f4df085?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 199.99 },
      { storeId: 2, price: 201.99 },
      { storeId: 3, price: 205.99 },
      { storeId: 4, price: 202.99 },
    ],
    rating: 4.0,
    colors: ["Black", "Silver"],
    sizes: ["One Size"]
  },
  {
    id: 3,
    name: "Headphones",
    description: "Noise-cancelling over-ear headphones.",
    image:
      "https://images.unsplash.com/photo-1511376777868-611b54f68947?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 59.99 },
      { storeId: 2, price: 64.99 },
      { storeId: 3, price: 55.99 },
      { storeId: 4, price: 60.99 },
    ],
    rating: 4.7,
    colors: ["Black", "White", "Red"],
    sizes: ["Standard"]
  },
  {
    id: 4,
    name: "Laptop",
    description: "High performance laptop for work and play.",
    image:
      "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 899.99 },
      { storeId: 2, price: 919.99 },
      { storeId: 3, price: 905.99 },
      { storeId: 4, price: 889.99 },
    ],
    rating: 4.6,
    colors: ["Silver", "Space Gray", "Gold"],
    sizes: ["13-inch", "15-inch", "17-inch"]
  },
  {
    id: 5,
    name: "Tablet",
    description: "Portable tablet for entertainment and productivity.",
    image:
      "https://images.unsplash.com/photo-1623126908029-58cb08a2b272?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 299.99 },
      { storeId: 2, price: 319.99 },
      { storeId: 3, price: 310.99 },
      { storeId: 4, price: 305.99 },
    ],
    rating: 4.3,
    colors: ["Black", "White", "Rose Gold"],
    sizes: ["8-inch", "10-inch", "12-inch"]
  },
  {
    id: 6,
    name: "Camera",
    description: "High-resolution DSLR camera for professional photography.",
    image:
      "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 499.99 },
      { storeId: 2, price: 500.99 },
      { storeId: 3, price: 510.99 },
      { storeId: 4, price: 505.99 },
    ],
    rating: 4.8,
    colors: ["Black", "Silver"],
    sizes: ["Body Only", "With Kit Lens"]
  },
  {
    id: 7,
    name: "Watch",
    description: "Smart watch with health tracking and notifications.",
    image:
      "https://images.unsplash.com/photo-1434056886845-dac89ffe9b56?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 199.99 },
      { storeId: 2, price: 209.99 },
      { storeId: 3, price: 201.99 },
      { storeId: 4, price: 202.99 },
    ],
    rating: 4.2,
    colors: ["Black", "Silver", "Gold"],
    sizes: ["Small", "Medium", "Large"]
  },
  {
    id: 8,
    name: "Backpack",
    description: "Durable backpack perfect for travel and daily use.",
    image:
      "https://images.unsplash.com/photo-1577733975197-3b950ca5cabe?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 49.99 },
      { storeId: 2, price: 54.99 },
      { storeId: 3, price: 52.99 },
      { storeId: 4, price: 47.99 },
    ],
    rating: 4.4,
    colors: ["Blue", "Black", "Green"],
    sizes: ["Standard"]
  },
  {
    id: 9,
    name: "Pizza",
    description: "Delicious cheese pizza with fresh ingredients.",
    image:
      "https://images.unsplash.com/photo-1588315029754-2dd089d39a1a?q=80&w=2942&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 10.99 },
      { storeId: 2, price: 13.99 },
      { storeId: 3, price: 11.99 },
      { storeId: 4, price: 12.49 },
    ],
    rating: 4.6,
    colors: [],
    sizes: ["Personal", "Medium", "Large"]
  },
  {
    id: 10,
    name: "Burger",
    description: "Juicy burger with fresh lettuce and tomato.",
    image:
      "https://images.unsplash.com/photo-1550547660-d9450f859349?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 8.99 },
      { storeId: 2, price: 7.99 },
      { storeId: 3, price: 8.49 },
      { storeId: 4, price: 8.99 },
    ],
    rating: 4.4,
    colors: [],
    sizes: ["Single", "Double"]
  },
  {
    id: 11,
    name: "Salad",
    description: "Fresh garden salad with a variety of vegetables.",
    image:
      "https://images.unsplash.com/photo-1551248429-40975aa4de74?q=80&w=3090&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    prices: [
      { storeId: 1, price: 6.99 },
      { storeId: 2, price: 7.49 },
      { storeId: 3, price: 6.19 },
      { storeId: 4, price: 7.29 },
    ],
    rating: 4.3,
    colors: [],
    sizes: ["Small", "Large"]
  },
  {
    id: 12,
    name: "Sushi Platter",
    description: "Assorted sushi platter with fresh fish and rice.",
    image:
      "https://images.unsplash.com/photo-1553621042-f6e147245754?ixlib=rb-1.2.1&auto=format&fit=crop&w=600&q=80",
    prices: [
      { storeId: 1, price: 15.99 },
      { storeId: 2, price: 16.99 },
      { storeId: 3, price: 15.49 },
      { storeId: 4, price: 14.99 },
    ],
    rating: 4.7,
    colors: [],
    sizes: ["8 pcs", "12 pcs", "16 pcs"]
  },
];


function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth's radius in km
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) *
    Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) *
    Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  return distance.toFixed(2);
}

function renderRating(rating) {
  const stars = [];
  const fullStars = Math.floor(rating);
  const halfStar = rating - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
  for (let i = 0; i < fullStars; i++) {
    stars.push(<FaStar key={`full-${i}`} className="star" />);
  }
  if (halfStar) {
    stars.push(<FaStarHalfAlt key="half" className="star" />);
  }
  for (let i = 0; i < emptyStars; i++) {
    stars.push(<FaRegStar key={`empty-${i}`} className="star" />);
  }
  return stars;
}


// Helper to get initial state from URL
const getInitialStateFromURL = () => {
  const params = new URLSearchParams(window.location.search);
  const storeIdParam = params.get('storeId');
  const searchParam = params.get('search');
  const productIdParam = params.get('product');
  const sizeParam = params.get('size'); // <-- New
  const qtyParam = params.get('qty');   // <-- New
  const cartParam = params.get('cart');

  let initialStore = stores[0];
  if (storeIdParam) {
    const foundStore = stores.find(s => s.id === parseInt(storeIdParam, 10));
    if (foundStore) initialStore = foundStore;
  }

  let initialProduct = null;
  let initialShowPurchaseModal = false;
  let initialModalSize = null; // <-- New
  let initialModalQty = 1;    // <-- New

  if (productIdParam) {
    const foundProduct = products.find(p => p.id === parseInt(productIdParam, 10));
    if (foundProduct) {
      initialProduct = foundProduct;
      initialShowPurchaseModal = true;

      // Validate and set initial size from URL if product has sizes
      if (sizeParam && foundProduct.sizes && foundProduct.sizes.includes(sizeParam)) {
        initialModalSize = sizeParam;
      } else if (foundProduct.sizes && foundProduct.sizes.length > 0) {
        // Default to first size if not specified or invalid in URL
        initialModalSize = foundProduct.sizes[0];
      }

      // Validate and set initial quantity from URL
      const qty = parseInt(qtyParam, 10);
      if (!isNaN(qty) && qty > 0) {
        initialModalQty = qty;
      }
    }
  }

  let initialShowCartModal = cartParam === 'open';
  if (initialShowPurchaseModal && initialShowCartModal) {
    initialShowCartModal = false;
  }


  return {
    store: initialStore,
    search: searchParam || "",
    product: initialProduct,
    showPurchase: initialShowPurchaseModal,
    showCart: initialShowCartModal,
    modalSize: initialModalSize,
    modalQty: initialModalQty
  };
};


function App() {
  const initialState = getInitialStateFromURL();
  const [currentStore, setCurrentStore] = useState(initialState.store);
  const [searchTerm, setSearchTerm] = useState(initialState.search);
  const [cartItems, setCartItems] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(initialState.product);
  const [showPurchaseModal, setShowPurchaseModal] = useState(initialState.showPurchase);
  const [showCartModal, setShowCartModal] = useState(initialState.showCart);

  const [modalSelectedSize, setModalSelectedSize] = useState(initialState.modalSize);
  const [modalQuantity, setModalQuantity] = useState(initialState.modalQty);
  // --- End lifted state ---


  // Effect to update URL when state changes
  useEffect(() => {
    const params = new URLSearchParams();

    if (currentStore && currentStore.id !== stores[0].id) {
      params.set('storeId', currentStore.id);
    }
    if (searchTerm) {
      params.set('search', searchTerm);
    }

    // --- Include modal selections in URL ---
    if (showPurchaseModal && selectedProduct) {
      params.set('product', selectedProduct.id);
      // Add size only if it's relevant and selected
      if (modalSelectedSize && selectedProduct.sizes && selectedProduct.sizes.length > 0) {
        params.set('size', modalSelectedSize);
      }
      // Add quantity if it's more than 1
      if (modalQuantity > 1) {
        params.set('qty', modalQuantity);
      }
    }
    // --- End modal selections ---
    else if (showCartModal) {
      params.set('cart', 'open');
    }

    const queryString = params.toString();
    const newUrl = queryString
      ? `${window.location.pathname}?${queryString}`
      : window.location.pathname;

    if (newUrl !== `${window.location.pathname}${window.location.search}`) {
      window.history.pushState({ path: newUrl }, '', newUrl);
    }
  }, [ // <-- Add modal size and quantity to dependencies
    currentStore,
    searchTerm,
    selectedProduct,
    showPurchaseModal,
    showCartModal,
    modalSelectedSize,
    modalQuantity
  ]);


  const handleStoreChange = (event) => {
    const selectedStore = stores.find(
      (store) => store.id === parseInt(event.target.value, 10)
    );
    setCurrentStore(selectedStore);
  };

  const filteredProducts = products.filter((product) =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // --- Updated modal handlers ---
  const openPurchaseModal = (product) => {
    setSelectedProduct(product);
    // Reset size/qty for the *newly selected* product
    setModalSelectedSize(product.sizes && product.sizes.length > 0 ? product.sizes[0] : null);
    setModalQuantity(1);
    setShowPurchaseModal(true);
    setShowCartModal(false);
  };

  const closePurchaseModal = () => {
    setSelectedProduct(null);
    setShowPurchaseModal(false);
    // Optionally reset size/qty here too, though opening resets anyway
    // setModalSelectedSize(null);
    // setModalQuantity(1);
  };

  const openCartModal = () => {
    setShowCartModal(true);
    setShowPurchaseModal(false);
    setSelectedProduct(null);
  }

  const closeCartModal = () => {
    setShowCartModal(false);
  }
  // --- End updated modal handlers ---

  const addToCart = (item) => {
    // Item now includes size/qty managed by App state
    setCartItems((prev) => [...prev, item]);
    closePurchaseModal();
  };

  const removeCartItem = (index) => {
    setCartItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleCheckout = () => {
    alert("Checkout successful!");
    setCartItems([]);
    closeCartModal();
  };

  return (
    <div className="App">
      {/* --- Header, Main, Footer structure remains the same --- */}
      <header className="header">
        <div className="header-left">
          <a
            href={home_url}
            style={{
              textDecoration: "none",
              color: "white",
              margin: "0 1rem",
              display: "flex",
              alignItems: "center",
            }}
          >
            <h3 style={{ color: "white", margin: "0", border: "2px solid white", padding: "0.5rem", borderRadius: "5px" }}>🏠 Home </h3>
          </a>
          <div className="logo">
            <h1>Shop</h1>
          </div>
          <div className="location-selector">
            <FaMapMarkerAlt className="location-icon" color="#333" />
            <select onChange={handleStoreChange} value={currentStore ? currentStore.id : ''}>
              {stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name} - {store.location}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="header-center">
          <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
        </div>
        <div className="header-right">
          <div
            className="cart-icon"
            onClick={openCartModal}
            style={{ cursor: "pointer" }}
          >
            <FaShoppingCart className="shopping-cart" />
            {cartItems.length > 0 && (
              <span className="cart-count">{cartItems.length}</span>
            )}
          </div>
        </div>
      </header>
      <main>
        <div className="product-list">
          {filteredProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              currentStore={currentStore}
              openPurchaseModal={openPurchaseModal}
            />
          ))}
        </div>
      </main>
      <footer className="footer">
        <p>© 2025 Shop.</p>
      </footer>

      {/* --- Pass lifted state down to PurchaseModal --- */}
      {showPurchaseModal && selectedProduct && (
        <Modal onClose={closePurchaseModal}>
          <PurchaseModal
            product={selectedProduct}
            currentStore={currentStore}
            addToCart={addToCart}
            closeModal={closePurchaseModal}
            // Pass state and setters for size/quantity
            modalSelectedSize={modalSelectedSize}
            setModalSelectedSize={setModalSelectedSize}
            modalQuantity={modalQuantity}
            setModalQuantity={setModalQuantity}
          />
        </Modal>
      )}
      {/* --- End Pass lifted state --- */}
      {showCartModal && (
        <Modal onClose={closeCartModal}>
          <CartModal
            cartItems={cartItems}
            removeCartItem={removeCartItem}
            handleCheckout={handleCheckout}
            closeModal={closeCartModal}
          />
        </Modal>
      )}
    </div>
  );
}

// --- SearchBar component remains the same ---
function SearchBar({ searchTerm, setSearchTerm }) {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search products..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button>
        <FaSearch />
      </button>
    </div>
  );
}


// --- ProductCard component remains the same ---
function ProductCard({ product, currentStore, openPurchaseModal }) {
  const currentPriceObj = product.prices.find(
    (price) => price.storeId === currentStore.id
  );
  const nearbyPrices = product.prices.filter(
    (price) => price.storeId !== currentStore.id
  );

  return (
    <div className="product-card">
      <img src={product.image} alt={product.name} className="product-img" />
      <div className="product-details">
        <h2 className="product-name">{product.name}</h2>
        <div className="rating">{renderRating(product.rating)}</div>
        <p className="product-description">{product.description}</p>
        <div className="specs">
          {product.colors && product.colors.length > 0 && (
            <div className="colors">
              <strong>Colors:</strong> {product.colors.join(", ")}
            </div>
          )}
          {product.sizes && product.sizes.length > 0 && (
            <div className="sizes">
              <strong>Sizes:</strong> {product.sizes.join(", ")}
            </div>
          )}
        </div>
        <div className="pricing-info">
          {currentPriceObj && (
            <div className="price current-price">
              <span className="label">Price:</span>{" "}
              <span className="value">${currentPriceObj.price}</span>{" "}
            </div>
          )}
          {nearbyPrices.length > 0 && (
            <div className="nearby-prices">
              <h3>Nearby Stores:</h3>
              {nearbyPrices.map((price) => {
                const store = stores.find((s) => s.id === price.storeId);
                if (!store) return null;
                const distance = calculateDistance(
                  currentStore.lat,
                  currentStore.lon,
                  store.lat,
                  store.lon
                );
                return (
                  <div key={store.id} className="nearby-price">
                    <span className="store-name">{store.name}:</span>{" "}
                    <span className="store-price">${price.price}</span>{" "}
                    <span className="store-distance">({distance} km away)</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <button
          className="buy-now-btn"
          onClick={() => openPurchaseModal(product)}
        >
          Buy Now
        </button>
      </div>
    </div>
  );
}

// --- Modal component remains the same ---
function Modal({ children, onClose }) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <button className="close-btn" onClick={onClose}>
          <FaTimes />
        </button>
        {children}
      </div>
    </div>
  );
}


// --- PurchaseModal updated to use props for state ---
function PurchaseModal({
  product,
  currentStore,
  addToCart,
  closeModal, // Still needed if AddToCart doesn't close it
  // Receive lifted state and setters
  modalSelectedSize,
  setModalSelectedSize,
  modalQuantity,
  setModalQuantity
}) {
  const currentPriceObj = product.prices.find(
    (price) => price.storeId === currentStore.id
  );

  // No local state for size/quantity needed here anymore
  // const [selectedSize, setSelectedSize] = useState(...);
  // const [quantity, setQuantity] = useState(1);

  // Still need local state for color as it wasn't requested to be in URL
  const [selectedColor, setSelectedColor] = useState(product.colors && product.colors.length > 0 ? product.colors[0] : null);


  const handleAdd = () => {
    const cartItem = {
      productId: product.id,
      name: product.name,
      image: product.image,
      price: currentPriceObj ? currentPriceObj.price : 0,
      selectedColor, // Use local state for color
      selectedSize: modalSelectedSize, // Use prop state for size
      quantity: modalQuantity, // Use prop state for quantity
    };
    addToCart(cartItem); // This now calls App's function, which closes modal
  };

  return (
    <div className="modal-content">
      <img src={product.image} alt={product.name} className="modal-img" />
      <h2>{product.name}</h2>
      <p>{product.description}</p>
      {currentPriceObj && (
        <p>
          <strong>Price:</strong> ${currentPriceObj.price}
        </p>
      )}
      <div className="modal-options">
        {/* Color still uses local state */}
        {product.colors && product.colors.length > 0 && (
          <div className="option" style={{ margin: "1rem" }}>
            <label>Color:</label>
            <select
              value={selectedColor || ''}
              onChange={(e) => setSelectedColor(e.target.value)}
            >
              {product.colors.map((color, idx) => (
                <option key={idx} value={color}>{color}</option>
              ))}
            </select>
          </div>
        )}
        {/* Size uses props state */}
        {product.sizes && product.sizes.length > 0 && (
          <div className="option" style={{ margin: "1rem" }}>
            <label>Size:</label>
            <select
              // Use prop value and setter
              value={modalSelectedSize || ''}
              onChange={(e) => setModalSelectedSize(e.target.value)} // Call setter from props
            >
              {product.sizes.map((size, idx) => (
                <option key={idx} value={size}>{size}</option>
              ))}
            </select>
          </div>
        )}
        {/* Quantity uses props state */}
        <div className="option" style={{ margin: "1rem" }}>
          <label>Quantity:</label>
          <input
            type="number"
            min="1"
            // Use prop value and setter
            value={modalQuantity}
            onChange={(e) => setModalQuantity(parseInt(e.target.value, 10) || 1)} // Call setter from props
          />
        </div>
      </div>
      <button className="add-to-cart-btn" onClick={handleAdd}>
        Add to Cart
      </button>
    </div>
  );
}


// --- CartModal component remains the same ---
function CartModal({ cartItems, removeCartItem, handleCheckout, closeModal }) {
  // Ensure cart items display correctly based on potentially null size/color
  return (
    <div className="modal-content">
      <h2>Your Cart</h2>
      {cartItems.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <div className="cart-items">
          {cartItems.map((item, idx) => (
            <div key={idx} className="cart-item">
              <img src={item.image} alt={item.name} className="cart-item-img" />
              <div className="cart-item-details">
                <h3>{item.name}</h3>
                <p>
                  {item.selectedColor && <><strong>Color:</strong> {item.selectedColor} | </>}
                  {item.selectedSize && <><strong>Size:</strong> {item.selectedSize} | </>}
                  <strong>Quantity:</strong> {item.quantity}
                </p>
                <p>
                  <strong>Price:</strong> ${item.price.toFixed(2)} each {/* Added toFixed for currency */}
                </p>
              </div>
              <button className="remove-btn" onClick={() => removeCartItem(idx)} style={{ cursor: "pointer", marginLeft: "auto" }}>
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
      {cartItems.length > 0 && (
        <button className="checkout-btn" onClick={handleCheckout}>
          Checkout
        </button>
      )}
    </div>
  );
}


export default App;