document.addEventListener('DOMContentLoaded', function () {
    const orderForm = document.querySelector('.order-form form');
    orderForm.addEventListener('submit', function (event) {
        const productSelect = document.getElementById('product');
        const quantityInput = document.getElementById('quantity');
        let hasError = false;

        // Clear previous error messages
        document.querySelectorAll('.text-danger').forEach(error => {
            error.textContent = '';
        });

        // Validate product selection
        if (!productSelect.value) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger';
            errorDiv.textContent = 'Please select a product.';
            productSelect.parentElement.appendChild(errorDiv);
            hasError = true;
        }

        // Validate quantity input
        if (!quantityInput.value || quantityInput.value <= 0) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-danger';
            errorDiv.textContent = 'Please enter a valid quantity.';
            quantityInput.parentElement.appendChild(errorDiv);
            hasError = true;
        }

        if (hasError) {
            event.preventDefault();
        }
    });
});