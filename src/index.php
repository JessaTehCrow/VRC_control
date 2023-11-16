<head>
    <link href="https://fonts.googleapis.com/css2?family=Source+Code+Pro&amp;family=Space+Mono&amp;display=swap" rel="stylesheet">
    <link rel="stylesheet" href="css/main.css?v=<?= time() ?>">
    <script src="js/main.js?v=<?= time() ?>"></script> 
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
    <title>Join room</title>
</head>
<body>
    <!-- Notification bar -->
    <div id="notification_bar" class="">
        <div id="notification" class="">
            <p>Message</p>
        </div>
    </div>

    <!-- Join room thingy -->
    <div id="join" class="">
        <div id="area">
            <p>Join Room</p>
            <input id="roomid" type="text" placeholder="ROOM" maxlength="5" autocomplete="off" >
            <input id="password" type="password" placeholder="Password" maxlength="16" autocomplete="off" >
            <button id="connect">Connect</button>
        </div>
    </div>

    <!-- Actual values and stuff -->
    <div id="content" class="hidden">
        <div id="header">
            <p>Room ID: <span id="id"></span></p>
            <i id="disconnect" class="material-icons">exit_to_app</i>
        </div>

        <div id="inputs">
            
        </div>

    </div>
</body>