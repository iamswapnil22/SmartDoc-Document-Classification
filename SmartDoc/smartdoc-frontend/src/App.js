import React, { useState } from 'react';
import './App.css';
import Navbar from './Navbar';
import documentsLogo from './documents.png';

function App() {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [results, setResults] = useState([]);
  const [downloadLink, setDownloadLink] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    setFiles([...event.target.files]);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setFiles([...event.dataTransfer.files]);
  };

  const handleUpload = async () => {
    setLoading(true);
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
    } finally {
      setLoading(false);
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
          <div className="upload-box ">
            <input
              type="file"
              className="file-input"
              multiple
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <button className="upload-button" onClick={() => document.querySelector('.file-input').click()}>
            <img src={documentsLogo} alt='file logo' className='file-logo'></img>
              <p className='button-text'>CHOOSE FILES</p>
            </button>
            <p>or drop files here</p>
          </div>
          <div className="files-box">
            {files.length > 0 && (
              <ul>
                {files.map((file, index) => (
                  <li key={index}>{file.name}</li>
                ))}
              </ul>
            )}
          </div>
          <button className="upload-button upload" onClick={handleUpload} disabled={loading}>
            {loading ? 'UPLOADING...' : 'UPLOAD FILES'}
          </button>
          {loading && <div className="loading-bar"></div>}
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
            <a className="upload-button download" href={downloadLink}>
              DOWNLOAD 
            </a>
          )}
        </div>
        <div className="description">
          <p>
            With SmartDoc, you can upload your unsorted documents and have them sorted automatically using the power of artificial intelligence! Our tool analyzes the content of your PDFs, classifies them, and provides you with a zip folder containing your sorted documents.
          </p>
        </div>
        <div className="features" id="features">
          <Feature text="Upload multiple documents easily" />
          <Feature text="AI-powered classification for accurate sorting" />
          <Feature text="Secure file processing and quick results" />
        </div>
        <div className="additional-info">
          <InfoSection
            title="SmartDoc: Your AI Document Organizer"
            text="Say goodbye to the hassle of manually sorting documents. With SmartDoc, just upload your files and let our AI handle the rest, providing you with a neatly organized set of documents."
          />
          <InfoSection
            title="Cross-Platform Compatibility"
            text="Our tool is browser-based and works on any device, whether it's Mac, Windows, Linux, or mobile. Enjoy seamless document organization wherever you are."
          />
          <InfoSection
            title="Advanced Text Recognition"
            text="SmartDoc uses precise text recognition to understand and classify your documents, ensuring they are sorted into the correct categories."
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
