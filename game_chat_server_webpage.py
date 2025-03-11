import network
import socket
import machine
import random
import ssd1306
import time

# WiFi Setup
SSID = "TampleDiago"
PASSWORD = "12345689"
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(SSID, PASSWORD)
while not sta.isconnected():
    time.sleep(1)
print("Connected! IP:", sta.ifconfig()[0])

ssid_ap = "Muneeb1368"
password_ap = "12345678"
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid_ap, password=password_ap, authmode=network.AUTH_WPA2_PSK)
print("AP Active, IP:", ap.ifconfig()[0])

# OLED Setup
i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def update_oled(message):
    oled.fill(0)
    oled.text("Dice Game:", 0, 0)
    oled.text(message[:16], 0, 20)
    oled.text(message[16:32], 0, 40)
    oled.show()
    print("OLED:", message)

# Game Logic
players = {"P1": {"name": None, "rolls": [], "score": 0},
           "P2": {"name": None, "rolls": [], "score": 0}}
current_player = "P1"
game_started = False
game_over = False

def roll_dice():
    return random.randint(1, 6)

def switch_player():
    global current_player
    current_player = "P2" if current_player == "P1" else "P1"

def determine_winner():
    p1_score = players["P1"]["score"]
    p2_score = players["P2"]["score"]
    if p1_score > p2_score:
        return f"{players['P1']['name']} Wins! {p1_score}-{p2_score}"
    elif p2_score > p1_score:
        return f"{players['P2']['name']} Wins! {p2_score}-{p1_score}"
    return "Tie!"

def reset_game(full_reset=False):
    global players, current_player, game_started, game_over
    if full_reset:
        players = {"P1": {"name": None, "rolls": [], "score": 0},
                   "P2": {"name": None, "rolls": [], "score": 0}}
    else:
        players["P1"]["rolls"] = []
        players["P2"]["rolls"] = []
        players["P1"]["score"] = 0
        players["P2"]["score"] = 0
    current_player = "P1"
    game_started = not full_reset
    game_over = False

# Game Stats JSON
def game_stats_json():
    status = f"{players[current_player]['name']}'s Turn" if game_started and not game_over else "Join Game" if not game_started else determine_winner()
    return f'{{"p1_name": "{players["P1"]["name"] or ""}", "p1_rolls": "{",".join(map(str, players["P1"]["rolls"]))}", "p1_score": {players["P1"]["score"]}, "p2_name": "{players["P2"]["name"] or ""}", "p2_rolls": "{",".join(map(str, players["P2"]["rolls"]))}", "p2_score": {players["P2"]["score"]}, "game_started": {str(game_started).lower()}, "game_over": {str(game_over).lower()}, "status": "{status}"}}'

