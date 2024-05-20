import socket
import json
import numpy as np
from ursina import *
import random
import threading

# Function to handle data reception in a separate thread
def receive_data():
    global data, conn, running
    while running:
        try:
            data = conn.recv(1024).decode('utf-8')
        except socket.error:
            running = False
            break

def update():
    global offset, collision, movement, score, life, data, t0, movement, movement_counter

    #Variable setting
    acceleration = score / 10000000
    score += 1 / 10
    player_speed = time.dt * 0.15
    offset += player_speed + acceleration
    train_speed = [time.dt * 0.45, time.dt * 0.25]
    train_spawn = [2, 1.2]
    gravity = 0.05

    #Recieve data
    if data:
        try:
            if data.count('{') != 1:
                choose = 0
                buffer_data = data.split('}')
                while buffer_data[choose][0] != '{':
                    choose += 1
                data = buffer_data[choose] + '}'
            obj = json.loads(data)
            if movement != "":
                if movement_counter < 20:
                    match movement:
                        case "RIGHT":
                            if movement_counter < 20:
                                player.x += 0.4
                                movement_counter += 1
                        case "LEFT":
                            if movement_counter < 20:
                                player.x -= 0.4
                                movement_counter += 1
                        case "UP":
                            if movement_counter < 20:
                                player.y += 0.3
                                movement_counter += 1
                        case "DOWN":
                            gravity = 0.2
                            movement = ""
                else:
                    movement = ""
                    movement_counter = 0
            else:
                t1 = time.time()
                if obj['motion'] == "RIGHT" and player.x < 8 and t1 - t0 >= 0.6:
                    movement = "RIGHT"
                    t0 = time.time()
                if obj['motion'] == "LEFT" and player.x > -8 and t1 - t0 >= 0.6:
                    movement = "LEFT"
                    t0 = time.time()
                if obj['motion'] == "UP" and player.y == 1:
                    movement = "UP"
                if obj['motion']  == "DOWN":
                    movement = "DOWN"
        except json.JSONDecodeError:
            pass
    camera.position = (player.x, 6, -125)
    
    setattr(rail0, "texture_offset", (0, offset))
    setattr(rail1, "texture_offset", (0, offset))
    setattr(rail2, "texture_offset", (0, offset))

    #Collision
    hit_info = player.intersects()
    if hit_info.hit:
        collision = True
        player.y = 8
    if collision:
        player.rotation_x += time.dt * 400
        player.color = color.red
        if player.rotation_x >= 360:
            collision = False
            player.color = color.white
            player.rotation_x = 0
            life -= 1

    #Life and Score
    Score.text = f'Score : {int(score)}'
    Life.text = f'Life  : {life}'
    if life <= 0:
        print('score:', {score})
        quit()

    #Gravity
    if player.y > 1:
        player.y -= gravity
    if player.y < 1:
        player.y = 1

    #Block
    for block in blocks:
        block.z -= player_speed + acceleration
        if block.z < -0.7:
            block.position = (1 * random.randint(-1, 1), 0.1, random.uniform(0.2, 1))

    #Train
    for train in trains:
        if train.rotation_y == 0:
            train.z -= train_speed[0] + acceleration
        else:
            train.z -= train_speed[1] + acceleration

        if train.z < -0.7:
            if train.rotation_y == 0:
                train.z = train_spawn[0]
            else:
                train.z = train_spawn[1]
            train.x = 1 * random.randint(-1, 1)

    if trains[0].x == trains[1].x:
        if trains[0].z >= trains[1].z:
            train_change = 0
        else:
            train_change = 1
        if trains[0].x == 0:
            if train_change:
                trains[1].x = random.choice([-1, 1])
            else:
                trains[0].x = random.choice([-1, 1])
        elif trains[0].x == -0.6:
            if train_change:
                trains[1].x = random.choice([0, 1])
            else:
                trains[0].x = random.choice([0, 1])
        else:
            if train_change:
                trains[1].x = random.choice([-1, 0])
            else:
                trains[0].x = random.choice([0, 1])

class Rail(Entity):
    def __init__(self, position):
        super().__init__()
        self.model = "cube"
        self.texture = "assets/rail.png"
        self.scale = (8, 0.5, 600)
        self.position = position

class Train(Entity):
    def __init__(self, position, angle):
        super().__init__()
        self.model = "assets/train.obj"
        self.texture = "assets/train.png"
        self.scale = (0.1, 1.3, 0.008)
        self.parent = rail0
        self.position = position
        self.collider = "box"
        self.rotation_y = angle

class Block(Entity):
    def __init__(self):
        super().__init__()
        self.model = "assets/block.obj"
        self.texture = "assets/block.png"
        self.parent = rail0
        self.scale = (0.025, 4, 0.18)
        self.position = (1 * random.randint(-1, 1), 0.5, random.random())
        self.collider = "box"
        self.rotation_y = 90

class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        self.model = "cube"
        self.texture = "assets/becky.png"
        self.scale = (2, 1, 0.0002)
        self.position = (0, 1.2, -95)
        self.collider = "box"
    # Key board control
    '''
    def input(self, key):
        if key == 'd' and self.x < 8:
            self.x += 8
        elif key == 'a' and self.x > -8:
            self.x -= 8
            camera.position.x -= 8
        elif key == 'space' and self.y == 1:
            self.y += 4
        elif key == 's' and self.y > 1:
            self.y = 1
    '''
app = Ursina()

HOST = '172.20.10.4'  # IP address
PORT = 8000  # Port to listen on (use ports > 1023)
data = ""
running = True

conn = socket.socket()
offset = 0
collision = False
movement = ""
movement_counter = 0
score = 0
life = 3

Score = Text(x=0.4, y=0.3)
Life = Text(x=0.4, y=0.32)
sky = Sky()

rail0 = Rail((0, 0, 0))
rail1 = Rail((-8, 0, 0))
rail2 = Rail((8, 0, 0))

train1 = Train((1, 1.2, .2), 0)
train2 = Train((-1, 1.2, .2), 180)
trains = [train1, train2]

blocks = []
for i in range(7):
    blocks.append(Block())

player = Player()

camera.position = (0, 6, -125)
camera.rotation_x = 4

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print("Starting server at:", (HOST, PORT))
conn, addr = s.accept()
print("Connected at", addr)

# Start a separate thread for data reception
threading.Thread(target=receive_data, daemon=True).start()

t0 = time.time()

app.run()
running = False
