import pygame
import sys
import random
import math

# ==========================================
# 1. KONFIGURASI DAN PARAMETER GLOBAL
# ==========================================
pygame.init()

TILE = 30  # Ukuran satu kotak grid (piksel)
ROWS = 21
COLS = 19
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE
FPS = 60

# Definisi Warna (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (33, 33, 255)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
PINK = (255, 184, 255)
ORANGE = (255, 184, 82)

# Peta Level (1: Dinding, . : Titik Makanan, 0: Ruang Kosong, P: Pacman, G: Hantu)
LEVEL_MAP = [
    "1111111111111111111",
    "1........1........1",
    "1.11.111.1.111.11.1",
    "1.................1",
    "1.11.1.11111.1.11.1",
    "1....1...1...1....1",
    "1111.111 0 111.1111",
    "0000.1   G   1.0000",
    "1111.1 11111 1.1111",
    "0000.0 1G G1 0.0000",
    "1111.1 11111 1.1111",
    "0000.1   G   1.0000",
    "1111.1 11111 1.1111",
    "1........1........1",
    "1.11.111.1.111.11.1",
    "1..1.....P.....1..1",
    "11.1.1.11111.1.1.11",
    "1....1...1...1....1",
    "1.111111.1.111111.1",
    "1.................1",
    "1111111111111111111"
]

