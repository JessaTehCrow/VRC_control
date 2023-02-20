parameters = document.querySelectorAll("input")
warning = document.querySelector("#warning")
save = document.querySelector("#save")
toggle_button = document.querySelector("#toggle_all")
confirm_button = document.querySelector("#confirm")

let toggle_status = true

toggle_button.onclick = function() {
    for (i=0; i<parameters.length;i++) {
        parameters[i].checked = toggle_status
    }
    toggle_status = !toggle_status   
}

console.log(parameters)
confirm_button.onclick = function() {
    used_parameters = []
    for (i=0; i<parameters.length; i++) {
        if (!parameters[i].checked && parameters[i].name != "") {
            used_parameters.push(parameters[i].name)
        }
    }
    console.log(used_parameters)
    if (used_parameters.length == 0) {
        warning.innerHTML = "Not enough parameters selected"
        return
    }
    used_parameters.unshift(save.checked)
    fetch("/submit", {
    method: "POST",
    body: JSON.stringify(used_parameters),
    headers: {
        "Content-type": "application/json; charset=UTF-8"
    }
    })

    setTimeout(() => {location.reload()}, 1000)
}

