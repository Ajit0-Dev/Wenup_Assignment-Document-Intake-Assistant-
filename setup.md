# Document Intake Assistant — Setup Guide

This guide provides the exact steps needed to get the project running flawlessly from a fresh clone.

## 1. Prerequisites
- **Node.js** (v18 or higher) for the React frontend
- **Python** (v3.10 or higher) for the FastAPI backend
- (Optional but recommended) A free API key from Google AI Studio (Gemini)

---

## 2. Backend Setup

The backend handles all business logic, validation, state management, and LLM communication.

1. **Open a terminal** and navigate to the backend directory:
   ```bash
   cd Wneup/backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:** `.\venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`

4. **Install the required Python packages:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure your environment variables:**
   - Copy the example `.env` file:
     - **Windows/macOS/Linux:** `cp .env.example .env` (or duplicate it manually in your editor)
   - Open `.env` and verify the settings. It should look like this:
     ```ini
     LLM_PROVIDER=gemini
     GEMINI_API_KEY=your-api-key-here
     GEMINI_MODEL=gemini-3.5-flash-lite
     ```
   - *Note: If you do not have an API key, you can change `LLM_PROVIDER=mock` to run the app using local test logic instead of a real LLM.*

6. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend will now be running at http://localhost:8000*

---

## 3. Frontend Setup

The frontend provides the user interface (built with React + Vite + TypeScript).

1. **Open a new terminal window** (leave the backend terminal running).
2. **Navigate to the frontend directory:**
   ```bash
   cd Wneup/frontend
   ```

3. **Install the Node dependencies:**
   ```bash
   npm install
   ```

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```
   *The frontend will now be running at http://localhost:5173*

---

## 4. How to Use

1. Open your browser and navigate to **http://localhost:5173**.
2. The application will automatically create a session and the assistant will greet you.
3. Start chatting! The assistant will guide you through the required questions.
4. Watch the **Information** panel on the right update live as you speak.
5. Click on the **Document Preview** tab to see your final generated legal document.

---

## 5. Running Tests

To verify that the application is perfectly stable, run the automated test suites:

**Backend Tests (39 tests):**
```bash
cd backend
# Make sure your virtual environment is active!
pytest -v
```

**Frontend Tests (3 tests):**
```bash
cd frontend
npm test
```
