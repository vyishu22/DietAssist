# DietAssist - Installation & Verification Checklist

Use this checklist to ensure your DietAssist installation is complete and working properly.

---

## ✅ Pre-Installation Requirements

- [ ] Python 3.8+ installed
- [ ] MongoDB installed or account created (MongoDB Atlas)
- [ ] Node.js or Python http.server available
- [ ] Git installed (optional)
- [ ] Postman or curl installed (for API testing)

**Verify Python Version**:
```bash
python --version
# Should show Python 3.8+
```

**Verify MongoDB**:
```bash
mongo --version
# or if using MongoDB Atlas, have connection string ready
```

---

## 📥 Step 1: Verify Project Structure

Check all required directories exist:

```
DietAssist_3/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   └── utils/
│   ├── run.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── css/
│   ├── js/
│   ├── pages/
│   └── index.html
│
└── README.md
```

- [ ] `/backend` folder exists
- [ ] `/backend/app` subfolder exists
- [ ] `/backend/app/models` folder exists
- [ ] `/backend/app/routes` folder exists
- [ ] `/backend/app/utils` folder exists
- [ ] `/backend/run.py` file exists
- [ ] `/backend/requirements.txt` file exists
- [ ] `/backend/.env` file exists
- [ ] `/frontend` folder exists
- [ ] `/frontend/css` folder exists
- [ ] `/frontend/css/styles.css` file exists
- [ ] `/frontend/js` folder exists (4 JS files)
- [ ] `/frontend/pages` folder exists (3 HTML files)
- [ ] `/frontend/index.html` file exists

**Verify from command line**:
```bash
cd DietAssist_3
ls -la backend
ls -la frontend
```

---

## 📦 Step 2: Install Backend Dependencies

Navigate to backend folder and install packages:

```bash
cd backend
pip install -r requirements.txt
```

- [ ] Flask installed
- [ ] Flask-CORS installed
- [ ] Flask-PyMongo installed
- [ ] PyJWT installed
- [ ] bcrypt installed
- [ ] python-dotenv installed
- [ ] pymongo installed

**Verify installations**:
```bash
pip list | grep -E "Flask|bcrypt|PyJWT"
```

Expected output should show all packages installed.

---

## 🗄️ Step 3: MongoDB Setup

### Option A: Local MongoDB

- [ ] MongoDB service running locally
- [ ] MongoDB connection string verified: `mongodb://localhost:27017/dietassist`

**Start MongoDB** (Windows):
```bash
mongod
```

**Test connection**:
```bash
mongo
> use dietassist
> show collections
```

### Option B: MongoDB Atlas (Cloud)

- [ ] MongoDB Atlas account created
- [ ] Cluster created
- [ ] Connection string obtained
- [ ] .env file updated with connection string

