import pygame
import random
import math
import time
import numpy as np

# Initialize Pygame
pygame.init()

# --- AUDIO SYNTHESIS SYSTEM ---
# We synthesize audio in-memory using NumPy so there are no external file dependencies.
class SoundManager:
    def __init__(self):
        self.enabled = True
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.generate_sounds()
        except Exception as e:
            print(f"Audio initialization failed: {e}. Running without sound.")
            self.enabled = False

    def make_sound_from_array(self, data, sample_rate=44100):
        # Scale and convert float array [-1.0, 1.0] to 16-bit signed PCM
        audio_data = (data * 32767 * 0.3).astype(np.int16)
        # Convert mono to stereo (duplicate channel)
        stereo_data = np.repeat(audio_data[:, None], 2, axis=1)
        return pygame.sndarray.make_sound(stereo_data)

    def generate_sounds(self):
        sample_rate = 44100

        # 1. Click Sound: short high-pitched blip
        click_dur = 0.05
        t_click = np.linspace(0, click_dur, int(sample_rate * click_dur), False)
        click_wave = np.sin(2 * np.pi * 1200 * t_click) * np.exp(-50 * t_click)
        self.sounds['click'] = self.make_sound_from_array(click_wave)

        # 2. Flag Sound: dual-tone quick pop
        flag_dur = 0.1
        t_flag = np.linspace(0, flag_dur, int(sample_rate * flag_dur), False)
        flag_wave = (np.sin(2 * np.pi * 600 * t_flag) + np.sin(2 * np.pi * 300 * t_flag)) * 0.5 * np.exp(-25 * t_flag)
        self.sounds['flag'] = self.make_sound_from_array(flag_wave)

        # 3. Main Explosion: deep bass rumble + sliding tone + decaying noise
        exp_dur = 1.0
        n_samples = int(sample_rate * exp_dur)
        t_exp = np.linspace(0, exp_dur, n_samples, False)
        # Noise component
        noise = np.random.uniform(-1.0, 1.0, n_samples)
        # Deep frequency sweep (120Hz down to 20Hz)
        freqs = np.linspace(120, 20, n_samples)
        phase = 2 * np.pi * np.cumsum(freqs) / sample_rate
        sub_bass = np.sin(phase)
        # Combine noise and sub-bass, then apply exponential decay
        exp_wave = (sub_bass * 0.6 + noise * 0.4) * np.exp(-4 * t_exp)
        self.sounds['explosion'] = self.make_sound_from_array(exp_wave)

        # 4. Small Cascade Explosion: slightly shorter, higher pitch/tighter rumble
        exp_s_dur = 0.4
        n_s_samples = int(sample_rate * exp_s_dur)
        t_s_exp = np.linspace(0, exp_s_dur, n_s_samples, False)
        noise_s = np.random.uniform(-1.0, 1.0, n_s_samples)
        freqs_s = np.linspace(160, 40, n_s_samples)
        phase_s = 2 * np.pi * np.cumsum(freqs_s) / sample_rate
        sub_s = np.sin(phase_s)
        exp_s_wave = (sub_s * 0.5 + noise_s * 0.5) * np.exp(-8 * t_s_exp) * 0.6  # softer volume
        self.sounds['explosion_small'] = self.make_sound_from_array(exp_s_wave)

        # 5. Victory Chime: ascending major 7th arpeggio
        vic_dur = 1.2
        t_vic = np.linspace(0, vic_dur, int(sample_rate * vic_dur), False)
        vic_wave = np.zeros_like(t_vic)
        # Notes: C5 (523.25), E5 (659.25), G5 (783.99), B5 (987.77), C6 (1046.50)
        chord = [523.25, 659.25, 783.99, 987.77, 1046.50]
        for idx, freq in enumerate(chord):
            delay = idx * 0.15
            start_idx = int(delay * sample_rate)
            t_note = t_vic[start_idx:] - delay
            note_wave = np.sin(2 * np.pi * freq * t_note) * np.exp(-5 * t_note)
            vic_wave[start_idx:] += note_wave * 0.35
        # Soft clip to prevent distortion
        vic_wave = np.clip(vic_wave, -1.0, 1.0)
        self.sounds['victory'] = self.make_sound_from_array(vic_wave)

    def play(self, sound_name):
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()


# --- SCREEN SHAKE MODULE ---
class ScreenShake:
    def __init__(self):
        self.intensity = 0.0
        self.duration = 0
        self.dx = 0
        self.dy = 0

    def trigger(self, intensity, duration):
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)

    def update(self):
        if self.duration > 0:
            self.dx = random.randint(-int(self.intensity), int(self.intensity))
            self.dy = random.randint(-int(self.intensity), int(self.intensity))
            # Slowly decay
            self.intensity *= 0.9
            self.duration -= 1
        else:
            self.dx = 0
            self.dy = 0


