# centrifugo-ws-chat

Learning centrifugo websocket

- Front - Jinja template
- Back - Python FastAPI
- WebSocket Server - [centrifugo](https://github.com/centrifugal/centrifugo)

Run dev container
```sh
docker-compose -f dev_compose.yaml up -d
docker-compose -f dev_compose.yaml ps
docker-compose -f dev_compose.yaml logs
```


Admin UI method publish
```json
{
  "user_id": "test",
  "text": "text"
}
```



### Other projects examples:
- https://github.com/Desire456/awesome-docker-compose/blob/76713c21bb8691609b0cb41f9cddaa1fcadd812b/centrifugo/config.json
- https://github.com/centrifugal/examples/blob/master/v6/leaderboard/backend/app.py
- ...


### TO DO:
- database (message history)
- redis (consumers)
