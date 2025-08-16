import React from 'react';

export default function SimpleTest() {
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <h1 style={{ color: '#333', marginBottom: '20px' }}>
        🎉 React is Working!
      </h1>
      
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        maxWidth: '500px',
        width: '100%'
      }}>
        <h2 style={{ color: '#4CAF50', marginTop: 0 }}>✅ Frontend Status</h2>
        <ul style={{ textAlign: 'left' }}>
          <li>✅ React is rendering</li>
          <li>✅ Vite dev server is working</li>
          <li>✅ Basic TypeScript compilation</li>
        </ul>
        
        <hr style={{ margin: '20px 0' }} />
        
        <div style={{ textAlign: 'center' }}>
          <a 
            href="/test" 
            style={{ 
              display: 'inline-block',
              backgroundColor: '#2196F3',
              color: 'white',
              padding: '10px 20px',
              textDecoration: 'none',
              borderRadius: '4px',
              margin: '0 10px'
            }}
          >
            🔧 Full Diagnostics
          </a>
          
          <a 
            href="/login" 
            style={{ 
              display: 'inline-block',
              backgroundColor: '#4CAF50',
              color: 'white',
              padding: '10px 20px',
              textDecoration: 'none',
              borderRadius: '4px',
              margin: '0 10px'
            }}
          >
            🔑 Try Login
          </a>
        </div>
        
        <p style={{ 
          marginTop: '20px', 
          fontSize: '14px', 
          color: '#666',
          textAlign: 'center'
        }}>
          If you can see this page, React is working correctly!
        </p>
      </div>
    </div>
  );
}
