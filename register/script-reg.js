document.getElementById("register-btn").addEventListener("click", function() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const age = document.getElementById("age").value;
    const name = document.getElementById("name").value;

    fetch("http://127.0.0.1:8000/users",{
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        name: name,
        age: parseInt(age),
        email: email,
        password: password
    })
})
.then(response => response.json())
.then(data => {
    if (data.message === "User created successfully!") {
        alert("User created successfully")
        window.location.href = "/login/log.html"
    } else {
        alert("Erro: " + data.detail)
    }
})
})
