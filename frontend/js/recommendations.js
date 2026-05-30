// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let currentRating = 0;
let userAllergies = []; // Store user allergies globally
let fetchedAlternatives = {
    food: [],
    drinks: [],
    snacks: []
}; // Store fetched alternatives globally
let latestRecommendations = {
    food: [],
    drinks: [],
    snacks: []
};

function parseCostMidpoint(costText) {
    if (!costText || typeof costText !== 'string') return 0;
    const nums = costText.match(/\d+/g);
    if (!nums || nums.length === 0) return 0;
    if (nums.length === 1) return Number(nums[0]);
    return (Number(nums[0]) + Number(nums[1])) / 2;
}

function chooseBaseItem(type) {
    const items = latestRecommendations[type] || [];
    if (!Array.isArray(items) || items.length === 0) {
        return { name: '', estimated_cost: '' };
    }

    let best = items[0];
    let bestCost = parseCostMidpoint(best.estimated_cost || '');

    items.forEach((item) => {
        const c = parseCostMidpoint(item && item.estimated_cost ? item.estimated_cost : '');
        if (c > bestCost) {
            best = item;
            bestCost = c;
        }
    });

    return {
        name: (best && best.name) || '',
        estimated_cost: (best && best.estimated_cost) || ''
    };
}

// Check authentication and load recommendations
window.addEventListener('load', async () => {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (!token || userType !== 'patient') {
        window.location.href = '../index.html';
        return;
    }
    
    // Load user allergies first
    await loadUserAllergies();
    renderAllergyMessages();
    await loadRecommendations();
});

// Load user allergies from API
async function loadUserAllergies() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/patient/health-information`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        userAllergies = data.allergies && Array.isArray(data.allergies) ? data.allergies : [];
    } catch (error) {
        console.error('Error loading allergies:', error);
        userAllergies = [];
    }
}

// Load recommendations from API
async function loadRecommendations() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/recommendations/get`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        console.log('API Response:', data); // debug output so we can inspect structure
        // expose for debugging/testing
        try { window._lastRecommendation = data; } catch (e) {};
        
        if (!response.ok) {
            showAlert(data.error || 'Failed to load recommendations', 'danger');
            return;
        }
        
        // Display alert if health conditions are critical
        if (data.alert_message?.show) {
            showAlert(data.alert_message.message, 'danger');
        }
        
        // Back-end returns Food/Drinks/Snacks keys with uppercase names; provide safe defaults
        let foodData = data.Food || data.food || { morning: [], afternoon: [], evening: [] };
        // accomodate old responses that used lunch/dinner naming
        if (foodData.lunch && !foodData.afternoon) {
            foodData.afternoon = foodData.lunch;
        }
        if (foodData.dinner && !foodData.evening) {
            foodData.evening = foodData.dinner;
        }
        // if backend returned an array by mistake treat it as morning list
        if (Array.isArray(foodData)) {
            console.warn('foodData was array, converting to object');
            foodData = { morning: foodData, afternoon: [], evening: [] };
        }
        const drinkData = data.Drinks || data.drinks || [];
        const snackData = data.Snacks || data.snacks || [];
        const avoidData = data.foods_to_avoid || data.foodsToAvoid || [];
        const tipsData = data.healthyTipsForToday || data.healthy_tips || {};

        latestRecommendations.food = [
            ...(foodData.morning || []),
            ...(foodData.afternoon || []),
            ...(foodData.evening || [])
        ];
        latestRecommendations.drinks = drinkData || [];
        latestRecommendations.snacks = snackData || [];

        displayFoodRecommendations(foodData);
        displayAvoidRecommendations(avoidData);
        displayDrinkRecommendations(drinkData);
        displaySnackRecommendations(snackData);
        displayHealthyTips(tipsData);
        displayHealthSummary();

        // show inline alternatives immediately so they are always visible
        // under the food recommendations.
        await loadInlineAlternatives();

        // **new behavior:** automatically expand the food alternatives so they
        // are visible without requiring the user to click the toggle button.
        // Previously we auto‑expanded all three categories, which resulted in
        // multiple network hits; caching now prevents duplicates but there's
        // no need to fetch drinks/snacks until the user asks.
        toggleAlternatives('food');
        // users can click to reveal drinks/snacks when desired
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    }
}

