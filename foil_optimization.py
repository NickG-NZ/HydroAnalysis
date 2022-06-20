"""
Optimization of hydrofoil span and chord properties for a given hull
at a specified speed and with a maximum power output (which prevents takeoff).
The objective function is to minimize power usage.

Eventually this optimization should include the economics of increasing power
vs. increasing fuel usage.
It should also handle full takeoff (if there is sufficient power available)
"""


if __name__ == "__main__":

    