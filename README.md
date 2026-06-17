# 🌌 Neon Mines

A sleek, cyberpunk-themed Minesweeper game built in Python using **Pygame** and **NumPy**. **Neon Mines** elevates the classic puzzle game with vibrant neon aesthetics, smooth animations, a custom particle engine, dynamic screen-shake, and real-time in-memory sound synthesis.

---

## 🚀 Key Features

*   **Cyberpunk Visual Design**: Rounded cell tiles, neon color palettes, glowing outlines on hover, and custom vector flag and mine designs.
*   **Ripple Sweep Reveal**: Sweeps open empty cells using a delayed flood-fill algorithm, creating a beautiful wave animation across the board.
*   **Shockwave Cascading Explosions**: Clicking a mine triggers a sequential explosion of all other mines, ripple-sorted by distance from the detonated cell.
*   **Tactile Particle Engine**: Rich, multi-layered particle system spawning fireballs, expanding smoke, high-speed sparks, and falling debris.
*   **In-Memory Sound Synthesis**: Real-time sound effects (clicks, flag placement, explosions, and victory major-7th arpeggios) synthesized mathematically in memory using **NumPy**—no external audio files required!
*   **Interactive Sidebar Dashboard**: Adjust game difficulty (Easy, Medium, Hard Preset Chips) and toggle game parameters (Sound, Screenshake, Particles) via sleek sliding switches.
*   **Power-User Chord Clicking**: Click a revealed number cell with adjacent flags matching its value to instantly resolve the surrounding tiles.

---

## 🎮 How to Play

### Controls
*   **Left Click**: Reveal a hidden cell.
*   **Right Click**: Toggle a flag on a hidden cell.
*   **Chord Click (Left Click on Revealed Number)**: If the number of surrounding flagged cells matches the number on the cell, left-clicking it will instantly reveal all other adjacent unflagged cells.

### Difficulty Presets
*   **Easy Preset**: 9 × 9 grid, 10 mines
*   **Medium Preset**: 16 × 16 grid, 40 mines
*   **Hard Preset**: 16 × 30 grid, 99 mines

---

## 🛠️ Installation & Setup

Ensure you have Python (version 3.8+) installed, then install the required dependencies:

```bash
pip install pygame numpy
```

Clone the repository and run the game:

```bash
git clone https://github.com/DimitrisTsiak/agy-vibes-minesweeper.git
cd agy-vibes-minesweeper
python main.py
```

---

## 📂 Project Structure

*   `main.py`: The complete, self-contained Python source code.
*   `.gitignore`: Clean list of ignored system, Python, and IDE cache files.
*   `README.md`: Project description and user manual.
