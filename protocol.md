S2C
Board:
welche farbe man ist, danach fen
`b<w/b>rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq fr 0 1` file, rank als zahl, start 0

B2B
Move: `mfrfrp` file, rank als zahl, start 0, promotion kbrq0

S2C
Available Moves: `M<frfr><frfr><frfr>...` file, rank als zahl, start 0, promotion von client dazuzudenken

S2C
Eval: `e<n>[m<M>]` n centipawns für weiß, matt in M zügen

S2C
Cap: `c`

C2S
Request: `r<s|b|g|m>` s -> Session id, b -> board, g -> open games, m -> valid moves

S2C
List of open games: `o[{"name": "...", "id": ..., "color": "w/b/r"}]` als Json formatiert weil name

C2S
New Game: `n<s<stufe>|p><w/b/r><pub|prv><Name>` neues spiel erstellen, wenn stockfish einzelspieler, wenn player -> Game-id, id ist [0000;zzzz] (Base 36), color als w/b/r, private = nur mit id joinbar, Name ist Spielername
Session-id ist [000000;zzzzzz] (Base 36)

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
* r: random

C2S
Join: `j<id><Name>` spiel beitreten, id = [0000;zzzz]

B2B
Client Session id: `s<id>`

S2C
Error: `E<e|i|F>` e = game is already full (or doesn't exist), i = invalid new game request, F = wrong format

S2C
Opponent name: `O<name>`