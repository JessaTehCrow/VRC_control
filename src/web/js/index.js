
function toggle(element, to = -1) {
    let name = element.name
    let parent = element.parentElement
    let locked = false

    if ((parent.classList.contains("locked") && to == -1) || to == 0) {
        parent.classList.remove("locked")
        element.src = "images/unlocked.png"
    } else {
        parent.classList.add("locked")
        element.src = "images/lock.png"
        locked = true
    }

    if ([1, 0].includes(to)) {
        return
    }

    fetch("/set", {
        method: "POST",
        body: JSON.stringify({
            "name": name,
            "type": "lock",
            "value": + locked
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
}

let images = document.querySelectorAll("img");
for (i = 0; i < images.length; i++) {
    let image = images[i]
    images[i].onclick = function () { toggle(image) }
}

function change_event(e, raw=false) {
    if (!raw) {
        elem = e.target
    } else {
        elem = e
    }
    var new_value = 0
    if (elem.type == "checkbox") {
        new_value = + elem.checked
    } else {
        new_value = elem.value
    }

    fetch("/set", {
        method: "POST",
        body: JSON.stringify({
            "name": elem.name,
            "type": "value",
            "value": new_value
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })

}

const inputs = document.querySelectorAll("input")

for (i = 0; i < inputs.length; i++) {
    elem = inputs[i]
    if (elem.type == "checkbox" || elem.type == "text") {
        elem.addEventListener('change', change_event)
    } else {
        elem.addEventListener('input', change_event, false)
    }
}


function update_values() {
    fetch('/get', {
        headers: {
            'Accept': 'application/json'
        }
    })
        .then(response => response.text())
        .then(text => {
            data = JSON.parse(text)
            for (let key in data) {

                item = document.querySelector("input[name='" + key + "']")
                locked = document.querySelector("img[name='" + key + "']")
                if (data[key].type == "Bool") {
                    item.checked = data[key].value
                } else {
                    item.value = data[key].value
                }

                toggle(locked, data[key].locked)
            }
        })
}

const text_inputs = document.querySelectorAll("input[type='number']")

function digit_only(e) {
    let new_value = parseInt(e.target.value + e.key)
    let min = parseInt(e.target.min)
    let max = parseInt(e.target.max)

    if (e.keyCode >= 48 && e.keyCode <= 57 && new_value <= max && new_value >= min) {
        e.target.value += e.key
        change_event(e)
    }
    else if (e.keyCode == 8) {
        e.target.value = 0
        change_event(e)
    }

    return false
}

for (i = 0; i < text_inputs.length; i++) {
    text_inputs[i].onkeydown = digit_only
}

setInterval(update_values, 1000)


const buttons = document.querySelectorAll("button")

for (i = 0; i < buttons.length; i++) {
    let btn = buttons[i]

    let target = document.querySelector("input[name='"+btn.name+"']")
    let max = parseInt(target.max)
    let min = parseInt(target.min)

    buttons[i].onclick = function() {
        if (btn.value == "-") {
            target.value = parseInt(target.value) - 1
        }
        else {
            target.value = parseInt(target.value) + 1
        }
        let number = parseInt(target.value);
        let new_val = Math.min(max, Math.max(min,number))

        target.value = new_val.toString()
        change_event(target, raw=true)
    }
}