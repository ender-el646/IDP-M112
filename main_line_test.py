# Line following test entry point.
# On the Pico: upload the agv/ folder, then upload THIS file as main.py
# so it runs on power-up and waits for the start button.
from agv import mission

mission.run_line_test()          # default: loading area 3 -> rack B2L (see agv/mission.py)
# mission.run_line_test('LA4', 'B1L')
