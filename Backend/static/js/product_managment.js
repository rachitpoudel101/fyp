document.addEventListener('DOMContentLoaded', function () {
    // Add Product Form Submission
    document.getElementById('addProductForm').addEventListener('submit', function (event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const errorDiv = document.getElementById('addProductError');
        const expiryDate = form.querySelector('[name="expiry_date"]');

        // Validate expiry date if provided
        if (expiryDate && expiryDate.value) {
            const today = new Date();
            const expiry = new Date(expiryDate.value);
            if (expiry <= today) {
                errorDiv.textContent = 'Expiry date must be in the future';
                errorDiv.classList.remove('d-none');
                return;
            }
        }

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                errorDiv.textContent = JSON.stringify(data.error);
                errorDiv.classList.remove('d-none');
            }
        })
        .catch(error => {
            errorDiv.textContent = 'An error occurred. Please try again.';
            errorDiv.classList.remove('d-none');
        });
    });

    // Delete Product Form Submission
    document.querySelectorAll('[id^="deleteProductForm"]').forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            const formData = new FormData(form);
            const productId = form.querySelector('input[name="delete_product_id"]').value;
            const errorDiv = document.getElementById(`deleteProductError${productId}`);

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    errorDiv.textContent = JSON.stringify(data.error);
                    errorDiv.classList.remove('d-none');
                }
            })
            .catch(error => {
                errorDiv.textContent = 'An error occurred. Please try again.';
                errorDiv.classList.remove('d-none');
            });
        });
    });

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});