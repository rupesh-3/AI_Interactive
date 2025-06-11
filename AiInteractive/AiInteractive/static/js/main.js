// Main JavaScript for AI Content Analyzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Set up form handlers
    setupFormHandlers();
    
    // Set up URL validation
    setupURLValidation();
    
    // Set up loading states
    setupLoadingStates();
    
    // Set up tooltips and other UI enhancements
    setupUIEnhancements();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupFormHandlers() {
    // URL form handler
    const urlForm = document.getElementById('urlForm');
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            const urlInput = document.getElementById('url');
            const url = urlInput.value.trim();
            
            if (!url) {
                e.preventDefault();
                showAlert('Please enter a URL to analyze.', 'error');
                return;
            }
            
            if (!isValidURL(url)) {
                e.preventDefault();
                showAlert('Please enter a valid URL.', 'error');
                return;
            }
            
            // Show loading state
            showFormLoading('analyzeBtn', 'loadingSpinner', 'Analyzing...');
        });
    }
    
    // Question form handler
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            const questionInput = document.getElementById('question');
            const question = questionInput.value.trim();
            
            if (!question) {
                e.preventDefault();
                showAlert('Please enter a question.', 'error');
                return;
            }
            
            if (question.length < 5) {
                e.preventDefault();
                showAlert('Please enter a more detailed question.', 'error');
                return;
            }
            
            // Show loading state
            showFormLoading('questionBtn', 'questionSpinner', 'Generating Answer...');
        });
    }
}

function setupURLValidation() {
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            const url = this.value.trim();
            const isValid = url === '' || isValidURL(url);
            
            // Update input styling based on validation
            if (url && !isValid) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (url && isValid) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });
        
        // Auto-add https:// if missing
        urlInput.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
                this.value = 'https://' + url;
            }
        });
    }
}

function setupLoadingStates() {
    // Handle page navigation loading states
    window.addEventListener('beforeunload', function() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            if (form.classList.contains('submitting')) {
                // Show loading state if form was submitted
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                }
            }
        });
    });
}

function setupUIEnhancements() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-permanent')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit forms
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeElement = document.activeElement;
            const form = activeElement.closest('form');
            
            if (form) {
                e.preventDefault();
                form.requestSubmit();
            }
        }
        
        // Escape key to clear form inputs
        if (e.key === 'Escape') {
            const activeElement = document.activeElement;
            if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
                activeElement.blur();
            }
        }
    });
}

// Utility Functions
function isValidURL(string) {
    try {
        // Add protocol if missing
        const url = string.startsWith('http://') || string.startsWith('https://') 
            ? string 
            : 'https://' + string;
        
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch (error) {
        return false;
    }
}

function showAlert(message, type = 'info', duration = 5000) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    const icon = type === 'error' ? 'exclamation-triangle' : 'info-circle';
    
    alertDiv.innerHTML = `
        <i class="fas fa-${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert alert at the top of the container
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            }, duration);
        }
    }
}

function showFormLoading(buttonId, spinnerId, loadingText) {
    const button = document.getElementById(buttonId);
    const spinner = document.getElementById(spinnerId);
    
    if (button) {
        button.disabled = true;
        button.innerHTML = `<i class="fas fa-cog fa-spin me-2"></i>${loadingText}`;
        
        // Mark form as submitting
        const form = button.closest('form');
        if (form) {
            form.classList.add('submitting');
        }
    }
    
    if (spinner) {
        spinner.classList.remove('d-none');
    }
}

function hideFormLoading(buttonId, spinnerId, originalText) {
    const button = document.getElementById(buttonId);
    const spinner = document.getElementById(spinnerId);
    
    if (button) {
        button.disabled = false;
        button.innerHTML = originalText;
        
        // Remove submitting class
        const form = button.closest('form');
        if (form) {
            form.classList.remove('submitting');
        }
    }
    
    if (spinner) {
        spinner.classList.add('d-none');
    }
}

// Example URL functions
function fillUrl(url) {
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.value = url;
        urlInput.focus();
        
        // Trigger validation
        urlInput.dispatchEvent(new Event('input'));
    }
}

// Word count and character count for textareas
function setupTextareaCounters() {
    const textareas = document.querySelectorAll('textarea[data-counter]');
    
    textareas.forEach(textarea => {
        const counter = document.getElementById(textarea.dataset.counter);
        
        if (counter) {
            const updateCounter = () => {
                const currentLength = textarea.value.length;
                const maxLength = textarea.getAttribute('maxlength') || 'unlimited';
                
                counter.textContent = `${currentLength}${maxLength !== 'unlimited' ? '/' + maxLength : ''} characters`;
                
                // Add warning class if approaching limit
                if (maxLength !== 'unlimited' && currentLength > maxLength * 0.9) {
                    counter.classList.add('text-warning');
                } else {
                    counter.classList.remove('text-warning');
                }
            };
            
            textarea.addEventListener('input', updateCounter);
            updateCounter(); // Initialize counter
        }
    });
}

// Initialize textarea counters when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupTextareaCounters);
} else {
    setupTextareaCounters();
}

// Error handling for network requests
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    
    // Show user-friendly error message
    if (e.error && e.error.message && e.error.message.includes('NetworkError')) {
        showAlert('Network error: Please check your internet connection and try again.', 'error');
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    
    // Show user-friendly error message
    showAlert('An unexpected error occurred. Please refresh the page and try again.', 'error');
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
        }, 0);
    });
}

// Accessibility improvements
function improveAccessibility() {
    // Add ARIA labels to interactive elements without them
    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
    
    interactiveElements.forEach(element => {
        if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
            const text = element.textContent || element.value || element.placeholder;
            if (text) {
                element.setAttribute('aria-label', text.trim());
            }
        }
    });
    
    // Improve focus indicators
    const focusableElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]');
    
    focusableElements.forEach(element => {
        element.addEventListener('focus', function() {
            this.setAttribute('data-focused', 'true');
        });
        
        element.addEventListener('blur', function() {
            this.removeAttribute('data-focused');
        });
    });
}

// Initialize accessibility improvements
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', improveAccessibility);
} else {
    improveAccessibility();
}
