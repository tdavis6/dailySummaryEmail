document.getElementById('send-email').addEventListener('click', function () {
    const messageElement = document.getElementById('message');
    messageElement.textContent = 'Email being generated.';
    messageElement.style.transition = 'opacity 0.5s';
    messageElement.style.opacity = 1;


    fetch('/api/send-email', {
        method: 'POST'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            messageElement.textContent = data.message || 'Email sent!';
            messageElement.style.opacity = 1;
            setTimeout(() => {
                messageElement.style.opacity = 0;
                setTimeout(() => {
                    messageElement.textContent = '';
                }, 1000);
            }, 5000);
        })
        .catch(error => {
            const messageElement = document.getElementById('message');
            messageElement.textContent = 'Error sending email!';
            messageElement.style.transition = 'opacity 0.5s';
            messageElement.style.opacity = 1;
            setTimeout(() => {
                messageElement.style.opacity = 0;
                setTimeout(() => {
                    messageElement.textContent = '';
                }, 1000);
            }, 5000);
        });
});

document.addEventListener('DOMContentLoaded', (event) => {
    // Fetch configuration data and populate form on load
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            Object.keys(data).forEach(key => {
                const element = document.querySelector(`[name="${key}"]`);
                if (element) {
                    element.value = data[key];
                }
            });
        });

    // Handle save button click event
    document.getElementById('save-settings').addEventListener('click', () => {
        const formData = new FormData(document.getElementById('config-form'));
        const configData = {};
        formData.forEach((value, key) => {
            configData[key] = value;
        });

        const messageElement = document.getElementById('message');
        messageElement.textContent = 'Configuration saving.';
        messageElement.style.transition = 'opacity 0.5s';
        messageElement.style.opacity = 1;

        fetch('/api/save-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        })
            .then(response => response.json())
            .then(data => {
                const messageElement = document.getElementById('message');
                messageElement.textContent = data.message;
                messageElement.style.transition = 'opacity 0.5s';
                messageElement.style.opacity = 1;
                setTimeout(() => {
                    messageElement.style.opacity = 0;
                    setTimeout(() => {
                        messageElement.textContent = '';
                    }, 1000);
                }, 5000);
            })
            .catch(error => {
                console.error('Error saving configuration:', error);
            });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("form");

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault(); // Prevent default form submission

        const password = document.querySelector("#password").value;
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({password}),
        });

        const result = await response.json();

        if (response.ok) {
            window.location.href = "/"; // Redirect to home on success
        } else {
            const errorMessage = document.createElement("p");
            errorMessage.classList.add("error");
            errorMessage.textContent = result.error || "Login failed.";
            document.querySelector(".container").appendChild(errorMessage);
        }
    });
});