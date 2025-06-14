import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import {WorkbookProvider} from "./ExcelViewer/WorkbookContext.tsx";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WorkbookProvider>
      <App />
    </WorkbookProvider>
  </StrictMode>
)
