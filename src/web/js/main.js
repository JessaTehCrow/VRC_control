const WS_HOST = "wss://crows.world/wss/:8081"

let types = {
    "bool": "checkbox",
    "int": "number",
    "float":"range"
}

function get_new_input(type, value) {
    let inp = document.createElement("input")
    inp.type = types[type]

    if (type == "bool") {
        inp.checked = value;
        return inp;
    }
    else if (type == "int") {
        inp.value = value;
        return inp;
    } else {
        inp.max = 1;
        inp.step = 0.0125;
        inp.min = 0;
        inp.value = value;
    }

    return inp;
}

let room_id
let password
let connect_button

let join_section
let content_section
let inputs

let disconnect
let id_display
let notification_bar
let notification

let notification_timeout
let data
let conn
let fields = {}
let instance_data = get_cookies()
let reconnect = instance_data["roomid"] !== undefined

let did_error = false

function save_cookies(data, days, prefix="crows-") {
    const d = new Date();
    d.setTime(d.getTime() + (days*(24*60*60*1000)));
    let expires = "expires=" + d.toUTCString();

    for (var key in data) {
        let value = JSON.stringify(data[key])
        document.cookie = prefix + key + "=" + value + ';' + expires + "; SameSite=strict; path=/;"
    }
}

function get_cookies(prefix="crows-") {
    let cookies = decodeURIComponent(document.cookie);
    let values = cookies.split(";")
    let data = {}

    for (var value in values) {
        value = values[value].trim()

        if (!value.startsWith(prefix)) {
            continue
        }
        
        let name = value.split("=")[0].substring(prefix.length)

        let val = value.substring(value.indexOf('=')+1)
        data[name] = JSON.parse(val)
    }
    return data
}

function delete_cookies(prefix="crows-") {
    let cookies = get_cookies()

    for (var key in cookies) {
        document.cookie = prefix + key + "=; Max-Age=-9999999999; SameSite=strict; Path=/;"

    }
}

function create_field(name, type, value, locked) {
    if (name in fields) {
        return;
    }

    let field = document.createElement("div")
    field.classList = (locked ? "field locked" : "field")

    let inp_area = document.createElement('div')
    inp_area.id = "input"
    
    let span = document.createElement("span")

    let title = document.createElement("p")
    title.innerHTML = name

    let icon = document.createElement("i")
    icon.classList = "material-icons"
    icon.onclick = (e) =>{lock_callback(name, type, e)}
    icon.innerHTML = (locked ? "lock_outline" : "lock_open")

    let inp = get_new_input(type, value)

    span.appendChild(title)
    span.appendChild(icon)
    field.appendChild(span)
    
    if (type == "int") {
        let minus = document.createElement("button")
        minus.innerHTML = "-"
        minus.onclick = (e) => {
            inp.value = Math.max(0, inp.value - 1)
            value_update_callback(name, type, locked, parseInt(inp.value), inp)
        }

        let plus = document.createElement("button")
        plus.onclick = (e) => {
            inp.value = parseInt(inp.value) + 1
            value_update_callback(name, type, locked, parseInt(inp.value), inp)
        }
        
        plus.innerHTML = "+"

        inp_area.append(minus)
        inp_area.append(inp)
        inp.onkeydown = number_only
        inp_area.append(plus)
    } else {
        inp_area.appendChild(inp)
    }

    field.appendChild(inp_area)


    inputs.appendChild(field)

    fields[name] = [field, icon, inp]

    inp.addEventListener("input", (e) => {
        value_update_callback(name, type, locked, inp.value, e)
    })
}

function number_only(e) {
    let char = String.fromCharCode(e.keyCode)
    return e.which == 8 || "0123456789".includes(char)
}


function hide_notification() {
    notification_bar.classList.remove("show")
    notification_timeout = null
}


function show_notification(msg, style) {
    notification_bar.classList.add("show")
    notification.classList = [style]
    notification.innerHTML = "<p>"+msg+"</p>"
}


function do_notification(msg, good) {
    style = (good) ? "good" : "bad";
    
    if (notification_timeout != null) {
        clearTimeout(notification_timeout)
        hide_notification()
        setTimeout(show_notification, 100, msg, style)
        
    } else {
        show_notification(msg, style)
    }
    notification_timeout = setTimeout(hide_notification, 5000)
}


function auto_caps(val) {
    val = val.target
    val.value = val.value.toUpperCase();
}

function connect(id, password="") {
    data = {
        "type":"connect",
        "data":{
            "id":id,
            "password":password
        }
    }

    conn.send(JSON.stringify(data))
}

function join_callback(val) {
    id = room_id.value
    pass = password.value

    connect(id, pass)
}


