// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let currentPatientId = null;

// Check authentication on page load
window.addEventListener('load', () => {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (!token || userType !== 'caretaker') {
        window.location.href = '../index.html';
        return;
    }
    
    // Display caretaker info
    const caretakerName = localStorage.getItem('caretakerName');
    const caretakerRole = localStorage.getItem('caretakerRole');
    document.getElementById('caretakerInfo').textContent = `${caretakerRole}: ${caretakerName}`;
});

// Handle patient access from search selection
async function loadPatientData(patientId) {
    const token = localStorage.getItem('token');
    currentPatientId = patientId;
    
    try {
        // Fetch patient data
        const patientResponse = await fetch(`${API_BASE_URL}/caretaker/patient/${patientId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!patientResponse.ok) {
            showAlert('Patient not found. Please try searching again.', 'danger');
            return;
        }
        
        const patientData = await patientResponse.json();
        
        // Display patient information
        displayPatientInfo(patientData);
        
        // Fetch recommendations
        const recoResponse = await fetch(`${API_BASE_URL}/recommendations/for-patient/${patientId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (recoResponse.ok) {
            const recommendations = await recoResponse.json();
            displayPatientRecommendations(recommendations);
        }
        
        // Fetch recommendation history
        const historyResponse = await fetch(`${API_BASE_URL}/recommendations/history/${patientId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (historyResponse.ok) {
            const historyData = await historyResponse.json();
            displayRecommendationHistory(historyData.recommendations);
        }
        
        document.getElementById('patientDataContainer').style.display = 'block';
        
        // Scroll to patient data
        document.getElementById('patientDataContainer').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    }
}

// Display patient information
function displayPatientInfo(patientData) {
    document.getElementById('patientName').textContent = patientData.name || '-';
    document.getElementById('patientAge').textContent = patientData.age || '-';
    document.getElementById('patientEmail').textContent = patientData.email || '-';
    
    // Display health information
    const healthContainer = document.getElementById('patientHealthContainer');
    healthContainer.innerHTML = '';
    
    if (patientData.health_information) {
        const health = patientData.health_information;
        let html = '<div class="patient-info">';
        
        if (health.health_conditions && Object.keys(health.health_conditions).length > 0) {
            const conditions = health.health_conditions;
            
            if (conditions.diabetes) {
                html += `<div class="patient-info-item"><span>Glucose Level:</span> <strong>${conditions.diabetes} mg/dL</strong></div>`;
            }
            
            if (conditions.blood_pressure) {
                html += `<div class="patient-info-item"><span>Blood Pressure:</span> <strong>${conditions.blood_pressure} mmHg</strong></div>`;
            }
            
            if (conditions.cholesterol) {
                html += `<div class="patient-info-item"><span>Cholesterol:</span> <strong>${conditions.cholesterol} mg/dL</strong></div>`;
            }
            
            if (conditions.obesity_bmi) {
                html += `<div class="patient-info-item"><span>BMI:</span> <strong>${conditions.obesity_bmi}</strong></div>`;
            }
        } else {
            html += '<p style="color: #999;">No health conditions recorded</p>';
        }
        
        if (health.allergies && health.allergies.length > 0) {
            html += `<div class="patient-info-item"><span>Allergies:</span> <strong>${health.allergies.join(', ')}</strong></div>`;
        }
        
        if (health.food_preference) {
            const prefEmoji = health.food_preference === 'vegetarian' ? '🌱' : '🥘';
            html += `<div class="patient-info-item"><span>Food Preference:</span> <strong>${prefEmoji} ${health.food_preference}</strong></div>`;
        }
        
        html += '</div>';
        healthContainer.innerHTML = html;
    } else {
        healthContainer.innerHTML = '<p style="color: #999;">No health information available</p>';
    }
}

// Display patient recommendations
function displayPatientRecommendations(recoData) {
    const container = document.getElementById('patientRecommendationsContainer');
    container.innerHTML = '';

    // Support both legacy/lowercase and current/capitalized payload shapes.
    const food = recoData.food || recoData.Food || {};
    const drinks = recoData.drinks || recoData.Drinks || [];
    const snacks = recoData.snacks || recoData.Snacks || [];
    const avoidFoods = recoData.foods_to_avoid || recoData.foodsToAvoid || [];
    const healthyTips = recoData.healthy_tips || recoData.healthyTipsForToday || {};
    const getMealItems = (mealKeyLower, mealKeyUpper) => {
        if (Array.isArray(food[mealKeyLower])) return food[mealKeyLower];
        if (Array.isArray(food[mealKeyUpper])) return food[mealKeyUpper];
        return [];
    };

    const morningItems = getMealItems('morning', 'Morning');
    const afternoonItems = getMealItems('afternoon', 'Afternoon');
    const eveningItems = getMealItems('evening', 'Evening');
    const firstFoodItem = morningItems[0] || afternoonItems[0] || eveningItems[0] || null;

    const getItemName = (item) => {
        if (typeof item === 'string') return item;
        return item?.name || '-';
    };
    const getItemReason = (item) => {
        if (typeof item === 'string') return '';
        return item?.reason || '';
    };
    const getItemCost = (item) => {
        if (typeof item === 'string') return '';
        return item?.estimated_cost || '';
    };

    const normalizeAvoidFood = (name) => {
        const n = String(name || '').trim();
        const lower = n.toLowerCase();
        if (!lower) return '';

        if (lower.includes('fried') || lower.includes('deep-fried')) {
            return 'Fried & Deep-fried foods';
        }
        if (lower.includes('dairy')) {
            return 'Full-fat dairy products';
        }
        if (lower.includes('milk') || lower.includes('cheese') || lower.includes('butter') || lower.includes('paneer')) {
            return 'Milk, Cheese, Butter, Paneer (dairy)';
        }
        return n;
    };

    const dedupeAvoidFoods = (items) => {
        const normalized = [];
        const seen = new Set();
        (items || []).forEach((it) => {
            const raw = typeof it === 'string' ? it : (it?.name || '');
            const name = normalizeAvoidFood(raw);
            const key = name.toLowerCase();
            if (!name || seen.has(key)) return;
            seen.add(key);
            normalized.push(name);
        });
        return normalized;
    };

    const renderRecoItem = (item) => {
        const name = getItemName(item);
        const reason = getItemReason(item);
        const cost = getItemCost(item);
        return `
            <div class="recommendation-item">
                <div class="recommendation-item-name">${name}</div>
                ${cost ? `<div class="recommendation-item-cost"><strong>Estimated Cost:</strong> ${cost}</div>` : ''}
                ${reason ? `<div class="recommendation-item-reason">${reason}</div>` : ''}
            </div>
        `;
    };
    
    // Alert if present
    if (recoData.alert_message?.show) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.innerHTML = `
            <div class="alert-title">⚠️ Health Alert</div>
            <div>${recoData.alert_message.message}</div>
        `;
        container.appendChild(alertDiv);
    }
    
    // Food Section
    const foodSection = document.createElement('div');
    foodSection.className = 'recommendation-section';
    foodSection.innerHTML = `
        <div class="section-header" onclick="toggleSection(this)">
            <span>🍽️ Food Recommendations</span>
            <span class="expand-icon">▼</span>
        </div>
        <div class="section-content">
            <div id="recoFood"></div>
            <div class="alternatives-message">Alternative food options are available.</div>
            <button class="btn btn-secondary" style="margin-top: 10px;" onclick="loadAlternativesForCaretaker('food')">Show Alternatives</button>
            <div id="foodAlternativesContainer" style="margin-top: 10px;"></div>
        </div>
    `;
    container.appendChild(foodSection);
    
    // Display food items
    const foodContent = foodSection.querySelector('#recoFood');
    
    // Morning
    if (morningItems.length > 0) {
        const morningDiv = document.createElement('div');
        morningDiv.className = 'meal-category';
        morningDiv.innerHTML = '<h4>🌅 Breakfast</h4>';
        
        morningItems.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.innerHTML = renderRecoItem(item);
            morningDiv.appendChild(itemDiv.firstElementChild);
        });
        
        foodContent.appendChild(morningDiv);
    }
    
    // Afternoon
    if (afternoonItems.length > 0) {
        const afternoonDiv = document.createElement('div');
        afternoonDiv.className = 'meal-category';
        afternoonDiv.innerHTML = '<h4>☀️ Lunch</h4>';
        
        afternoonItems.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.innerHTML = renderRecoItem(item);
            afternoonDiv.appendChild(itemDiv.firstElementChild);
        });
        
        foodContent.appendChild(afternoonDiv);
    }
    
    // Evening
    if (eveningItems.length > 0) {
        const eveningDiv = document.createElement('div');
        eveningDiv.className = 'meal-category';
        eveningDiv.innerHTML = '<h4>🌙 Dinner</h4>';
        
        eveningItems.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.innerHTML = renderRecoItem(item);
            eveningDiv.appendChild(itemDiv.firstElementChild);
        });
        
        foodContent.appendChild(eveningDiv);
    }

    if (morningItems.length === 0 && afternoonItems.length === 0 && eveningItems.length === 0) {
        foodContent.innerHTML = '<p style="color: #777; font-style: italic;">Primary recommendation is unavailable right now. Please use alternatives below.</p>';
    }
    
    // Drinks Section
    const drinksSection = document.createElement('div');
    drinksSection.className = 'recommendation-section';
    drinksSection.innerHTML = `
        <div class="section-header" onclick="toggleSection(this)">
            <span>🥤 Drink Recommendations</span>
            <span class="expand-icon">▼</span>
        </div>
        <div class="section-content">
            <div id="recoDrinks"></div>
            <div class="alternatives-message">Alternative options are available.</div>
            <button class="btn btn-secondary" style="margin-top: 10px;" onclick="loadAlternativesForCaretaker('drinks')">Show Alternatives</button>
            <div id="drinkAlternativesContainer" style="margin-top: 10px;"></div>
        </div>
    `;
    container.appendChild(drinksSection);
    
    const drinksContent = drinksSection.querySelector('#recoDrinks');
    if (drinks && drinks.length > 0) {
        drinks.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.innerHTML = renderRecoItem(item);
            drinksContent.appendChild(itemDiv.firstElementChild);
        });
    } else {
        drinksContent.innerHTML = '<p style="color: #777; font-style: italic;">Primary recommendation is unavailable right now. Please use alternatives below.</p>';
    }
    
    // Snacks Section
    const snacksSection = document.createElement('div');
    snacksSection.className = 'recommendation-section';
    snacksSection.innerHTML = `
        <div class="section-header" onclick="toggleSection(this)">
            <span>🍿 Snack Recommendations</span>
            <span class="expand-icon">▼</span>
        </div>
        <div class="section-content">
            <div id="recoSnacks"></div>
            <div class="alternatives-message">Alternative options are available.</div>
            <button class="btn btn-secondary" style="margin-top: 10px;" onclick="loadAlternativesForCaretaker('snacks')">Show Alternatives</button>
            <div id="snackAlternativesContainer" style="margin-top: 10px;"></div>
        </div>
    `;
    container.appendChild(snacksSection);
    
    const snacksContent = snacksSection.querySelector('#recoSnacks');
    if (snacks && snacks.length > 0) {
        snacks.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.innerHTML = renderRecoItem(item);
            snacksContent.appendChild(itemDiv.firstElementChild);
        });
    } else {
        snacksContent.innerHTML = '<p style="color: #777; font-style: italic;">Primary recommendation is unavailable right now. Please use alternatives below.</p>';
    }

    // Foods to Avoid Section (current recommendation)
    const normalizedAvoidFoods = dedupeAvoidFoods(avoidFoods);
    if (normalizedAvoidFoods.length > 0) {
        const avoidSection = document.createElement('div');
        avoidSection.className = 'recommendation-section';
        avoidSection.innerHTML = `
            <div class="section-header" onclick="toggleSection(this)">
                <span>⚠️ Foods to Avoid</span>
                <span class="expand-icon">▼</span>
            </div>
            <div class="section-content">
                <ul id="avoidFoodsList" style="margin: 0; padding-left: 20px;"></ul>
            </div>
        `;
        container.appendChild(avoidSection);

        const avoidList = avoidSection.querySelector('#avoidFoodsList');
        normalizedAvoidFoods.forEach(name => {
            const li = document.createElement('li');
            li.textContent = name;
            li.style.marginBottom = '6px';
            avoidList.appendChild(li);
        });
    }

    // Keep references for alternatives lookup.
    window.__caretakerRecoRefs = {
        firstFoodItem,
        firstDrinkItem: drinks[0] || null,
        firstSnackItem: snacks[0] || null,
    };
    
    // Healthy Tips Section
    if (healthyTips && Object.keys(healthyTips).length > 0) {
        const tipsSection = document.createElement('div');
        tipsSection.className = 'card';
        tipsSection.innerHTML = '<div style="margin-bottom: 15px;"><h3 style="color: var(--primary-color);">💡 Healthy Tips</h3></div>';
        
        let tipsHtml = '';
        if (healthyTips.hydration) {
            tipsHtml += `<div class="tip-item"><span class="tip-icon">💧</span>${healthyTips.hydration}</div>`;
        }
        if (healthyTips.exercise) {
            tipsHtml += `<div class="tip-item"><span class="tip-icon">🏃</span>${healthyTips.exercise}</div>`;
        }
        if (healthyTips.sleep) {
            tipsHtml += `<div class="tip-item"><span class="tip-icon">😴</span>${healthyTips.sleep}</div>`;
        }
        if (healthyTips.specific) {
            tipsHtml += `<div class="tip-item"><span class="tip-icon">⚕️</span>${healthyTips.specific}</div>`;
        }
        
        tipsSection.innerHTML += tipsHtml;
        container.appendChild(tipsSection);
    }
}

async function loadAlternativesForCaretaker(category) {
    const token = localStorage.getItem('token');
    if (!token || !currentPatientId) {
        showAlert('Select a patient first.', 'danger');
        return;
    }

    const refs = window.__caretakerRecoRefs || {};
    let item = null;
    let targetContainerId = 'foodAlternativesContainer';
    if (category === 'drinks') {
        item = refs.firstDrinkItem;
        targetContainerId = 'drinkAlternativesContainer';
    } else if (category === 'snacks') {
        item = refs.firstSnackItem;
        targetContainerId = 'snackAlternativesContainer';
    } else {
        item = refs.firstFoodItem;
    }

    const target = document.getElementById(targetContainerId);
    if (!target) return;
    target.innerHTML = '<p style="color:#666;">Loading alternatives...</p>';

    try {
        const body = {
            category,
            patient_id: currentPatientId,
            food_name: item?.name || '',
            food_cost: item?.estimated_cost || ''
        };

        const response = await fetch(`${API_BASE_URL}/recommendations/alternatives`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        if (!response.ok) {
            target.innerHTML = `<p style="color:#d9534f;">${data.error || 'Failed to load alternatives'}</p>`;
            return;
        }

        const alternatives = data.alternatives || [];
        if (alternatives.length === 0) {
            target.innerHTML = '<p style="color:#999; font-style:italic;">No alternatives available</p>';
            return;
        }

        target.innerHTML = alternatives.map((alt) => `
            <div class="recommendation-item" style="margin-top:8px; border-left: 4px solid #2e7d32;">
                <div class="recommendation-item-name">${alt.name}</div>
                <div class="recommendation-item-reason">${alt.reason}</div>
                ${alt.estimated_cost ? `<div class="recommendation-item-reason"><strong>Estimated Cost:</strong> ${alt.estimated_cost}</div>` : ''}
            </div>
        `).join('');
    } catch (error) {
        target.innerHTML = `<p style="color:#d9534f;">${error.message}</p>`;
    }
}

// Section toggle functionality
function toggleSection(headerElement) {
    const header = headerElement;
    const content = headerElement.parentElement.querySelector('.section-content');
    const icon = headerElement.querySelector('.expand-icon');
    
    content.classList.toggle('collapsed');
    icon.classList.toggle('rotated');
}

// Logout function
function logout() {
    localStorage.clear();
    window.location.href = '../index.html';
}

// Search patients function
async function searchPatients() {
    const searchTerm = document.getElementById('patientSearch').value.trim();
    
    if (!searchTerm) {
        document.getElementById('searchResultsContainer').style.display = 'none';
        return;
    }
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/caretaker/search-patients?query=${encodeURIComponent(searchTerm)}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            showAlert(errorData.error || 'Search failed', 'danger');
            return;
        }
        
        const results = await response.json();
        displaySearchResults(results);
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    }
}

// Display recommendation history
function displayRecommendationHistory(recommendations) {
    const container = document.getElementById('patientRecommendationsContainer');
    
    if (!recommendations || recommendations.length === 0) {
        return; // No history to display
    }
    
    // Helper to deduplicate and clean avoid foods list
    function deduplicateAvoidFoods(foodsList) {
        if (!foodsList || foodsList.length === 0) return [];
        
        // Extract names and normalize
        const seen = new Set();
        const unique = [];
        
        for (const food of foodsList) {
            const name = typeof food === 'string' ? food : food.name || '';
            if (name && !seen.has(name.toLowerCase())) {
                seen.add(name.toLowerCase());
                unique.push(name);
            }
        }
        
        // Sort for consistent display
        return unique.sort();
    }
    
    // Add history section
    const historySection = document.createElement('div');
    historySection.className = 'recommendation-section';
    historySection.style.marginTop = '30px';
    historySection.innerHTML = `
        <div class="section-header" onclick="toggleSection(this)">
            <span>📋 Recommendation History</span>
            <span class="expand-icon">▼</span>
        </div>
        <div class="section-content">
            <div id="historyList" style="max-height: 400px; overflow-y: auto;"></div>
        </div>
    `;
    container.appendChild(historySection);
    
    const historyList = historySection.querySelector('#historyList');
    recommendations.forEach((rec, idx) => {
        const date = new Date(rec.created_at).toLocaleString();
        const recDiv = document.createElement('div');
        recDiv.style.cssText = 'padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 10px; background-color: #fafafa;';
        
        let foodsHtml = '';
        
        // Helper to format meal items with cost
        const formatMealItem = (item) => {
            if (typeof item === 'string') return item;
            const name = item.name || item;
            const cost = item.estimated_cost ? ` (${item.estimated_cost})` : '';
            return name + cost;
        };
        
        if (rec.breakfast && rec.breakfast.length > 0) {
            foodsHtml += `<div><strong>🌅 Breakfast:</strong> ${rec.breakfast.map(f => formatMealItem(f)).join(', ')}</div>`;
        }
        if (rec.lunch && rec.lunch.length > 0) {
            foodsHtml += `<div><strong>☀️ Lunch:</strong> ${rec.lunch.map(f => formatMealItem(f)).join(', ')}</div>`;
        }
        if (rec.dinner && rec.dinner.length > 0) {
            foodsHtml += `<div><strong>🌙 Dinner:</strong> ${rec.dinner.map(f => formatMealItem(f)).join(', ')}</div>`;
        }
        if (rec.drinks && rec.drinks.length > 0) {
            foodsHtml += `<div><strong>🥤 Drinks:</strong> ${rec.drinks.map(f => formatMealItem(f)).join(', ')}</div>`;
        }
        if (rec.snacks && rec.snacks.length > 0) {
            foodsHtml += `<div><strong>🍿 Snacks:</strong> ${rec.snacks.map(f => formatMealItem(f)).join(', ')}</div>`;
        }
        
        const typeBadge = '🤖 Recommender'; // all recommendations now LLM-based
        
        // Format avoid foods as bullet list
        const avoidsArray = deduplicateAvoidFoods(rec.foods_to_avoid || []);
        const avoidsHtml = avoidsArray.length > 0 
            ? `<div style="color: #d9534f; margin-top: 8px;"><strong>⚠️ Foods to Avoid:</strong><ul style="margin: 5px 0; padding-left: 20px;">${avoidsArray.map(f => `<li>${f}</li>`).join('')}</ul></div>`
            : '';
        
        recDiv.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div><strong>${typeBadge}</strong></div>
                <div style="font-size: 0.9em; color: #999;">📅 ${date}</div>
            </div>
            ${foodsHtml}
            ${avoidsHtml}
        `;
        
        historyList.appendChild(recDiv);
    });
}

// Display search results
function displaySearchResults(results) {
    const container = document.getElementById('searchResultsContainer');
    const resultsList = document.getElementById('searchResultsList');
    
    if (!results || results.length === 0) {
        resultsList.innerHTML = '<p style="color: #999; font-style: italic;">No patients found.</p>';
        container.style.display = 'block';
        return;
    }
    
    resultsList.innerHTML = '';
    results.forEach(patient => {
        const resultDiv = document.createElement('div');
        resultDiv.style.cssText = 'padding: 10px; border-bottom: 1px solid #e0e0e0; cursor: pointer; border-radius: 4px; transition: background-color 0.2s;';
        resultDiv.onmouseover = () => resultDiv.style.backgroundColor = '#e8f4ff';
        resultDiv.onmouseout = () => resultDiv.style.backgroundColor = 'transparent';
        
        resultDiv.innerHTML = `
            <div style="font-weight: 600; color: #0066cc;">${patient.name}</div>
            <div style="font-size: 0.9em; color: #666;">📧 ${patient.email}</div>
        `;
        
        resultDiv.onclick = () => selectPatient(patient._id);
        resultsList.appendChild(resultDiv);
    });
    
    container.style.display = 'block';
}

// Show alert message
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.padding = '15px 20px';
    alert.style.borderRadius = '8px';
    alert.style.zIndex = '9999';
    alert.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    alert.style.minWidth = '300px';
    
    if (type === 'danger') {
        alert.style.background = '#f8d7da';
        alert.style.color = '#721c24';
        alert.style.border = '1px solid #f5c6cb';
    } else if (type === 'success') {
        alert.style.background = '#d4edda';
        alert.style.color = '#155724';
        alert.style.border = '1px solid #c3e6cb';
    } else {
        alert.style.background = '#d1ecf1';
        alert.style.color = '#0c5460';
        alert.style.border = '1px solid #bee5eb';
    }
    
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// Select patient from search results
function selectPatient(patientId) {
    document.getElementById('searchResultsContainer').style.display = 'none';
    document.getElementById('patientSearch').value = '';
    loadPatientData(patientId);
}