**Update .env**:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dietassist?retryWrites=true&w=majority
```

---

## ⚙️ Step 4: Configuration Verification

Check `.env` file:

```
MONGO_URI=mongodb://localhost:27017/dietassist
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
PORT=5000
```

- [ ] MONGO_URI is set correctly
- [ ] SECRET_KEY has a value
- [ ] DEBUG is set to True (for development)
- [ ] PORT is 5000

For production change:
- [ ] DEBUG to False
- [ ] SECRET_KEY to a strong random string
- [ ] MONGO_URI to production database

---

## 🔒 Rate Limiter (Production)

For production you should use a persistent storage backend for rate limits (Redis is recommended). Configure a Redis URL and set it in your environment:

```
RATELIMIT_STORAGE_URL=redis://:password@redis-host:6379/0
# or
REDIS_URL=redis://:password@redis-host:6379/0
```

- [ ] Redis instance available and accessible from the application
- [ ] `RATELIMIT_STORAGE_URL` (or `REDIS_URL`) set in `.env` or environment
- [ ] `redis` Python package is installed (added to `backend/requirements.txt`)

The app will automatically use the Redis backend for `Flask-Limiter` when the URL env var is provided. If not set, the app uses an in-memory limiter (not recommended for production). 

---

## 🚀 Step 5: Start Backend Server

```bash
cd backend
python run.py
```

Expected output:
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

- [ ] Server starts without errors
- [ ] No import errors
- [ ] No database connection errors
- [ ] Server running on port 5000

**Keep this terminal open** and open a new terminal for frontend.

---

## 🌐 Step 6: Start Frontend Server

Open a new terminal in the `frontend` folder:

```bash
cd frontend
python -m http.server 8000
```

Or using Node.js:
```bash
npx http-server
```

Expected output:
```
Serving HTTP on 0.0.0.0 port 8000
```

- [ ] Server starts without errors
- [ ] Serving files on port 8000
- [ ] No port conflicts

---

## 🖥️ Step 7: Access Application

Open browser and navigate to:
```
http://localhost:8000
```

- [ ] Landing page loads
- [ ] Logo visible
- [ ] Buttons visible
- [ ] No console errors (F12)
- [ ] Responsive design works

---

## 🧪 Step 8: API Connection Test

### Test 1: Registration Request

Open browser console (F12) and run:

```javascript
fetch('http://localhost:5000/api/auth/patient/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: 'Test User',
    age: 30,
    email: 'test@example.com',
    password: 'testpass123'
  })
})
.then(r => r.json())
.then(d => console.log(d))
```

- [ ] Request completes without errors
- [ ] Response includes user_id
- [ ] Response includes token
- [ ] HTTP status 201

### Test 2: Login Request

```javascript
fetch('http://localhost:5000/api/auth/patient/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'testpass123'
  })
})
.then(r => r.json())
.then(d => console.log(d))
```

- [ ] Login successful
- [ ] Token returned
- [ ] Status 200

---

## 🎯 Step 9: End-to-End User Flow Test

### Patient Flow

1. **Register**
   - [ ] Click "Patient Register"
   - [ ] Fill form
   - [ ] Click Submit
   - [ ] Redirected to health form

2. **Health Information**
   - [ ] Enter name
   - [ ] Select health conditions
   - [ ] Add allergies
   - [ ] Select food preference
   - [ ] Click "Save & Get Recommendations"

3. **Recommendations**
   - [ ] See breakfast, lunch, dinner
   - [ ] See drinks section
   - [ ] See snacks section
   - [ ] See healthy tips sidebar
   - [ ] Click expand/collapse sections
   - [ ] Submit feedback with rating

### Caretaker Flow

1. **Register**
   - [ ] Click "Caretaker Access"
   - [ ] Click "Register"
   - [ ] Fill form with role selection
   - [ ] Redirected to dashboard

2. **Access Patient**
   - [ ] Enter patient ID (from patient registration)
   - [ ] Click "View Patient Data"
   - [ ] See patient information
   - [ ] See patient recommendations
   - [ ] Data is read-only

---

## 📊 Step 10: Database Verification

Check MongoDB has data:

```bash
mongo
> use dietassist
> db.users.find().pretty()
> db.health_information.find().pretty()
> db.feedback.find().pretty()
```

- [ ] Users collection has entries
- [ ] Health information saved
- [ ] Feedback stored
- [ ] Timestamps present

---

## 🔍 Step 11: Frontend Feature Checklist

### Landing Page
- [ ] Logo and tagline visible
- [ ] Feature cards display properly
- [ ] Buttons clickable
- [ ] Modals open/close smoothly

### Health Form
- [ ] All health conditions visible
- [ ] Input fields functional
- [ ] Allergies tag system works
- [ ] Add/remove allergies works
- [ ] Food preference radio buttons work

### Recommendations
- [ ] Sections expand/collapse
- [ ] All meal categories visible
- [ ] Reasons display correctly
- [ ] Sidebar tips visible
- [ ] Star rating interactive
- [ ] Feedback form submits

### Caretaker Dashboard
- [ ] Patient ID input works
- [ ] View button functional
- [ ] Patient data displays
- [ ] Recommendations visible
- [ ] Read-only interface

---

## ⚠️ Step 12: Error Checking

### Check Browser Console (F12 → Console)
- [ ] No red errors
- [ ] No CORS errors
- [ ] No undefined variables
- [ ] API calls successful

### Check Backend Terminal
- [ ] No Python errors
- [ ] No ImportError messages
- [ ] Request logs showing
- [ ] 200/201 status codes

### Check Network Tab (F12 → Network)
- [ ] API requests going to `localhost:5000`
- [ ] Status codes 200/201
- [ ] No 404 errors
- [ ] Response data visible

---

## 🔐 Step 13: Security Verification

- [ ] Passwords hashed (check MongoDB, not plain text)
- [ ] Tokens in localStorage (check DevTools)
- [ ] CORS working (cross-origin requests successful)
- [ ] No sensitive data in response errors
- [ ] Authentication required for protected endpoints

---

## 📈 Step 14: Performance Checks

Load recommendations page and check:

- [ ] Page loads in < 2 seconds
- [ ] Animations smooth (not choppy)
- [ ] No memory leaks (DevTools)
- [ ] Responsive on mobile view (F12 → Device Mode)

---

## ✅ Step 15: Final Verification Checklist

- [ ] Both frontend and backend servers running
- [ ] Landing page accessible
- [ ] Can register as patient
- [ ] Can register as caretaker
- [ ] Can login and access health form
- [ ] Can save health information
- [ ] Recommendations generate correctly
- [ ] Can provide feedback
- [ ] Caretaker can access patient data
- [ ] All animations working smoothly
- [ ] Responsive on mobile
- [ ] No console errors
- [ ] Database has user data
- [ ] API endpoints responding

---

## 🚀 Deployment Preparation

Before deployment, verify:

- [ ] .env updated with production values
- [ ] DEBUG set to False
- [ ] SECRET_KEY is strong random string
- [ ] MONGO_URI points to production database
- [ ] All tests pass
- [ ] No console errors
- [ ] Responsive design tested on multiple devices

---

## 📝 Common Issues & Solutions

### Port Already in Use
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill process
taskkill /PID <PID> /F
```

