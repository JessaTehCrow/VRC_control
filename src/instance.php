<?php
namespace MyApp;

use Ratchet\ConnectionInterface;

function new_id($length = idLength) {
    $characters = '0123456789BCDEFGHIJKLMNOPQRSTUVWXYZ';
    $charactersLength = strlen($characters);
    $randomString = '';
    for ($i = 0; $i < $length; $i++) {
        $randomString .= $characters[random_int(0, $charactersLength - 1)];
    }
    return $randomString;
}

class Instance {
    public string $id;
    public bool $closed;

    protected $clients;
    protected array $data;

    private ConnectionInterface $host;
    private string $password;

    function __construct($host, $password, $data) {
        foreach ($data as $key => $value) {
            array_push($data[$key], false);
        }

        $this->clients = new \SplObjectStorage;
        $this->host = $host;
        $this->password = $password;
        $this->id = new_id();
        $this->closed = false;
        $this->data = $data;
        $this->connect($host, $password);

        debug("\x1b[1;32mCreated room \x1b[0m{$this->id}\x1b[1;32m by user {$host->resourceId}");
    }


    function is_host(ConnectionInterface $conn) {
        return $conn == $this->host;
    }


    function close() {
        foreach ($this->clients as $client) {
            $client->send(Errors::$DISCONNECTED);
        }

        $this->closed = true;
        
        debug("\x1b[1;31mClosed room \x1b[0m{$this->id}");
    }


    function connect($conn, $password) {
        if ($password != $this->password) {
            return [false, Errors::$WRONG_PASSWORD];
        }
        $conn->send(json_encode(["type" => "connected", "data" => ["id"=>$this->id, "password"=>$this->password, "data"=>$this->data]]));
        debug("\x1b[1;32mUser ($conn->resourceId) connected to room \x1b[0m{$this->id}");
        $this->clients->attach($conn);
        return [true, ""];
    }


    function disconnect($conn) {
        $conn->send(Errors::$DISCONNECTED);
        
        debug("\x1b[1;31mUser ({$conn->resourceId}) disconnected from room \x1b[0m{$this->id}");
        
        if ($conn == $this->host) {
            debug("\x1b[1;31mClosing room \x1b[0m{$this->id}");
            $this->close();
        }
        $this->clients->detach($conn);
    }


    function send(string $json, $host=null) {
        foreach ($this->clients as $client) {
            if ($client != $host){
                $client->send($json);
            }
        }
    }


    function update(array $data, $host): array {
        $lock = isset($data["locked"]);

        if (!isset($this->data[$data["name"]])) {
            return [false,Errors::$WRONG_PARAMETER];
        }

        if (!$lock && !is_type($this->data[$data["name"]][0], $data["value"])) {
            return [false, Errors::$WRONG_VALUE];
        }
        
        if ($lock) {
            $this->data[$data["name"]][2] = $data["locked"];
        } else {
            $this->data[$data["name"]][1] = $data["value"];
        }
        
        $info = $this->data[$data["name"]];
        $this->send(json_encode([
            "type" => "update",
            "data" => [
                "name" => $data["name"],
                "type" => $info[0],
                "value" => $info[1],
                "locked" => $info[2]
            ]
        ]), $host);
        return [true,""];
    }
}


class Instances {
    private array $instances;

    protected array $clients;

    function new_instance(ConnectionInterface $host, string $password, array $data) {
        $instance = new Instance($host, $password, $data);
        $this->instances[$instance->id] = $instance;
    }


    function is_instance(string $id) {
        return isset($this->instances[$id]);
    }


    function get_instance(string $id) {
        if (!$this->is_instance($id)) {
            return false;
        }

        return $this->instances[$id];
    }


    function connect(array $request, $client) {
        $success = false;
        $password = "";

        if (!isset($request["data"]["id"])) {
            return [false, Errors::$NO_ID];
        }
        if (isset($request["data"]["password"])) {
            $password = $request["data"]["password"];
        }

        $id = $request["data"]["id"];
        if ($this->is_instance($id)) {
            $instance = $this->instances[$id];
            [$success, $error] = $instance->connect($client, $password);

            if (!$success) {
                return [false,$error];
            }

            $client_hash = spl_object_hash($client);
            $this->clients[$client_hash] = $id;
            
            $result = ["message" => "Successfully connected to room", "data" => ["id" => $id]];

        } else {
            $result = ["message" => "Room ID does not exist"];
        }
        
        $result["success"] = $success;
        return [$success,json_encode($result)];
    }


    function create(array $request, $client) {
        $client_hash = spl_object_hash($client);
        
        if (!isset($request["data"])) {
            return [false, Errors::$NO_DATA];
        }
        elseif (!all_set($request["data"], ["data"]) || !valid_data($request["data"]["data"])) {
            return [false, Errors::$WRONG_DATA];
        }
        
        $password = "";
        if (isset($request["data"]["password"])) {
            $password = $request["data"]["password"];    
        }

        if (strlen($password) > maxPasswordLength) {
            return [false, Errors::$PASSWORD_TOO_LONG];
        }

        $instance = new Instance($client, $password, $request["data"]["data"]);
        $id = $instance->id;

        $this->instances[$id] = $instance;
        $this->clients[$client_hash] = $id;

        return [true,json_encode(["success" => true, "message" => "Room created", "data" => ["id" => $id, "password" => $password]])];
    }


    function get_client_instance($client): bool|Instance {
        $client_hash = spl_object_hash($client);

        if (isset($this->clients[$client_hash])) {
            $instance_id = $this->clients[$client_hash];

            if (!isset($this->instances[$instance_id])) {
                $this->clients[$client_hash] = null;
                return false;

            } else if ($this->instances[$instance_id]->closed) {
                return false;
            }

            return $this->instances[$this->clients[$client_hash]];
        }
        return false;
    }

    function disconnect($client) {
        $client_hash = spl_object_hash($client);

        
        $instance = $this->get_client_instance($client);
        if (!$instance) {
            return;
        }
        
        $instance->disconnect($client);
        if ($instance->closed) {
            unset($this->instances[$instance->id]);
        }
        
        $this->clients[$client_hash] = null;
    }
}