document.addEventListener('DOMContentLoaded', function () {
    const dashboardButton = document.getElementById('dashboardButton');
    dashboardButton.addEventListener('click', function () {
        try {
            window.location.href = '/order_dashboard/';
        } catch (error) {
            console.error('Error redirecting to order dashboard:', error);
            alert('An error occurred while redirecting to the order dashboard. Please try again.');
        }
    });
});