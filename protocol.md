S2C
Board:
welche farbe man ist, danach fen
`b w rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq fr 0 1` file, rank als zahl, start 0

B2O
Move: `mfrfrp` file, rank als zahl, start 0, promotion kbrq0

S2C
Available Moves: `Mfrfrfrfrfrfr...` file, rank als zahl, start 0

S2C
Eval: `e<n>[m<M>]` n centipawns für weiß, matt in M zügen

S2C
Cap: `c`

C2S
Request: `r<s|b|g>` s -> Session id, b -> board, n = new game, s = stockfish, g = public games

S2C
List of public games: `[{"name": "...", "id": ..., "color": "w/b/r"}]` als Json formatiert weil name

C2S
New Game: `n<s<stufe>|p><w/b/r><pub|prv><Name>` neues spiel erstellen, wenn stockfish einzelspieler, wenn player -> Game-id, id ist [0x0000;0xffff], color als w/b/r, private = nur mit id joinbar, Name ist Spielername

S2C
Game-Id: `i<id>`

Stockfish-stufen:
* w: worstfish mit eval
* W: worstfish mit depth
* 1: 1 ms
* e: eval
* d: depth 18
* D: depth 25
* n: 50k nodes
* N: 1M nodes
* t: 100 ms
* T: 1500 ms

C2S
Join: `j<id>` spiel beitreten

S2C
Session id: `s<id>`