// Fetch AI-powered recommendations via server-side Gemini integration
async function fetchAIRecommendations() {
    const token = localStorage.getItem('token');
    const aiButton = document.querySelector('.navbar-menu .btn-primary');
    try {
        if (aiButton) {
            aiButton.disabled = true;
            aiButton.textContent = 'Loading...';
        }

        showAlert('Fetching AI recommendations...', 'info');

        const response = await fetch(`${API_BASE_URL}/recommendations/genai`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        if (!response.ok) {
            showAlert(data.error || 'Failed to fetch AI recommendations', 'danger');
            if (aiButton) {
                aiButton.disabled = false;
                aiButton.textContent = 'Use GenAI';
            }
            return;
        }

        // If doctorAlert present, show prominently
        if (data.doctorAlert) {
            showAlert(data.doctorAlert, 'danger');
        }

        // Map GenAI structure to existing UI functions
        const foodData = {
            morning: data.Food?.Morning || [],
            afternoon: data.Food?.Afternoon || [],
            evening: data.Food?.Evening || []
        };
        const avoidData = data.foods_to_avoid || [];

        displayFoodRecommendations(foodData);
        displayAvoidRecommendations(avoidData);
        displayDrinkRecommendations(data.Drinks || []);
        displaySnackRecommendations(data.Snacks || []);
        displayHealthyTips(data.healthyTipsForToday || {});

        // Update alternatives fixed text
        document.querySelectorAll('.alternatives-message').forEach(el => {
            el.textContent = '💡 ' + (data.alternativeMessage || 'Alternative food options are available.');
        });

        showAlert('AI recommendations loaded', 'success');
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        if (aiButton) {
            aiButton.disabled = false;
            aiButton.textContent = 'Use GenAI';
        }
    }
}


// Display food recommendations (with meals)
function displayFoodRecommendations(foodData) {
    const container = document.getElementById('foodContent');
    container.innerHTML = '';
    
    // Morning
    const morningDiv = document.createElement('div');
    morningDiv.className = 'meal-category';
    morningDiv.innerHTML = '<h4>🌅 Breakfast</h4>';
    
    if (foodData.morning && foodData.morning.length > 0) {
        foodData.morning.forEach(item => {
            const name = typeof item === 'string' ? item : (item && item.name) || '';
            const reason = item && typeof item === 'object' ? item.reason || '' : '';
            const estimatedCost = item && typeof item === 'object' ? item.estimated_cost || '' : '';
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${name}</div>
                <div class="recommendation-item-reason">${reason}</div>
                ${estimatedCost ? `<div class="recommendation-item-cost">Estimated Cost: ${estimatedCost}</div>` : ''}
            `;
            morningDiv.appendChild(itemDiv);
        });
    } else {
        morningDiv.innerHTML += '<p style="color: #999; font-style: italic;">No recommendations available</p>';
    }
    container.appendChild(morningDiv);
    
    // Afternoon
    const afternoonDiv = document.createElement('div');
    afternoonDiv.className = 'meal-category';
    afternoonDiv.innerHTML = '<h4>☀️ Lunch</h4>';
    
    if (foodData.afternoon && foodData.afternoon.length > 0) {
        foodData.afternoon.forEach(item => {
            const name = typeof item === 'string' ? item : (item && item.name) || '';
            const reason = item && typeof item === 'object' ? item.reason || '' : '';
            const estimatedCost = item && typeof item === 'object' ? item.estimated_cost || '' : '';
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${name}</div>
                <div class="recommendation-item-reason">${reason}</div>
                ${estimatedCost ? `<div class="recommendation-item-cost">Estimated Cost: ${estimatedCost}</div>` : ''}
            `;
            afternoonDiv.appendChild(itemDiv);
        });
    } else {
        afternoonDiv.innerHTML += '<p style="color: #999; font-style: italic;">No recommendations available</p>';
    }
    container.appendChild(afternoonDiv);
    
    // Evening
    const eveningDiv = document.createElement('div');
    eveningDiv.className = 'meal-category';
    eveningDiv.innerHTML = '<h4>🌙 Dinner</h4>';
    
    if (foodData.evening && foodData.evening.length > 0) {
        foodData.evening.forEach(item => {
            const name = typeof item === 'string' ? item : (item && item.name) || '';
            const reason = item && typeof item === 'object' ? item.reason || '' : '';
            const estimatedCost = item && typeof item === 'object' ? item.estimated_cost || '' : '';
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${name}</div>
                <div class="recommendation-item-reason">${reason}</div>
                ${estimatedCost ? `<div class="recommendation-item-cost">Estimated Cost: ${estimatedCost}</div>` : ''}
            `;
            eveningDiv.appendChild(itemDiv);
        });
    } else {
        eveningDiv.innerHTML += '<p style="color: #999; font-style: italic;">No recommendations available</p>';
    }
    container.appendChild(eveningDiv);
}

// Display drink recommendations (no meal divisions)

function displayAvoidRecommendations(avoidData) {
    const container = document.getElementById('avoidContent');
    if (!container) return;
    container.innerHTML = '';
    const header = document.createElement('h4');
    header.textContent = '🚫 Foods to Avoid';
    container.appendChild(header);

    if (avoidData && avoidData.length > 0) {
        avoidData.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item avoid-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${item.name}</div>
                <div class="recommendation-item-reason">${item.reason}</div>
            `;
            container.appendChild(itemDiv);
        });
    } else {
        container.innerHTML += '<p style="color: #999; font-style: italic;">No foods to avoid</p>';
    }
}

function renderAllergyMessages() {
    const container = document.getElementById('allergyMessages');
    if (!container) return;

    container.innerHTML = '';
    if (!userAllergies || userAllergies.length === 0) {
        const item = document.createElement('div');
        item.className = 'allergy-message-item';
        item.textContent = 'No allergy restrictions found in your profile.';
        container.appendChild(item);
        return;
    }

    userAllergies.forEach((allergy) => {
        const item = document.createElement('div');
        item.className = 'allergy-message-item';
        item.textContent = `Allergy alert: foods containing ${allergy} are excluded from your plan.`;
        container.appendChild(item);
    });
}

function displayDrinkRecommendations(drinksData) {
    const container = document.getElementById('drinksContent');
    container.innerHTML = '';

    const header = document.createElement('h4');
    header.textContent = '🥤 Drinks';
    container.appendChild(header);
    
    if (drinksData && drinksData.length > 0) {
        drinksData.forEach(item => {
            const name = typeof item === 'string' ? item : (item && item.name) || '';
            const reason = item && typeof item === 'object' ? item.reason || '' : '';
            const estimatedCost = item && typeof item === 'object' ? item.estimated_cost || '' : '';
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${name}</div>
                <div class="recommendation-item-reason">${reason}</div>
                ${estimatedCost ? `<div class="recommendation-item-cost">Estimated Cost: ${estimatedCost}</div>` : ''}
            `;
            container.appendChild(itemDiv);
        });
    } else {
        container.innerHTML = '<p style="color: #999; font-style: italic;">No recommendations available</p>';
    }
}

// Display snack recommendations (no meal divisions)
function displaySnackRecommendations(snacksData) {
    const container = document.getElementById('snacksContent');
    container.innerHTML = '';

    const header = document.createElement('h4');
    header.textContent = '🍿 Snacks';
    container.appendChild(header);
    
    if (snacksData && snacksData.length > 0) {
        snacksData.forEach(item => {
            const name = typeof item === 'string' ? item : (item && item.name) || '';
            const reason = item && typeof item === 'object' ? item.reason || '' : '';
            const estimatedCost = item && typeof item === 'object' ? item.estimated_cost || '' : '';
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${name}</div>
                <div class="recommendation-item-reason">${reason}</div>
                ${estimatedCost ? `<div class="recommendation-item-cost">Estimated Cost: ${estimatedCost}</div>` : ''}
            `;
            container.appendChild(itemDiv);
        });
    } else {
        container.innerHTML = '<p style="color: #999; font-style: italic;">No recommendations available</p>';
    }
}

// Display healthy tips
function displayHealthyTips(tipsData) {
    const container = document.getElementById('tipsContent');
    container.innerHTML = '';
    
    const tips = [];
    
    // Add general tips
    if (tipsData.hydration) {
        tips.push({ icon: '💧', text: tipsData.hydration });
    }
    
    if (tipsData.exercise) {
        tips.push({ icon: '🏃', text: tipsData.exercise });
    }
    
    if (tipsData.sleep) {
        tips.push({ icon: '😴', text: tipsData.sleep });
    }
    
    if (tipsData.specific) {
        tips.push({ icon: '⚕️', text: tipsData.specific });
    }
    
    tips.forEach(tip => {
        const tipDiv = document.createElement('div');
        tipDiv.className = 'tip-item';
        // convert newline characters to <br> for display
        const safeText = tip.text.replace(/\n/g, '<br>');
        tipDiv.innerHTML = `<span class="tip-icon">${tip.icon}</span>${safeText}`;
        container.appendChild(tipDiv);
    });
}

// Display health summary
async function displayHealthSummary() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/patient/health-information`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        const container = document.getElementById('healthSummary');
        container.innerHTML = '';
        
        if (data.health_conditions && Object.keys(data.health_conditions).length > 0) {
            let html = '';
            
            if (data.health_conditions.diabetes) {
                html += `<div class="patient-info-item"><span>Glucose:</span> <strong>${data.health_conditions.diabetes} mg/dL</strong></div>`;
            }
            
            if (data.health_conditions.blood_pressure) {
                html += `<div class="patient-info-item"><span>BP:</span> <strong>${data.health_conditions.blood_pressure} mmHg</strong></div>`;
            }
            
            if (data.health_conditions.cholesterol) {
                html += `<div class="patient-info-item"><span>Cholesterol:</span> <strong>${data.health_conditions.cholesterol} mg/dL</strong></div>`;
            }
            
            if (data.health_conditions.obesity_bmi) {
                html += `<div class="patient-info-item"><span>BMI:</span> <strong>${data.health_conditions.obesity_bmi}</strong></div>`;
            }
            
            if (data.allergies && data.allergies.length > 0) {
                html += `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color);"><strong>Allergies:</strong> ${data.allergies.join(', ')}</div>`;
            }
            
            if (data.food_preference) {
                html += `<div class="patient-info-item"><span>Preference:</span> <strong>${data.food_preference === 'vegetarian' ? '🌱 Vegetarian' : '🥘 Non-Vegetarian'}</strong></div>`;
            }
            
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: #999;">No health information provided</p>';
        }
    } catch (error) {
        console.error('Error loading health summary:', error);
    }
}

