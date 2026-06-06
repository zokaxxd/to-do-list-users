const token = localStorage.getItem("token")

if (!token) {
    window.location.href = "/login/log.html"
}

function carregarTarefas() {
    fetch("http://127.0.0.1:8000/tasks", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(response => response.json())
    .then(data => {
        const lista = document.getElementById("to-do-list")
        lista.innerHTML = ""

        data.tasks.forEach(task => {
    const item = document.createElement("li")
    item.innerText = task.title

    // botão de concluir
    const btnConcluir = document.createElement("button")
    btnConcluir.innerText = "✓"
    btnConcluir.onclick = () => concluirTarefa(task.id)

    // botão de deletar
    const btnDeletar = document.createElement("button")
    btnDeletar.innerText = "✕"
    btnDeletar.onclick = () => deletarTarefa(task.id)

    // se já estiver concluída, risca o texto
    if (task.completed) {
        item.style.textDecoration = "line-through"
        item.style.opacity = "0.5"
    }

    item.appendChild(btnConcluir)
    item.appendChild(btnDeletar)
    lista.appendChild(item)
})
        })
    }


carregarTarefas()

document.querySelector(".box-msg").addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        const titulo = this.value.trim()
        if (!titulo) return

        fetch("http://127.0.0.1:8000/tasks", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ title: titulo })
        })
        .then(response => response.json())
        .then(() => {
            this.value = ""
            carregarTarefas()
        })
    }
})

function concluirTarefa(id) {
    fetch(`http://127.0.0.1:8000/tasks/${id}`, {
        method: "PUT",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(() => carregarTarefas())
}

function deletarTarefa(id) {
    fetch(`http://127.0.0.1:8000/tasks/${id}`, {
        method: "DELETE",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(() => carregarTarefas())
}