import React, { useState } from 'react';
import './App.css';
import Navbar from './Navbar';

function App() {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);
  const [downloadLink, setDownloadLink] = useState('');

  const handleFileChange = (event) => {
    setFiles([...event.target.files]);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setFiles([...event.dataTransfer.files]);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload files');
      }

      const data = await response.json();
      setMessage(data.message);
      setResults(data.filter(item => item.class)); // Filter to show only classification results
      const downloadData = data.find(item => item.download_link);
      if (downloadData) {
        setDownloadLink(`http://localhost:5000${downloadData.download_link}`);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      setMessage('Failed to upload files');
    }
  };

  return (
    <div className="App" onDrop={handleDrop} onDragOver={(e) => e.preventDefault()}>
      <Navbar />
      <header className="App-header" id="home">
        <h1>SmartDoc - Document Classifier</h1>
      </header>
      <main>
        <div className="upload-container" id="upload">
          <div className="upload-box">
            <input
              type="file"
              className="file-input"
              multiple
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <button className="upload-button" onClick={() => document.querySelector('.file-input').click()}>
              CHOOSE FILES
            </button>
            <p>or drop files here</p>
          </div>
          <div>
            {files.length > 0 && (
              <ul>
                {files.map((file, index) => (
                  <li key={index}>{file.name}</li>
                ))}
              </ul>
            )}
          </div>
          <button className="upload-button" onClick={handleUpload}>
            UPLOAD FILES
          </button>
          {message && <div className="message">{message}</div>}
          {results.length > 0 && (
            <div className="results">
              <h2>Classification Results</h2>
              <ul>
                {results.map((result, index) => (
                  <li key={index}>{result.file} - {result.class}</li>
                ))}
              </ul>
            </div>
          )}
          {downloadLink && (
            <a href={downloadLink} className="download-button" download>
              DOWNLOAD SORTED DOCUMENTS
            </a>
          )}
        </div>
        <div className="description">
          <p>
            With AI PDF, you can utilize the powers of artificial intelligence to summarize PDFs for free! The
            interactive chat function lets you request specific information to be summarized and presented to you in a matter of seconds. AI PDF Summarizer lets you understand document contents without having to read through every page.
          </p>
        </div>
        <div className="features" id="features">
          <Feature text="Chat with a PDF for free, without sign-up" />
          <Feature text="TLS encryption for secure file processing" />
          <Feature text="An AI assistant for instant PDFs summaries" />
        </div>
        <div className="additional-info">
          <InfoSection
            title="A Free AI for All Things PDF"
            text="The future is now! Chat with your PDF files just as easily as you would with ChatGPT. Smallpdf's AI PDF is free to use without"
          />
          <InfoSection
            title="Works on Your Device"
            text="AI PDF is a browser-based tool. That means that you can use it to summarize PDFs on Mac, Windows, Linux, and mobile. You just"
          />
          <InfoSection
            title="Text Recognition for Your PDF Files"
            text="When you upload a file into AI PDF, our tool uses precise text recognition to give you a summary of its content. You can also ask"
          />
        </div>
      </main>
    </div>
  );
}

const Feature = ({ text }) => (
  <div className="feature">
    <span>✔</span>
    <p>{text}</p>
  </div>
);

const InfoSection = ({ title, text }) => (
  <div className="info-section">
    <h3>{title}</h3>
    <p>{text}</p>
  </div>
);

export default App;
