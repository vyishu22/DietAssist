// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Check authentication on page load
window.addEventListener('load', () => {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (!token || userType !== 'patient') {
        window.location.href = '../index.html';
        return;
    }
    
    loadHealthInformation();
});

// Toggle health condition input
function toggleInput(fieldId) {
    const checkbox = document.getElementById(fieldId + 'Check');
    const input = document.getElementById(fieldId);
    input.disabled = !checkbox.checked;
    if (!checkbox.checked) {
        input.value = '';
    }
}

// Allergies management
let allergies = [];

function addAllergy() {
    const input = document.getElementById('allergyInput');
    const allergy = input.value.trim();
    
    if (!allergy) {
        alert('Please enter an allergy');
        return;
    }
    
    if (allergies.includes(allergy)) {
        alert('This allergy is already added');
        return;
    }
    
    allergies.push(allergy);
    input.value = '';
    renderAllergies();
}

function removeAllergy(index) {
    allergies.splice(index, 1);
    renderAllergies();
}

function renderAllergies() {
    const container = document.getElementById('allergyTags');
    container.innerHTML = '';
    
    allergies.forEach((allergy, index) => {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            ${allergy}
            <button type="button" class="tag-remove" onclick="removeAllergy(${index})">×</button>
        `;
        container.appendChild(tag);
    });
}

// Allow adding allergy with Enter key
document.addEventListener('DOMContentLoaded', () => {
    const allergyInput = document.getElementById('allergyInput');
    if (allergyInput) {
        allergyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addAllergy();
            }
        });
    }
});

// Load existing health information
async function loadHealthInformation() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/patient/health-information`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Populate form with existing data
            document.getElementById('name').value = data.name || '';
            
            // Health conditions
            if (data.health_conditions) {
                if (data.health_conditions.diabetes) {
                    document.getElementById('diabetesCheck').checked = true;
                    document.getElementById('diabetes').disabled = false;
                    document.getElementById('diabetes').value = data.health_conditions.diabetes;
                }
                
                if (data.health_conditions.blood_pressure) {
                    document.getElementById('bloodPressureCheck').checked = true;
                    document.getElementById('bloodPressure').disabled = false;
                    document.getElementById('bloodPressure').value = data.health_conditions.blood_pressure;
                }
                
                if (data.health_conditions.cholesterol) {
                    document.getElementById('cholesterolCheck').checked = true;
                    document.getElementById('cholesterol').disabled = false;
                    document.getElementById('cholesterol').value = data.health_conditions.cholesterol;
                }
                
                if (data.health_conditions.obesity_bmi) {
                    document.getElementById('bmiCheck').checked = true;
                    document.getElementById('bmi').disabled = false;
                    document.getElementById('bmi').value = data.health_conditions.obesity_bmi;
                }
            }
            
            // Allergies
            if (data.allergies && Array.isArray(data.allergies)) {
                allergies = [...data.allergies];
                renderAllergies();
            }
            
            // Food preference
            if (data.food_preference) {
                document.querySelector(`input[name="foodPreference"][value="${data.food_preference}"]`).checked = true;
            }
        }
    } catch (error) {
        console.error('Error loading health information:', error);
    }
}

// Save health information
document.getElementById('healthForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const token = localStorage.getItem('token');
    
    // Build health conditions object
    const healthConditions = {};
    
    if (document.getElementById('diabetesCheck').checked) {
        healthConditions.diabetes = document.getElementById('diabetes').value;
    }
    
    if (document.getElementById('bloodPressureCheck').checked) {
        healthConditions.blood_pressure = document.getElementById('bloodPressure').value;
    }
    
    if (document.getElementById('cholesterolCheck').checked) {
        healthConditions.cholesterol = document.getElementById('cholesterol').value;
    }
    
    if (document.getElementById('bmiCheck').checked) {
        healthConditions.obesity_bmi = document.getElementById('bmi').value;
    }
    
    const foodPreference = document.querySelector('input[name="foodPreference"]:checked').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/patient/health-information`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name,
                health_conditions: healthConditions,
                allergies,
                food_preference: foodPreference
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert('Error: ' + data.error);
            return;
        }
        
        // Redirect to server-rendered recommendations page
        window.location.href = `http://localhost:5000/recommendations?token=${encodeURIComponent(token)}`;
    } catch (error) {
        alert('Error saving health information: ' + error.message);
    }
});

// Navigation functions
function goToDashboard() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '../index.html';
        return;
    }
    window.location.href = `http://localhost:5000/recommendations?token=${encodeURIComponent(token)}`;
}

function logout() {
    localStorage.clear();
    window.location.href = '../index.html';
}
