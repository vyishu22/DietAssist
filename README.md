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

