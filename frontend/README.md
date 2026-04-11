# Legal Document QA — React Frontend

A modern React + TypeScript frontend for the Legal Document QA system, built with Vite and TailwindCSS.

## Features

- **Document Upload**: Drag-and-drop interface for PDF, DOCX, and TXT files
- **Intelligent Query**: Semantic search with auto-complete suggestions
- **Bilingual Answers**: Toggle between English and Hindi responses
- **Source Citations**: Expandable source cards with document names and snippets
- **Document Management**: List and delete ingested documents
- **Settings Panel**: Configure language, retrieved chunks, Ollama model, and index
- **Dark Mode**: One-click theme toggle persisted in localStorage
- **Responsive Design**: Optimised for mobile, tablet, and desktop

## Prerequisites

- Node.js 18+
- npm 9+
- The FastAPI backend running (see root `README.md`)

## Quick Start

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Copy environment template
cp .env.example .env

# 4. Start the development server
npm run dev
```

Open http://localhost:5173

The Vite dev server proxies `/api/*` requests to `http://localhost:8000` automatically.

## Running the Backend

From the repository root:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn api.main:app --reload
```

The API will be available at http://localhost:8000.  
Interactive docs: http://localhost:8000/docs

## Build for Production

```bash
npm run build        # outputs to frontend/dist/
npm run preview      # preview the production build locally
```

## Docker

Use the root `docker-compose.yml` to start everything together:

```bash
docker compose up --build
```

| Service   | URL                     |
|-----------|-------------------------|
| Frontend  | http://localhost:3000   |
| API       | http://localhost:8000   |
| Endee DB  | http://localhost:8080   |

## Project Structure

```
frontend/
├── public/
│   └── images/
│       └── legal-doc-icon.svg
├── src/
│   ├── components/
│   │   ├── Header.tsx            Navigation with theme toggle
│   │   ├── DocumentUpload.tsx    Drag-drop uploader with progress
│   │   ├── QueryInterface.tsx    Search bar with auto-complete
│   │   ├── ResultsDisplay.tsx    Chat-style answer display
│   │   ├── DocumentList.tsx      List of ingested documents
│   │   └── SettingsPanel.tsx     Language & model settings
│   ├── pages/
│   │   ├── Home.tsx              Hero + feature overview
│   │   ├── Dashboard.tsx         Main workspace (upload + query)
│   │   └── Documents.tsx         Document management page
│   ├── services/
│   │   └── api.ts                Typed API client
│   ├── hooks/
│   │   ├── useDocuments.ts       Document operations
│   │   ├── useQuery.ts           Query + suggestions
│   │   └── usePreferences.ts     Theme & language preferences
│   ├── context/
│   │   └── AppContext.tsx        Global state (React Context)
│   ├── types/
│   │   └── index.ts              Shared TypeScript types
│   ├── styles/
│   │   ├── globals.css           Tailwind base + component classes
│   │   └── variables.css         CSS custom properties
│   ├── App.tsx
│   └── main.tsx
├── .env.example
├── Dockerfile
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

## Environment Variables

| Variable              | Default                      | Description                    |
|-----------------------|------------------------------|--------------------------------|
| `VITE_API_BASE_URL`   | *(empty — uses Vite proxy)*  | Full API URL in production     |
| `VITE_OLLAMA_MODEL`   | `mistral`                    | Default LLM model name         |
| `VITE_OLLAMA_URL`     | `http://localhost:11434`     | Ollama server URL              |
| `VITE_INDEX_NAME`     | `legal_docs`                 | Default Endee index            |
