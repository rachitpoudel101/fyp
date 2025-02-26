document.addEventListener('DOMContentLoaded', function () {
    const loginButton = document.querySelector('.btn-primary');
    loginButton.addEventListener('click', function (event) {
        try {
            window.location.href = '/login/';
        } catch (error) {
            console.error('Error redirecting to login page:', error);
            alert('An error occurred while redirecting to the login page. Please try again.');
        }
    });
});