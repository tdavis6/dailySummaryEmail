document.addEventListener('DOMContentLoaded', () => {
    // Fetch configuration data and populate the form on load
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            // Populate all standard inputs
            Object.keys(data).forEach(key => {
                const element = document.querySelector(`[name="${key}"]`);
                if (element && (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT')) {
                    element.value = data[key];
                }

                // Handle toggles (True/False)
                const hiddenInput = document.getElementById(`${key}-hidden`);
                if (hiddenInput) {
                    const toggleCheckbox = document.querySelector(`input.toggle-input[data-linked-input="${key}-hidden"]`);
                    if (toggleCheckbox) {
                        if (data[key] === "True") {
                            toggleCheckbox.checked = true;
                            hiddenInput.value = "True";
                        } else {
                            toggleCheckbox.checked = false;
                            hiddenInput.value = "False";
                        }
                    }
                }

                // Handle segmented controls (e.g., UNIT_SYSTEM, TIME_SYSTEM, LOGGING_LEVEL)
                const segmentedControl = document.querySelector(`.segmented-control[data-linked-input="${key}-hidden"]`);
                if (segmentedControl) {
                    const radios = segmentedControl.querySelectorAll('input[type="radio"]');
                    const hiddenInput = document.getElementById(`${key}-hidden`);
                    radios.forEach(radio => {
                        if (radio.value === data[key]) {
                            radio.checked = true;
                            if (hiddenInput) {
                                hiddenInput.value = data[key];
                            }
                        }
                    });
                }
            });
        })
        .catch(error => {
            console.error('Error fetching configuration:', error);
        });

    // Event listener for toggles
    document.querySelectorAll('input.toggle-input').forEach(toggle => {
        toggle.addEventListener('change', function () {
            const linkedInputId = this.getAttribute('data-linked-input');
            const linkedInput = document.getElementById(linkedInputId);
            if (linkedInput) {
                linkedInput.value = this.checked ? "True" : "False";
            }
        });
    });

    // Event listener for segmented controls
    document.querySelectorAll('.segmented-control').forEach(control => {
        const linkedInputId = control.getAttribute('data-linked-input');
        const hiddenInput = document.getElementById(linkedInputId);

        const radios = control.querySelectorAll('input[type="radio"]');
        radios.forEach(radio => {
            radio.addEventListener('change', function () {
                if (this.checked && hiddenInput) {
                    hiddenInput.value = this.value;
                }
            });
        });
    });

    // Save Settings button event
    document.getElementById('save-settings').addEventListener('click', () => {
        const formData = new FormData(document.getElementById('config-form'));
        const configData = {};
        formData.forEach((value, key) => {
            configData[key] = value;
        });

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

    // Send Email Now button event
    document.getElementById('send-email').addEventListener('click', () => {
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
                messageElement.textContent = 'Error sending email!';
                messageElement.style.opacity = 1;
                setTimeout(() => {
                    messageElement.style.opacity = 0;
                    setTimeout(() => {
                        messageElement.textContent = '';
                    }, 1000);
                }, 5000);
        });
    });
});
