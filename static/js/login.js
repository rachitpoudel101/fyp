document.addEventListener('DOMContentLoaded', function () {
    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Find the associated password input field
            const passwordInput = this.parentNode.querySelector('input');
            const eyeIcon = this.querySelector('.password-eye-icon');
            const eyeSlashIcon = this.querySelector('.password-eye-slash-icon');
            
            // Toggle password visibility
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.classList.add('hidden');
                eyeSlashIcon.classList.remove('hidden');
            } else {
                passwordInput.type = 'password';
                eyeIcon.classList.remove('hidden');
                eyeSlashIcon.classList.add('hidden');
            }
        });
    });

    // Existing form validation code
    const form = document.querySelector('form');
    if (!form) return; // Guard clause if form doesn't exist
    
    form.addEventListener('submit', function (event) {
        let hasError = false;

        // Clear previous error messages
        document.querySelectorAll('.text-danger').forEach(error => {
            error.textContent = '';
        });

        // Validate each field
        form.querySelectorAll('input').forEach(field => {
            if (!field.value.trim()) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-danger';
                errorDiv.textContent = `${field.name} is required.`;
                field.parentElement.appendChild(errorDiv);
                hasError = true;
            }
        });

        // If there are validation errors, prevent the form submission
        if (hasError) {
            event.preventDefault();
            return;
        }

        // Get CSRF token from the form
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Check if this is the login form based on URL path
        if (window.location.pathname.includes('login')) {
            // Use AJAX for login to handle email verification errors
            event.preventDefault();
            
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => {
                if (response.redirected) {
                    // Handle redirects
                    window.location.href = response.url;
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return; // Already handled redirect
                
                if (data.email_verification_error) {
                    // Show email verification popup
                    showModal('Email Verification Required', 
                        'Your email is not verified. Please check your inbox for the verification email.',
                        'Go to Login', () => window.location.reload());
                } else if (!data.success) {
                    // Show generic error popup
                    showModal('Login Failed', data.message || 'Invalid credentials', 'Try Again', () => {
                        // Clear password field
                        document.querySelector('input[type="password"]').value = '';
                    });
                } else if (data.success) {
                    // Redirect to the URL provided in the response
                    window.location.href = data.redirect_url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // In case of error, fall back to normal form submission
                form.submit();
            });
        } else if (window.location.pathname.includes('signup')) {
            // Similar logic for signup with CSRF token
            event.preventDefault();
            
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error:', error);
                form.submit();
            })
            .then(data => {
                if (data && !data.success) {
                    // Handle errors
                    showModal('Signup Failed', data.message || 'An error occurred', 'OK', null);
                } else {
                    // If successful, submit the form normally
                    form.submit();
                }
            });
        }
    });
    
    // Function to create and show a modal popup
    function showModal(title, message, buttonText, onClose) {
        // Create modal background
        const modalBg = document.createElement('div');
        modalBg.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.className = 'bg-white rounded-lg p-6 max-w-md mx-4 w-full animate-bounce-once';
        
        // Add title
        const modalTitle = document.createElement('h3');
        modalTitle.className = 'text-xl font-bold text-gray-900 mb-4';
        modalTitle.textContent = title;
        
        // Add message
        const modalMessage = document.createElement('p');
        modalMessage.className = 'text-gray-700 mb-6';
        modalMessage.textContent = message;
        
        // Add button
        const modalButton = document.createElement('button');
        modalButton.className = 'w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-300';
        modalButton.textContent = buttonText;
        
        // Append elements
        modal.appendChild(modalTitle);
        modal.appendChild(modalMessage);
        modal.appendChild(modalButton);
        modalBg.appendChild(modal);
        document.body.appendChild(modalBg);
        
        // Handle button click
        modalButton.addEventListener('click', function() {
            document.body.removeChild(modalBg);
            if (typeof onClose === 'function') {
                onClose();
            }
        });
    }
    
    // Enhanced auto-hide functionality to handle various error types
    const errorNotification = document.getElementById('error-notification');
    
    // Check if there are any errors to display
    if (errorNotification) {
        // Display the error notification
        errorNotification.style.display = 'flex';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorNotification.style.opacity = '0.9';
            errorNotification.style.transition = 'opacity 0.5s ease-out';
        }, 5000);
        
        setTimeout(() => {
            errorNotification.style.display = 'none';
        }, 5500);
    }
    
    // Track form submissions
    if (form) {
        form.addEventListener('submit', function() {
            localStorage.setItem('lastSubmitTime', Date.now().toString());
        });
    }
    
    // Flip animation code
    const signupLink = document.querySelector('a[href*="signup"]');
    
    if (signupLink) {
        signupLink.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.add('animating');
            
            // Target only the login form container instead of the whole card
            const container = document.querySelector('.login-container');
            container.classList.add('card-flip');
            
            // Trigger animation with slight delay to ensure proper rendering
            setTimeout(() => {
                container.classList.add('flipped');
            }, 50);
            
            // Redirect after animation completes
            setTimeout(() => {
                window.location.href = signupLink.href;
            }, 700);
        });
    }
});