// Section toggle functionality
function toggleSection(headerElement) {
    const header = headerElement;
    const content = headerElement.parentElement.querySelector('.section-content');
    const icon = headerElement.querySelector('.expand-icon');

    const isExpanded = content.getAttribute('data-expanded') !== 'false';
    if (isExpanded) {
        content.classList.add('collapsed');
        content.setAttribute('data-expanded', 'false');
        header.classList.add('collapsed');
    } else {
        content.classList.remove('collapsed');
        content.setAttribute('data-expanded', 'true');
        header.classList.remove('collapsed');
    }

    icon.classList.toggle('rotated', content.getAttribute('data-expanded') === 'false');
}

// Rating system
function setRating(rating) {
    currentRating = rating;
    document.getElementById('ratingValue').value = rating;
    
    const stars = document.querySelectorAll('#ratingStars .star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
            star.style.color = '#ffc107';
        } else {
            star.classList.remove('active');
            star.style.color = 'inherit';
        }
    });
}

// Feedback submission is handled on a separate page (`feedback.html`).
// Guard any leftover listener attachment to avoid errors when `feedbackForm` is absent.
const _feedbackFormEl = document.getElementById('feedbackForm');
if (_feedbackFormEl) {
    _feedbackFormEl.addEventListener('submit', async (e) => {
        e.preventDefault();

        const rating = parseInt(document.getElementById('ratingValue').value);
        const comment = document.getElementById('feedbackComment').value;
        const token = localStorage.getItem('token');

        if (!rating) {
            alert('Please select a rating');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/feedback/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    rating,
                    comment,
                    recommendation_type: 'general'
                })
            });

            const data = await response.json();

            if (!response.ok) {
                alert('Error: ' + data.error);
                return;
            }

            // Reset form
            _feedbackFormEl.reset();
            document.querySelectorAll('#ratingStars .star').forEach(star => {
                star.classList.remove('active');
                star.style.color = 'inherit';
            });
            document.getElementById('ratingValue').value = '';
            currentRating = 0;

            showAlert('Thank you for your feedback!', 'success');
        } catch (error) {
            alert('Error submitting feedback: ' + error.message);
        }
    });
}

