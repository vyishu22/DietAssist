# DietAssist - API Testing Guide

This guide helps you test all DietAssist API endpoints using curl, Postman, or the browser console.

---

## 📋 Base URL
```
http://localhost:5000/api
```

---

## 🔐 Authentication Endpoints

### 1. Patient Registration
**Endpoint**: `POST /auth/patient/register`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/auth/patient/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 35,
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Expected Response**:
```json
{
  "message": "Patient registered successfully",
  "user_id": "507f1f77bcf86cd799439011",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_type": "patient"
}
```

---

### 2. Patient Login
**Endpoint**: `POST /auth/patient/login`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/auth/patient/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Expected Response**:
```json
{
  "message": "Login successful",
  "user_id": "507f1f77bcf86cd799439011",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_type": "patient",
  "name": "John Doe"
}
```

---

### 3. Caretaker Registration
**Endpoint**: `POST /caretaker/register`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/caretaker/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Smith",
    "email": "doctor@hospital.com",
    "password": "password123",
    "role": "Doctor"
  }'
```

**Valid Roles**: Doctor, Parent, Nutritionist, Guardian, Others

---

### 4. Caretaker Login
**Endpoint**: `POST /caretaker/login`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/caretaker/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "password123"
  }'
```

---

### 5. Verify Token
**Endpoint**: `POST /auth/verify-token`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/auth/verify-token \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 👤 Patient Endpoints

### 6. Get Health Information
**Endpoint**: `GET /patient/health-information`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/patient/health-information \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response**:
```json
{
  "id": "507f1f77bcf86cd799439012",
  "name": "John Doe",
  "health_conditions": {
    "diabetes": "120",
    "blood_pressure": "120/80",
    "cholesterol": "200",
    "obesity_bmi": "24.5"
  },
  "allergies": ["Peanuts", "Shellfish"],
  "food_preference": "non-vegetarian"
}
```

---

### 7. Save Health Information
**Endpoint**: `POST /patient/health-information`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/patient/health-information \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "John Doe",
    "health_conditions": {
      "diabetes": "120",
      "blood_pressure": "120/80",
      "cholesterol": "200",
      "obesity_bmi": "24.5"
    },
    "allergies": ["Peanuts", "Shellfish"],
    "food_preference": "non-vegetarian"
  }'
```

---

### 8. Get Patient Profile
**Endpoint**: `GET /patient/profile`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/patient/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 👨‍⚕️ Caretaker Endpoints

### 9. Get Patient Data (Caretaker Access)
**Endpoint**: `GET /caretaker/patient/<patient_id>`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/caretaker/patient/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer CARETAKER_TOKEN_HERE"
```

**Expected Response**:
```json
{
  "patient_id": "507f1f77bcf86cd799439011",
  "name": "John Doe",
  "age": 35,
  "email": "john@example.com",
  "health_information": {
    "name": "John Doe",
    "health_conditions": {
      "diabetes": "120"
    },
    "allergies": ["Peanuts"],
    "food_preference": "non-vegetarian"
  }
}
```

---

### 10. Get Caretaker Profile
**Endpoint**: `GET /caretaker/profile`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/caretaker/profile \
  -H "Authorization: Bearer CARETAKER_TOKEN_HERE"
```

---

## 🍽️ Recommendation Endpoints

### 11. Get Personalized Recommendations
**Endpoint**: `POST /recommendations/get`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/recommendations/get \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PATIENT_TOKEN_HERE"
```

**Expected Response**:
```json
{
  "alert_message": {
    "show": false,
    "message": "",
    "conditions": []
  },
  "food": {
    "morning": [
      {
        "name": "Oatmeal with berries",
        "reason": "Rich in fiber and antioxidants for sustained energy"
      }
    ],
    "afternoon": [...],
    "evening": [...]
  },
  "drinks": [
    {
      "name": "Water",
      "reason": "Essential for hydration and metabolic function"
    }
  ],
  "snacks": [...],
  "healthy_tips": {
    "hydration": "Drink at least 8-10 glasses of water daily",
    "exercise": "Aim for 30 minutes of moderate physical activity",
    "sleep": "Get 7-9 hours of quality sleep",
    "specific": "Maintain balanced nutrition with whole foods"
  }
}
```

---

### 12. Get Patient Recommendations (Caretaker)
**Endpoint**: `GET /recommendations/for-patient/<patient_id>`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/recommendations/for-patient/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer CARETAKER_TOKEN_HERE"
```

---

## 💬 Feedback Endpoints

### 13. Submit Feedback
**Endpoint**: `POST /feedback/submit`

**Curl**:
```bash
curl -X POST http://localhost:5000/api/feedback/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PATIENT_TOKEN_HERE" \
  -d '{
    "rating": 5,
    "comment": "The recommendations were very helpful!",
    "recommendation_type": "general"
  }'
