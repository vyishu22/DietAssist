# DietAssist - Visual Architecture & User Flow Guide

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT SIDE (Browser)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Landing Page   │  │ Patient Portal   │  │  Caretaker   │  │
│  │   (index.html)   │  │   (Pages/*.html) │  │   Dashboard  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────┘  │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
│                    ┌────────────┴────────────┐                  │
│                    │   JavaScript Layer     │                  │
│                    │  (auth.js, *-page.js) │                  │
│                    │  LocalStorage + Fetch  │                  │
│                    └────────────┬────────────┘                  │
│                                 │                               │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │      HTTP Requests        │
                    │   (GET/POST + JWT Token)  │
                    └─────────────┬──────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────┐
│                    SERVER SIDE (Flask API)                      │
├─────────────────────────────────┼───────────────────────────────┤
│                                 │                               │
│              ┌──────────────────┴──────────────────┐            │
│              │      Flask App (run.py)            │            │
│              │  ├─ CORS Middleware               │            │
│              │  ├─ JWT Verification              │            │
│              │  └─ Error Handling                │            │
│              └──────────────────┬──────────────────┘            │
│                                 │                               │
│   ┌─────────────────────────────┼──────────────────────────┐   │
│   │                Route Handlers                         │   │
│   │                                                        │   │
│   │  ┌────────────────┐ ┌────────────────┐              │   │
│   │  │  auth.py       │ │  patient.py    │              │   │
│   │  │  - register    │ │  - health info │              │   │
│   │  │  - login       │ │  - profile     │              │   │
│   │  └────────────────┘ └────────────────┘              │   │
│   │                                                        │   │
│   │  ┌────────────────┐ ┌────────────────┐              │   │
│   │  │ caretaker.py   │ │recommendations │              │   │
│   │  │ - register     │ │ - get reco     │              │   │
│   │  │ - patient data │ │ - for patient  │              │   │
│   │  └────────────────┘ └────────────────┘              │   │
│   │                                                        │   │
│   │  ┌────────────────┐                                  │   │
│   │  │  feedback.py   │                                  │   │
│   │  │  - submit      │                                  │   │
│   │  │  - history     │                                  │   │
│   │  └────────────────┘                                  │   │
│   │                                                        │   │
│   └────────────────────────────┬─────────────────────────┘   │
│                                │                               │
│              ┌─────────────────┴─────────────────┐             │
│              │    Utility Layer                  │             │
│              │  ├─ auth_utils.py (hash, JWT)    │             │
│              │  ├─ recommendations.py (engine)   │             │
│              │  └─ models.py (database models)   │             │
│              └─────────────────┬─────────────────┘             │
│                                │                               │
└────────────────────────────────┼───────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   Database Connection   │
                    │   (PyMongo + JWT)       │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────┼───────────────────────────────┐
│                   DATABASE (MongoDB)                           │
├────────────────────────────────┼───────────────────────────────┤
│                                │                               │
│  ┌──────────────────┐  ┌───────┴────────┐  ┌────────────────┐ │
│  │ Users Collection │  │ Health Info    │  │  Feedback      │ │
│  ├──────────────────┤  ├────────────────┤  ├────────────────┤ │
│  │ _id              │  │ _id            │  │ _id            │ │
│  │ name             │  │ user_id        │  │ user_id        │ │
│  │ email            │  │ name           │  │ rating         │ │
│  │ password_hash    │  │ health_cond    │  │ comment        │ │
│  │ age (patient)    │  │ allergies      │  │ recommendation │ │
│  │ role (caretaker) │  │ food_pref      │  │ created_at     │ │
│  │ user_type        │  │ created_at     │  └────────────────┘ │
│  │ created_at       │  │ updated_at     │                     │
│  └──────────────────┘  └────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👥 User Flow Diagrams

### Patient User Flow

```
START
  │
  ├─→ [Landing Page]
  │        │
  │        ├─→ "Patient Register" → [Register Modal]
  │        │        │
  │        │        └─→ Enter: name, age, email, password
  │        │        │
  │        │        └─→ POST /api/auth/patient/register
  │        │        │
  │        │        └─→ ✓ Success → Store token → Redirect
  │        │
  │        ├─→ "Patient Login" → [Login Modal]
  │        │        │
  │        │        └─→ Enter: email, password
  │        │        │
  │        │        └─→ POST /api/auth/patient/login
  │        │        │
  │        │        └─→ ✓ Success → Store token → Redirect
  │
  └─→ [Health Information Page] (health-information.html)
         │
         ├─→ Fill Health Form
         │        ├─ Enter name
         │        ├─ Select health conditions (with values)
         │        ├─ Add allergies (tag system)
         │        └─ Choose food preference
         │
         ├─→ POST /api/patient/health-information
         │
         └─→ ✓ Success → Redirect to Recommendations
         
    [Recommendations Dashboard] (recommendations.html)
         │
         ├─→ GET /api/recommendations/get
         │
         ├─→ Display:
         │        ├─ Alert (if multiple conditions critical)
         │        ├─ Food Section (expandable)
         │        │   ├─ Breakfast
         │        │   ├─ Lunch
         │        │   └─ Dinner
         │        ├─ Drinks Section
         │        ├─ Snacks Section
         │        └─ Healthy Tips (sidebar)
         │
         ├─→ Submit Feedback
         │        ├─ Select rating (1-5 stars)
         │        ├─ Enter comment
         │        └─ POST /api/feedback/submit
         │
         ├─→ Edit Health Info
         │        └─ Return to Health Form
         │
         └─→ Logout
              └─ Clear localStorage → Return to Landing
```

### Caretaker User Flow

```
START
  │
  ├─→ [Landing Page]
  │        │
  │        └─→ "Caretaker Access"
  │               │
  │               ├─→ "Register" → [Register Modal]
  │               │        │
  │               │        └─→ Enter: name, email, role, password
  │               │        │
  │               │        └─→ POST /api/caretaker/register
  │               │        │
  │               │        └─→ ✓ Success → Store token → Redirect
  │               │
  │               └─→ "Login" → [Login Modal]
  │                        │
  │                        └─→ Enter: email, password
  │                        │
  │                        └─→ POST /api/caretaker/login
  │                        │
  │                        └─→ ✓ Success → Store token → Redirect
  │
  └─→ [Caretaker Dashboard] (caretaker-dashboard.html)
         │
         ├─→ Enter Patient ID
         │
         ├─→ GET /api/caretaker/patient/<patient_id>
         │
         ├─→ Display Patient Information:
         │        ├─ Name, Age, Email
         │        ├─ Health Conditions & Values
         │        ├─ Allergies
         │        └─ Food Preference
         │
         ├─→ GET /api/recommendations/for-patient/<patient_id>
         │
         ├─→ Display Patient Recommendations:
         │        ├─ Food (Breakfast, Lunch, Dinner)
         │        ├─ Drinks
         │        ├─ Snacks
         │        ├─ Health Tips
         │        └─ Alert (if present)
         │
         └─→ (Read-Only - No Modifications)
              │
              └─→ Logout
                  └─ Clear localStorage → Return to Landing
```

---

## 🔄 API Communication Flow

### Patient Data Workflow

```
Frontend (JavaScript)
    │
    ├─ User fills health form
    │
    ├─ POST /api/patient/health-information
    │    │
    │    Headers: Authorization: Bearer JWT_TOKEN
    │    Body: {
    │      name, health_conditions, allergies, food_preference
    │    }
    │
    ▼
Backend (Flask Route: patient.py)
    │
    ├─ Verify JWT token
    │
    ├─ Validate input data
    │
    ├─ Create HealthInformation model
    │
    ├─ Save to MongoDB
    │
    ▼
MongoDB
    │
    └─ Store in health_information collection
         {
           _id, user_id, name, health_conditions, 
           allergies, food_preference, created_at, updated_at
         }

Backend Response
    │
    ├─ HTTP 200 OK
    │ {"message": "...", "id": "..."}
    │
    ▼
Frontend
    │
    └─ Redirect to recommendations.html
```

### Recommendation Generation Workflow

```
Frontend (JavaScript)
    │
    ├─ Load recommendations.html
    │
    ├─ POST /api/recommendations/get
    │    │
    │    Headers: Authorization: Bearer JWT_TOKEN
    │
    ▼
Backend (Flask Route: recommendations.py)
    │
    ├─ Verify JWT token
    │
    ├─ Get user ID from token
    │
    ├─ Query MongoDB for health_information
    │
    ▼
LLM-based Engine (gemini_recommender.py)
    │
    ├─ Construct prompt with name, health conditions, allergies, preference
    │
    ├─ POST to OpenRouter API using stored API key
    │
    ├─ Receive structured JSON response with meals/drinks/snacks etc.
    │
    ├─ Extract and validate JSON, inject doctorAlert/alert_message if needed
    │
    ▼
Backend Response
    │
    ├─ HTTP 200 OK
    │ {
    │   alert_message: {...},
    │   Food: { Morning: [...], Afternoon: [...], Evening: [...] },
    │   Drinks: [...],
    │   Snacks: [...],
    │   alternativeMessage: "...",
    │   healthyTipsForToday: {...}
    │ }
```

    │   snacks: [...],
    │   healthy_tips: {...}
    │ }
    │
    ▼
Frontend
    │
    ├─ Display food section (expandable)
    │    ├─ Morning → Breakfast items
    │    ├─ Afternoon → Lunch items
    │    └─ Evening → Dinner items
    │
    ├─ Display drinks section
    │
    ├─ Display snacks section
    │
    ├─ Display healthy tips (sidebar)
    │
    └─ Display alert (if present)
```

---

## 🔐 Authentication Flow

```
User Registration
    │
    ├─ Frontend: POST /api/auth/patient/register
    │    Body: { name, age, email, password }
    │
    ▼
Backend: auth.py
    │
    ├─ Validate input
    │    ├─ Email format valid?
    │    ├─ Password strength?
    │    └─ Email not already registered?
    │
    ├─ Hash password with bcrypt
    │    └─ hash_password(password) → password_hash
    │
    ├─ Create User object
    │
    ├─ Save to MongoDB (users collection)
    │
    ├─ Generate JWT token
    │    └─ generate_token(user_id, 'patient')
    │       └─ Payload: {user_id, user_type, exp}
    │
    ▼
Response: HTTP 201 Created
    {
      message: "Patient registered successfully",
      user_id: "507f1f77bcf86cd799439011",
      token: "eyJ0eXAiOiJKV1QiLCJhbGc...",
      user_type: "patient"
    }

Frontend
    │
    ├─ Store token in localStorage
    │    └─ localStorage.setItem('token', token)
    │
    ├─ Store user info
    │    ├─ localStorage.setItem('userId', user_id)
    │    ├─ localStorage.setItem('userType', 'patient')
    │    └─ localStorage.setItem('userName', name)
    │
    └─ Redirect to health-information.html


User Login
    │
    ├─ Frontend: POST /api/auth/patient/login
    │    Body: { email, password }
    │
    ▼
Backend: auth.py
    │
    ├─ Find user by email
    │
    ├─ Verify password
    │    └─ verify_password(password, password_hash)
    │    └─ Returns: True/False
    │
    ├─ Generate JWT token
    │    └─ generate_token(user_id, 'patient')
    │
    ▼
Response: HTTP 200 OK
    {
      message: "Login successful",
      user_id: "...",
      token: "...",
      user_type: "patient",
      name: "..."
    }

Frontend
    │
    ├─ Store token & user info
    │
    └─ Redirect to health-information.html


Protected Route Access
    │
    ├─ Frontend: GET /api/patient/health-information
    │    Headers: Authorization: Bearer eyJ0eXAi...
    │
    ▼
Backend
    │
    ├─ Extract token from header
    │    └─ token = header.replace('Bearer ', '')
    │
    ├─ Verify token
    │    └─ verify_token(token)
    │    └─ Checks: signature, expiration, format
    │
    ├─ Get user_id from token payload
    │
    ├─ Proceed with request
    │
    └─ (If token invalid: return 401 Unauthorized)
```

---

## 📊 Data Flow Example

### Health Condition Analysis Example

```
User Input:
    diabetes: 150 mg/dL
    blood_pressure: 140/90
    cholesterol: 220 mg/dL
    obesity_bmi: 28
    allergies: ["Peanuts", "Dairy"]
    food_preference: "vegetarian"

↓

Recommendation Engine Analysis:

1. Alert Check:
   - diabetes (150) > safe (100) ✓ Alert
   - blood_pressure (140/90) > safe (120/80) ✓ Alert
   - cholesterol (220) > safe (200) ✓ Alert
   - obesity_bmi (28) > safe (24.9) ✓ Alert
   
   Result: 4 conditions exceed threshold
   → Show doctor consultation alert ⚠️

2. Recommendation Generation:
   
   - Since diabetes detected: Use diabetes-specific foods
   - Since obesity detected: Use low-calorie foods
   - (Diabetes is primary condition)
   
   Breakfast Options:
   [
     "Unsweetened oatmeal with cinnamon"
     → "Low glycemic index helps control blood sugar"
   ]
   
   Apply Filters:
   - Remove items with Peanuts ✗
   - Remove items with Dairy ✗
   - Keep vegetarian items ✓
   - Keep non-vegetarian items ✗
   
   Final Breakfast:
   [
     "Unsweetened oatmeal with cinnamon",
     "Spinach and mushroom omelet",
     "Whole wheat toast with avocado"
   ]

3. Drinks Recommendation:
   
   - Diabetes foods + obesity foods → low carb drinks
   - Filter by allergies
   
   Result:
   [
     "Water",
     "Unsweetened green tea",
     "Herbal tea (cinnamon)",
     "Vegetable broth"
   ]

4. Snacks Recommendation:
   
   - Low carb, high protein
   - Filter by allergies + preferences
   
   Result:
   [
     "Almonds and walnuts",
     "Cheese and whole grain crackers",
     "Vegetable sticks with yogurt dip"
   ]

5. Healthy Tips:
   
   Default tips:
   - 💧 Hydration: "Drink 8-10 glasses water daily"
   - 🏃 Exercise: "30 minutes moderate activity daily"
   - 😴 Sleep: "7-9 hours quality sleep"
   
   Condition-specific:
   - ⚕️ Diabetes: "Monitor glucose regularly..."
   - ⚕️ Obesity: "Practice portion control..."
   → Show Diabetes (primary condition)

Output to Frontend:
{
  alert_message: {
    show: true,
    message: "⚠️ Health Alert: Your Diabetes, Blood Pressure, 
             Cholesterol, BMI levels are above safe thresholds. 
             Please consult with a healthcare professional..."
  },
  food: {
    morning: [...3 items],
    afternoon: [...3 items],
    evening: [...3 items]
  },
  drinks: [...4 items],
  snacks: [...3 items],
  healthy_tips: {
    hydration: "...",
    exercise: "...",
    sleep: "...",
    specific: "Monitor blood glucose regularly..."
  }
}

Frontend Display:
- Show red alert box at top
- Expand Food section → Show meals
- Collapse Drinks initially
- Show Snacks
- Display tips in sidebar
- All with smooth animations
```

---

## 🎯 Feature Implementation Map

```
LANDING PAGE
├─ Logo & Tagline
├─ Feature Cards (3)
├─ Patient Login Modal
│  ├─ Email input
│  ├─ Password input
│  └─ Submit button
├─ Patient Register Modal
│  ├─ Name input
│  ├─ Age input
│  ├─ Email input
│  ├─ Password input
│  └─ Submit button
├─ Caretaker Login Modal
│  ├─ Email input
│  ├─ Password input
│  └─ Submit button
└─ Caretaker Register Modal
   ├─ Name input
   ├─ Email input
   ├─ Role selector
   ├─ Password input
   └─ Submit button

HEALTH INFORMATION PAGE
├─ Personal Information
│  └─ Name input
├─ Health Conditions
│  ├─ Diabetes (checkbox + value)
│  ├─ Blood Pressure (checkbox + value)
│  ├─ Cholesterol (checkbox + value)
│  └─ BMI (checkbox + value)
├─ Allergies
│  ├─ Tag display area
│  ├─ Input field
│  └─ Add button
├─ Food Preference
│  ├─ Vegetarian radio
│  └─ Non-vegetarian radio
└─ Action Buttons
   ├─ Save & Get Recommendations
   └─ Skip for Now

RECOMMENDATIONS PAGE
├─ Alert Container (conditional)
├─ Main Recommendations (3 columns on desktop)
│  ├─ Food Section (expandable)
│  │  ├─ Breakfast
│  │  │  └─ Items with reasons
│  │  ├─ Lunch
│  │  │  └─ Items with reasons
│  │  └─ Dinner
│  │     └─ Items with reasons
│  ├─ Drinks Section (expandable)
│  │  └─ Items with reasons
│  └─ Snacks Section (expandable)
│     └─ Items with reasons
├─ Feedback Section
│  ├─ Star rating system
│  ├─ Comment textarea
│  └─ Submit button
└─ Sidebar (sticky)
   ├─ Healthy Tips Panel
   │  ├─ Hydration tip
   │  ├─ Exercise tip
   │  ├─ Sleep tip
   │  └─ Condition-specific tip
   └─ Health Summary Panel
      ├─ Health conditions display
      ├─ Allergies display
      └─ Food preference display

CARETAKER DASHBOARD
├─ Patient Access Form
│  ├─ Patient ID input
│  └─ View Patient Data button
├─ Patient Information (conditional)
│  ├─ Name, Age, Email
│  └─ Health conditions display
├─ Recommendations Display (if found)
│  ├─ Food recommendations
│  ├─ Drinks recommendations
│  ├─ Snacks recommendations
│  └─ Healthy tips
└─ Read-Only Interface (no edits allowed)
```

---

## 📈 Data Persistence Flow

```
User Action → Frontend State → API Request → Backend Processing → 
Database Storage → Response → Frontend Update → User Feedback

Example: Saving Health Information

User fills form
    ↓
form.submit() event
    ↓
Collect form data into object
    ↓
POST /api/patient/health-information with JWT token
    ↓
Backend receives request
    ↓
Verify JWT token → Get user_id
    ↓
Validate incoming data
    ↓
Create HealthInformation object
    ↓
Call model.save() method
    ↓
MongoDB insert/update operation
    ↓
Database returns result
    ↓
Backend returns HTTP 200 + health_id
    ↓
Frontend receives response
    ↓
Show success message
    ↓
Redirect to recommendations page
    ↓
Auto-load recommendations
    ↓
Display personalized results
    ↓
User sees recommendations with their data
```

---

## ✅ Complete Feature Checklist by Component

```
AUTHENTICATION SYSTEM
├─ Patient registration ✓
├─ Patient login ✓
├─ Caretaker registration ✓
├─ Caretaker login ✓
├─ JWT token generation ✓
├─ Password hashing (bcrypt) ✓
├─ Token verification ✓
└─ Session management ✓

HEALTH PROFILE
├─ Store health conditions ✓
├─ Store allergies ✓
├─ Store food preference ✓
├─ Retrieve health data ✓
├─ Update health data ✓
└─ Display health summary ✓

RECOMMENDATIONS ENGINE
├─ Analyze diabetes ✓
├─ Analyze blood pressure ✓
├─ Analyze cholesterol ✓
├─ Analyze BMI ✓
├─ Generate breakfast ✓
├─ Generate lunch ✓
├─ Generate dinner ✓
├─ Generate drinks ✓
├─ Generate snacks ✓
├─ Filter allergies ✓
├─ Apply food preference ✓
├─ Generate health tips ✓
├─ Detect critical conditions ✓
└─ Generate alerts ✓

FEEDBACK SYSTEM
├─ Submit ratings ✓
├─ Submit comments ✓
├─ Store feedback ✓
├─ Retrieve feedback history ✓
└─ Display feedback confirmation ✓

CARETAKER MODULE
├─ Caretaker roles ✓
├─ Patient lookup ✓
├─ Read-only access ✓
├─ Display patient data ✓
├─ Display patient recommendations ✓
└─ No edit permissions ✓

USER INTERFACE
├─ Landing page ✓
├─ Modal dialogs ✓
├─ Health form ✓
├─ Expandable sections ✓
├─ Sidebar layout ✓
├─ Star rating UI ✓
├─ Tag system for allergies ✓
├─ Responsive design ✓
├─ Smooth animations ✓
└─ Professional styling ✓

DATABASE
├─ Users collection ✓
├─ Health information collection ✓
├─ Feedback collection ✓
├─ Index optimization ✓
└─ Data validation ✓

API ENDPOINTS
├─ 3 Auth endpoints ✓
├─ 3 Patient endpoints ✓
├─ 3 Caretaker endpoints ✓
├─ 2 Recommendation endpoints ✓
└─ 2 Feedback endpoints ✓

SECURITY
├─ Password hashing ✓
├─ JWT authentication ✓
├─ CORS enabled ✓
├─ Input validation ✓
├─ Error handling ✓
└─ Read-only caretaker access ✓
```

---

This visual guide helps you understand:
- How the system is structured
- How users interact with the application
- How data flows through the system
- How recommendations are generated
- How all components work together

**For more details, refer to other documentation files in the project root.**
