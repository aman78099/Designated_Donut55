// Form switching functionality

// Switch from the login form to the signup form
function showSignup() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('signupForm').classList.add('active');

    const imageContent = document.querySelector('.image-content');

    imageContent.innerHTML = `
        <h2>Welcome Back!</h2>
        <p>To keep connected with us please login with your personal information</p>
    `;
}


// Switch from the signup form to the login form
function showLogin() {
    document.getElementById('loginForm').classList.add('active');
    document.getElementById('signupForm').classList.remove('active');

    const imageContent = document.querySelector('.image-content');

    imageContent.innerHTML = `
        <h2>Hello, Friend!</h2>
        <p>Enter your personal details and start your journey with us today</p>
    `;
}


// Signup form validation

// Check the signup form before allowing it to be submitted
document.getElementById('signupFormSubmit').addEventListener('submit', function(e) {

    if (!validateSignupForm()) {
        e.preventDefault();
        return;
    }

});


// Check that the passwords match and meet the minimum length
function validateSignupForm() {

    const password = document.querySelector(
        '#signupForm input[name="password"]'
    ).value;

    const confirmPassword = document.querySelector(
        '#signupForm input[name="confirm_password"]'
    ).value;


    // Check whether both entered passwords are the same
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return false;
    }


    // Check that the password contains at least 8 characters
    if (password.length < 8) {
        alert('Password must be at least 8 characters long!');
        return false;
    }


    return true;
}


// Enhanced form interactions

// Add focus, blur, and email validation behaviour to form inputs
document.querySelectorAll('.form-control').forEach(input => {

    // Change the input styling when the user selects a field
    input.addEventListener('focus', function() {

        this.parentNode.querySelector('i').style.color = '#3b82f6';

        this.classList.add('focused');

    });


    // Reset the input styling when the user leaves a field
    input.addEventListener('blur', function() {

        if (!this.value) {
            this.parentNode.querySelector('i').style.color = '#94a3b8';
        }

        this.classList.remove('focused');

    });


    // Real-time email validation

    // Check whether the entered email follows a valid email format
    input.addEventListener('input', function() {

        if (this.type === 'email') {

            const isValid =
                /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.value);

            this.classList.toggle(
                'success',
                isValid && this.value.length > 0
            );

            this.classList.toggle(
                'error',
                !isValid && this.value.length > 0
            );
        }

    });

});


// Smooth page load animation

// Apply a fade-in animation when the page finishes loading
window.addEventListener('load', function() {

    document.querySelector('.container').style.animation =
        'fadeIn 1s ease';

});


// Keyboard shortcuts

// Allow the user to switch between forms using keyboard shortcuts
document.addEventListener('keydown', function(e) {

    if (e.altKey && e.key === 's') {
        showSignup();

    } else if (e.altKey && e.key === 'l') {
        showLogin();
    }

});