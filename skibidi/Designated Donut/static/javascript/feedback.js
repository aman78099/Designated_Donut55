// Run the code after the webpage has fully loaded
document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("feedbackForm");
    const button = document.getElementById("Submit");

    // Change the button text when the feedback form is submitted
    form.addEventListener("submit", function(event) {
        event.preventDefault();
        button.textContent = "Thank you!";
    });
});