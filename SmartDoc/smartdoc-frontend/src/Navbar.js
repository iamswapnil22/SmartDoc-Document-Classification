import React from 'react';
import './Navbar.css';
import webLogo from './docs.png';
function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
        <img src={webLogo} alt='file logo' className='web-logo'></img>
        SmartDoc
        </div>
        <ul className="navbar-menu">
          <li className="navbar-item">
            <a href="#home" className="navbar-link">Home</a>
          </li>
          <li className="navbar-item">
            <a href="#upload" className="navbar-link">Upload</a>
          </li>
          <li className="navbar-item">
            <a href="#features" className="navbar-link">Features</a>
          </li>
          <li className="navbar-item">
            <a href="#contact" className="navbar-link">Contact</a>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
