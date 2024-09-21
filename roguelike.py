import random
import os
import heapq
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Dungeon and player stats initialization
WIDTH = 20
HEIGHT = 10
player_health = 100
max_health = 100
level = 1
player_x = WIDTH // 2
player_y = HEIGHT // 2

# Define enemy types
enemies = []
enemy_types = {'X': {'base_health': 10, 'damage': 5}, 'E': {'base_health': 20, 'damage': 10}}  # Scaling health
fireballs = []  # To store fireballs in flight

# Dungeon creation
def create_dungeon():
    global dungeon, WIDTH, HEIGHT
    dungeon = [['.' for _ in range(WIDTH)] for _ in range(HEIGHT)]

    # Randomly place walls
    for i in range(int(WIDTH * HEIGHT * 0.2)):  # 20% walls
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        dungeon[y][x] = '#'

# A* pathfinding algorithm for enemies
def a_star_search(start, goal):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while open_list:
        _, current = heapq.heappop(open_list)

        if current == goal:
            break

        neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Adjacent movement (up, down, left, right)
        for dx, dy in neighbors:
            next_pos = (current[0] + dx, current[1] + dy)
            if 0 <= next_pos[0] < WIDTH and 0 <= next_pos[1] < HEIGHT and dungeon[next_pos[1]][next_pos[0]] != '#':
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(goal, next_pos)
                    heapq.heappush(open_list, (priority, next_pos))
                    came_from[next_pos] = current

    # Reconstruct path
    current = goal
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

# Function to spawn an enemy at a random position
def spawn_enemy(type_char):
    while True:
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        if dungeon[y][x] == '.' and (x != player_x or y != player_y):  # Avoid player position
            return {'x': x, 'y': y, 'type': type_char, 'health': enemy_types[type_char]['base_health'] + level * 5}

