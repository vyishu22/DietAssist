// Feedback page script
const API_BASE_URL = 'http://localhost:5000/api';

// Simple alert helper (page-local)
function showAlert(message, type = 'info') {
    const existing = document.getElementById('pageAlert');
    if (existing) existing.remove();
    const alert = document.createElement('div');
    alert.id = 'pageAlert';
    alert.className = `alert alert-${type}`;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = 9999;
    alert.style.padding = '12px 18px';
    alert.style.borderRadius = '8px';
    alert.style.boxShadow = '0 6px 18px rgba(0,0,0,0.08)';
    alert.style.background = type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1';
    alert.style.color = type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460';
    alert.textContent = message;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 4000);
}

// Simple rating handling
document.addEventListener('DOMContentLoaded', () => {
    const stars = document.querySelectorAll('#ratingStars .star');
    const ratingInput = document.getElementById('ratingValue');

    stars.forEach(star => {
        star.addEventListener('click', () => {
            const val = parseInt(star.getAttribute('data-value'));
            ratingInput.value = val;
            stars.forEach((s, idx) => {
                if (idx < val) {
                    s.classList.add('active');
                    s.textContent = '★';
                    s.style.color = '#ffc107';
                } else {
                    s.classList.remove('active');
                    s.textContent = '☆';
                    s.style.color = 'inherit';
                }
            });
        });
    });

    // Form submit
    const feedbackForm = document.getElementById('feedbackForm');
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const rating = parseInt(document.getElementById('ratingValue').value);
        const comment = document.getElementById('feedbackComment').value;
        const token = localStorage.getItem('token');

        if (!rating) {
            alert('Please select a rating');
            return;
        }

        try {
            const res = await fetch(`${API_BASE_URL}/feedback/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ rating, comment, recommendation_type: 'general' })
            });

            const data = await res.json();
            if (!res.ok) {
                alert('Error: ' + (data.error || 'Unable to submit feedback'));
                return;
            }

            alert('Thanks for your feedback!');
            feedbackForm.reset();
            window.location.href = '../pages/recommendations.html';
        } catch (err) {
            alert('Error submitting feedback: ' + err.message);
        }
    });
});

function logout() {
    localStorage.clear();
    window.location.href = '../index.html';
}
// API already declared above; do not redeclare here

// Character counter
const commentField = document.getElementById('feedbackComment');
const charCount = document.querySelector('.char-count');

if (commentField) {
    commentField.addEventListener('input', (e) => {
        const count = e.target.value.length;
        charCount.textContent = `${count} / 500 characters`;
    });
}

// Star Rating System
let selectedRating = 0;
const stars = document.querySelectorAll('.star');
const ratingLabel = document.getElementById('ratingLabel');
const ratingValue = document.getElementById('ratingValue');

stars.forEach(star => {
    star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.rating);
        setStarRating(selectedRating);
    });
    
    star.addEventListener('mouseover', () => {
        const hoverRating = parseInt(star.dataset.rating);
        highlightStars(hoverRating);
    });
});

document.getElementById('ratingStars')?.addEventListener('mouseout', () => {
    highlightStars(selectedRating);
});

function highlightStars(rating) {
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
    
    updateRatingLabel(rating);
}

function setStarRating(rating) {
    selectedRating = rating;
    highlightStars(rating);
    ratingValue.value = rating;
}

function updateRatingLabel(rating) {
    const labels = [
        'Select a rating',
        'Poor',
        'Fair',
        'Good',
        'Very Good',
        'Excellent'
    ];
    
    if (ratingLabel) {
        ratingLabel.textContent = labels[rating] || 'Select a rating';
    }
}

// Form Submission
const feedbackForm = document.getElementById('feedbackForm');

if (feedbackForm) {
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Validate rating
        if (selectedRating === 0) {
            showAlert('Please select a rating', 'error');
            return;
        }
        
        const comment = document.getElementById('feedbackComment').value.trim();
        const recommendationType = document.querySelector('input[name="recommendation_type"]:checked').value;
        const alternativesHelpful = document.querySelector('input[name="alternatives_helpful"]:checked')?.value || '';
        
        try {
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Submitting...';
            
            const response = await fetch(`${API_BASE_URL}/feedback/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    rating: selectedRating,
                    comment: comment,
                    recommendation_type: recommendationType,
                    alternatives_helpful: alternativesHelpful
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showAlert('✓ Thank you for your feedback! It helps us improve.', 'success');
                
                // Reset form
                feedbackForm.reset();
                selectedRating = 0;
                highlightStars(0);
                
                // Redirect after 2 seconds
                setTimeout(() => {
                    window.location.href = 'recommendations.html';
                }, 2000);
            } else {
                showAlert(data.error || 'Error submitting feedback', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 Submit Feedback';
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to submit feedback. Please try again.', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = '📤 Submit Feedback';
        }
    });
}

// Navigation Functions
function backToDashboard() {
    window.location.href = 'recommendations.html';
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('userType');
    localStorage.removeItem('userName');
    window.location.href = '../index.html';
}

// Alert Display
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type}`;
    alertEl.innerHTML = `
        <div class="alert-content">
            ${message}
        </div>
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    alertContainer.appendChild(alertEl);
    
    setTimeout(() => {
        if (alertEl.parentElement) {
            alertEl.remove();
        }
    }, 5000);
}

// Auto-redirect if not authenticated
window.addEventListener('load', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '../index.html';
    }
});