# --- PARTICLE MODULE ---
class Particle:
    def __init__(self, x, y, p_type):
        self.x = x
        self.y = y
        self.p_type = p_type  # 'fire', 'smoke', 'spark', 'debris', 'victory'
        self.life = 1.0
        
        angle = random.uniform(0, 2 * math.pi)
        
        if p_type == 'fire':
            speed = random.uniform(1.5, 6.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.radius = random.uniform(5, 12)
            self.decay = random.uniform(0.015, 0.035)
            self.gravity = 0.04
            self.drag = 0.95
        elif p_type == 'smoke':
            speed = random.uniform(0.5, 2.0)
            self.vx = math.cos(angle) * speed * 0.5
            self.vy = -random.uniform(0.8, 2.5) # drift upwards
            self.radius = random.uniform(8, 16)
            self.decay = random.uniform(0.01, 0.02)
            self.gravity = -0.01
            self.drag = 0.98
        elif p_type == 'spark':
            speed = random.uniform(6.0, 14.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.radius = random.uniform(1.5, 3.5)
            self.decay = random.uniform(0.03, 0.06)
            self.gravity = 0.1
            self.drag = 0.93
        elif p_type == 'debris':
            speed = random.uniform(2.0, 5.0)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed - 2.0  # slight pop up
            self.radius = random.uniform(2.5, 5.5)
            self.decay = random.uniform(0.01, 0.02)
            self.gravity = 0.22
            self.drag = 0.985
            self.color = random.choice([
                (71, 85, 105), (100, 116, 139), (47, 55, 71), (30, 41, 59)
            ])
            self.angle = random.uniform(0, 360)
            self.rot_speed = random.uniform(-10, 10)
        elif p_type == 'victory':
            # Confetti shooting upwards
            self.vx = random.uniform(-2.5, 2.5)
            self.vy = -random.uniform(9.0, 17.0)
            self.radius = random.uniform(4, 9)
            self.decay = random.uniform(0.01, 0.018)
            self.gravity = 0.25
            self.drag = 0.975
            self.color = random.choice([
                (236, 72, 153),   # pink
                (6, 182, 212),    # cyan
                (16, 185, 129),   # emerald
                (245, 158, 11),   # amber
                (139, 92, 246),   # violet
                (239, 68, 68)     # red
            ])
            self.angle = random.uniform(0, 360)
            self.rot_speed = random.uniform(-12, 12)

    def update(self):
        if self.p_type in ['debris', 'victory']:
            self.angle += self.rot_speed
            
        self.vy += self.gravity
        self.vx *= self.drag
        self.vy *= self.drag
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surface):
        if self.life <= 0:
            return
        
        alpha = int(self.life * 255)
        
        if self.p_type == 'fire':
            # Dynamic colors based on life: White/Yellow -> Orange -> Red -> Slate
            if self.life > 0.65:
                color = (255, 255, 200)
            elif self.life > 0.4:
                color = (251, 146, 60) # orange-400
            elif self.life > 0.18:
                color = (239, 68, 68)  # red-500
            else:
                color = (71, 85, 105)  # slate-600
                
            rad = int(max(1, self.radius * self.life))
            
            # Simple soft glow using surface blitting (if radius is large enough)
            if rad > 3 and self.life > 0.3:
                glow_rad = rad * 2
                glow_surf = pygame.Surface((glow_rad * 2, glow_rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, alpha // 5), (glow_rad, glow_rad), glow_rad)
                surface.blit(glow_surf, (int(self.x - glow_rad), int(self.y - glow_rad)))
                
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), rad)
            
        elif self.p_type == 'smoke':
            # Expands and fades out
            rad = int(self.radius * (1.8 - self.life))
            if rad > 0:
                glow_surf = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                # Soft charcoal-grey smoke
                pygame.draw.circle(glow_surf, (15, 23, 42, alpha // 6), (rad, rad), rad)
                surface.blit(glow_surf, (int(self.x - rad), int(self.y - rad)))
                
        elif self.p_type == 'spark':
            # Draw spark as a line reflecting velocity direction
            speed = math.sqrt(self.vx**2 + self.vy**2)
            if speed > 0.1:
                dx = (self.vx / speed) * self.radius * 3.5
                dy = (self.vy / speed) * self.radius * 3.5
                color = (254, 240, 138) if random.random() > 0.4 else (251, 146, 60)
                pygame.draw.line(surface, color, (int(self.x), int(self.y)), (int(self.x - dx), int(self.y - dy)), int(max(1, self.radius)))
                
        elif self.p_type == 'debris':
            # Draw spinning polygon
            rad = int(max(1, self.radius))
            rad_deg = math.radians(self.angle)
            cos_a = math.cos(rad_deg)
            sin_a = math.sin(rad_deg)
            points = [
                (self.x + rad * cos_a - rad * sin_a, self.y + rad * sin_a + rad * cos_a),
                (self.x - rad * cos_a - rad * sin_a, self.y - rad * sin_a + rad * cos_a),
                (self.x - rad * cos_a + rad * sin_a, self.y - rad * sin_a - rad * cos_a),
                (self.x + rad * cos_a + rad * sin_a, self.y + rad * sin_a - rad * cos_a)
            ]
            pygame.draw.polygon(surface, self.color, points)
            
        elif self.p_type == 'victory':
            # Spinning confetti rectangles
            rad_w = int(max(1, self.radius))
            rad_h = int(max(1, self.radius * 0.5))
            rad_deg = math.radians(self.angle)
            cos_a = math.cos(rad_deg)
            sin_a = math.sin(rad_deg)
            points = [
                (self.x + rad_w * cos_a - rad_h * sin_a, self.y + rad_w * sin_a + rad_h * cos_a),
                (self.x - rad_w * cos_a - rad_h * sin_a, self.y - rad_w * sin_a + rad_h * cos_a),
                (self.x - rad_w * cos_a + rad_h * sin_a, self.y - rad_w * sin_a - rad_h * cos_a),
                (self.x + rad_w * cos_a + rad_h * sin_a, self.y + rad_w * sin_a + rad_h * cos_a)
            ]
            pygame.draw.polygon(surface, self.color, points)


# --- HELPERS FOR TEXT ---
def get_font(size, bold=False):
    fonts = ["segoeui", "centurygothic", "arial", "helvetica"]
    for name in fonts:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except:
            continue
    return pygame.font.Font(None, size)

def draw_glowing_text(surface, text, font, x, y, text_color, glow_color):
    # Render soft glow shadows
    glow_surf = font.render(text, True, glow_color)
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        surface.blit(glow_surf, (x + dx, y + dy))
    # Render foreground text
    main_surf = font.render(text, True, text_color)
    surface.blit(main_surf, (x, y))


# --- DRAWING VECTOR UTILITIES ---
def draw_flag_vector(surface, x, y, size):
    cx = x + size // 2
    cy = y + size // 2
    unit = size / 24

    # Gentle pulsing amber glow behind the flag
    pulse = math.sin(time.time() * 7) * 0.5 + 0.5
    glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (249, 115, 22, int(pulse * 30)), (size // 2, size // 2), int(size // 3.2))
    surface.blit(glow_surf, (x, y))

    # Flag pole (white)
    px = cx - unit
    py_start = cy - 6 * unit
    py_end = cy + 6 * unit
    pygame.draw.line(surface, (241, 245, 249), (px, py_start), (px, py_end), int(max(1.5, unit)))

    # Orange-red flag fabric triangle
    tx1 = px
    ty1 = py_start
    tx2 = cx + 6 * unit
    ty2 = cy - 2.5 * unit
    tx3 = px
    ty3 = cy + 1 * unit
    pygame.draw.polygon(surface, (239, 68, 68), [(tx1, ty1), (tx2, ty2), (tx3, ty3)])

    # Stand
    bx1 = cx - 4 * unit
    bx2 = cx + 2 * unit
    by = py_end
    pygame.draw.line(surface, (148, 163, 184), (bx1, by), (bx2, by), int(max(1.5, unit)))

def draw_bomb_vector(surface, cx, cy, size, is_exploded):
    rad = size * 0.28
    unit = size / 24

    if is_exploded:
        # Charred explosion look
        pygame.draw.circle(surface, (239, 68, 68), (int(cx), int(cy)), int(rad))
        pygame.draw.circle(surface, (245, 158, 11), (int(cx), int(cy)), int(rad * 0.6))
        pygame.draw.circle(surface, (255, 255, 255), (int(cx), int(cy)), int(rad * 0.25))
        return

    # Steel-grey body
    pygame.draw.circle(surface, (30, 41, 59), (int(cx), int(cy)), int(rad))
    # Glowing neon-red indicator core
    pygame.draw.circle(surface, (239, 68, 68), (int(cx), int(cy)), int(rad * 0.45))

    # Spikes sticking out
    spike_len = rad + 3 * unit
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad_deg = math.radians(angle)
        sx = cx + math.cos(rad_deg) * spike_len
        sy = cy + math.sin(rad_deg) * spike_len
        ex = cx + math.cos(rad_deg) * rad
        ey = cy + math.sin(rad_deg) * rad
        pygame.draw.line(surface, (15, 23, 42), (sx, sy), (ex, ey), int(max(1.5, unit)))


# --- CELL & BOARD OBJECTS ---
class Cell:
    def __init__(self, r, c):
        self.r = r
        self.c = c
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.is_exploded_mine = False
        self.neighbor_mines = 0

        # Animation states
        self.reveal_scale = 0.0
        self.is_revealing = False
        
        # Hover transparency
        self.hover_alpha = 0.0
        self.target_hover_alpha = 0.0


class Board:
    def __init__(self, rows, cols, num_mines, area_w, area_h, game):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.area_w = area_w
        self.area_h = area_h
        self.game = game

        # Calculate cell sizing to fit board area
        self.tile_size = min(area_w // cols, area_h // rows)
        self.board_w = self.tile_size * cols
        self.board_h = self.tile_size * rows
        self.offset_x = (area_w - self.board_w) // 2
        self.offset_y = (area_h - self.board_h) // 2

        self.grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
        self.first_click = True
        self.generated = False

        # Queues for animations and effects
        self.reveal_queue = [] # list of (cell, delay_frames)
        self.pending_explosions = [] # list of (r, c, distance) for cascading booms
        self.cascade_timer = 0

        # Colors for neighbors
        self.num_colors = {
            1: (6, 182, 212),    # Cyan
            2: (16, 185, 129),   # Green
            3: (239, 68, 68),    # Red
            4: (139, 92, 246),   # Purple
            5: (245, 158, 11),   # Amber
            6: (20, 184, 166),   # Teal
            7: (236, 72, 153),   # Pink
            8: (244, 63, 94)     # Rose
        }

    def generate(self, start_r, start_c):
        # Build list of available spots avoiding clicked cell + adjacent neighbors
        pool = []
        for r in range(self.rows):
            for c in range(self.cols):
                if abs(r - start_r) <= 1 and abs(c - start_c) <= 1:
                    continue
                pool.append((r, c))

        # Fallback if board is too small for buffer
        if len(pool) < self.num_mines:
            pool = []
            for r in range(self.rows):
                for c in range(self.cols):
                    if r == start_r and c == start_c:
                        continue
                    pool.append((r, c))

        mines = random.sample(pool, self.num_mines)
        for r, c in mines:
            self.grid[r][c].is_mine = True

        # Compute neighbor numbers
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    continue
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.grid[nr][nc].is_mine:
                                count += 1
                self.grid[r][c].neighbor_mines = count

        self.generated = True

    def queue_reveal(self, start_r, start_c):
        # BFS to discover all safe cells with ripple delays
        visited = set()
        queue = [(start_r, start_c, 0)]
        visited.add((start_r, start_c))

        to_reveal = []
        while queue:
            r, c, dist = queue.pop(0)
            to_reveal.append((self.grid[r][c], dist))

            if self.grid[r][c].neighbor_mines == 0 and not self.grid[r][c].is_mine:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if (nr, nc) not in visited and not self.grid[nr][nc].is_flagged:
                                visited.add((nr, nc))
                                queue.append((nr, nc, dist + 1))

        # Queue reveal animations with incremental delay
        for cell, dist in to_reveal:
            if not cell.is_revealed:
                # 2 frames delay per distance step creates a gorgeous sweep animation
                delay = dist * 2
                self.reveal_queue.append((cell, delay))

    def update(self):
        # Update cell animations
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                # Hover interpolation
                cell.hover_alpha += (cell.target_hover_alpha - cell.hover_alpha) * 0.15
                # Reveal interpolation
                if cell.is_revealing:
                    cell.reveal_scale += (1.0 - cell.reveal_scale) * 0.18
                    if cell.reveal_scale >= 0.99:
                        cell.reveal_scale = 1.0
                        cell.is_revealing = False

        # Process ripple reveal queue
        still_queued = []
        triggered_sound = False
        for cell, delay in self.reveal_queue:
            if delay <= 0:
                if not cell.is_revealed:
                    cell.is_revealed = True
                    cell.reveal_scale = 0.0
                    cell.is_revealing = True
                    if not triggered_sound and self.game.sound_enabled:
                        self.game.sounds.play('click')
                        triggered_sound = True
            else:
                still_queued.append((cell, delay - 1))
        self.reveal_queue = still_queued

        # Process cascading mine explosions
        if self.game.game_over and not self.game.won and self.pending_explosions:
            self.cascade_timer += 1
            # Trigger next explosion every 4 frames (approx 0.06s)
            if self.cascade_timer >= 4:
                self.cascade_timer = 0
                r, c, _ = self.pending_explosions.pop(0)
                cell = self.grid[r][c]
                cell.is_revealed = True
                cell.is_exploded_mine = True
                
                # Dynamic feedback
                if self.game.shake_enabled:
                    self.game.screen_shake.trigger(intensity=5.0, duration=8)
                if self.game.sound_enabled:
                    self.game.sounds.play('explosion_small')

                # Spawn explosive debris and sparks
                cx = self.offset_x + c * self.tile_size + self.tile_size // 2
                cy = self.offset_y + r * self.tile_size + self.tile_size // 2
                self.game.create_explosion(cx, cy, particle_count=40)

    def draw(self, surface):
        # Draw board grid base container
        pygame.draw.rect(surface, (15, 23, 42), (self.offset_x, self.offset_y, self.board_w, self.board_h), border_radius=12)
        # Outer thin grid border
        pygame.draw.rect(surface, (30, 41, 59), (self.offset_x, self.offset_y, self.board_w, self.board_h), width=2, border_radius=12)

        # Draw cells
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                x = self.offset_x + c * self.tile_size
                y = self.offset_y + r * self.tile_size

                if not cell.is_revealed:
                    # Draw unrevealed button
                    rect = pygame.Rect(x + 2, y + 2, self.tile_size - 4, self.tile_size - 4)
                    bg_color = (30, 41, 59) # slate-800
                    pygame.draw.rect(surface, bg_color, rect, border_radius=6)

                    # Border color styling
                    border_color = (51, 65, 85) # slate-700
                    if cell.hover_alpha > 0.02:
                        # Glow hover border
                        glow_r = int(51 + (6 - 51) * cell.hover_alpha)
                        glow_g = int(65 + (182 - 65) * cell.hover_alpha)
                        glow_b = int(85 + (212 - 85) * cell.hover_alpha)
                        border_color = (glow_r, glow_g, glow_b)
                        
                        # Soft background glow overlay
                        glow_surf = pygame.Surface((self.tile_size - 4, self.tile_size - 4), pygame.SRCALPHA)
                        pygame.draw.rect(glow_surf, (6, 182, 212, int(cell.hover_alpha * 40)), (0, 0, self.tile_size - 4, self.tile_size - 4), border_radius=6)
                        surface.blit(glow_surf, (x + 2, y + 2))
                    
                    pygame.draw.rect(surface, border_color, rect, width=1, border_radius=6)

                    # Flag indicator
                    if cell.is_flagged:
                        draw_flag_vector(surface, x, y, self.tile_size)

                else:
                    # Draw revealed recessed slot
                    cx = x + self.tile_size / 2
                    cy = y + self.tile_size / 2
                    w = (self.tile_size - 4) * cell.reveal_scale
                    h = (self.tile_size - 4) * cell.reveal_scale
                    
                    if w > 0 and h > 0:
                        rect = pygame.Rect(cx - w / 2, cy - h / 2, w, h)
                        # Dark void background
                        pygame.draw.rect(surface, (2, 6, 17), rect, border_radius=6)
                        pygame.draw.rect(surface, (15, 23, 42), rect, width=1, border_radius=6)

                        # Render content if scaling is sufficient
                        if cell.reveal_scale > 0.5:
                            if cell.is_mine:
                                draw_bomb_vector(surface, cx, cy, self.tile_size, cell.is_exploded_mine)
                            elif cell.neighbor_mines > 0:
                                # Standard numbers
                                num = cell.neighbor_mines
                                color = self.num_colors.get(num, (255, 255, 255))
                                f_size = int(self.tile_size * 0.62)
                                font = get_font(f_size, bold=True)
                                txt = font.render(str(num), True, color)
                                surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))

    def get_cell_at(self, board_mx, board_my):
        # Subtract board offsets to check grid coordinates
        grid_x = board_mx - self.offset_x
        grid_y = board_my - self.offset_y
        if 0 <= grid_x < self.board_w and 0 <= grid_y < self.board_h:
            c = int(grid_x // self.tile_size)
            r = int(grid_y // self.tile_size)
            if 0 <= r < self.rows and 0 <= c < self.cols:
                return self.grid[r][c]
        return None

    def trigger_defeat(self, clicked_cell):
        # Defeat trigger
        self.game.game_over = True
        self.game.won = False
        self.game.stop_timer()

        # Detonate clicked mine
        clicked_cell.is_revealed = True
        clicked_cell.is_exploded_mine = True

        # Big blast effects
        if self.game.sound_enabled:
            self.game.sounds.play('explosion')
        if self.game.shake_enabled:
            self.game.screen_shake.trigger(intensity=22.0, duration=35)

        cx = self.offset_x + clicked_cell.c * self.tile_size + self.tile_size // 2
        cy = self.offset_y + clicked_cell.r * self.tile_size + self.tile_size // 2
        self.game.create_explosion(cx, cy, particle_count=180)

        # Prepare sequential explosion list of other mines sorted by distance
        self.pending_explosions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine and not (r == clicked_cell.r and c == clicked_cell.c):
                    dist = math.sqrt((r - clicked_cell.r)**2 + (c - clicked_cell.c)**2)
                    self.pending_explosions.append((r, c, dist))

        # Sort so shockwave travels outwards
        self.pending_explosions.sort(key=lambda x: x[2])
        self.cascade_timer = 0

    def check_victory(self):
        # Win condition check
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                # If a non-mine cell is not revealed, game is not yet won
                if not cell.is_mine and not cell.is_revealed:
                    return False
        return True

    def trigger_victory(self):
        self.game.game_over = True
        self.game.won = True
        self.game.stop_timer()

        # Play beautiful win sound
        if self.game.sound_enabled:
            self.game.sounds.play('victory')

        # Auto-flag remaining unflagged mines for visual completion
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_mine and not cell.is_flagged:
                    cell.is_flagged = True

    def handle_chord(self, cell):
        # Fast double-click chord solver
        if not cell.is_revealed or cell.neighbor_mines == 0:
            return

        # Check neighbor flags
        flag_count = 0
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = cell.r + dr, cell.c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    n_cell = self.grid[nr][nc]
                    neighbors.append(n_cell)
                    if n_cell.is_flagged:
                        flag_count += 1

        if flag_count == cell.neighbor_mines:
            # Reveal all unflagged neighbors
            detonated_cell = None
            for n in neighbors:
                if not n.is_revealed and not n.is_flagged:
                    if n.is_mine:
                        detonated_cell = n
                    else:
                        if n.neighbor_mines == 0:
                            self.queue_reveal(n.r, n.c)
                        else:
                            n.is_revealed = True
                            n.is_revealing = True
                            n.reveal_scale = 0.0
                            if self.game.sound_enabled:
                                self.game.sounds.play('click')

            if detonated_cell:
                self.trigger_defeat(detonated_cell)
            elif self.check_victory():
                self.trigger_victory()


# --- INTERACTIVE CONTROL INTERFACES ---
class ChipButton:
    def __init__(self, x, y, w, h, text, is_selected_func):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.is_selected_func = is_selected_func
        self.rect = pygame.Rect(x, y, w, h)
        self.hover_val = 0.0

    def update(self, mouse_pos):
        target = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self.hover_val += (target - self.hover_val) * 0.18

    def draw(self, surface, font):
        selected = self.is_selected_func()

        if selected:
            # Active selection
            bg_color = (30, 41, 59)
            border_color = (6, 182, 212) # glowing cyan
            text_color = (255, 255, 255)
        else:
            # Idle/Hovered states
            bg_r = int(15 + (30 - 15) * self.hover_val)
            bg_g = int(23 + (41 - 23) * self.hover_val)
            bg_b = int(42 + (59 - 42) * self.hover_val)
            bg_color = (bg_r, bg_g, bg_b)

            bd_r = int(51 + (71 - 51) * self.hover_val)
            bd_g = int(65 + (85 - 65) * self.hover_val)
            bd_b = int(85 + (105 - 85) * self.hover_val)
            border_color = (bd_r, bd_g, bd_b)
            
            text_color = (148, 163, 184) if self.hover_val < 0.1 else (241, 245, 249)

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=8)

        # Glowing outline for selected chips
        if selected:
            glow_surf = pygame.Surface((self.w + 6, self.h + 6), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (6, 182, 212, 35), (0, 0, self.w + 6, self.h + 6), border_radius=10)
            surface.blit(glow_surf, (self.x - 3, self.y - 3))

        txt_surf = font.render(self.text, True, text_color)
        surface.blit(txt_surf, (self.x + (self.w - txt_surf.get_width()) // 2, self.y + (self.h - txt_surf.get_height()) // 2))

    def check_click(self, pos):
        return self.rect.collidepoint(pos)


class ActionButton:
    def __init__(self, x, y, w, h, text):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.hover_val = 0.0

    def update(self, mouse_pos):
        target = 1.0 if self.rect.collidepoint(mouse_pos) else 0.0
        self.hover_val += (target - self.hover_val) * 0.18

    def draw(self, surface, font):
        # Glow color blend
        bg_r = int(79 + (99 - 79) * self.hover_val)
        bg_g = int(70 + (90 - 70) * self.hover_val)
        bg_b = int(229 + (255 - 229) * self.hover_val)
        bg_color = (bg_r, bg_g, bg_b) # primary indigo/violet gradient

        if self.hover_val > 0.02:
            glow_surf = pygame.Surface((self.w + 12, self.h + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (99, 102, 241, int(self.hover_val * 45)), (0, 0, self.w + 12, self.h + 12), border_radius=14)
            surface.blit(glow_surf, (self.x - 6, self.y - 6))

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (129, 140, 248), self.rect, width=2, border_radius=10)

        txt_surf = font.render(self.text, True, (255, 255, 255))
        surface.blit(txt_surf, (self.x + (self.w - txt_surf.get_width()) // 2, self.y + (self.h - txt_surf.get_height()) // 2))

    def check_click(self, pos):
        return self.rect.collidepoint(pos)


class ToggleSwitch:
    def __init__(self, x, y, w, h, label, default=True):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.state = default
        self.val = 1.0 if default else 0.0
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        target = 1.0 if self.state else 0.0
        self.val += (target - self.val) * 0.22

    def draw(self, surface, font):
        # Draw parameter label
        lbl = font.render(self.label, True, (203, 213, 225))
        surface.blit(lbl, (self.x - lbl.get_width() - 15, self.y + (self.h - lbl.get_height()) // 2))

        # Background slider color transition: gray-500 to cyan-500
        r = int(71 + (6 - 71) * self.val)
        g = int(85 + (182 - 85) * self.val)
        b = int(105 + (212 - 105) * self.val)
        
        pygame.draw.rect(surface, (r, g, b), self.rect, border_radius=self.h // 2)

        # Knob offset calculations
        knob_r = (self.h - 6) // 2
        kx = self.x + 3 + knob_r + int(self.val * (self.w - 6 - knob_r * 2))
        ky = self.y + self.h // 2
        pygame.draw.circle(surface, (255, 255, 255), (kx, ky), knob_r)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.state = not self.state
            return True
        return False


# --- MAIN GAME APPLICATION ---
class Game:
    def __init__(self):
        self.screen_w = 1024
        self.screen_h = 768
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Neon Mines // Cyberpunk Minesweeper")

        self.clock = pygame.time.Clock()
        self.running = True

        # System controllers
        self.sounds = SoundManager()
        self.screen_shake = ScreenShake()
        
        # User settings
        self.sound_enabled = self.sounds.enabled
        self.shake_enabled = True
        self.particles_enabled = True

        # Game states
        self.difficulty = "medium"  # easy, medium, hard
        self.game_over = False
        self.won = False
        
        # Timer variables
        self.timer_started = False
        self.start_time = 0
        self.elapsed_time = 0

        # Dynamic particles list
        self.particles = []

        # Create sidebar components
        self.setup_ui()
        
        # Build layout grid
        self.init_board()

    def setup_ui(self):
        # 1. Difficulty toggle chips
        self.diff_buttons = [
            ChipButton(25, 120, 70, 36, "EASY", lambda: self.difficulty == "easy"),
            ChipButton(105, 120, 75, 36, "MEDIUM", lambda: self.difficulty == "medium"),
            ChipButton(190, 120, 70, 36, "HARD", lambda: self.difficulty == "hard")
        ]

        # 2. Main actions
        self.restart_button = ActionButton(25, 480, 230, 48, "INITIALIZE RESET")

        # 3. Parameter toggles
        self.toggles = [
            ToggleSwitch(205, 570, 50, 24, "SOUND EFFECTS", self.sound_enabled),
            ToggleSwitch(205, 615, 50, 24, "SCREEN SHAKE", self.shake_enabled),
            ToggleSwitch(205, 660, 50, 24, "PARTICLES", self.particles_enabled)
        ]

    def init_board(self):
        # Difficulty matrices configurations
        if self.difficulty == "easy":
            rows, cols, mines = 9, 9, 10
        elif self.difficulty == "medium":
            rows, cols, mines = 16, 16, 40
        else: # hard
            rows, cols, mines = 16, 30, 99

        # Space bounds for right-aligned board canvas
        board_area_w = 700
        board_area_h = 700
        self.board = Board(rows, cols, mines, board_area_w, board_area_h, self)
        
        # Refresh timing variables
        self.timer_started = False
        self.start_time = 0
        self.elapsed_time = 0
        self.game_over = False
        self.won = False
        self.particles.clear()

    def start_timer(self):
        self.timer_started = True
        self.start_time = time.time() - self.elapsed_time

    def stop_timer(self):
        self.timer_started = False

    def update_timer(self):
        if self.timer_started and not self.game_over:
            self.elapsed_time = int(time.time() - self.start_time)

    def create_explosion(self, x, y, particle_count=100):
        if not self.particles_enabled:
            return
        
        # Add diverse particle types to make explosion multi-layered and dynamic
        # Flames
        for _ in range(int(particle_count * 0.4)):
            self.particles.append(Particle(x, y, 'fire'))
        # Smoke puffs
        for _ in range(int(particle_count * 0.25)):
            self.particles.append(Particle(x, y, 'smoke'))
        # High speed sparks
        for _ in range(int(particle_count * 0.2)):
            self.particles.append(Particle(x, y, 'spark'))
        # Shrapnel / solid debris
        for _ in range(int(particle_count * 0.15)):
            self.particles.append(Particle(x, y, 'debris'))

    def trigger_victory_effects(self):
        if not self.particles_enabled:
            return
        # Continuous stream from bottom-left and bottom-right corners
        for px in [300, 980]:
            for _ in range(12):
                self.particles.append(Particle(px, 730, 'victory'))

    def update(self):
        # Update system shakes
        self.screen_shake.update()

        # Update sidebar interface controls
        m_pos = pygame.mouse.get_pos()
        for b in self.diff_buttons:
            b.update(m_pos)
        self.restart_button.update(m_pos)
        for t in self.toggles:
            t.update()

        # Maintain configurations with switches
        self.sound_enabled = self.toggles[0].state and self.sounds.enabled
        self.shake_enabled = self.toggles[1].state
        self.particles_enabled = self.toggles[2].state

        # Update grid board logic
        self.board.update()

        # Tick timer
        self.update_timer()

        # Victory firework trigger tick
        if self.game_over and self.won and random.random() < 0.12:
            self.trigger_victory_effects()

        # Process active particles physics
        still_alive = []
        for p in self.particles:
            p.update()
            if p.life > 0:
                still_alive.append(p)
        self.particles = still_alive

    def draw(self):
        # Dark cyberpunk slate-950 viewport background
        self.screen.fill((2, 6, 17))

        # --- DRAW SIDEBAR ---
        # Sidebar divider backdrop
        pygame.draw.rect(self.screen, (15, 23, 42), (0, 0, 280, self.screen_h))
        pygame.draw.line(self.screen, (30, 41, 59), (280, 0), (280, self.screen_h), width=2)

        # Title block
        draw_glowing_text(self.screen, "NEON MINES", get_font(38, bold=True), 25, 30, (255, 255, 255), (6, 182, 212))
        lbl_sub = get_font(14).render("CYBERNETIC PROXIMITY GRID", True, (71, 85, 105))
        self.screen.blit(lbl_sub, (25, 75))

        # Section headings
        lbl_h1 = get_font(16, bold=True).render("DIFFICULTY PRESET", True, (148, 163, 184))
        self.screen.blit(lbl_h1, (25, 100))

        # Draw presets
        for b in self.diff_buttons:
            b.draw(self.screen, get_font(13, bold=True))

        # --- STATS PANEL ---
        # Draw glowing slate-900 box
        stats_rect = pygame.Rect(25, 175, 230, 280)
        pygame.draw.rect(self.screen, (9, 15, 30), stats_rect, border_radius=12)
        pygame.draw.rect(self.screen, (30, 41, 59), stats_rect, width=2, border_radius=12)

        # 1. System state orb
        orb_x, orb_y = 55, 215
        if self.game_over:
            orb_color = (239, 68, 68) if not self.won else (16, 185, 129)
            orb_txt = "SYSTEM DEPLOYED" if self.won else "GRID CORRUPTED"
            glow_col = (16, 185, 129) if self.won else (239, 68, 68)
        else:
            orb_color = (6, 182, 212)
            orb_txt = "MONITORING ACTIVE"
            glow_col = (6, 182, 212)

        # Glowing pulsing core
        pulse = math.sin(time.time() * 6) * 0.4 + 0.6
        glow_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_col, int(pulse * 50)), (16, 16), int(12 * pulse + 4))
        self.screen.blit(glow_surf, (orb_x - 16, orb_y - 16))
        pygame.draw.circle(self.screen, orb_color, (orb_x, orb_y), 7)

        lbl_state = get_font(13, bold=True).render(orb_txt, True, (241, 245, 249))
        self.screen.blit(lbl_state, (80, 207))

        # Divider line
        pygame.draw.line(self.screen, (30, 41, 59), (40, 245), (240, 245), width=1)

        # 2. Digital Timer displays
        lbl_time_hdr = get_font(13, bold=True).render("CHRONOMETER TIME", True, (100, 116, 139))
        self.screen.blit(lbl_time_hdr, (45, 260))

        min_val = self.elapsed_time // 60
        sec_val = self.elapsed_time % 60
        timer_str = f"{min_val:02d}:{sec_val:02d}"
        draw_glowing_text(self.screen, timer_str, get_font(34, bold=True), 45, 280, (255, 255, 255), (6, 182, 212))

        # 3. Mines count displays
        # Calculate remaining mines
        flagged_count = 0
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if self.board.grid[r][c].is_flagged:
                    flagged_count += 1
        mines_left = max(-99, self.board.num_mines - flagged_count)

        lbl_mine_hdr = get_font(13, bold=True).render("UNRESOLVED CORES", True, (100, 116, 139))
        self.screen.blit(lbl_mine_hdr, (45, 350))
        
        mines_str = f"{mines_left:02d} / {self.board.num_mines:02d}"
        draw_glowing_text(self.screen, mines_str, get_font(34, bold=True), 45, 370, (255, 255, 255), (249, 115, 22))

        # Draw restart Action button
        self.restart_button.draw(self.screen, get_font(14, bold=True))

        # Draw parameter toggles
        for t in self.toggles:
            t.draw(self.screen, get_font(12, bold=True))

        # --- DRAW BOARD (WITH SHAKE SHIFT) ---
        # We blit board onto a separate surface to easily apply local screen shake
        board_canvas = pygame.Surface((700, 700), pygame.SRCALPHA)
        self.board.draw(board_canvas)

        # Draw active explosion particles directly on board canvas so they shake too!
        for p in self.particles:
            if p.p_type != 'victory':
                p.draw(board_canvas)

        # Offset board blitting for screenshakes
        bx = 300 + self.screen_shake.dx
        by = 34 + self.screen_shake.dy
        self.screen.blit(board_canvas, (bx, by))

        # Draw victory confetti particles (drawn in global space so they cover sidebar too)
        for p in self.particles:
            if p.p_type == 'victory':
                p.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                # 1. Check sidebar interface interactions first
                # Check difficulty chips
                for i, b in enumerate(self.diff_buttons):
                    if b.check_click(pos):
                        diffs = ["easy", "medium", "hard"]
                        if self.difficulty != diffs[i]:
                            self.difficulty = diffs[i]
                            self.init_board()
                            if self.sound_enabled:
                                self.sounds.play('click')
                        return

                # Check action trigger
                if self.restart_button.check_click(pos):
                    self.init_board()
                    if self.sound_enabled:
                        self.sounds.play('click')
                    return

                # Check toggles
                for t in self.toggles:
                    if t.check_click(pos):
                        if self.sound_enabled:
                            self.sounds.play('click')
                        return

                # 2. Check board canvas inputs
                if not self.game_over:
                    # Translate mouse coordinate into local board canvas offset
                    board_mx = pos[0] - 300
                    board_my = pos[1] - 34
                    cell = self.board.get_cell_at(board_mx, board_my)

                    if cell:
                        # Left Click -> Reveal Cell
                        if event.button == 1:
                            if cell.is_flagged:
                                return # ignore flagged cell interactions

                            if self.board.first_click:
                                self.board.generate(cell.r, cell.c)
                                self.board.first_click = False
                                self.start_timer()

                            # If clicking a revealed cell, check for chord solver
                            if cell.is_revealed:
                                self.board.handle_chord(cell)
                            else:
                                if cell.is_mine:
                                    self.board.trigger_defeat(cell)
                                else:
                                    # Safe cell reveal
                                    if cell.neighbor_mines == 0:
                                        self.board.queue_reveal(cell.r, cell.c)
                                    else:
                                        cell.is_revealed = True
                                        cell.is_revealing = True
                                        cell.reveal_scale = 0.0
                                        if self.sound_enabled:
                                            self.sounds.play('click')

                                    # Check win
                                    if self.board.check_victory():
                                        self.board.trigger_victory()

                        # Right Click -> Flag Cell
                        elif event.button == 3:
                            if not cell.is_revealed:
                                cell.is_flagged = not cell.is_flagged
                                if self.sound_enabled:
                                    self.sounds.play('flag')

            # Handle mouse movements to feed hover glows
            if event.type == pygame.MOUSEMOTION:
                pos = event.pos
                board_mx = pos[0] - 300
                board_my = pos[1] - 34
                
                # Reset target hover alphas on all cells, highlight only current hover
                for r in range(self.board.rows):
                    for c in range(self.board.cols):
                        self.board.grid[r][c].target_hover_alpha = 0.0

                if not self.game_over:
                    hovered_cell = self.board.get_cell_at(board_mx, board_my)
                    if hovered_cell:
                        hovered_cell.target_hover_alpha = 1.0

    def run(self):
        while self.running:
            self.clock.tick(60) # Lock frame rates
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
