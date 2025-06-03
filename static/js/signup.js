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

    // Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(event) {
            let hasError = false;

            // Clear previous error messages
            document.querySelectorAll('.text-danger').forEach(error => {
                error.textContent = '';
            });

            // Validate each field
            form.querySelectorAll('input[required]').forEach(field => {
                if (!field.value.trim()) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'text-danger text-xs text-red-500 mt-1';
                    errorDiv.textContent = `${field.name} is required.`;
                    field.parentElement.appendChild(errorDiv);
                    hasError = true;
                }
            });

            // Check if passwords match
            const password1 = form.querySelector('input[name="password1"]');
            const password2 = form.querySelector('input[name="password2"]');
            
            if (password1 && password2 && password1.value !== password2.value) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-danger text-xs text-red-500 mt-1';
                errorDiv.textContent = 'Passwords do not match.';
                password2.parentElement.appendChild(errorDiv);
                hasError = true;
            }

            // Get CSRF token from the form
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Check if username and password are the same
            const username = form.querySelector('input[name="username"]').value;
            const password = form.querySelector('input[name="password1"]').value;
            
            if (username === password) {
                event.preventDefault();
                showModal('Security Warning', 
                    'Username and password cannot be the same for security reasons.', 
                    'OK', null);
                return;
            }

            if (hasError) {
                event.preventDefault();
                return;
            }

            // Use AJAX for signup submission
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
                    window.location.href = response.url;
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (!data) return; // Already handled redirect
                
                if (data && !data.success) {
                    if (data.same_credentials_error) {
                        showModal('Security Warning', 
                            'Username and password cannot be the same for security reasons.',
                            'OK', null);
                    } else if (data.errors) {
                        // Display validation errors
                        let errorMessage = 'Please fix the following errors:\n';
                        for (const [field, errors] of Object.entries(data.errors)) {
                            errorMessage += `• ${field}: ${errors.join(', ')}\n`;
                        }
                        showModal('Form Validation Failed', errorMessage, 'OK', null);
                    } else {
                        showModal('Signup Failed', data.message || 'An unknown error occurred.', 'OK', null);
                    }
                } else {
                    // On success, submit the form normally
                    form.submit();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                form.submit(); // Fall back to normal form submission
            });
        });
    }

    // Function to create and show a modal popup for errors
    function showModal(title, message, buttonText) {
        // Create modal background
        const modalBg = document.createElement('div');
        modalBg.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        
        // Create modal content
        const modal = document.createElement('div');
        modal.className = 'bg-white rounded-lg p-6 max-w-md mx-4 w-full';
        
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
        });
    }

    // Flip animation for login link
    const loginLink = document.querySelector('a[href*="login"]');
    
    if (loginLink) {
        loginLink.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.add('animating');
            
            // Target only the signup form container instead of the whole card
            const container = document.querySelector('.signup-container');
            container.classList.add('card-flip');
            
            // Trigger animation with slight delay to ensure proper rendering
            setTimeout(() => {
                container.classList.add('flipped');
            }, 50);
            
            // Redirect after animation completes
            setTimeout(() => {
                window.location.href = loginLink.href;
            }, 700);
        });
    }
});