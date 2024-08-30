import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [datasetConnected, setDatasetConnected] = useState(false);
  const [evaluationStatus, setEvaluationStatus] = useState('');
  const [evaluationId, setEvaluationId] = useState('');

  const connectDataset = async () => {
    try {
      // In a real application, you'd implement actual dataset connection logic here
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulating connection delay
      setDatasetConnected(true);
    } catch (error) {
      console.error('Error connecting dataset:', error);
    }
  };

  const checkEvaluationStatus = async () => {
    if (!evaluationId) {
      setEvaluationStatus('No evaluation in progress');
      return;
    }

    try {
      const response = await axios.get(`http://localhost:5002/evaluation_status/${evaluationId}`);
      setEvaluationStatus(response.data.status);
    } catch (error) {
      console.error('Error checking evaluation status:', error);
      setEvaluationStatus('Error checking status');
    }
  };

  useEffect(() => {
    const interval = setInterval(checkEvaluationStatus, 5000);
    return () => clearInterval(interval);
  }, [evaluationId]);

  return (
    <div className="App">
      <h1>Gatortron Data Owner Node</h1>
      <button onClick={connectDataset} disabled={datasetConnected}>Connect Dataset</button>
      {datasetConnected && <p>Dataset connected successfully</p>}
      <input 
        type="text" 
        value={evaluationId} 
        onChange={(e) => setEvaluationId(e.target.value)} 
        placeholder="Enter Evaluation ID"
      />
      <button onClick={checkEvaluationStatus}>Check Evaluation Status</button>
      {evaluationStatus && <p>Evaluation Status: {evaluationStatus}</p>}
    </div>
  );
}

export default App;