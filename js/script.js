const wrapper = document.querySelector('.wrapper');
const loginLink = document.querySelector('.login-link');
const registerLink = document.querySelector('.register-link');
const btnPop = document.querySelector('.btnLogin');
const iconClose = document.querySelector('.icon-close');
const welcomeMessage = document.querySelector(".welcome-message");
const loginForm = document.getElementById("login-form");

registerLink.addEventListener('click', () => {
    wrapper.classList.add('active');
});

loginLink.addEventListener('click', () => {
    wrapper.classList.remove('active');
});

btnPop.addEventListener('click', () => {
    wrapper.classList.add('active-popup');
});

iconClose.addEventListener('click', () => {
    wrapper.classList.remove('active-popup');
    welcomeMessage.style.display = "block";
});


btnPop.addEventListener("click", function () {
    welcomeMessage.style.display = "none";
});


// submit event listener for login form
loginForm.addEventListener("submit", (event) => {

    event.preventDefault();

    // Get the values from the form fields
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    // AJAX request -> Flask backend to check the login credentials
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/login");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = () => {
        if (xhr.status === 200) {
            // Redirect to the main page if the login was successful
            window.location.href = "/main";
        } else {
            // error message
            const errorMessage = document.getElementById("error-message");
            errorMessage.textContent = "Invalid username or password.";
        }
    };
    const data = JSON.stringify({ username, password });
    xhr.send(data);
});