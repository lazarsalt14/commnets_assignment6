# Traffic Simulation Project

## Overview

This project simulates network traffic flow and generates both visual and statistical outputs based on a given network topology. By running the main script, you can observe how traffic behaves across the network and analyze performance metrics.

## Installation

Before running the project, install the required dependencies:

```
pip install matplotlib numpy pillow
```

## How to Run

1. Ensure that the `traffic_sim` folder is in the same directory as `main.py`.
2. Run the following command:

   ```
   python main.py
   ```

## Outputs

Running `main.py` generates the following files:

* **`simulation.gif`**
  A visual representation of the network simulation. It shows how traffic flows through the network over time. You can modify the network topology in the code to produce different visualizations.

* **`statistics.txt`**
  Contains useful metrics and data collected during the simulation. This may include traffic statistics, node performance, or other relevant insights depending on the implementation.
* **`statistics.png`**
  A graphical representation of the collected data. This file visualizes key metrics from the simulation using plots, making it easier to interpret trends and performance.

## Customization

* You can modify the network topology in the code to experiment with different configurations.
* After making changes, rerun `main.py` to generate updated outputs.

## Notes

* Ensure the directory structure is maintained for correct execution.
* Outputs will be overwritten each time `main.py` is run unless handled otherwise in the code.
