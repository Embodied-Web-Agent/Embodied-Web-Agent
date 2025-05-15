import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import WikiPage from './WikiPage';
import './App.css';

function Home() {
  const blockStyle = {
    width: '200px',
    height: '250px',
    border: '1px solid #ccc',
    borderRadius: '8px',
    margin: '20px',
    textDecoration: 'none',
    color: '#333',
    overflow: 'hidden',
    boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
    transition: 'transform 0.2s',
  };

  const blockHoverStyle = {
    transform: 'scale(1.05)',
  };

  const containerStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    background: '#f9f9f9',
  };

  const imageStyle = {
    width: '100%',
    height: '150px',
    objectFit: 'cover',
  };

  const [hoveredBlock, setHoveredBlock] = React.useState(null);

  return (
    <div style={containerStyle}>
      <a
        href="http://98.80.38.242:1206/"
        style={{
          ...blockStyle,
          ...(hoveredBlock === 'recipe' ? blockHoverStyle : {})
        }}
        onMouseEnter={() => setHoveredBlock('recipe')}
        onMouseLeave={() => setHoveredBlock(null)}
      >
        <img
          src="https://images.unsplash.com/photo-1542010589005-d1eacc3918f2?q=80&w=2984&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" 
          alt="Recipe Website"
          style={imageStyle}
        />
        <div style={{ padding: '10px', textAlign: 'center' }}>
          <h3>Recipe</h3>
        </div>
      </a>

      <a
        href="http://98.80.38.242:1207/"
        style={{
          ...blockStyle,
          ...(hoveredBlock === 'shopping' ? blockHoverStyle : {})
        }}
        onMouseEnter={() => setHoveredBlock('shopping')}
        onMouseLeave={() => setHoveredBlock(null)}
      >
        <img
          src="https://images.unsplash.com/photo-1472851294608-062f824d29cc?q=80&w=2304&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" 
          alt="Shopping Website"
          style={imageStyle}
        />
        <div style={{ padding: '10px', textAlign: 'center' }}>
          <h3>Shopping</h3>
        </div>
      </a>

      <a
        href="http://98.80.38.242:3000/#map=7/42.896/-76.481&layers=Y"
        style={{
          ...blockStyle,
          ...(hoveredBlock === 'map' ? blockHoverStyle : {})
        }}
        onMouseEnter={() => setHoveredBlock('map')}
        onMouseLeave={() => setHoveredBlock(null)}
      >
        <img
          src="https://plus.unsplash.com/premium_photo-1682310071124-33632135b2ee?q=80&w=1512&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" 
          alt="Street Map"
          style={imageStyle}
        />
        <div style={{ padding: '10px', textAlign: 'center' }}>
          <h3>Open Street Map</h3>
        </div>
      </a>

      <Link
        to="/wiki"
        style={{
          ...blockStyle,
          ...(hoveredBlock === 'wiki' ? blockHoverStyle : {})
        }}
        onMouseEnter={() => setHoveredBlock('wiki')}
        onMouseLeave={() => setHoveredBlock(null)}
      >
        <img
          src="https://images.unsplash.com/photo-1657256031790-e898b7b3f3eb?q=80&w=1548&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" 
          alt="Wikipedia"
          style={imageStyle}
        />
        <div style={{ padding: '10px', textAlign: 'center' }}>
          <h3>Wikipedia</h3>
        </div>
      </Link>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/wiki" element={<WikiPage />} />
      </Routes>
    </Router>
  );
}

export default App;
