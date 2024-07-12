# API details

## To Server

### Types

- `connect`
- `reconnect`
- `create`
- `disconnect`
- `update`

___

### Connect

- Web call

#### sent

```json
{
    "type":"connect",
    "data": {
        "id": ROOM_ID > String,
        "password": PASSWORD > String
    }
}
```

#### result

```json
{
    "success":true,
    "message":"Successfully connected to room",
    "data": {
        "id": ROOM_ID
    }
}
```

or

```json
{
    "success":false, 
    "message": ERROR_MESSAGE > string
}
```

### reconnect

- Client call

#### Sent

```json
{
    "type": "reconnect",
    "data": {
        "id": ROOM_ID > string,
        "secret": SECRET_ID > string,
    }
}
```

Returns

```json
    "type":"reconnect",
    "success":true,
    "message":"Successfully reconnected to room"
```
___

### create

- Client call

#### Sent

```json
{
    "type":"create",
    "data":{
        "password" : PASSWORD > string,
        "data": {
            KEY > string : [
                TYPE > string,
                VALUE > Any,
            ]
            . . .
        }
    }
}
```

#### Result

```json 
{
    "type":"create"
    "success":true,
    "message":"Room created",
    "data": {
        "id": ROOM_ID,
        "password": PASSWORD,
        "secret": SECRET_ID,
    }
}
```

or

```json
{
    "success":false, 
    "message": ERROR_MESSAGE > string
}
```

___

### Disconnect

- Client call
- Web call

#### Sent

```json 
{
    "type":"disconnect"
}
```

#### Result

```json
{
    "type":"disconnect",
    "success":false, 
    "message":"Disconnected from room"
}
```

___ 

### Update

- Web call

#### Sent

```json 
{
    "type":"update",
    "data":{
        "name": KEY_NAME > string,
        "type": TYPE > string,
        "value": VALUE > any,
        "locked": LOCKED > bool
    }
}
```