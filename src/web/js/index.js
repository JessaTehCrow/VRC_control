
function toggle(element, to=-1) {
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
    
    if ([1,0].includes(to)){
        return
    }

    fetch("/set", {
        method: "POST",
        body: JSON.stringify({
            "name":name,
            "type":"lock",
            "value": + locked
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })
}

let images = document.querySelectorAll("img");
for (i=0; i<images.length; i++) {
    let image = images[i]
    images[i].onclick = function() {toggle(image)}
}

function change_event(e) {
    elem = e.target
    var new_value = 0
    if (elem.type == "checkbox") {
        new_value = + elem.checked
    } else {
        new_value = elem.value
    }

    fetch("/set", {
        method: "POST",
        body: JSON.stringify({
            "name":elem.name,
            "type":"value",
            "value":new_value
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    })

}

const inputs = document.querySelectorAll("input")

for (i=0; i<inputs.length; i++) {
    elem = inputs[i]
    if (elem.type == "checkbox"){
        elem.addEventListener('change', change_event)
    } else {
        elem.addEventListener('input', change_event, false)
    }
}



function update_values(){
    fetch('/get', {
        headers: {
            'Accept': 'application/json'
    }})
    .then(response => response.text())
    .then(text => {
        data = JSON.parse(text)
        console.log(data)
        for (let key in data) {

            item = document.querySelector("input[name='"+key+"']")
            locked = document.querySelector("img[name='"+key+"']")
            if (data[key].type == "Bool") {
                item.checked = data[key].value
            } else {
                item.value = data[key].value
            }

            toggle(locked, data[key].locked)
        }
    })
}

setInterval(update_values, 1000)