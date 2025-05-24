// filepath: /c:/Users/Rachit Poudel/Desktop/fyp/Backend/user/static/js/orders.js
document.addEventListener('DOMContentLoaded', function () {
    const statusForms = document.querySelectorAll('form');

    statusForms.forEach(form => {
        form.addEventListener('submit', function (event) {
            const select = form.querySelector('select[name="status"]');
            if (!select.value) {
                event.preventDefault();
                alert('Please select a valid status.');
            }
        });
    });
});