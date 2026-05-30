# Registration Error Debugging Guide

## "Failed to fetch" Error - Solutions

This error typically means the frontend can't reach the backend. Here's how to fix it:

---

## ✅ Step 1: Check if Backend is Running

### On PowerShell, navigate to backend and start the server:

```powershell
cd c:\Users\Home\Desktop\Dietassist_3\backend
python run.py
```

**Expected output:**
```
WARNING in app.run_wrapper: This is a development server. Do not use it in production.
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

**❌ If you see errors**, continue to Step 2.

---

## ✅ Step 2: Install Backend Dependencies

If backend fails to run, install required packages:

```powershell
cd c:\Users\Home\Desktop\Dietassist_3\backend
pip install -r requirements.txt
```

**Then try running again:**
```powershell
python run.py
```

---

## ✅ Step 3: Check MongoDB Connection

The error might be MongoDB-related. Verify:

### A. Check if MongoDB is running locally:
```powershell
# If you have MongoDB installed locally, start it:
mongod
```

### B. If you don't have local MongoDB, use MongoDB Atlas (Cloud):

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a cluster
4. Get your connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/database`)
5. Update `.env` file:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dietassist
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
PORT=5000
```

---

## ✅ Step 4: Verify API is Accessible

With backend running, test the API in another PowerShell window:

```powershell
# Test if backend is running
curl http://localhost:5000/

# Test the registration endpoint
curl -X POST http://localhost:5000/api/auth/patient/register `
  -H "Content-Type: application/json" `
  -d '{"name":"Test","age":25,"email":"test@example.com","password":"password123"}'
```

**Expected response:**
```json
{
  "message": "Patient registered successfully",
  "user_id": "...",
  "token": "...",
  "user_type": "patient"
}
```

---

## ✅ Step 5: Start Frontend Server

In another PowerShell window:

```powershell
cd c:\Users\Home\Desktop\Dietassist_3\frontend
python -m http.server 8000
```

**Expected output:**
```
Serving HTTP on 0.0.0.0 port 8000 ...
```

---

## ✅ Step 6: Access the Application

Open in your browser:
```
http://localhost:8000
```

Try registering again.

---

## 🔍 Browser Console Debugging

If registration still fails:

1. **Open browser DevTools** (Press `F12`)
2. **Go to Console tab**
3. **Try registering** and check for error messages
4. **Go to Network tab**
5. **Try registering again** and look for failed requests
6. **Click on the failed request** and check:
   - Status (should be 201 for registration success)
   - Response (should show the success message or error details)
   - Request (verify correct endpoint URL and data)

---

## Common Issues & Fixes

### Issue 1: "Failed to fetch" with no error details
**Cause:** Backend not running
**Fix:** Run `python run.py` in backend folder

### Issue 2: "Failed to fetch" after 5+ seconds
**Cause:** Backend is slow or MongoDB not responding
**Fix:** Check MongoDB connection in Step 3

### Issue 3: CORS error in console
**Cause:** CORS not configured correctly
**Fix:** Backend CORS is set to allow all origins - should work. Restart backend.

### Issue 4: "Email already registered"
**Cause:** User already exists
**Fix:** Use a different email address

### Issue 5: "Invalid email format"
**Cause:** Email doesn't match validation pattern
**Fix:** Use format like: user@example.com

### Issue 6: "Password must be at least 6 characters"
**Cause:** Password too short
**Fix:** Use password with 6+ characters

---

## ✅ Complete Startup Checklist

```
TERMINAL 1 (Backend):
[ ] cd c:\Users\Home\Desktop\Dietassist_3\backend
[ ] python run.py
[ ] See "Running on http://127.0.0.1:5000"

TERMINAL 2 (Frontend):
[ ] cd c:\Users\Home\Desktop\Dietassist_3\frontend
[ ] python -m http.server 8000
[ ] See "Serving HTTP on 0.0.0.0 port 8000"

BROWSER:
[ ] Open http://localhost:8000
[ ] Click "Patient Register"
[ ] Fill in form:
    - Name: John Doe
    - Age: 25
    - Email: john@example.com
    - Password: password123
[ ] Click Register
[ ] Should see success message and redirect
```

---

## 📊 Architecture Check

The registration flow should work like this:

```
Frontend (Browser)
    ↓ User submits form
    ↓ JavaScript collects data
    ↓ POST /api/auth/patient/register (to localhost:5000)
    ↓
Backend (Flask on port 5000)
    ↓ Receives request
    ↓ Validates input
    ↓ Checks MongoDB for existing user
    ↓ Hashes password
    ↓ Saves to MongoDB
    ↓ Generates JWT token
    ↓ Returns 201 Created with token
    ↓
Frontend (Browser)
    ↓ Receives response
    ↓ Stores token in localStorage
    ↓ Redirects to health information page
    ↓
User sees new page = SUCCESS ✓
```

---

## 🆘 Still Having Issues?

If none of the above works, run these diagnostic commands:

```powershell
# Check Python version
python --version

# Check pip packages
pip list | grep -E "flask|pymongo|jwt|bcrypt"

# Try importing modules in Python
python -c "import flask; import flask_pymongo; import jwt; import bcrypt; print('All modules installed!')"

# Test MongoDB connection
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB connected!')"
```

**If anything fails, that's the problem.**

---

## 📝 Quick Reference

| Component | Port | Command | URL |
|-----------|------|---------|-----|
| Backend | 5000 | `python run.py` | http://localhost:5000 |
| Frontend | 8000 | `python -m http.server 8000` | http://localhost:8000 |
| MongoDB | 27017 | `mongod` | mongodb://localhost:27017 |

