import pygame
import random
from collections import deque
import time
import serial
 
# Initialize pygame
pygame.init()
 
# Define constants for the window size and colors
CELL_SIZE = 30  # Reduced cell size for a smaller, more complex maze
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
BACKGROUND_COLOR = (245, 245, 245)
WALL_COLOR = (50, 50, 50)
PLAYER_COLOR = (30, 144, 255)  # Dodger Blue for the player
TRACE_COLOR = (173, 216, 230)  # Light Blue for AI trace
GOAL_COLOR = (220, 20, 60)  # Crimson for the goal
GUIDE_COLOR = (255, 215, 0)  # Gold for the guide AI
NUMERO_COM = "3"
 
 
# ser = serial.Serial(
#     port='/dev/ttyS0',  # Replace with your port, e.g., 'COM3' for Windows
#     baudrate=115200,    # Match the baud rate of your UART device
#     bytesize=serial.EIGHTBITS,
#     parity=serial.PARITY_NONE,
#     stopbits=serial.STOPBITS_ONE,
#     timeout=1           # Optional: Timeout for read operations
# )
 
 
# Function to generate the maze with a path
def generate_maze(width, height):
    maze = [['#' for _ in range(2 * width + 1)] for _ in range(2 * height + 1)]
   
    def carve_passages(x, y):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        maze[2 * y + 1][2 * x + 1] = ' '  # Mark cell as open
 
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and maze[2 * ny + 1][2 * nx + 1] == '#':
                maze[y + ny + 1][x + nx + 1] = ' '  # Open the wall
                carve_passages(nx, ny)
 
    carve_passages(0, 0)
    maze[1][1] = ' '  # Start position
    maze[2 * height - 1][2 * width - 1] = ' '  # Goal position
    return maze
 
# Pathfinding algorithm (Breadth-first search) to find the shortest path
def find_path(maze, start, goal):
    queue = deque([(start, [start])])
    visited = set()
 
    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == goal:
            return path
 
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= ny < len(maze) and 0 <= nx < len(maze[0]) and maze[ny][nx] == ' ' and (nx, ny) not in visited:
                queue.append(((nx, ny), path + [(nx, ny)]))
                visited.add((nx, ny))
 
    return []
 
# Function to calculate Manhattan distance to the goal
def manhattan_distance(pos, goal):
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
 
# Function to draw the maze, the player, guide AI, and AI path trace
def draw_maze(window, maze, player_pos, guide_pos, path, goal_pos):
    window.fill(BACKGROUND_COLOR)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == '#':
                pygame.draw.rect(window, WALL_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(window, BACKGROUND_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
 
    # Draw AI path trace
    for (px, py) in path:
        pygame.draw.rect(window, TRACE_COLOR, (px * CELL_SIZE, py * CELL_SIZE, CELL_SIZE, CELL_SIZE))
 
    # Draw player
    pygame.draw.rect(window, PLAYER_COLOR, (player_pos[0] * CELL_SIZE, player_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
 
    # Draw guide AI
    pygame.draw.rect(window, GUIDE_COLOR, (guide_pos[0] * CELL_SIZE, guide_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
   
    # Draw goal
    pygame.draw.rect(window, GOAL_COLOR, (goal_pos[0] * CELL_SIZE, goal_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
 
    pygame.display.update()
 
# Function to move the player
def move_player(player_pos, direction, maze):
    x, y = player_pos
    if direction == 'up' and maze[y - 1][x] != '#':
        return (x, y - 1)
    elif direction == 'down' and maze[y + 1][x] != '#':
        return (x, y + 1)
    elif direction == 'left' and maze[y][x - 1] != '#':
        return (x - 1, y)
    elif direction == 'right' and maze[y][x + 1] != '#':
        return (x + 1, y)
    return player_pos
 
# Function to update the guide AI position towards the goal
def move_guide(guide_pos, path):
    if guide_pos in path:
        next_index = path.index(guide_pos) + 1
        if next_index < len(path):
            return path[next_index]
    return guide_pos
 
def send_maze(maze, player_pos, path, ser):
    for index_ligne, val_ligne in enumerate(maze):
        for index_colonne, val_colonne in enumerate(val_ligne):
            maze_pos = (index_ligne, index_colonne)
            if(maze_pos == player_pos):
                ser.write('X'.encode("utf-8"))
            elif(check_Ai_Path(maze_pos, path)):
                ser.write('P'.encode("utf-8"))
            elif(val_colonne == '#'):
                ser.write("M".encode("utf-8"))
            elif(val_colonne == ' '):
                ser.write('0'.encode("utf-8"))
        ser.write('N'.encode("utf-8"))
 
def check_Ai_Path(maze_pos, path):
    for i in path:
        if(maze_pos == i):
            return True
    return False
 
# Main game function
def main():
    # Set up the game window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Maze Game with Guide AI")
 
    # Initialize maze parameters
    #maze_width = random.randint(5, 7)  # Smaller width for a more compact maze
    #maze_height = random.randint(5, 6)  # Smaller height for a more compact maze
    maze_width = 4
    maze_height = 3
    maze = generate_maze(maze_width, maze_height)
    start, goal = (1, 1), (2 * maze_width - 1, 2 * maze_height - 1)
 
    player_pos = start  # Player starts at the top-left
    guide_pos = start  # Guide AI starts with the player
    path = find_path(maze, start, goal)  # AI's path from start to goal
 
    # Game loop variables
    running = True
    path_index = 0
    last_move_time = time.time()
    last_distance = manhattan_distance(player_pos, goal)
 
    ser = serial.Serial(
        port = 'COM' + NUMERO_COM,
        baudrate=19200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
   
    while running:
        # Draw maze and player with AI trace and guide AI
        draw_maze(window, maze, player_pos, guide_pos, path[:path_index], goal)
        send_maze(maze, player_pos, path, ser)
        # Check for quit event and key presses for player movement
        moved = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    player_pos = move_player(player_pos, 'up', maze)
                    moved = True
                elif event.key == pygame.K_s:
                    player_pos = move_player(player_pos, 'down', maze)
                    moved = True
                elif event.key == pygame.K_a:
                    player_pos = move_player(player_pos, 'left', maze)
                    moved = True
                elif event.key == pygame.K_d:
                    player_pos = move_player(player_pos, 'right', maze)
                    moved = True
 
        # Check if player moved and update last_move_time
        #### THE PROB IS here we need tho update the maze.
        # if moved:
        #     last_move_time = time.time()
 
        #     # Check if the player moved further from the goal
        #     current_distance = manhattan_distance(player_pos, goal)
        #     if current_distance > last_distance:
        #         path_index = len(path)  # Show full path if the player is off-course
        #     else:
        #         last_distance = current_distance
 
        # Show guide AI path if inactive for over 3 seconds
        if moved:
             last_move_time = time.time()
        if time.time() - last_move_time > 20:
           
            path_index = len(path)
 
        # Update guide AI position along the path
        guide_pos = move_guide(guide_pos, path)
 
        # Check if player has reached the goal
        if player_pos == goal:
            font = pygame.font.SysFont(None, 36)
            text = font.render("Congratulations!", True, GOAL_COLOR)
            window.blit(text, (150, WINDOW_HEIGHT // 2))
            pygame.display.update()
            pygame.time.wait(2000)  # Wait 2 seconds before closing
            running = False
 
        pygame.time.Clock().tick(15)  # Control the game frame rate
 
    pygame.quit()
 
# Run the game
if __name__ == "__main__":
    main()