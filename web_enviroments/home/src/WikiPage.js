import React from 'react';

function WikiPage() {
  const wikiLink = "http://98.80.38.242:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing";
  const home_url = 'http://98.80.38.242:1220/';
  
  return (
    <div>
      <header style={{
        backgroundColor: '#333',
        padding: '10px 20px',
        color: '#fff',
        textAlign: 'center'
      }}>

        <a href={home_url} style={{
          textDecoration: "none",
          color: "white",
          margin: "0 1rem",
          display: "flex",
          alignItems: "center",
        }}>
          <h3 style={{ color: "white", margin: "0", border: "2px solid white", padding: "0.5rem", borderRadius: "5px" }}>🏠 Home </h3>
        </a>
      
      </header>

      <main style={{ padding: '20px' }}>
        <iframe
          src={wikiLink}
          title="Wikipedia Content"
          style={{
            width: '100%',
            height: '80vh',
            border: 'none'
          }}
        />
      </main>
    </div>
  );
}

export default WikiPage;
