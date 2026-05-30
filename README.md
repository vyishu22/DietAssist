# DietAssist

## Overview

DietAssist is an AI-powered nutrition recommendation system that provides personalized meal, snack, and drink suggestions based on a user's health conditions, allergies, dietary preferences, and budget. The application uses Large Language Models (LLMs) and Machine Learning to generate safe, customized diet plans and continuously improve recommendations through user feedback.

## Features

* Personalized diet recommendations
* Health condition and allergy-based meal planning
* Budget-conscious food suggestions
* AI-generated nutrition tips
* User feedback and rating system
* Caretaker support and monitoring
* Recommendation history tracking

## Tech Stack

### Frontend

* React.js
* Tailwind CSS
* Axios

### Backend

* FastAPI (Python)
* MongoDB
* Pydantic

### AI/ML

* OpenRouter LLM Integration
* Machine Learning Personalizer (`personalizer.joblib`)
* Recommendation Ranking Engine

## Project Structure

```text
DietAssist/
│
├── frontend/
│   ├── src/
  ├── public/
  └── package.json
│
├── backend/
│   ├── app/
  │   ├── models/
  │   ├── services/
  │   ├── routes/
  │   └── database/
  └── requirements.txt
│
└── README.md
```

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd DietAssist
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
MONGODB_URL=your_mongodb_connection_string
DATABASE_NAME=dietassist
OPENROUTER_API_KEY=your_api_key
```

## How It Works

1. User enters health information and dietary preferences.
2. AI generates personalized meal recommendations.
3. ML model ranks recommendations based on user profile.
4. Safety rules validate the generated diet plan.
5. Recommendations are stored in MongoDB.
6. User feedback improves future recommendations.

## Future Enhancements

* Nutrition tracking dashboard
* BMI and calorie analysis
* Multi-language support
* Mobile application
* Advanced recommendation learning

## License

This project is developed for educational and research purposes.

# DietAssist - Healthcare Diet Recommendation System

A professional, full-stack web application that provides personalized diet recommendations based on individual health conditions, allergies, and food preferences.

## Features

### Patient Features
- **Secure Authentication**: User registration and login with password hashing
- **Health Profile Management**: Track health conditions including:
  - Diabetes (glucose levels in mg/dL)
  - Blood Pressure (mmHg)
  - Cholesterol (mg/dL)
  - BMI (Body Mass Index)
  - Food allergies and intolerances
  - Food preferences (vegetarian/non-vegetarian)

- **Personalized Recommendations**: Dynamic diet recommendations based on:
  - Morning (Breakfast), Afternoon (Lunch), and Evening (Dinner) meals
  - Drinks with health-based reasoning
  - Snacks with nutritional guidance
  - Health tips for lifestyle improvements

- **Health Alerts**: Professional medical guidance message when multiple health conditions exceed safe thresholds

- **Feedback System**: Rate and comment on recommendations to improve future suggestions

### Caretaker Features
- **Secure Caretaker Access**: Separate authentication system for doctors, nutritionists, parents, guardians, and others
- **Patient Data Access**: View patient health information and recommendations using patient ID
- **Read-Only Interface**: Professional interface for monitoring patient health

## Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: MongoDB
- **Authentication**: JWT with bcrypt password hashing
- **API**: RESTful APIs with CORS support

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations and responsive design
- **JavaScript**: Vanilla JS with Fetch API for frontend-backend integration
- **Icons**: Emoji-based icons for modern UI

## Project Structure

```
DietAssist_3/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app initialization
│   │   ├── models/
│   │   │   └── models.py            # Database models
│   │   ├── routes/
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── patient.py           # Patient data endpoints
│   │   │   ├── caretaker.py         # Caretaker endpoints
│   │   │   ├── recommendations.py   # Recommendation engine endpoints
│   │   │   └── feedback.py          # Feedback system endpoints
│   │   └── utils/
│   │       ├── auth_utils.py        # Authentication utilities
│   │       └── recommendations.py   # Recommendation engine
│   ├── run.py                       # Flask app entry point
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables
│
└── frontend/
    ├── index.html                   # Landing page
    ├── css/
    │   └── styles.css               # Global styles
    ├── js/
    │   ├── auth.js                  # Authentication logic
    │   ├── health-information.js    # Health form logic
    │   ├── recommendations.js       # Recommendations display logic
    │   └── caretaker-dashboard.js   # Caretaker dashboard logic
    └── pages/
        ├── health-information.html  # Health profile form
        ├── recommendations.html     # Recommendations display
        └── caretaker-dashboard.html # Caretaker interface
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB (running locally or cloud instance)
- Node.js or Python for local server

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
MONGO_URI=mongodb://localhost:27017/dietassist
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
PORT=5000
OPENROUTER_API_KEY=your_openrouter_key_here   # you can choose any valid key and update it as needed
```
- **Optional dataset seeding:**
  Alternatives are generated on‑demand via the OpenRouter API; the
  previous local dataset and seeding script have been deprecated.

  On the front end, food alternatives are now displayed **inline beneath the
  main recommendations** so patients always see them immediately (the old
  toggle panel remains available for drinks/snacks or manual review).

  On the front end, the alternatives section is automatically expanded when the
  recommendations page loads, so patients immediately see substitute options
  without having to click a toggle button. The collapse toggle remains available
  if they prefer to hide the list.
  ```
3. Run tests (pytest):

```bash
# From project root
cd backend
pytest -q
```

Note: Tests mock Gemini and authentication where appropriate, so they can be run locally without real API keys or database records.

## Continuous Integration (GitHub Actions)

A GitHub Actions workflow is included to run tests on push and pull requests. To enable it:

1. Add a repository secret named `OPENROUTER_API_KEY` with your OpenRouter API key (Settings → Secrets and variables → Actions → New repository secret).

