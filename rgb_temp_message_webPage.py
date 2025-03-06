import network
import socket
import machine
import neopixel
import dht
import ssd1306
import time

# === WiFi Configuration ===
SSID = "TampleDiago"
PASSWORD = "12345688"

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(SSID, PASSWORD)

while not sta.isconnected():
    time.sleep(1)
print("Connected! Station IP:", sta.ifconfig()[0])

ssid_ap = "Muneeb1368"
password_ap = "12345678"
auth_mode = network.AUTH_WPA2_PSK

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=ssid_ap, password=password_ap, authmode=auth_mode)
print("Access Point Active")
print("AP IP Address:", ap.ifconfig()[0])

# === NeoPixel Setup ===
pin = 48
pixel = 1
np = neopixel.NeoPixel(machine.Pin(pin), pixel)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()
    print(f"Set Color to: R={r}, G={g}, B={b}")

# === DHT11 Sensor Setup ===
dht_pin = machine.Pin(4)
sensor = dht.DHT11(dht_pin)

def read_dht():
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()
        return temp, hum
    except Exception as e:
        print("DHT Error:", e)
        return "Error", "Error"

# === OLED Display Setup ===
i2c = machine.SoftI2C(scl=machine.Pin(9), sda=machine.Pin(8))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def update_oled(message):
    oled.fill(0)
    oled.text("Message:", 0, 0)
    oled.text(message, 0, 20)
    oled.show()
    print("OLED Updated:", message)

# === Weather Condition Logic ===
def get_weather_condition(temp, hum):
    if temp == "Error" or hum == "Error":
        return "Unknown"
    temp = float(temp)
    hum = float(hum)
    
    if 25 <= temp <= 30 and 40 <= hum <= 50:
        return "Normal"
    elif temp < 25 and hum < 40:
        return "Dry or Cool"
    elif 20 <= temp <= 30 and hum > 64:
        return "Cool or Moist"
    elif temp > 40 and hum < 50:
        return "Hot or Dry"
    else:
        return "Other"

# === Web Server Setup ===
def webpage(temp, hum, message):
    weather = get_weather_condition(temp, hum)
    html = """<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Control Panel</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1e1e2f, #2a4066);
            color: #fff;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        h2 {
            text-align: center;
            color: #00f05c;
            text-shadow: 0 0 10px rgba(0, 240, 92, 0.8);
            margin-bottom: 30px;
        }
        .main-container {
            display: flex;
            justify-content: center;
            gap: 30px;
            max-width: 900px;
            margin: auto;
        }
        .left-column {
            display: flex;
            flex-direction: column;
            gap: 20px;
            width: 320px;
        }
        .right-column {
            width: 320px;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 240, 92, 0.3);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(0, 240, 92, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .container:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0, 240, 92, 0.5);
        }
        h3 {
            color: #00f05c;
            margin-top: 0;
            text-shadow: 0 0 5px rgba(0, 240, 92, 0.6);
        }
        .input-group {
            margin-bottom: 5px;
        }
        .input-group label {
            display: inline-block;
            width: 60px;
            color: #e0e0e0;
        }
        .input-group input[type="number"],
        input[type="text"] {
            width: 120px;
            padding: 8px;
            border: none;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            outline: none;
            transition: background 0.3s ease;
            margin-bottom: 10px;
        }
        .input-group input:focus {
            background: rgba(255, 255, 255, 0.3);
        }
        button {
            background: linear-gradient(45deg, #00f05c, #00c4b4);
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            color: #fff;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 15px rgba(0, 240, 92, 0.7);
        }
        .sensor-reading {
            background: linear-gradient(90deg, #00f05c33, #00c4b433);
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0px 50px 0px;
            margin-top: 10px;
            animation: glow 2s infinite alternate;
        }
        @keyframes glow {
            from { box-shadow: 0 0 10px rgba(0, 240, 92, 0.3); }
            to { box-shadow: 0 0 20px rgba(0, 240, 92, 0.6); }
        }
        .sensor-reading p {
            margin: 5px 0;
            color: #e0e0e0;
        }
        .sensor-reading strong {
            color: #fff;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <h2>ESP32 RGB & Sensor Control</h2>
    <div class="main-container">
        <div class="left-column">
            <div class="container">
                <h3>Set NeoPixel Color</h3>
                <form action="/" method="GET">
                    <div class="input-group">
                        <label>Red:</label> <input type="number" name="r" min="0" max="255"><br>
                        <label>Green:</label> <input type="number" name="g" min="0" max="255"><br>
                        <label>Blue:</label> <input type="number" name="b" min="0" max="255"><br>
                    </div>
                    <button type="submit">Set Color</button>
                </form>
            </div>
            <div class="container">
                <h3>Update OLED Display</h3>
                <form action="/" method="GET">
                    <input type="text" name="msg" placeholder="Enter message" maxlength="20">
                    <button type="submit">Send to OLED</button>
                </form>
                <p>Last Message: <strong>""" + str(message) + """</strong></p>
            </div>
        </div>
        <div class="right-column">
            <div class="container">
                <h3>Temperature & Humidity</h3>
                <div class="sensor-reading">
                    <p>Temperature: <strong>""" + str(temp) + """C</strong></p>
                    <p>Humidity: <strong>""" + str(hum) + """%</strong></p>
                    <p>Weather: <strong>""" + str(weather) + """</strong></p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    return html

# Initialize socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((sta.ifconfig()[0], 80))
s.listen(5)

oled_message = "Hello!"

while True:
    conn, addr = s.accept()
    print('Got connection from', addr)
    request = conn.recv(1024).decode()
    print("Request Received:\n", request)

    if "favicon.ico" in request:
        conn.close()
        continue

    # Default values
    r, g, b = 0, 0, 0
    message = oled_message

    # Parse GET request parameters
    try:
        if '?' in request:
            params = request.split('?')[1].split(' ')[0]
            pairs = params.split('&')
            for pair in pairs:
                key, value = pair.split('=')
                if key == 'r':
                    r = int(value)
                elif key == 'g':
                    g = int(value)
                elif key == 'b':
                    b = int(value)
                elif key == 'msg':
                    message = value.replace('+', ' ')[:20]
    except Exception as e:
        print("Error parsing request:", e)

    print(f"Parsed Values - R: {r}, G: {g}, B: {b}, Message: {message}")
    # Update hardware
    set_color(r, g, b)
    update_oled(message)
    oled_message = message

    # read sensor data
    temp, hum = read_dht()

    # Send response
    response = webpage(temp, hum, message)
    conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
    conn.send(response)
    conn.close()
