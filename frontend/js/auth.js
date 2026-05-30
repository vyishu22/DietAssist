// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Modal Functions
function showPatientLogin() {
    document.getElementById('patientLoginModal').classList.add('show');
}

function showPatientRegister() {
    document.getElementById('patientRegisterModal').classList.add('show');
}

function showCaretakerLogin() {
    document.getElementById('caretakerLoginModal').classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
    // Reset form
    const form = document.querySelector(`#${modalId} form`);
    if (form) form.reset();
}

function switchModal(closeModalId, openModalId) {
    closeModal(closeModalId);
    setTimeout(() => {
        document.getElementById(openModalId).classList.add('show');
    }, 300);
}

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('show');
    }
});

// Patient Login Handler
document.getElementById('patientLoginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/patient/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showError('Login failed: ' + data.error);
            return;
        }
        
        // Store token and user info
        localStorage.setItem('token', data.token);
        localStorage.setItem('userId', data.user_id);
        localStorage.setItem('userType', 'patient');
        localStorage.setItem('userName', data.name);
        
        // Redirect to health information page
        window.location.href = 'pages/health-information.html';
    } catch (error) {
        showError('Error: ' + error.message);
    }
});

// Patient Register Handler
document.getElementById('patientRegisterForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('regName').value;
    const age = document.getElementById('regAge').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/patient/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, age, email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showError('Registration failed: ' + data.error);
            return;
        }
        
        // Store token and user info
        localStorage.setItem('token', data.token);
        localStorage.setItem('userId', data.user_id);
        localStorage.setItem('userType', 'patient');
        localStorage.setItem('userName', data.name);
        
        // Redirect to health information page
        window.location.href = 'pages/health-information.html';
    } catch (error) {
        showError('Error: ' + error.message);
    }
});

// Caretaker Login Handler
document.getElementById('caretakerLoginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('caretakerLoginEmail').value;
    const password = document.getElementById('caretakerLoginPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/caretaker/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showError('Login failed: ' + data.error);
            return;
        }
        
        // Store token and user info
        localStorage.setItem('token', data.token);
        localStorage.setItem('caretakerId', data.caretaker_id);
        localStorage.setItem('userType', 'caretaker');
        localStorage.setItem('caretakerName', data.name);
        localStorage.setItem('caretakerRole', data.role);
        
        // Redirect to caretaker dashboard
        window.location.href = 'pages/caretaker-dashboard.html';
    } catch (error) {
        showError('Error: ' + error.message);
    }
});

// Caretaker Register Handler
document.getElementById('caretakerRegisterForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('caretakerRegName').value;
    const email = document.getElementById('caretakerRegEmail').value;
    const role = document.getElementById('caretakerRegRole').value;
    const password = document.getElementById('caretakerRegPassword').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/caretaker/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, role, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showError('Registration failed: ' + data.error);
            return;
        }
        
        // Store token and user info
        localStorage.setItem('token', data.token);
        localStorage.setItem('caretakerId', data.caretaker_id);
        localStorage.setItem('userType', 'caretaker');
        localStorage.setItem('caretakerName', data.name);
        localStorage.setItem('caretakerRole', data.role);
        
        // Redirect to caretaker dashboard
        window.location.href = 'pages/caretaker-dashboard.html';
    } catch (error) {
        showError('Error: ' + error.message);
    }
});

// Error notification - with visual feedback
function showError(message) {
    const alert = document.createElement('div');
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.background = '#f8d7da';
    alert.style.color = '#721c24';
    alert.style.padding = '15px 20px';
    alert.style.borderRadius = '8px';
    alert.style.zIndex = '9999';
    alert.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// Previously supported a clear-session button on the landing page, now removed.
// The auto-redirect logic at load handles existing tokens, so manual clearing is
// no longer necessary.  This function is kept for compatibility if ever needed.
function clearSession() {
    localStorage.clear();
    location.reload();
}

// Check if user is already logged in and redirect accordingly
window.addEventListener('load', () => {
    // Only redirect if on landing page (index.html)
    const currentPage = window.location.pathname;
    if (!currentPage.includes('index.html') && !currentPage.endsWith('/')) {
        return; // Don't auto-redirect if already on another page
    }
    
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('userType');
    
    if (token && userType === 'patient') {
        window.location.href = 'pages/health-information.html';
    } else if (token && userType === 'caretaker') {
        window.location.href = 'pages/caretaker-dashboard.html';
    }
});
