<?php

function debug(...$msg) {
    echo implode(" ", $msg) . "\x1b[0m\n";
}

function all_set(array $arr, array $values) {
    foreach ($values as $val) {
        if (!isset($arr[$val])){
            return false;
        }
    }
    return true;
}

function is_type($type, $value): bool {
    if ($type == "bool") {
        return is_bool($value);
    } elseif ($type == "float") {
        return is_float($value) || is_int($value);
    } elseif ($type == "int") {
        return is_int($value);
    } else {
        return false;
    }
}

function valid_value($value) {
    if (is_bool($value) || is_float($value) || is_int($value)) {
        return true;
    }
    return false;
}


function valid_update(array $data): bool {
    if (!isset($data["data"]["name"]) || !(isset($data["data"]["locked"]) || isset($data["data"]["value"]))) {
        return false;
    }
    $data = $data["data"];
    $name = $data["name"];

    if (!is_string($name)) {
        return false;
    }
    
    if (isset($data["locked"])) {
        if (!is_bool($data["locked"])) {
            return false;
        } 
    }
    elseif (!valid_value($data["value"])) {
        echo($data["value"]);
        return false;
    }
    
    return true;
}

function valid_data(array $data) {
    foreach ($data as $key => $value) {
        if (!is_array($value) || count($value) != 2 || !is_string($key)) {
            echo "fail 1";
            return false;
        }
        
        [$type, $value] = $value;
        if (!is_type($type, $value)) {
            return false;
        }
    }
    return true;
}