2. The workflow runs `pytest` in the `backend` folder and uses the `OPENROUTER_API_KEY` from secrets during the job.

Workflow file: `.github/workflows/ci.yml`

### Rate limiting & retry behavior

- The `POST /api/recommendations/genai` endpoint is rate-limited on the server (default: 10 requests/hour per IP). If exceeded, the API returns `429 Too Many Requests` with a JSON body:

```json
{ "error": "Too many requests", "message": "You have reached the request limit. Please try again later." }
```

- The server also preserves `Retry-After` headers returned by the limiter, so clients can read when to retry.

### Sentry: Release & Environment

If you use Sentry for monitoring, provide the following environment variables in production:

- `SENTRY_DSN` — your Sentry project DSN
- `SENTRY_RELEASE` — (optional) release identifier for tracking (e.g. git tag)
- `SENTRY_ENV` — (optional) environment label (e.g. `staging`, `production`)

When configured, Sentry will automatically capture uncaught exceptions and include release and environment tags in events.

3. Run Flask server:
```bash
python run.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

1. Install a simple HTTP server (if needed):
```bash
# Using Python 3
python -m http.server 8000

# Or using Node.js
npx http-server
```

2. Open in browser:
- Navigate to `http://localhost:8000` (or appropriate port)
- The landing page will load automatically

## API Endpoints

### Authentication
- `POST /api/auth/patient/register` - Patient registration
- `POST /api/auth/patient/login` - Patient login
- `POST /api/auth/verify-token` - Token verification

### Patient Routes
- `GET /api/patient/health-information` - Get health data
- `POST /api/patient/health-information` - Save health data
- `GET /api/patient/profile` - Get patient profile

### Caretaker Routes
- `POST /api/caretaker/register` - Caretaker registration
- `POST /api/caretaker/login` - Caretaker login
- `GET /api/caretaker/patient/<patient_id>` - Get patient data
- `GET /api/caretaker/profile` - Get caretaker profile

### Recommendations
- `POST /api/recommendations/get` - Get personalized recommendations
- `GET /api/recommendations/for-patient/<patient_id>` - Get patient recommendations (caretaker)
- `POST /api/recommendations/genai` - Get server-side AI-powered recommendations (now served via OpenRouter)

## AI Integration (OpenRouter)

Server-side AI recommendations are now provided via OpenRouter. The endpoint `POST /api/recommendations/genai` delegates to the OpenRouter API and returns a validated, structured JSON object only (Food -> Morning/Afternoon/Evening, Drinks, Snacks, `alternativeMessage`, `healthyTipsForToday`, and optionally `doctorAlert`).

- Configure your API key in `backend/.env` as `OPENROUTER_API_KEY` (do NOT expose this key to the frontend).
- The server calls OpenRouter and returns a validated, structured JSON object only. The frontend fetches this endpoint with the user's JWT token; no keys are present on the client.

Installation notes:
- Ensure `requests` is installed via `pip install -r backend/requirements.txt` and add `OPENROUTER_API_KEY` to your `.env` before running the backend.

### Feedback
- `POST /api/feedback/submit` - Submit feedback
- `GET /api/feedback/history` - Get feedback history

## User Flow

### Patient Flow
1. **Landing Page**: Welcome with login/register options
2. **Registration/Login**: Create account or sign in
3. **Health Information**: Fill in health conditions, allergies, preferences
4. **Recommendations**: View personalized recommendations with collapsible sections
5. **Feedback**: Rate and comment on recommendations

### Caretaker Flow
1. **Landing Page**: Caretaker access button
2. **Registration/Login**: Sign up with role selection
3. **Dashboard**: Enter patient ID to view data
4. **Patient Data**: View read-only health information and recommendations

## Key Design Features

### Modern UI/UX
- Gradient backgrounds and smooth animations
- Card-based layout for content organization
- Responsive design for mobile and desktop
- Color-coded sections (green for primary, blue for accents)
- Hover effects and transitions for interactivity

### Security
- Password hashing with bcrypt
- JWT token-based authentication
- CORS configuration for API security
- Input validation on frontend and backend
- Read-only access for caretaker role

### Accessibility
- Semantic HTML structure
- Clear typography with proper font hierarchy
- Color contrast for readability
- Intuitive navigation
- Error messages and success confirmations

## Recommendation Engine

All diet suggestions are generated on‑demand by a generative AI model via the
OpenRouter API.  The server builds a prompt containing the patient’s health
values, allergies and preferences, then returns a structured JSON response
with breakfast/lunch/dinner/drinks/snacks, alternative messages and health
tips.

The code running in this repository no longer contains any handwritten rule
sets – previous local engine logic was removed and all calls are routed to the
LLM.  The AI output is validated, doctor alerts are injected for critical
values, and results are cached briefly for performance.

## Feedback System

Users can provide feedback that helps improve recommendations:
- Star rating (1-5) for recommendation quality
- Comment field for specific feedback
- Stored for future algorithm improvement
- Accessible feedback history

## Future Enhancements

- Machine learning for improved recommendations based on feedback
- Multi-language support
- Mobile app development
- Calendar-based meal planning
- Nutritionist collaboration features
- Advanced analytics and reporting
- Wearable device integration
- Email/SMS notifications
- Appointment booking system

## Error Handling

The application includes comprehensive error handling:
- Form validation on frontend and backend
- HTTP status codes for API responses
- User-friendly error messages
- Loading states and spinner animations
- Alert messages for critical conditions

## Browser Compatibility

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is designed for academic demonstration and healthcare use cases.

## Support

For issues or questions, please contact the development team.

---

**DietAssist** - Making Healthcare Diet Recommendations Simple and Personalized
>>>>>>> 1e7ea58 (Initial commit)
