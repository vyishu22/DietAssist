# DietAssist - Complete File Index & Navigation Guide

## 📑 Documentation Files

Located in root directory (`c:\Users\Home\Desktop\Dietassist_3\`)

| File | Purpose | Read Time |
|------|---------|-----------|
| **README.md** | Comprehensive project documentation | 15 min |
| **QUICK_START.md** | Setup and installation instructions | 10 min |
| **PROJECT_SUMMARY.md** | Detailed implementation summary | 20 min |
| **API_TESTING.md** | API endpoints and testing guide | 15 min |
| **FILE_INDEX.md** | This file - complete file listing | 10 min |

---

## 🗂️ Backend Files

### Root Backend (`backend/`)

| File | Purpose | Details |
|------|---------|---------|
| **run.py** | Flask application entry point | Starts server on port 5000 |
| **requirements.txt** | Python dependencies | 7 packages listed |
| **.env** | Environment configuration | Database URI, secret key, port |

### App Module (`backend/app/`)

| File | Purpose | Lines | Purpose |
|------|---------|-------|---------|
| **__init__.py** | Flask factory & app setup | 32 | Creates and configures Flask app |

### Models (`backend/app/models/`)

| File | Purpose | Classes | Purpose |
|------|---------|---------|---------|
| **models.py** | Database models | 4 | User, HealthInformation, Caretaker, Feedback |
| **__init__.py** | Package init | - | Empty |

**Models Details**:
- `User` - Patient registration and authentication
- `HealthInformation` - Health conditions, allergies, preferences
- `Caretaker` - Doctor/Nutritionist/Parent/Guardian data
- `Feedback` - User ratings and comments

### Routes (`backend/app/routes/`)

| File | Endpoints | Count | Purpose |
|------|-----------|-------|---------|
| **auth.py** | `/api/auth/*` | 3 | Patient/caretaker authentication |
| **patient.py** | `/api/patient/*` | 3 | Patient health data management |
| **caretaker.py** | `/api/caretaker/*` | 3 | Caretaker access & patient lookup |
| **recommendations.py** | `/api/recommendations/*` | 2 | Dynamic recommendation generation |
| **feedback.py** | `/api/feedback/*` | 2 | Feedback submission and history |
| **__init__.py** | - | - | Package init |

**Endpoints Total**: 13 active endpoints

### Utils (`backend/app/utils/`)

| File | Functions | Purpose |
|------|-----------|---------|
| **auth_utils.py** | 6 | Password hashing, JWT, validation |
| **recommendations.py** | 12+ | Recommendation engine logic |
| **__init__.py** | - | Package init |

**Auth Utils**:
- `hash_password()` - Bcrypt hashing
- `verify_password()` - Password checking
- `generate_token()` - JWT creation
- `verify_token()` - Token validation
- `validate_email()` - Email format
- `validate_password()` - Password strength

**Recommendation Engine**:
- `get_recommendations()` - Main method
- `_check_health_alerts()` - Alert detection
- `_generate_food_recommendations()` - Food meals
- `_get_morning_foods()` - Breakfast items
- `_get_afternoon_foods()` - Lunch items
- `_get_evening_foods()` - Dinner items
- `_generate_drink_recommendations()` - Beverages
- `_generate_snack_recommendations()` - Snacks
- `_generate_healthy_tips()` - Lifestyle advice
- Plus filtering and validation methods

---

## 🎨 Frontend Files

### Root Frontend (`frontend/`)

| File | Purpose | Size |
|------|---------|------|
| **index.html** | Landing page | 3.5 KB |

**Contains**:
- Landing section with logo and tagline
- Feature cards (3 columns)
- 4 Modal dialogs for auth
- Patient login/register
- Caretaker login/register

### CSS (`frontend/css/`)

| File | Sections | Lines | Size |
|------|----------|-------|------|
| **styles.css** | Global + component styles | 850+ | 45 KB |

**Sections**:
1. Global styles & CSS variables
2. Landing page styling
3. Button styles (3 variants)
4. Feature cards
5. Modal styling
6. Form styling
7. Health condition cards
8. Tag system
9. Recommendation sections
10. Sidebar styling
11. Alert messages
12. Feedback section
13. Caretaker dashboard
14. Animations (8 types)
15. Responsive breakpoints
16. Loading states

**CSS Variables** (15 colors):
- Primary: Green (#00a86b)
- Secondary: Red (#ff6b6b)
- Accent: Teal (#4ecdc4)
- Status: Success, warning, danger, info

### JavaScript (`frontend/js/`)

| File | Purpose | Functions | Size |
|------|---------|-----------|------|
| **auth.js** | Landing page logic | 8 | 5 KB |
| **health-information.js** | Health form logic | 7 | 6 KB |
| **recommendations.js** | Recommendations display | 12+ | 8 KB |
| **caretaker-dashboard.js** | Caretaker interface | 5 | 7 KB |

**auth.js Functions**:
- Modal management (show/close/switch)
- Patient registration handler
- Patient login handler
- Caretaker registration handler
- Caretaker login handler
- Auto-redirect on load

**health-information.js Functions**:
- Health condition toggle
- Allergy management (add/remove/render)
- Form submission
- Data loading
- Navigation

**recommendations.js Functions**:
- Recommendation loading
- Display functions (food/drinks/snacks)
- Healthy tips rendering
- Health summary display
- Section toggle (expand/collapse)
- Rating system
- Feedback submission
- Alert display

**caretaker-dashboard.js Functions**:
- Patient data retrieval
- Patient info display
- Recommendation display
- Health profile rendering
- Section toggle

### Pages (`frontend/pages/`)

| File | Purpose | Sections |
|------|---------|----------|
| **health-information.html** | Health profile form | Personal info + 4 conditions + allergies + preference |
| **recommendations.html** | Recommendations display | 3 main sections + sidebar + feedback |
| **caretaker-dashboard.html** | Caretaker interface | Patient lookup + data display |

**health-information.html Sections**:
- Personal information (name)
- Health conditions:
  - Diabetes (mg/dL)
  - Blood Pressure (mmHg)
  - Cholesterol (mg/dL)
  - BMI
- Food allergies (tag input)
- Food preference (radio buttons)
- Submit buttons

**recommendations.html Sections**:
- Alert container
- Food recommendations (expandable)
  - Breakfast
  - Lunch
  - Dinner
- Drinks recommendations
- Snacks recommendations
- Feedback form with rating
- Sidebar:
  - Healthy Tips
  - Health Summary

**caretaker-dashboard.html Sections**:
- Patient access form
- Patient information display
- Health profile
- Recommendations display
  - Food (with meals)
  - Drinks
  - Snacks
  - Healthy Tips

---

## 📊 Database Schema

### Collections

#### Users Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  password_hash: String,
  age: Number (patients only),
  user_type: "patient" | "caretaker",
  role: String (caretaker roles),
  created_at: DateTime
}
```

#### Health Information Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  name: String,
  health_conditions: {
    diabetes: String,
    blood_pressure: String,
    cholesterol: String,
    obesity_bmi: String
  },
  allergies: [String],
  food_preference: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

#### Feedback Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  rating: Number,
  comment: String,
  recommendation_type: String,
  created_at: DateTime
}
```

---

## 🔌 API Endpoints Summary

### Total: 13 Endpoints

#### Authentication (3)
- `POST /api/auth/patient/register`
- `POST /api/auth/patient/login`
- `POST /api/auth/verify-token`

#### Patient (3)
- `GET /api/patient/health-information`
- `POST /api/patient/health-information`
- `GET /api/patient/profile`

#### Caretaker (3)
- `POST /api/caretaker/register`
- `POST /api/caretaker/login`
- `GET /api/caretaker/patient/<patient_id>`
- `GET /api/caretaker/profile`

#### Recommendations (2)
- `POST /api/recommendations/get`
- `GET /api/recommendations/for-patient/<patient_id>`

#### Feedback (2)
- `POST /api/feedback/submit`
- `GET /api/feedback/history`

---

## 📦 Dependencies

### Backend (requirements.txt)
```
Flask==2.3.3
flask-cors==4.0.0
flask-pymongo==2.3.0
PyJWT==2.8.0
bcrypt==4.0.1
python-dotenv==1.0.0
pymongo==4.4.1
```

### Frontend
- No dependencies (vanilla HTML/CSS/JS)
- Uses browser's Fetch API

---

## 🗺️ Navigation Guide

### For Setup
1. Start with **QUICK_START.md** for installation
2. Read **README.md** for features overview
3. Use **API_TESTING.md** to test endpoints

### For Development
1. Backend code: `backend/app/` folder
2. Frontend code: `frontend/` folder
3. Review models: `backend/app/models/models.py`
4. Check routes: `backend/app/routes/`

### For Customization
1. Modify colors: `frontend/css/styles.css` (CSS variables)
2. Update health conditions: recommendations are now generated exclusively via OpenRouter API; no local file.
3. Add endpoints: `backend/app/routes/`
4. Extend models: `backend/app/models/models.py`

### For Testing
1. API testing: **API_TESTING.md**
2. Frontend testing: Use browser DevTools
3. Database testing: MongoDB CLI or Compass

---

## 🎯 Key Locations

| Task | Location |
|------|----------|
| Change port | `backend/.env` |
| Change database | `backend/.env` (MONGO_URI) |
| Modify colors | `frontend/css/styles.css` |
| Add health condition | handled by OpenRouter prompt; no local engine |
| Create new endpoint | `backend/app/routes/` |
| Change landing page | `frontend/index.html` |
| Modify form fields | `frontend/pages/health-information.html` |
| Update recommendations UI | `frontend/pages/recommendations.html` |

---

## 📈 File Statistics

### Backend
- **Total Files**: 14
- **Python Files**: 10
- **Lines of Code**: ~1,800
- **Endpoints**: 13
- **Models**: 4
- **Utility Functions**: 18+

### Frontend
- **Total Files**: 8
- **HTML Files**: 4
- **CSS Files**: 1
- **JavaScript Files**: 4
- **Lines of Code**: ~1,500
- **Functions**: 30+

### Documentation
- **Total Files**: 5
- **Total Words**: ~8,000
- **Total Lines**: ~700

**Grand Total**:
- **Files**: 27
- **Lines of Code**: ~3,300
- **Documentation**: ~8,000 words

---

## ✅ File Checklist

### Backend
- [x] run.py - Flask entry point
- [x] requirements.txt - Dependencies
- [x] .env - Configuration
- [x] app/__init__.py - App factory
- [x] models/models.py - Database models
- [x] routes/auth.py - Authentication
- [x] routes/patient.py - Patient data
- [x] routes/caretaker.py - Caretaker access
- [x] routes/recommendations.py - Recommendations
- [x] routes/feedback.py - Feedback system
- [x] utils/auth_utils.py - Auth helpers
- [x] utils/recommendations.py - Recommendation engine

### Frontend
- [x] index.html - Landing page
- [x] css/styles.css - Global styles
- [x] js/auth.js - Authentication logic
- [x] js/health-information.js - Health form
- [x] js/recommendations.js - Recommendations display
- [x] js/caretaker-dashboard.js - Caretaker interface
- [x] pages/health-information.html - Health form page
- [x] pages/recommendations.html - Recommendations page
- [x] pages/caretaker-dashboard.html - Caretaker page

### Documentation
- [x] README.md - Main documentation
- [x] QUICK_START.md - Setup guide
- [x] PROJECT_SUMMARY.md - Implementation summary
- [x] API_TESTING.md - API testing guide
- [x] FILE_INDEX.md - This file

---

## 🚀 Next Steps

### To Get Started
1. Read **QUICK_START.md**
2. Install dependencies
3. Start MongoDB
4. Run backend: `python run.py`
5. Run frontend: `python -m http.server 8000`
6. Visit `http://localhost:8000`

### To Test
1. Follow **API_TESTING.md**
2. Test each endpoint
3. Try user workflows

### To Customize
1. Review **PROJECT_SUMMARY.md**
2. Check specific files in this index
3. Modify as needed
4. Test changes

### To Deploy
1. Read deployment section in **QUICK_START.md**
2. Set production environment variables
3. Use appropriate server (Gunicorn, Nginx)
4. Configure database (MongoDB Atlas)

---

## 📞 File Help

For questions about specific files, check:
- **File structure**: This index
- **Setup issues**: QUICK_START.md
- **Features**: README.md
- **Implementation**: PROJECT_SUMMARY.md
- **API problems**: API_TESTING.md

---

**DietAssist - Complete File Reference Guide**

*Last Updated: January 3, 2026*

*Total Project Files: 27 | Total Code Lines: 3,300 | Total Documentation: 8,000 words*
