document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("feedbackForm");
    const button = document.getElementById("Submit");

    form.addEventListener("submit", function(event) {
        event.preventDefault();
        button.textContent = "Thank you!";
    });
});