// Alert display function
function showAlert(message, type = 'info') {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    
    const title = type === 'danger' ? '⚠️ Alert' : type === 'success' ? '✓ Success' : 'ℹ️ Info';
    alert.innerHTML = `
        <div class="alert-title">${title}</div>
        <div>${message}</div>
    `;
    
    container.innerHTML = '';
    container.appendChild(alert);
    
    if (type === 'success') {
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Fetch alternatives from API
async function fetchAlternativesFromAPI(type) {
    // avoid re-fetching if we've already retrieved items for this category
    if (fetchedAlternatives[type] && fetchedAlternatives[type].length > 0) {
        return fetchedAlternatives[type];
    }

    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/recommendations/alternatives`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            
            body: JSON.stringify({
                category: type === 'food' ? 'food' : type === 'drinks' ? 'drinks' : 'snacks',
                food_name: chooseBaseItem(type).name,
                food_cost: chooseBaseItem(type).estimated_cost
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showAlert('Failed to load alternatives: ' + (data.error || 'Unknown error'), 'warning');
            return [];
        }
        
        // Store fetched alternatives for use in applyAlternatives
        const alternatives = data.alternatives || [];
        fetchedAlternatives[type] = alternatives;
        
        return alternatives;
    } catch (error) {
        console.error('Error fetching alternatives:', error);
        showAlert('Error loading alternatives: ' + error.message, 'warning');
        return [];
    }
}

// Load and display alternatives inline (never hidden)
async function loadInlineAlternatives() {
    const items = await fetchAlternativesFromAPI('food');
    const container = document.getElementById('foodContent');
    if (!container) return;

    if (items.length === 0) {
        return; // nothing to show
    }

    // add a header for the inline alternatives
    const header = document.createElement('h4');
    header.textContent = '🔁 Alternatives';
    container.appendChild(header);

    items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'recommendation-item alternative-item';
        itemDiv.innerHTML = `
            <div class="recommendation-item-name">${item.name}</div>
            <div class="recommendation-item-reason">${item.reason}</div>
            ${item.estimated_cost ? `<div class="recommendation-item-cost">Estimated Cost: ${item.estimated_cost}</div>` : ''}
        `;
        container.appendChild(itemDiv);
    });
}

// Toggle Alternative Display (fetch from API)
function toggleAlternatives(type) {
    const altContent = document.getElementById(`${type}Alternatives`);
    const altText = document.getElementById(`${type}AltText`);
    
    if (altContent.style.display === 'none' || altContent.style.display === '') {
        // Show alternatives
        altContent.style.display = 'block';
        altText.textContent = 'Hide Alternatives';
        
        // Populate alternatives if empty
        if (altContent.innerHTML === '') {
            altContent.innerHTML = '<p style="color: #999; font-style: italic; grid-column: 1/-1; text-align: center;">Loading alternatives...</p>';
            
            // Fetch from API
            fetchAlternativesFromAPI(type).then(items => {
                if (items.length === 0) {
                    altContent.innerHTML = '<p style="color: #999; font-style: italic; grid-column: 1/-1;">No alternatives available.</p>';
                } else {
                    const itemsHTML = items.map(item => `
                        <div class="recommendation-item alternative-item">
                            <div class="item-name">${item.name}</div>
                            <div class="item-reason">${item.reason}</div>
                            ${item.estimated_cost ? `<div class="recommendation-item-cost">Estimated Cost: ${item.estimated_cost}</div>` : ''}
                        </div>
                    `).join('');
                    
                    const applyBtn = `<div style="grid-column: 1/-1; text-align:center; margin-top:10px;"><button class="btn btn-primary btn-sm" onclick="applyAlternatives('${type}')">Apply Alternatives for ${type}</button></div>`;
                    altContent.innerHTML = itemsHTML + applyBtn;
                }
            });
        }
    } else {
        // Hide alternatives
        altContent.style.display = 'none';
        altText.textContent = 'Show Alternatives';
    }
}

// Apply alternatives as the active recommendations for a type
function applyAlternatives(type) {
    // Use fetched alternatives from API
    const items = fetchedAlternatives[type] || [];
    
    if (items.length === 0) {
        showAlert('No alternatives available to apply.', 'warning');
        return;
    }
    
    if (type === 'food') {
        // Replace the main foodContent with alternatives grouped into meals
        const container = document.getElementById('foodContent');
        container.innerHTML = '';
        const morningDiv = document.createElement('div');
        morningDiv.className = 'meal-category';
        morningDiv.innerHTML = '<h4>🌅 Breakfast</h4>';
        const afternoonDiv = document.createElement('div');
        afternoonDiv.className = 'meal-category';
        afternoonDiv.innerHTML = '<h4>☀️ Lunch</h4>';
        const eveningDiv = document.createElement('div');
        eveningDiv.className = 'meal-category';
        eveningDiv.innerHTML = '<h4>🌙 Dinner</h4>';

        // Simple distribution across meals
        items.forEach((item, idx) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${item.name}</div>
                <div class="recommendation-item-reason">${item.reason}</div>
                ${item.estimated_cost ? `<div class="recommendation-item-cost">Estimated Cost: ${item.estimated_cost}</div>` : ''}
            `;
            if (idx % 3 === 0) morningDiv.appendChild(itemDiv);
            else if (idx % 3 === 1) afternoonDiv.appendChild(itemDiv);
            else eveningDiv.appendChild(itemDiv);
        });

        container.appendChild(morningDiv);
        container.appendChild(afternoonDiv);
        container.appendChild(eveningDiv);
    } else if (type === 'drinks') {
        const container = document.getElementById('drinksContent');
        container.innerHTML = '';
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${item.name}</div>
                <div class="recommendation-item-reason">${item.reason}</div>
                ${item.estimated_cost ? `<div class="recommendation-item-cost">Estimated Cost: ${item.estimated_cost}</div>` : ''}
            `;
            container.appendChild(itemDiv);
        });
    } else if (type === 'snacks') {
        const container = document.getElementById('snacksContent');
        container.innerHTML = '';
        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-item-name">${item.name}</div>
                <div class="recommendation-item-reason">${item.reason}</div>
                ${item.estimated_cost ? `<div class="recommendation-item-cost">Estimated Cost: ${item.estimated_cost}</div>` : ''}
            `;
            container.appendChild(itemDiv);
        });
    }
    // Close the alternatives section after applying
    const altContent = document.getElementById(`${type}Alternatives`);
    const altText = document.getElementById(`${type}AltText`);
    if (altContent) {
        altContent.style.display = 'none';
    }
    if (altText) altText.textContent = 'Show Alternatives';
    showAlert('Alternative options applied to ' + type, 'success');
}

// Navigation functions
function goToHealth() {
    window.location.href = 'health-information.html';
}

function goToFeedback() {
    window.location.href = 'feedback.html';
}

function logout() {
    localStorage.clear();
    window.location.href = '../index.html';
}
