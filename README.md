# Genetic Algorithm Dino Run AI

A Python-based simulation where Artificial Intelligence learns to play the classic "Dino Run" game using Neural Networks and Genetic Algorithms.

The AI starts completely random and "evolves" over generations, learning to jump over cacti, duck under obstacles, and manage speed increases. This project features a full UI for managing simulation settings and saving progress.

## What's New in This Update

* **Main Menu System:** A graphical start screen to easily navigate between new games, loading saves, and settings.
* **Save & Load Logic:**
    * **Auto-Save:** The game automatically detects when a Dino breaks the all-time high score and saves its "brain" (weights & biases) to the "best_genes" folder.
    * **Smart Naming:** Save files are named by generation and origin (e.g., gen_15_gene_1.json) to track lineage.
    * **Load Menu:** A dedicated screen to view and load your top 5 performing Dinos from previous sessions.
* **In-Game Settings Menu:** Adjust simulation variables like FPS, Speed, and Population Size in real-time without editing code. You can also make extra adjustments in config.json.
* **Virtual Environment Support:** Project structure optimized for running inside a Python virtual environment.

## Installation & Usage (Using venv)

It is highly recommended to run this project in a virtual environment to keep dependencies clean.

1. Prerequisites
   Ensure you have Python 3.10 or newer installed.

2. Create a Virtual Environment
   Open your terminal in the project folder and run:
   python -m venv venv
   if you have many python versions:
   python -[your python version] venv venv

3. Activate the Virtual Environment
   - Windows (Command Prompt):
     venv\Scripts\activate.bat
   - Windows (PowerShell):
     .\venv\Scripts\Activate.ps1
   - Mac/Linux:
     source venv/bin/activate

   (You should see "(venv)" appear at the start of your command line.)

4. Install Dependencies
   With the environment active, install the required libraries:
   pip install -r requirements.txt

5. Run the Simulation
   python main.py

## How the AI Works

This project does not use hard-coded rules. It simulates a biological brain process:

1. Senses (Inputs): The Dino receives three inputs: Distance to the next obstacle, current Game Speed, and its Y-Position.
2. Brain (Neural Net): These inputs are processed through weighted connections in a simple neural network.
3. Action (Outputs):
   - If the Output is greater than 0.5, the Dino JUMPS.
   - If the Output is less than -0.5, the Dino DUCKS.
4. Evolution: The Dinos that survive the longest are selected as "parents." Their genes (weights) are copied, mutated slightly, and passed to the next generation.

## Project Structure

* main.py: The core game loop, AI logic, and UI system.
* config.json: Stores user settings (FPS, Speed, etc.). Created automatically on the first run.
* requirements.txt: List of dependencies required to run the game.
* best_genes/: Folder where high-score DNA files are stored.
* assets/: Folder containing images for the Dino and Cactus.

## Controls

* Mouse: Navigate Menus.
* ESC: Return to the Main Menu from the simulation.