# Function to place enemies based on level
def place_enemies():
    global enemies
    enemies = []
    if level % 5 == 0:
        enemies.extend([spawn_enemy('E') for _ in range(level // 5)])  # Stronger enemies on every 5th level
    else:
        enemies.extend([spawn_enemy('X') for _ in range(level)])  # Scale enemies with level

# Function to display the dungeon, enemies, player, and fireballs
def display_dungeon():
    os.system('clear')  # For Windows, use 'cls' instead of 'clear'

    # Display health bar with color
    health_percentage = player_health / max_health * 100
    if health_percentage >= 70:
        health_color = Fore.GREEN
    elif health_percentage >= 40:
        health_color = Fore.YELLOW
    else:
        health_color = Fore.RED

    health_bar = '[' + '#' * (player_health * 10 // max_health) + ' ' * (10 - (player_health * 10 // max_health)) + ']'
    print(f"Health: {health_color}{health_bar} {player_health}/{max_health}")

    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x == player_x and y == player_y:
                print(Fore.GREEN + Style.BRIGHT + '@', end='')  # Bold and green player
            else:
                enemy_here = False
                fireball_here = False
                for enemy in enemies:
                    if enemy['x'] == x and enemy['y'] == y:
                        print(Fore.RED + Style.BRIGHT + enemy['type'], end='')  # Bold and red enemies
                        enemy_here = True
                        break
                for fireball in fireballs:
                    if fireball['x'] == x and fireball['y'] == y:
                        print(Fore.RED + 'F', end='')  # Red fireball
                        fireball_here = True
                        break
                if not enemy_here and not fireball_here:
                    print(dungeon[y][x], end='')
        print()

# Function to handle player movement
def move_player(dx, dy):
    global player_x, player_y
    new_x = player_x + dx
    new_y = player_y + dy

    # Check if the new position is within bounds and not a wall
    if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT and dungeon[new_y][new_x] != '#':
        player_x = new_x
        player_y = new_y

# Enemy movement using A* pathfinding
def move_enemies():
    global player_health
    for enemy in enemies[:]:  # Use a copy of the list to avoid modification errors
        path = a_star_search((enemy['x'], enemy['y']), (player_x, player_y))
        if path:  # If a path exists, move the enemy along the path
            next_step = path[0]
            enemy['x'], enemy['y'] = next_step

        # Check if the enemy has reached the player
        if enemy['x'] == player_x and enemy['y'] == player_y:
            print(f"Enemy {enemy['type']} attacks!")
            player_health -= enemy_types[enemy['type']]['damage']
            if player_health <= 0:
                print("You have been killed by the enemy!")
                return False  # End game
    return True

# Combat when the player moves into an enemy tile
def check_for_combat():
    global player_health
    for enemy in enemies[:]:  # Use a copy of the list to allow removal
        if player_x == enemy['x'] and player_y == enemy['y']:
            print(f"Fighting enemy {enemy['type']}!")
            enemy['health'] -= 10 + level * 2  # Player deals damage, scaling with level
            player_health -= enemy_types[enemy['type']]['damage']  # Enemy attacks back
            print(f"Enemy {enemy['type']} health: {enemy['health']}")
            if enemy['health'] <= 0:
                print(f"Enemy {enemy['type']} has been defeated!")
                enemies.remove(enemy)
            if player_health <= 0:
                print("You have been killed!")
                return False  # End the game if the player dies

# Fireball combat
def shoot_fireball(direction):
    global fireballs
    fireball_speed = 2  # Fireball moves 2 tiles per turn
    dx, dy = 0, 0
    if direction == 'w':  # Up
        dx, dy = 0, -1
    elif direction == 's':  # Down
        dx, dy = 0, 1
    elif direction == 'a':  # Left
        dx, dy = -1, 0
    elif direction == 'd':  # Right
        dx, dy = 1, 0

    # Fireball initial position
    fireball_x, fireball_y = player_x + dx, player_y + dy
    fireballs.append({'x': fireball_x, 'y': fireball_y, 'dx': dx, 'dy': dy, 'speed': fireball_speed})

# Move fireballs
def move_fireballs():
    global fireballs
    for fireball in fireballs[:]:
        for _ in range(fireball['speed']):  # Fireball moves 2 tiles per turn
            fireball['x'] += fireball['dx']
            fireball['y'] += fireball['dy']

            # Check for collision with walls
            if fireball['x'] < 0 or fireball['x'] >= WIDTH or fireball['y'] < 0 or fireball['y'] >= HEIGHT or dungeon[fireball['y']][fireball['x']] == '#':
                fireballs.remove(fireball)
                break

            # Check for collision with enemies
            for enemy in enemies[:]:  # Iterate over a copy to allow removal
                if fireball['x'] == enemy['x'] and fireball['y'] == enemy['y']:
                    print(f"Fireball hit enemy {enemy['type']}!")
                    enemy['health'] -= 20 + level * 5  # Fireball damage increases with level
                    if enemy['health'] <= 0:
                        print(f"Enemy {enemy['type']} has been defeated by fireball!")
                        enemies.remove(enemy)
                    fireballs.remove(fireball)
                    break

# Level progression
def next_level():
    global WIDTH, HEIGHT, player_health, max_health, level, player_x, player_y
    level += 1
    WIDTH += 5
    HEIGHT += 5
    player_health = min(player_health + 40, max_health)  # Heal more as the level increases
    max_health += 10  # Increase max health per level
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    create_dungeon()
    place_enemies()

# Game loop
def game_loop():
    global player_health
    create_dungeon()
    place_enemies()

    while player_health > 0:
        display_dungeon()
        action = input("Move (WASD), Shoot (X), or Quit (Q): ").lower()

        if action == 'w':  # Up
            move_player(0, -1)
        elif action == 's':  # Down
            move_player(0, 1)
        elif action == 'a':  # Left
            move_player(-1, 0)
        elif action == 'd':  # Right
            move_player(1, 0)
        elif action == 'x':  # Shooting
            direction = input("Aim direction (WASD): ").lower()
            shoot_fireball(direction)
            move_fireballs()
            continue
        elif action == 'q':  # Quit the game
            print("Thanks for playing!")
            break

        check_for_combat()

        # Move enemies after player
        if not move_enemies():
            break  # End game if the player is dead

        # Move fireballs
        move_fireballs()

        # If no enemies are left, move to the next level
        if not enemies:
            print(f"Level {level} cleared! Proceeding to the next level.")
            next_level()

    print("Game over! You died.")

if __name__ == '__main__':
    game_loop()
