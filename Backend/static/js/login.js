document.addEventListener('DOMContentLoaded', function () {
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
});