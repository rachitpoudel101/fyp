document.addEventListener('DOMContentLoaded', function () {
    const updateStockForms = document.querySelectorAll('form');

    updateStockForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            const stockChangeInput = form.querySelector('input[name="stock_change"]');
            const stockChangeValue = parseInt(stockChangeInput.value, 10);

            if (isNaN(stockChangeValue) || stockChangeValue <= 0) {
                event.preventDefault();
                alert('Please enter a valid positive number for stock change.');
            }
        });
    });
});