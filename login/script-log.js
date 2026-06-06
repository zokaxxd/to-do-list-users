document.getElementById("login-btn").addEventListener("click", function() 
{
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("http://127.0.0.1:8000/login",{
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `username=${email}&password=${password}`
    })

    .then(response => response.json())
    .then(data => {
        if (data.access_token) {
            localStorage.setItem("token", data.access_token);
            window.location.href = "../index.html";
        } else {
            alert("Error: " + data.detail);
    }})
})