# Webpage
def webpage():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Dice Duel</title>
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #fff;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        h1 {
            font-size: 3em;
            color: #00ffcc;
            text-shadow: 0 0 15px rgba(0, 255, 204, 0.7);
            margin-bottom: 20px;
        }
        .join {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            width: 300px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            text-align: center;
        }
        .game-container {
            display: flex;
            gap: 20px;
            max-width: 800px;
            margin-top: 20px;
            display: none;
        }
        .game {
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
            width: 380px;
            background: linear-gradient(45deg, #1a1a2e, #16213e);
        }
        input {
            padding: 8px;
            border: none;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.9);
            color: #0f2027;
            width: 150px;
            margin: 5px 0;
        }
        button {
            padding: 10px;
            font-size: 1.1em;
            background: linear-gradient(45deg, #ff6b6b, #ff8e53);
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            width: 100%;
            margin: 5px 0;
            transition: all 0.3s ease;
        }
        button:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(255, 107, 107, 0.7);
        }
        button:disabled {
            background: #555;
        }
        .stats {
            margin-top: 15px;
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            font-size: 1.1em;
            color: #e0e0e0;
            text-align: left;
            line-height: 1.5;
        }
        .stats .player {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            padding: 5px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
        }
        .status {
            color: #ffd700;
            font-weight: bold;
            margin-top: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Dice Duel</h1>
    <div class="join" id="join">
        <form action="/" method="GET">
            <p><input id="p1_name" name="p1_name" placeholder="Player 1" maxlength="10"></p>
            <p><input id="p2_name" name="p2_name" placeholder="Player 2" maxlength="10"></p>
            <button type="submit" id="startButton" name="start" value="1">Start</button>
        </form>
    </div>
    <div class="game-container" id="gameContainer">
        <div class="game">
            <form action="/" method="GET">
                <button type="submit" id="rollButton" name="roll" value="1">Roll</button>
            </form>
            <form action="/" method="GET">
                <button type="submit" id="restartButton" name="restart" value="1" style="display: none;">Restart</button>
            </form>
            <form action="/" method="GET">
                <button type="submit" id="exitButton" name="exit" value="1" style="display: none;">Exit</button>
            </form>
            <div class="stats">
                <div class="player"><span id="p1_name_display"></span><span>Rolls: <span id="p1_rolls">None</span>, Score: <span id="p1_score">0</span></span></div>
                <div class="player"><span id="p2_name_display"></span><span>Rolls: <span id="p2_rolls">None</span>, Score: <span id="p2_score">0</span></span></div>
                <div class="status" id="status">Join Game</div>
            </div>
        </div>
    </div>
    <script>
        function refreshGame() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('join').style.display = data.game_started ? 'none' : 'block';
                    document.getElementById('gameContainer').style.display = data.game_started ? 'flex' : 'none';
                    if (data.game_started) {
                        document.getElementById('p1_name').disabled = true;
                        document.getElementById('p2_name').disabled = true;
                    }
                    document.getElementById('p1_name_display').innerText = data.p1_name;
                    document.getElementById('p1_rolls').innerText = data.p1_rolls || 'None';
                    document.getElementById('p1_score').innerText = data.p1_score;
                    document.getElementById('p2_name_display').innerText = data.p2_name;
                    document.getElementById('p2_rolls').innerText = data.p2_rolls || 'None';
                    document.getElementById('p2_score').innerText = data.p2_score;
                    document.getElementById('status').innerText = data.status;
                    document.getElementById('rollButton').disabled = !data.game_started || data.game_over;
                    document.getElementById('restartButton').style.display = data.game_over ? 'block' : 'none';
                    document.getElementById('exitButton').style.display = data.game_over ? 'block' : 'none';
                });
        }
        setInterval(refreshGame, 2000);
        window.onload = refreshGame;
    </script>
</body>
</html>"""
    return html

# Server Loop
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((sta.ifconfig()[0], 80))
s.listen(5)

while True:
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        print("Request Received:\n", request)

        if "favicon.ico" in request:
            conn.send("HTTP/1.1 404 Not Found\r\n\r\n")
        elif "/stats" in request:
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{game_stats_json()}".encode())
        else:
            if '?' in request:
                params = dict(pair.split('=') for pair in request.split('?')[1].split(' ')[0].split('&'))
                if 'p1_name' in params and not players["P1"]["name"]:
                    players["P1"]["name"] = params['p1_name'].replace('+', ' ')[:10]
                    update_oled(f"{players['P1']['name']} joined!")
                if 'p2_name' in params and not players["P2"]["name"]:
                    players["P2"]["name"] = params['p2_name'].replace('+', ' ')[:10]
                    update_oled(f"{players['P2']['name']} joined!")
                if 'start' in params and params['start'] == '1' and players["P1"]["name"] and players["P2"]["name"] and not game_started:
                    game_started = True
                    update_oled("Game Started!")
                if 'roll' in params and params['roll'] == '1' and game_started and not game_over:
                    if len(players[current_player]["rolls"]) < 6:
                        dice_result = roll_dice()
                        players[current_player]["rolls"].append(dice_result)
                        players[current_player]["score"] += dice_result
                        update_oled(f"{players[current_player]['name']}: {dice_result}")
                        switch_player()
                    if len(players["P1"]["rolls"]) == 6 and len(players["P2"]["rolls"]) == 6:
                        game_over = True
                        winner = determine_winner()
                        update_oled(winner)
                if 'restart' in params and params['restart'] == '1' and game_over:
                    reset_game()
                    update_oled("Game Restarted!")
                if 'exit' in params and params['exit'] == '1' and game_over:
                    reset_game(full_reset=True)
                    update_oled("Game Exited!")
            conn.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{webpage()}".encode())
        conn.close()

    except Exception as e:
        print("Error:", e)
        conn.close()