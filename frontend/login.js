const API_URL = "http://127.0.0.1:8000";

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");

loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    loginMessage.textContent = "";
    loginMessage.style.color = "";

    try {

        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Invalid email or password"
            );
        }

        console.log("Login successful:", data);

        // Save login information
        localStorage.setItem("itbisLoggedIn", "true");
        localStorage.setItem("itbisUser", data.email);
        localStorage.setItem("itbisRole", data.role);

        // Open dashboard
        window.location.href = "index.html";

    } catch (error) {

        console.error("Login error:", error);

        loginMessage.textContent = error.message;
        loginMessage.style.color = "#dc2626";
    }
});