# Cyber Defense AI

A Pygame-based educational simulator for demonstrating classic AI search and decision-making algorithms in a cyber-defense setting.

The project visualizes a network as a graph and lets you explore how different algorithms behave across multiple problem families:

- uninformed search: BFS, DFS, UCS
- informed search: Greedy Best-First Search, A*, IDA*
- local search: Simple Hill Climbing, Steepest Hill Climbing, Simulated Annealing
- complex environments: Belief-State Search, Partial Observation, AND-OR Graph Search
- CSP: Backtracking, Forward Checking, Min-Conflicts
- adversarial search: Minimax, Alpha-Beta Pruning, Expectimax

## Features

- interactive Pygame UI with animated step-by-step execution
- graph visualization with node/edge highlighting
- live logs, metrics, and compare mode
- support for multiple map scenarios
- hover/select node inspection in the right panel
- scrolling panels for long algorithm output

## Project structure

```text
Cyber-Defense-AI/
├─ algorithms/          # Search, CSP, local search, adversarial, complex-environment solvers
├─ core/                # Graph, state, models, metrics, map loader, utilities
├─ maps/                # JSON maps used by the simulator
├─ tests/               # Unit tests for algorithms and UI wiring
├─ ui/                  # Pygame application, panels, graph view, log view, stats view
├─ main.py              # Application entry point
└─ README.md
```

## Requirements

- Python 3.10+ recommended
- Pygame
- pytest for running tests

## Installation

```bash
pip install pygame pytest
```

If your environment uses a virtual environment, activate it first.

## Run the simulator

```bash
python main.py
```

## Run the test suite

```bash
python -m pytest tests -q
```

## Controls

- `Space` — start / pause simulation
- `S` — step once
- `R` — reset current run
- `Esc` — exit
- mouse wheel — scroll long panels when hovering them

## Included maps

The app currently loads several JSON scenarios from the `maps/` folder, including:

- `pathfinding_basic.json`
- `weighted_network.json`
- `defense_optimization.json`
- `belief_hidden.json`
- `belief_partial.json`
- `csp_segmentation.json`
- `adversarial_game.json`

## Notes

- This project is a simulation for learning and visualization only.
- Algorithms are separated from the UI and return step events so that the interface can animate each decision.
- Compare mode can be used to view multiple algorithms side-by-side for the same scenario.

## License

No explicit license has been provided in the repository.
