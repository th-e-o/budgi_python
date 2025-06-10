import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import '@univerjs/design/lib/index.css';
import '@univerjs/ui/lib/index.css';
import UniverStreamlitComponent from "./UniverStreamlitComponent.tsx"


const root = ReactDOM.createRoot(document.getElementById('root')!)
root.render(
  <React.StrictMode>
    <UniverStreamlitComponent />
  </React.StrictMode>
)