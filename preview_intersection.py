"""Capture the actual SUMO-GUI rendering of the revised intersection."""
from pathlib import Path
import sumolib
import traci

root=Path(__file__).resolve().parent
model=root/'models/eglinton_danforth'
traci.start([sumolib.checkBinary('sumo-gui'),'-c',str(root/'Eglinton_Danforth.sumocfg'),
             '--window-size','1200,900','--no-step-log','true','--start'])
try:
    for _ in range(100):
        traci.simulationStep()
    view=traci.gui.getIDList()[0]
    net=sumolib.net.readNet(str(model/'intersection.net.xml'))
    x,y=net.getNode('TCS379').getCoord()
    traci.gui.setOffset(view,x,y)
    traci.gui.setZoom(view,300)
    traci.gui.screenshot(view,str(model/'intersection_preview.png'),width=1200,height=900)
    traci.simulationStep()
    print(model/'intersection_preview.png')
finally:
    traci.close(wait=False)
