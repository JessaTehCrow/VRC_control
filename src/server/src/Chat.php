<?php
namespace MyApp;

require "utils.php";
require "instance.php";
require "errors.php";

define("idLength", 5);
define("maxPasswordLength", 16);

use Ratchet\MessageComponentInterface;
use Ratchet\ConnectionInterface;

class Chat implements MessageComponentInterface {
    protected $instances;
    protected $unassigned_clients;


    public function __construct() {
        $this->unassigned_clients = new \SplObjectStorage;
        $this->instances = new Instances;
    }


    public function onOpen(ConnectionInterface $conn) {
        $this->unassigned_clients->attach($conn);
        debug("\x1b[1;33mNew connection ({$conn->resourceId})");
    }


    public function onMessage(ConnectionInterface $from, $msg) {
        $value = json_decode($msg, true);

        if ($value == NULL || !isset($value["type"])) {
            $from->send(Errors::$NO_TYPE);
            return;
        }

        $connected = $this->instances->get_client_instance($from);

        // Instance handling //

        // Connect to room
        if ($value["type"] == "connect") {
            if ($connected) {
                $from->send(Errors::$ALREADY_CONNECTED);
                return;
            }

            [$result, $response] = $this->instances->connect($value, $from);

            if ($result) {
                $this->unassigned_clients->detach($from);
                $from->send($response);

            } else {
                $from->send($response);
                return;
            }
        }

        // Create room
        elseif ($value["type"] == "create") {
            if ($connected) {
                $from->send(Errors::$ALREADY_CONNECTED);
                return;
            }

            [$result, $response] = $this->instances->create($value, $from);

            if ($result) {
                $this->unassigned_clients->detach($from);
            }

            $from->send($response);
        } 

        // Disconnect from room
        elseif ($value["type"] == "disconnect") {
            if (!$connected) {
                $from->send(Errors::$NOT_CONNECTED);
                return;
            }

            $this->instances->disconnect($from);
        }

        // Update values within room
        elseif ($value["type"] == "update") {
            if (!$connected) {
                $from->send(Errors::$NOT_CONNECTED);
                return;
            } elseif (!valid_update($value)) {
                $from->send(Errors::$WRONG_DATA);
                return;
            }
            [$status, $response] = $connected->update($value["data"], $from);
            if (!$status) {
                $from->send($response);
            }
        }

        // Fuck all
        else {
            $from->send(Errors::$WRONG_TYPE);
        }
    }


    public function onClose(ConnectionInterface $conn) {
        $this->instances->disconnect($conn);
        debug("\x1b[1;31mUser ({$conn->resourceId}) disconnected");
    }


    public function onError(ConnectionInterface $conn, \Exception $e) {
        echo "An error has occurred: {$e->getMessage()}\n";

        $conn->close();
    }
}