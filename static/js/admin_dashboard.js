
document.addEventListener('DOMContentLoaded', function () {
    // Add Product Form Submission
    document.getElementById('addProductForm').addEventListener('submit', function (event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const errorDiv = document.getElementById('addProductError');

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
});