### MongoDB Connection Error
```
Error: connect ECONNREFUSED 127.0.0.1:27017
```
Solution: Start MongoDB service

### CORS Error
```
Access to XMLHttpRequest blocked by CORS policy
```
Solution: Backend CORS already configured, check frontend URL

### Module Not Found
```
ModuleNotFoundError: No module named 'flask'
```
Solution: Run `pip install -r requirements.txt`

### Token Not Working
```
Unauthorized error when accessing protected routes
```
Solution: Check token in localStorage, refresh if expired

---

## 📊 Testing API Endpoints

All 13 endpoints should return successful responses:

```bash
# Test patient registration
curl -X POST http://localhost:5000/api/auth/patient/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","age":30,"email":"test@test.com","password":"pass123"}'

# Test patient login
curl -X POST http://localhost:5000/api/auth/patient/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123"}'

# Use returned token for other requests
curl -X GET http://localhost:5000/api/patient/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

- [ ] All 13 endpoints respond correctly
- [ ] HTTP status codes appropriate (200, 201, 400, 401, 409, etc.)
- [ ] Error messages helpful
- [ ] Database operations persist

---

## 🎯 Success Indicators

✅ Your DietAssist installation is complete when:

1. ✅ Frontend loads without errors
2. ✅ Backend API responds to requests
3. ✅ User registration and login works
4. ✅ Health information can be saved
5. ✅ Recommendations generate dynamically
6. ✅ Feedback system functional
7. ✅ Caretaker access works
8. ✅ Database stores all data
9. ✅ No console errors
10. ✅ Responsive design works
11. ✅ Animations smooth
12. ✅ All 13 API endpoints working

---

## 📞 Support & Troubleshooting

**For setup help**: See QUICK_START.md
**For API issues**: See API_TESTING.md
**For features**: See README.md
**For implementation**: See PROJECT_SUMMARY.md

---

## 📋 Installation Complete Checklist

Print this checklist and mark completed items:

```
SYSTEM SETUP
- [ ] Python 3.8+ installed
- [ ] MongoDB ready
- [ ] Project files downloaded

BACKEND SETUP
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Backend server running
- [ ] No startup errors

FRONTEND SETUP
- [ ] Frontend server running
- [ ] Landing page loads
- [ ] No console errors

FUNCTIONALITY
- [ ] Patient registration works
- [ ] Patient login works
- [ ] Health form functional
- [ ] Recommendations generate
- [ ] Feedback system works
- [ ] Caretaker access works

VERIFICATION
- [ ] Database has data
- [ ] API endpoints working
- [ ] 13/13 endpoints respond
- [ ] Responsive design works
- [ ] Animations smooth

DEPLOYMENT READY
- [ ] All tests pass
- [ ] Production configs set
- [ ] Security verified
- [ ] Performance acceptable
- [ ] Documentation complete
```

---

**✅ Installation Verification Complete!**

Your DietAssist application is ready to use. 

Start developing or deploy to production.

*For questions, refer to documentation files in the project root.*