# ==========================================
# 2. KELAS ENTITAS (PLAYER & MUSUH)
# ==========================================
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE - 4, TILE - 4)
        self.rect.center = (x + TILE // 2, y + TILE // 2)
        self.speed = 3
        self.dx = 0
        self.dy = 0
        self.next_dx = 0
        self.next_dy = 0
        self.angle = 0
        self.anim_timer = 0
        self.score = 0

    def move(self, walls):
        # 1. Coba bergerak ke arah yang ditekan (next_direction)
        test_rect = self.rect.copy()
        test_rect.x += self.next_dx * self.speed
        test_rect.y += self.next_dy * self.speed

        collision = False
        for wall in walls:
            if test_rect.colliderect(wall):
                collision = True
                break

        # Jika arah yang ditekan bebas dari halangan, ubah arah utama
        if not collision:
            self.dx = self.next_dx
            self.dy = self.next_dy

            # Menentukan sudut rotasi untuk render (menghadap ke mana)
            if self.dx > 0: self.angle = 0
            elif self.dx < 0: self.angle = 180
            elif self.dy > 0: self.angle = 270
            elif self.dy < 0: self.angle = 90

        # 2. Eksekusi pergerakan di Sumbu X
        self.rect.x += self.dx * self.speed
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.dx > 0: self.rect.right = wall.left
                if self.dx < 0: self.rect.left = wall.right

        # 3. Eksekusi pergerakan di Sumbu Y
        self.rect.y += self.dy * self.speed
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.dy > 0: self.rect.bottom = wall.top
                if self.dy < 0: self.rect.top = wall.bottom

        # Mekanisme Screen Wrap (tembus layar kiri ke kanan)
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH

    def draw(self, surface):
        self.anim_timer += 1
        center = self.rect.center
        radius = TILE // 2 - 2

        # Animasi buka-tutup mulut Pac-Man
        if (self.anim_timer // 8) % 2 == 0:
            # Mulut setengah terbuka (gambar lingkaran lalu potong dengan polygon hitam)
            pygame.draw.circle(surface, YELLOW, center, radius)
            
            # Kalkulasi titik potong polygon untuk mulut
            # Kita menggunakan trigonometri dasar untuk rotasi
            angle_rad = math.radians(self.angle)
            p1 = center
            p2_x = center[0] + radius * 1.5 * math.cos(math.radians(self.angle + 30))
            p2_y = center[1] - radius * 1.5 * math.sin(math.radians(self.angle + 30))
            p3_x = center[0] + radius * 1.5 * math.cos(math.radians(self.angle - 30))
            p3_y = center[1] - radius * 1.5 * math.sin(math.radians(self.angle - 30))
            
            pygame.draw.polygon(surface, BLACK, [p1, (p2_x, p2_y), (p3_x, p3_y)])
        else:
            # Mulut penuh
            pygame.draw.circle(surface, YELLOW, center, radius)

class Ghost:
    def __init__(self, x, y, color):
        self.start_x = x
        self.start_y = y
        self.rect = pygame.Rect(x, y, TILE - 4, TILE - 4)
        self.rect.center = (x + TILE // 2, y + TILE // 2)
        self.speed = 2
        self.dx = random.choice([-1, 1])
        self.dy = 0
        self.color = color

    def move(self, walls):
        # AI Sederhana: Bergerak terus hingga menabrak/di persimpangan, lalu acak arah
        self.rect.x += self.dx * self.speed
        collision_x = False
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.dx > 0: self.rect.right = wall.left
                if self.dx < 0: self.rect.left = wall.right
                collision_x = True

        self.rect.y += self.dy * self.speed
        collision_y = False
        for wall in walls:
            if self.rect.colliderect(wall):
                if self.dy > 0: self.rect.bottom = wall.top
                if self.dy < 0: self.rect.top = wall.bottom
                collision_y = True

        # Wrap around seperti player
        if self.rect.left > WIDTH: self.rect.right = 0
        if self.rect.right < 0: self.rect.left = WIDTH

        # Jika menabrak, pilih arah baru secara dinamis
        if collision_x or collision_y or random.random() < 0.015:
            valid_directions = []
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            
            for d in directions:
                test_rect = self.rect.copy()
                # Proyeksi ke depan sedikit untuk mengecek ketersediaan jalur
                test_rect.x += d[0] * self.speed * 8 
                test_rect.y += d[1] * self.speed * 8
                
                # Pastikan arah baru tidak menabrak dinding dan tidak berbalik arah secara instan
                if not any(test_rect.colliderect(w) for w in walls):
                    # Hindari berbalik 180 derajat kecuali terpaksa (jalan buntu)
                    if (d[0] * -1 != self.dx or d[1] * -1 != self.dy) or (collision_x and collision_y):
                        valid_directions.append(d)
            
            if valid_directions:
                new_dir = random.choice(valid_directions)
                self.dx, self.dy = new_dir[0], new_dir[1]

    def draw(self, surface):
        # Menggambar Hantu: Bentuk dasar gabungan lingkaran atas dan persegi bawah
        center_x, center_y = self.rect.center
        radius = TILE // 2 - 2
        
        # Kepala (Setengah lingkaran)
        pygame.draw.circle(surface, self.color, (center_x, center_y - 2), radius)
        # Badan (Persegi panjang)
        pygame.draw.rect(surface, self.color, (center_x - radius, center_y - 2, radius * 2 + 1, radius + 2))
        
        # Mata putih
        pygame.draw.circle(surface, WHITE, (center_x - 4, center_y - 4), 3)
        pygame.draw.circle(surface, WHITE, (center_x + 4, center_y - 4), 3)
        # Pupil biru
        pygame.draw.circle(surface, BLUE, (center_x - 4 + self.dx*2, center_y - 4 + self.dy*2), 1)
        pygame.draw.circle(surface, BLUE, (center_x + 4 + self.dx*2, center_y - 4 + self.dy*2), 1)

# ==========================================
# 3. KONTROL UTAMA (GAME ENGINE)
# ==========================================
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 40)) # +40px untuk area skor
    pygame.display.set_caption("Pac-Man Python Terstruktur")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("impact", 24)

    # Parsing Peta
    walls = []
    dots = []
    ghosts = []
    player = None
    ghost_colors = [RED, CYAN, PINK, ORANGE]
    ghost_index = 0

    for row_idx, row in enumerate(LEVEL_MAP):
        for col_idx, char in enumerate(row):
            x = col_idx * TILE
            y = row_idx * TILE
            if char == '1':
                walls.append(pygame.Rect(x, y, TILE, TILE))
            elif char == '.':
                # Posisi titik adalah pusat grid
                dots.append(pygame.Rect(x + TILE//2 - 3, y + TILE//2 - 3, 6, 6))
            elif char == 'P':
                player = Player(x, y)
            elif char == 'G':
                color = ghost_colors[ghost_index % len(ghost_colors)]
                ghosts.append(Ghost(x, y, color))
                ghost_index += 1

    game_over = False
    game_won = False

    # Main Game Loop
    running = True
    while running:
        clock.tick(FPS)
        
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over or game_won:
                    if event.key == pygame.K_r: # Restart logika
                        main()
                        return
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                else:
                    if event.key == pygame.K_UP:
                        player.next_dx, player.next_dy = 0, -1
                    elif event.key == pygame.K_DOWN:
                        player.next_dx, player.next_dy = 0, 1
                    elif event.key == pygame.K_LEFT:
                        player.next_dx, player.next_dy = -1, 0
                    elif event.key == pygame.K_RIGHT:
                        player.next_dx, player.next_dy = 1, 0

        # 2. Logika Pembaruan Status (Update)
        if not game_over and not game_won:
            player.move(walls)
            
            for ghost in ghosts:
                ghost.move(walls)
                # Tabrakan Hantu dan Player (Hitbox diperkecil agar lebih adil)
                if player.rect.colliderect(ghost.rect.inflate(-10, -10)):
                    game_over = True

            # Memakan Makanan (Dots)
            eaten_dots = [dot for dot in dots if player.rect.colliderect(dot)]
            for dot in eaten_dots:
                dots.remove(dot)
                player.score += 10

            if len(dots) == 0:
                game_won = True

        # 3. Proses Render Layar (Draw)
        screen.fill(BLACK)

        # Gambar Dinding
        for wall in walls:
            pygame.draw.rect(screen, BLUE, wall, 1, border_radius=4)
            # Isi dalam dinding dengan biru gelap
            inner_wall = wall.inflate(-4, -4)
            pygame.draw.rect(screen, (0, 0, 100), inner_wall, border_radius=4)

        # Gambar Titik Makanan
        for dot in dots:
            pygame.draw.rect(screen, WHITE, dot, border_radius=3)

        # Gambar Entitas
        if not game_over:
            player.draw(screen)
        for ghost in ghosts:
            ghost.draw(screen)

        # UI (Score Bar)
        score_text = font.render(f"SCORE: {player.score}", True, WHITE)
        screen.blit(score_text, (10, HEIGHT + 5))

        # Status Akhir
        if game_over:
            go_text = font.render("GAME OVER! Press 'R' to Restart", True, RED)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2))
        elif game_won:
            win_text = font.render("YOU WIN! Press 'R' to Restart", True, YELLOW)
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Menjalankan engine
    main()