# DietAssist - Quick Start Guide

## Installation Steps

### Step 1: Install Backend Dependencies

Open a terminal and navigate to the backend folder:

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: MongoDB Setup

Ensure MongoDB is running. If using local MongoDB:

```bash
# Windows
mongod

# macOS (with Homebrew)
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

Or use MongoDB Atlas (cloud):
- Sign up at https://www.mongodb.com/cloud/atlas
- Create a cluster
- Update MONGO_URI in `.env` with your connection string

### Step 3: Configure Environment

The `.env` file is already set with defaults:
```
MONGO_URI=mongodb://localhost:27017/dietassist
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
PORT=5000
```

For production, change DEBUG to False and use a strong SECRET_KEY.

### Step 4: Start Backend Server

From the `backend` folder:

```bash
python run.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### Step 5: Start Frontend Server

Open another terminal and navigate to the frontend folder:

```bash
# Using Python 3
python -m http.server 8000

# Using Node.js
npx http-server
```

### Step 6: Access Application

Open your browser and go to:
```
http://localhost:8000
```

## Usage

### For Patients

1. **Landing Page**: Click "Patient Register" or "Patient Login"
2. **Registration**: 
   - Enter your name, age, email, and password
   - Click "Register"
3. **Health Information**:
   - Fill in your health conditions (diabetes, blood pressure, etc.)
   - Add food allergies
   - Select food preference
   - Click "Save & Get Recommendations"
4. **View Recommendations**:
   - See personalized breakfast, lunch, dinner
   - View drink and snack recommendations
   - Check healthy tips
   - Submit feedback using star rating

### For Caretakers

1. **Landing Page**: Click "Caretaker Access"
2. **Registration**:
   - Enter your name, email
   - Select your role (Doctor, Parent, Nutritionist, Guardian, Others)
   - Enter password
   - Click "Register"
3. **Dashboard**:
   - Enter a patient ID (from patient's profile after they register)
   - View patient's health information
   - See patient's diet recommendations
   - All data is read-only

## Getting Patient ID

After a patient registers, they can find their patient ID in:
- Browser console (localStorage.getItem('userId'))
- Or share it manually from the database

## Troubleshooting

### Port Already in Use
- Change port in `.env` (for backend)
- Use different port for frontend: `python -m http.server 9000`

### MongoDB Connection Error
- Ensure MongoDB is running
- Check MONGO_URI in `.env`
- For MongoDB Atlas, ensure IP is whitelisted

### CORS Error
- Backend CORS is already configured
- Ensure frontend and backend URLs match

### Frontend Not Loading
- Clear browser cache
- Check if server is running on correct port
- Open developer console for errors

## File Locations

- **Landing Page**: `frontend/index.html`
- **API Base URL**: `http://localhost:5000/api` (in JavaScript files)
- **Database**: Configure in `backend/.env`

## Development Tips

1. Keep backend terminal open to see request logs
2. Use browser DevTools (F12) to debug frontend
3. Check MongoDB to verify data is saving
4. Use `localStorage` to view stored auth tokens

## Production Deployment

### Backend (Using Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend (Using Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    root /path/to/frontend;
    index index.html;
    
    location / {
        try_files $uri /index.html;
    }
}
```

### Environment Variables (Production)

```
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/dietassist
SECRET_KEY=generate-a-strong-random-key
DEBUG=False
PORT=5000
```

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  password_hash: String,
  age: Number (patients only),
  user_type: "patient" | "caretaker",
  role: String (caretaker roles),
  created_at: Date
}
```

### Health Information Collection
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
  food_preference: "vegetarian" | "non-vegetarian",
  created_at: Date,
  updated_at: Date
}
```

### Feedback Collection
```javascript
{
  _id: ObjectId,
  user_id: String,
  rating: Number (1-5),
  comment: String,
  recommendation_type: String,
  created_at: Date
}
```

## Performance Tips

1. Use MongoDB indexing for user lookups
2. Cache recommendations for 24 hours
3. Compress API responses
4. Use CDN for static assets
5. Implement pagination for patient lists

## Security Recommendations

1. Use HTTPS in production
2. Implement rate limiting on API
3. Add request validation
4. Use environment variables for secrets
5. Implement audit logging
6. Regular security audits
7. Update dependencies regularly

---

For more details, see README.md
