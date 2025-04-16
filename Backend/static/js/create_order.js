document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('createOrderForm');
    const errorMessages = document.querySelectorAll('.error-message');

    form.addEventListener('submit', function (event) {
        let hasError = false;

        // Clear previous error messages
        errorMessages.forEach(error => {
            error.textContent = '';
        });

        // Validate each field
        form.querySelectorAll('input, select, textarea').forEach(field => {
            if (!field.value.trim()) {
                const errorMessage = field.parentElement.querySelector('.error-message');
                if (errorMessage) {
                    errorMessage.textContent = `${field.name} is required.`;
                }
                hasError = true;
            }
        });

        if (hasError) {
            event.preventDefault();
        }
    });
});