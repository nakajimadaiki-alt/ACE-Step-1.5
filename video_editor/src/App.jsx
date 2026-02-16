import React from 'react';
import Editor from './components/Editor';
import ExportRenderer from './components/ExportRenderer';
import './styles/global.css';

function App() {
  const path = window.location.pathname;

  if (path === '/export') {
    return <ExportRenderer />;
  }

  return (
    <div className="App">
      <Editor />
    </div>
  );
}

export default App;
