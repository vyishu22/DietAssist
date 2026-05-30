# DietAssist - Fresh Start Guide

## ✅ Current Status

Both servers are now running and clean:

```
✅ Backend:  http://localhost:5000 (Flask)
✅ Frontend: http://localhost:8000 (HTTP Server)
```

---

## 🚀 How to Use the Application

### **STEP 1: Open the Landing Page**

Open your browser and go to:
```
http://localhost:8000
```

You should see:
- **DietAssist** logo and tagline
- Three buttons: Patient Login, Patient Register, Caretaker Access
- Feature cards explaining the system

### **STEP 2: Register as a Patient**

1. Click **"Patient Register"** button
2. Fill in the form:
   - **Full Name**: e.g., "John Doe"
   - **Age**: e.g., "30"
   - **Email**: e.g., "john@example.com"
   - **Password**: e.g., "password123"
3. Click **"Register"** button
4. **Auto-redirect** → You go to Health Information page

### **STEP 3: Complete Health Profile**

On the Health Information page:

1. **Full Name**: Should be pre-filled (edit if needed)
2. **Health Conditions** (check and enter values):
   - ☑ Diabetes (mg/dL): e.g., 150
   - ☑ Blood Pressure (mmHg): e.g., 140/90
   - ☑ Cholesterol (mg/dL): e.g., 220
   - ☑ BMI: e.g., 28
3. **Allergies**:
   - Type in allergies (e.g., "Peanuts")
   - Click "+ Add" or press Enter
   - See tags appear below
4. **Food Preference**:
   - Select either "Vegetarian" or "Non-Vegetarian"
5. Click **"Save & Get Recommendations"**
6. **Auto-redirect** → Recommendations page

### **STEP 4: View Personalized Recommendations**

On the Recommendations page, you'll see:

**Main Content:**
- 🍽️ **Food Recommendations**
  - Breakfast items (with health reasons)
  - Lunch items (with health reasons)
  - Dinner items (with health reasons)
  - Click "Show Alternatives" to see alternative foods
  - Click "Apply Alternatives for food" to use them

- 🥤 **Drink Recommendations** (expandable)
  - Water, tea, herbal beverages
  - Each with health reasoning

- 🍿 **Snack Recommendations** (expandable)
  - Nuts, fruits, yogurt options
  - Filtered by your allergies and preferences

**Sidebar:**
- 💡 **Healthy Tips for Today**
  - Hydration tips
  - Exercise suggestions
  - Sleep recommendations
  - Condition-specific tips

- 📊 **Your Health Summary**
  - Your health conditions and values
  - Allergies listed
  - Food preference

**Alert** (if multiple conditions critical):
- ⚠️ Red alert showing which conditions need doctor consultation

### **STEP 5: Submit Feedback**

1. Click **"Go to Feedback Page"** button (at bottom of recommendations)
2. On Feedback page:
   - Click stars to rate (1-5 stars)
   - (Optional) Add comments
   - Click **"Submit Feedback"**
3. **Auto-redirect** → Back to Recommendations page

### **STEP 6: Edit Health Info or Logout**

From Recommendations page:
- Click **"Edit Health Info"** → Go back to health information form
- Click **"Logout"** → Clear session, return to landing page

---

## 🔄 Alternative Food Options Feature

When viewing recommendations:

1. Click **"Show Alternatives"** under any section (Food/Drinks/Snacks)
2. See list of alternative items appear with health reasons
3. Click **"Apply Alternatives for [type]"** to replace the main recommendations
4. Main section updates with the alternatives
5. Success message shows confirmation

---

## 🐛 Troubleshooting

### If landing page doesn't show (goes straight to health-info):
```javascript
// Open browser console (F12) and run:
localStorage.clear()
// Then refresh the page
```

### If "Failed to fetch" error appears:
- Check both servers are running:
  ```powershell
  netstat -aon | findstr :5000  # Should show LISTENING
  netstat -aon | findstr :8000  # Should show LISTENING
  ```
- Restart servers if needed

### If recommendations don't appear:
- Check browser Console (F12) for JavaScript errors
- Check Network tab to see if API calls succeeded
- Verify backend is running with: `curl http://localhost:5000`

---

## 📝 Key Features Implemented

✅ Patient Registration & Login
✅ Caretaker Registration & Login  
✅ Health Condition Tracking (Diabetes, BP, Cholesterol, BMI)
✅ Allergy Management (add/remove tags)
✅ Food Preference Selection (Vegetarian/Non-Veg)
✅ Personalized Diet Recommendations
✅ Dynamic Recommendations Based on Health Data
✅ Alternative Food Options
✅ Healthy Tips Generation
✅ Health Alert System
✅ Feedback Submission & Storage
✅ Professional UI with Animations
✅ Responsive Design
✅ Token-Based Authentication (JWT)
✅ MongoDB Integration

---

## 🎯 Current Servers

```
Backend:  http://127.0.0.1:5000/api
Frontend: http://127.0.0.1:8000

Full URL: http://localhost:8000
```

---

## 🔐 Test Accounts

After registration, you can log in with:
- Email: your registered email
- Password: your registered password

---

**Ready to test? Open http://localhost:8000 and start registering!** 🎉
