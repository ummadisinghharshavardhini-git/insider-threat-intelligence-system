fetch("http://127.0.0.1:8000/health")
    .then(response => response.json())
    .then(data => {
        document.querySelector(".card p").textContent = data.status;
    })
    .catch(error => {
        document.querySelector(".card p").textContent = "Offline";
    });