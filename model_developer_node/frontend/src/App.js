import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [files, setFiles] = useState({
    config: null,
    model: null,
    tokenizer_config: null,
    vocab: null,
    merges: null
  });
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [evaluationId, setEvaluationId] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event, fileType) => {
    setFiles({
      ...files,
      [fileType]: event.target.files[0]
    });
  };

  const handleUpload = async () => {
    const formData = new FormData();
    Object.entries(files).forEach(([key, file]) => {
      if (file) {
        formData.append(key, file);
      }
    });

    try {
      const response = await axios.post('http://localhost:5000/upload_model', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setUploadedFiles(response.data.uploaded_files);
      setError(null);
    } catch (error) {
      setError('Error uploading model: ' + error.response?.data?.error || error.message);
    }
  };

  const initiateEvaluation = async () => {
    try {
      const response = await axios.post('http://localhost:5000/initiate_evaluation', {
        model_files: uploadedFiles
      });
      setEvaluationId(response.data.evaluation_id);
      setError(null);
    } catch (error) {
      setError('Error initiating evaluation: ' + error.response?.data?.error || error.message);
    }
  };

  const getResults = async () => {
    try {
      const response = await axios.get(`http://localhost:5000/get_results/${evaluationId}`);
      setResults(response.data);
      setError(null);
    } catch (error) {
      setError('Error fetching results: ' + error.response?.data?.error || error.message);
    }
  };

  return (
    <div className="App">
      <h1>Gatortron Model Developer Node</h1>
      <div>
        <h2>Upload Model Files</h2>
        <input type="file" onChange={(e) => handleFileChange(e, 'config')} accept=".json" />
        <label>Config File</label>
        <br />
        <input type="file" onChange={(e) => handleFileChange(e, 'model')} accept=".bin" />
        <label>Model File</label>
        <br />
        <input type="file" onChange={(e) => handleFileChange(e, 'tokenizer_config')} accept=".json" />
        <label>Tokenizer Config File</label>
        <br />
        <input type="file" onChange={(e) => handleFileChange(e, 'vocab')} accept=".json" />
        <label>Vocab File</label>
        <br />
        <input type="file" onChange={(e) => handleFileChange(e, 'merges')} accept=".txt" />
        <label>Merges File</label>
        <br />
        <button onClick={handleUpload}>Upload Model Files</button>
      </div>
      {uploadedFiles.length > 0 && (
        <div>
          <h3>Uploaded Files:</h3>
          <ul>
            {uploadedFiles.map((file, index) => (
              <li key={index}>{file}</li>
            ))}
          </ul>
        </div>
      )}
      <button onClick={initiateEvaluation} disabled={uploadedFiles.length === 0}>Initiate Evaluation</button>
      {evaluationId && <p>Evaluation ID: {evaluationId}</p>}
      <button onClick={getResults} disabled={!evaluationId}>Get Results</button>
      {error && <p style={{color: 'red'}}>{error}</p>}
      {results && (
        <div>
          <h2>Evaluation Results</h2>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;