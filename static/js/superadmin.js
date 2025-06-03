document.addEventListener('DOMContentLoaded', function() {
    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    if (passwordToggles.length > 0) {
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
    }

    // Get the add admin form
    const addAdminForm = document.getElementById('add-admin-form');
    
    if (addAdminForm) {
        addAdminForm.addEventListener('submit', function(event) {
            // Get username and password values
            const username = document.getElementById('id_username').value;
            const password = document.getElementById('id_password1').value;
            
            // Check if username and password are the same
            if (username === password) {
                event.preventDefault(); // Prevent form submission
                
                // Show error modal
                showErrorModal(
                    "Security Warning", 
                    "Username and password cannot be the same for security reasons. Please use a different password."
                );
                return false;
            }
        });
    }

    // Function to display error modal
    function showErrorModal(title, message) {
        // If we're using Tailwind UI (from the template style)
        const modalHTML = `
            <div class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-gray-900 bg-opacity-50">
                <div class="relative bg-white rounded-lg shadow-xl mx-4 max-w-md w-full">
                    <div class="px-6 py-4 border-b border-gray-200">
                        <h3 class="text-lg font-medium text-red-600">${title}</h3>
                    </div>
                    <div class="p-6">
                        <p class="text-gray-700">${message}</p>
                    </div>
                    <div class="bg-gray-100 px-6 py-4 flex justify-end">
                        <button type="button" id="closeErrorModal" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Create a container for the modal
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer);
        
        // Add event listener to the close button
        document.getElementById('closeErrorModal').addEventListener('click', function() {
            document.body.removeChild(modalContainer);
        });
    }
});
