document.addEventListener('DOMContentLoaded', function () {
    // Existing form validation code
    const form = document.querySelector('form');
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

        if (hasError) {
            event.preventDefault();
        }
    });
    
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