<?php
namespace MyApp;

class Errors{
    
    public static $NO_DATA = '{"success":false, "message":"No data supplied"}';
    public static $NO_ID = '{"success":false, "message":"No room ID provided"}';
    public static $NO_TYPE = '{"success":false, "message":"No type supplied"}';
    
    public static $WRONG_PASSWORD = '{"success":false, "message":"Invalid password for room"}';
    public static $WRONG_TYPE = '{"success":false, "message":"Invalid type supplied"}';
    public static $WRONG_DATA = '{"success":false, "message":"Invalid data supplied"}';
    public static $WRONG_PARAMETER = '{"success":false, "message":"Parameter does not exist"}';
    public static $WRONG_VALUE = '{"success":false, "message":"Invalid paramater value"}';
    
    public static $NOT_IN_INSTANCE = '{"success":false, "message":"Not in instance"}';
    public static $NOT_CONNECTED = '{"success":false, "message":"Not connected to any room"}';
    
    public static $PASSWORD_TOO_LONG = '{"success":false, "message":"Incorrect password for room"}';
    public static $DISCONNECTED = '{"type":"disconnect","success":false, "message":"Disconnected from room"}';
    public static $ALREADY_CONNECTED = '{"success":false, "message":"Already connected to a room"}';

}