function handle_connect(data) {
    join_section.classList = ["hidden"]
    content_section.classList = []
    id_display.innerHTML = data["data"]["id"]
    
    document.title ="Room " + data["data"]["id"]
    
    let fields = data["data"]["data"]

    instance_data["roomid"] = data["data"]["id"]
    instance_data["password"] = data["data"]["password"]
    
    save_cookies(instance_data, 1)

    for (var key in fields) {
        let type, value, locked
        [type, value, locked] = fields[key]
        
        create_field(key, type, value, locked)
    }
}


function handle_disconnect() {
    join_section.classList = []
    content_section.classList = ["hidden"]
    room_id.value = ""
    password.value = ""

    document.title = "Join room"

    reconnect = false
    delete_cookies()
}


function update(data) {
    let name = data["name"]
    let type = data["type"]
    let value = data["value"]
    let locked = data["locked"]

    if (!(name in fields)) {
        handle_disconnect();
        return;
    }

    let field, icon, inp
    [field, icon, inp] = fields[name]

    if (type == "bool") {
        inp.checked = value
    } else {
        inp.value = value
    }

    let new_icon = (locked ? "lock_outline" : "lock_open")
    let new_class = (locked ? "field locked" : "field")

    field.classList = new_class
    icon.innerHTML = new_icon
}


function handle_message(msg) {
    data = JSON.parse(msg)
    console.log(msg)

    if ("message" in data) {
        if (reconnect && data["message"] == "Room ID does not exist") {
            delete_cookies();
            instance_data = {}
            do_notification("Unable to reconnect: Room does not exist")
        } else {
            do_notification(data["message"], data["success"])
        }
    }

    if ("type" in data) {
        type = data["type"]

        if (type == "connected") {
            fields = {}
            inputs.innerHTML = ""
            setTimeout(handle_connect, 100, data)

        } else if (type == "disconnect") {
            handle_disconnect()   

        } else if (type == "update") {
            update(data["data"])
        }
    }
}


function new_conn(onOpen, onMessage, onError) {
    let conn = new WebSocket(WS_HOST)
    conn.onopen = onOpen;
    conn.onmessage =onMessage;
    conn.onerror = onError;
    return conn
}


function error_callback() {
    console.log("Failed connection to server")
    conn.close()
    if (did_error == false){
        do_notification("Failed to connect to server", 0)
        handle_message('{"type":"disconnect"}')
        did_error = true
    }
    
    onopen = conn.onopen
    onmessage = conn.onmessage
    onerror = conn.onerror
    
    function renew() {
        console.log("Attempting reconnect to server...")
        conn = new_conn(onopen, onmessage, onerror)
    }
    
    setTimeout(renew, 1000)
}


function open_callback(){ 
    if (did_error) {
        do_notification("Connected to server", 1)
    }

    if (reconnect) {
        connect(instance_data["roomid"], instance_data["password"])
    }
    console.log("Connected to server")
    did_error = false;
}


function lock_callback(name, type, element) {
    let icon = element.target
    let span = icon.parentElement
    let field = span.parentElement
    let locked = icon.innerHTML == "lock_outline"
    
    icon.innerHTML = (locked ? "lock_open" : "lock_outline")
    field.classList = (locked ? "field" : "field locked")

    conn.send(JSON.stringify({
        "type":"update",
        "data":{
            "name":name,
            "locked":!locked
        }
    }))
}   


function value_update_callback(name, type, locked, value, element) {
    if (type == "bool") {
        value = element.target.checked
    }
    else if (type == "float") {
        value = parseFloat(value)
    } else {
        if (value == "") {
            value = 0
        } else {
            value = parseInt(value)
        }
    }

    let data = JSON.stringify({
        "type":"update",
        "data":{
            "name":name,
            "value":value
        }
    })
    console.log("Send:",data)
    conn.send(data)
}


window.onload = function() {
    room_id = document.querySelector("#roomid")
    connect_button = document.querySelector("#connect")
    notification_bar = document.querySelector("#notification_bar")
    notification = document.querySelector("#notification")
    content_section = document.querySelector("#content")
    password = document.querySelector("#password")
    join_section = document.querySelector("#join")
    id_display = document.querySelector("#id")
    disconnect = document.querySelector("#disconnect")
    inputs = document.querySelector("#inputs")

    disconnect.onclick = function(){conn.send('{"type":"disconnect"}')};
    room_id.oninput = auto_caps
    connect_button.onclick = join_callback

    notification.classList.remove("hidden")

    conn = new_conn(onopen=open_callback, 
                    onmessage=(e) => handle_message(e.data), 
                    onerror=error_callback);
    
}
