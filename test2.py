import websocket

def error(*a):
    print(a)


while True:
    app = websocket.WebSocketApp("ws://localhost:8080", on_error=error)
    app.run_forever()
