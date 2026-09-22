// Form switching functionality

function showSignup() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('signupForm').classList.add('active');

    const imageContent = document.querySelector('.image-content');

    imageContent.innerHTML = `
        <h2>Welcome Back!</h2>
        <p>To keep connected with us please login with your personal information</p>
    `;
}


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

document.getElementById('signupFormSubmit').addEventListener('submit', function(e) {

    if (!validateSignupForm()) {
        e.preventDefault();
        return;
    }

});


function validateSignupForm() {

    const password = document.querySelector(
        '#signupForm input[name="password"]'
    ).value;

    const confirmPassword = document.querySelector(
        '#signupForm input[name="confirm_password"]'
    ).value;


    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return false;
    }


    if (password.length < 8) {
        alert('Password must be at least 8 characters long!');
        return false;
    }


    return true;
}


// Enhanced form interactions

document.querySelectorAll('.form-control').forEach(input => {

    input.addEventListener('focus', function() {

        this.parentNode.querySelector('i').style.color = '#3b82f6';

        this.classList.add('focused');

    });


    input.addEventListener('blur', function() {

        if (!this.value) {
            this.parentNode.querySelector('i').style.color = '#94a3b8';
        }

        this.classList.remove('focused');

    });


    // Real-time email validation

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

window.addEventListener('load', function() {

    document.querySelector('.container').style.animation =
        'fadeIn 1s ease';

});


// Keyboard shortcuts

document.addEventListener('keydown', function(e) {

    if (e.altKey && e.key === 's') {
        showSignup();

    } else if (e.altKey && e.key === 'l') {
        showLogin();
    }

});