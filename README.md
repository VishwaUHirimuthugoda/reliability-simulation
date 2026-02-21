# Stochastic Reliability Analysis of a Power System
A Monte Carlo simulation app built with Python and Streamlit to analyze 
the reliability of a power system consisting of a Main Grid and Backup Generator.

## Live Demo
[Click here to open the app](https://reliability-simulation-86t7fjmltbkut39ee8utzn.streamlit.app/)

## Features
- Custom MRG32k3a random number generator (no external libraries)
- Models component failures using Gamma, Exponential, and Normal distributions
- Simulates repair cycles and dormant/active backup failure modes
- Displays Reliability Function R(t) and Monte Carlo Convergence plots
- Adjustable parameters via interactive sidebar

## How to Run Locally

### 1. Clone the repository
git clone https://github.com/VishwaUHirimuthugoda/reliability-simulation.git
cd reliability-simulation

### 2. Install dependencies
pip install -r requirements.txt

### 3. Run the app
streamlit run app.py

## Simulation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Mission Time | Total operating time in hours | 200 |
| Main Alpha | Shape parameter for Gamma distribution | 2.0 |
| Main Beta | Scale parameter for Gamma distribution | 50.0 |
| Lambda Active | Failure rate of backup (active mode) | 0.02 |
| Lambda Dormant | Failure rate of backup (dormant mode) | 0.001 |
| Repair Mu | Mean repair time (hours) | 10.0 |
| Repair Sigma | Standard deviation of repair time | 2.0 |

## Tech Stack
- Python 
- Streamlit
- Matplotlib

## Team
| Name | GitHub |
|------|--------|
| Vishwa Hirimuthugoda | [VishwaUHirimuthugoda](https://github.com/VishwaUHirimuthugoda) |
| Yasiru Chandira | — |
| Ishanka Dilshan | — |
```