```

**Rating**: 1-5

---

### 14. Get Feedback History
**Endpoint**: `GET /feedback/history`

**Curl**:
```bash
curl -X GET http://localhost:5000/api/feedback/history \
  -H "Authorization: Bearer PATIENT_TOKEN_HERE"
```

**Expected Response**:
```json
{
  "feedback": [
    {
      "id": "507f1f77bcf86cd799439013",
      "rating": 5,
      "comment": "Very helpful!",
      "recommendation_type": "general",
      "created_at": "2026-01-03T10:30:00"
    }
  ]
}
```

---

## 🧪 Testing Workflow

### Complete User Journey Test

**Step 1: Register Patient**
```bash
# Register
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/patient/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "age": 30,
    "email": "test@example.com",
    "password": "testpass123"
  }' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"
```

**Step 2: Save Health Information**
```bash
curl -X POST http://localhost:5000/api/patient/health-information \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test User",
    "health_conditions": {
      "diabetes": "150",
      "blood_pressure": "140/90",
      "cholesterol": "220",
      "obesity_bmi": "28"
    },
    "allergies": ["Peanuts", "Dairy"],
    "food_preference": "vegetarian"
  }'
```

**Step 3: Get Recommendations**
```bash
curl -X POST http://localhost:5000/api/recommendations/get \
  -H "Authorization: Bearer $TOKEN"
```

**Step 4: Submit Feedback**
```bash
curl -X POST http://localhost:5000/api/feedback/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "rating": 4,
    "comment": "Good recommendations but limited variety",
    "recommendation_type": "general"
  }'
```

---

## 🔍 Testing with Postman

1. Open Postman
2. Create a new collection "DietAssist"
3. Add requests for each endpoint
4. Set up environment variable:
   - Name: `token`
   - Value: Paste your JWT token
5. Use `{{token}}` in Authorization headers

---

## ⚠️ Common Errors & Solutions

### 401 Unauthorized
```json
{"error": "No token provided"}
```
**Solution**: Add Authorization header with valid token

### 409 Conflict
```json
{"error": "Email already registered"}
```
**Solution**: Use a different email address

### 404 Not Found
```json
{"error": "Patient not found"}
```
**Solution**: Check if patient ID exists in database

### 400 Bad Request
```json
{"error": "Missing required fields"}
```
**Solution**: Ensure all required fields are provided

---

## 🔐 Token Management

### Get Token from Browser
1. Open browser DevTools (F12)
2. Go to Console tab
3. Run: `localStorage.getItem('token')`
4. Copy the token value

### Token Expiration
- Tokens expire in 30 days
- After expiration, user must login again
- No refresh token mechanism (implement for production)

---

## 📊 Health Condition Values (Examples)

### Normal Ranges
```
Diabetes (Fasting): < 100 mg/dL
Blood Pressure: < 120/80 mmHg
Cholesterol (Total): < 200 mg/dL
BMI: 18.5 - 24.9
```

### Test Values
```
High Diabetes: 150, 200, 250
High BP: 140/90, 160/100
High Cholesterol: 220, 250, 300
High BMI: 28, 30, 35
```

---

## 🚀 Performance Testing

### Check API Response Time
```bash
time curl -X GET http://localhost:5000/api/patient/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Load Testing (using Apache Bench)
```bash
ab -n 100 -c 10 http://localhost:5000/api/patient/profile
```

---

## 📝 Database Query Examples

### View All Users
```javascript
db.users.find().pretty()
```

### View User's Health Data
```javascript
db.health_information.findOne({ user_id: "507f1f77bcf86cd799439011" })
```

### View Feedback
```javascript
db.feedback.find({ user_id: "507f1f77bcf86cd799439011" }).pretty()
```

---

## ✅ Endpoint Checklist

- [ ] Patient Registration
- [ ] Patient Login
- [ ] Get Health Information
- [ ] Save Health Information
- [ ] Get Patient Profile
- [ ] Caretaker Registration
- [ ] Caretaker Login
- [ ] Get Caretaker Profile
- [ ] Get Patient Data (Caretaker)
- [ ] Get Recommendations
- [ ] Get Patient Recommendations (Caretaker)
- [ ] Submit Feedback
- [ ] Get Feedback History
- [ ] Verify Token

---

## 🎯 Success Criteria

- ✅ All endpoints return 200-201 status codes
- ✅ Error responses include helpful messages
- ✅ Tokens are valid and not expired
- ✅ Data persists in MongoDB
- ✅ Recommendations vary by health conditions
- ✅ Allergies are properly filtered
- ✅ Caretaker access is read-only

---

**Happy Testing! 🧪**

For more details, see README.md and QUICK_START.md
