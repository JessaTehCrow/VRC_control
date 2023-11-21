<?php
use React\EventLoop\Loop;
use Ratchet\Server\IoServer;
use Ratchet\Http\HttpServer;
use Ratchet\WebSocket\WsServer;
use MyApp\Chat;

require dirname(__DIR__) . '/server/vendor/autoload.php';

$server = new HttpServer(
                new WsServer(
                    new Chat()
                )
            );

$loop = Loop::get();
$secure_websockets = new React\Socket\SocketServer('127.0.0.1:8081', [
    'local_cert' => '/etc/letsencrypt/live/crows.world/fullchain.pem', // path to your cert
    'local_pk' => '/etc/letsencrypt/live/crows.world/privkey.pem', // path to your server private key
    'verify_peer' => false
], $loop);

$secure_websockets_server = new IoServer($server, $secure_websockets, $loop);
$secure_websockets_server->run();