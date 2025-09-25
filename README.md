# AI Flappy Bird

A.I. Flappy bird project made for the Seattle University A.n.I.Ma.L club.

<img src="demo.gif" width="300" />

# Repo Roadmap

- `main_solo.py` is a solo version of the game that you can play
- `main_ai.py` is the version adapted to train an A.I.
- `config.txt` is the config file that **NEAT** uses.
- `score.txt` is the high score of the solo game!

# Explanation

For a general explanation of what's going on, see: [explanation.md](explanation.md)

# Setup

Clone the repository:

```bash
git clone https://github.com/m1chaelwilliams/aiflappybird
```

## Open in it in a code editor (recommended):

For **VS Code**:

```bash
code .
```

## Open a terminal in the root directory of the project and create a virtual environment:

For Windows:

```bash
python -m venv .venv
```

For Mac:

```bash
python3 -m venv .venv
```

## Activate your virtual environment:

For Windows:

```bash
.venv/bin/activate
```

For Mac:

```bash
source .venv/bin/activate
```

## Install the dependencies with pip (pip3 for mac):

```bash
pip install pygame-ce
pip install neat-python
```

## Run the project!

For Windows:

```bash
python -m main_(solo/ai)
```

For Mac:

```bash
python3 -m main_(solo/ai).py
```

## Credits

I used [Tech with Tim's series](https://youtube.com/playlist?list=PLzMcBGfZo4-lwGZWXz5Qgta_YNX3_vLS2&si=2zazEkI7Tu0zfd8K) as inspiration for this project, but I did not follow along entirely. The implementations are similar in that they both use NEAT-Python, but this repository contains unique debugging visuals and an entirely different structure to the game code itself.

