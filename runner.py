#!/usr/bin/env python
"""
@file    runner.py
@author  Lena Kalleske
@author  Daniel Krajzewicz
@author  Michael Behrisch
@author  Jakob Erdmann
@author  Victor Torres
@author  Samara Leal
@date    2009-03-26
@updated 2014-08-25
@version $Id: runner.py 16379 2014-05-14 09:28:38Z behrisch $

Tutorial for traffic light control via the TraCI interface.

SUMO, Simulation of Urban MObility; see http://sumo-sim.org/
Copyright (C) 2009-2014 DLR/TS, Germany

This file is part of SUMO.
SUMO is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.
"""

"""
- Nao deixei as 3 setas pois ha muitos conflitos e os carros ao inves de resolverem os conflitos preferem seguir em frente para nao parar o transito
"""
import os, sys
import optparse
import subprocess
import random

# we need to import python modules from the $SUMO_HOME/tools directory
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', "tools")) # tutorial in tests
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..")), "tools")) # tutorial in docs
    from sumolib import checkBinary
except ImportError:
    sys.exit("please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")

import traci
# the port used for communicating with your sumo instance
PORT = 8873

def geraSinais(NS,SN,OL,LO):
    tempoAmarelo = 3

    # Nao utilizar o 'g' pois conta com o fator prioridade
    UD_G = "GGGGGGrrrrrrrrrrrrrrrrrr" # Cada posicao da variavel é um estado do sinal. Sinais funcionam a partir de estados (esta variavel).
    UD_Y = "yyyyyyrrrrrrrrrrrrrrrrrr"

    DU_G = "rrrrrrGGGGGGrrrrrrrrrrrr"
    DU_Y = "rrrrrryyyyyyrrrrrrrrrrrr"

    RL_G = "rrrrrrrrrrrrGGGGGGrrrrrr"
    RL_Y = "rrrrrrrrrrrryyyyyyrrrrrr"

    LR_G = "rrrrrrrrrrrrrrrrrrGGGGGG"
    LR_Y = "rrrrrrrrrrrrrrrrrryyyyyy"
    
    PROGRAM = []

    for i in range(0,NS):
        PROGRAM.append(UD_G)
    for i in range(0,tempoAmarelo):
        PROGRAM.append(UD_Y) # amarelo

    for i in range(0,SN):
        PROGRAM.append(DU_G)
    for i in range(0,tempoAmarelo):
        PROGRAM.append(DU_Y)

    for i in range(0,OL):
        PROGRAM.append(RL_G)
    for i in range(0,tempoAmarelo):
        PROGRAM.append(RL_Y)

    for i in range(0,LO):
        PROGRAM.append(LR_G)
    for i in range(0,tempoAmarelo):
        PROGRAM.append(LR_Y)

    return PROGRAM

# Chamada (ciclo) do programa principal.
# Verde = 15s
# Amarelo = 3s
# Vermelho = Ciclo - 15-3 (verde e amarelo do sinal aberto)

estatico = True
if estatico:
    PROGRAM = geraSinais(15,15,15,15) # A cada unidade de tempo no SUMO é rodado um estado (posicao) deste vetor
else:
    PROGRAM = geraSinais(26,19,19,19) # Inicial fuzzy
def generate_routefile():
    # Gera as rotas    
    with open("data/cross.rou.xml", "w") as routes:
        print >> routes, """<routes>
        <vType id="typeWE" accel="1.0" decel="4.5" sigma="0.0" length="5" minGap="3" maxSpeed="15" guiShape="passenger"/>
        <vType id="typeNS" accel="1.0" decel="4.5" sigma="0.0" length="5" minGap="3" maxSpeed="15" guiShape="passenger"/>
        <!-- Right -->  
            <route id="right" edges="51o 1i 2o 52i" />
            <route id="right-down" edges="51o 1i 3o 53i" />
            <route id="right-up" edges="51o 1i 4o 54i" />
        
        <!-- Left -->
            <route id="left"  edges="52o 2i 1o 51i" />
            <route id="left-down"  edges="52o 2i 4o 54i" />
            <route id="left-up"  edges="52o 2i 3o 53i" />

        <!-- Down -->
            <route id="down"  edges="54o 4i 3o 53i" />
            <route id="down-left"  edges="54o 4i 1o 51i" />
            <route id="down-right"  edges="54o 4i 2o 52i" />

        <!-- Up -->
            <route id="up" edges="53o 3i 4o 54i" />
            <route id="up-right" edges="53o 3i 2o 52i"/>
            <route id="up-left" edges="53o 3i 1o 51i"/> 
           """
        lastVeh = 0
        vehNr = 0
        rotasNS = ['down','down-left','down-right']
        rotasSN = ['up','up-right','up-left']
        rotasLO = ['left','left-down','left-up']
        rotasOL = ['right','right-down','right-up']

        random.seed(42) # make tests reproducible
        N = 86400 # number of time steps. 24h = 86400
        for i in range(N): # Cada via tera N chances de conseguir que um carro apareca no instante i
            # O Controle do fluxo de carros pode ser feito aqui, maiores chances de aparecerem de uma vez (pico)
            if i < 21600: # Entre 0 e 6 da manha
                # Probabilidade de ocorrencia de carros nas vias por unidade de tempo. A direcao que o carro toma depois do sinal é indiferente ate agora
                # Para cada passo [0,21600], a probabilidade de um carro ir de Norte a Sul é de ~0.09%

                #06:00 10 4 4 4

                pNS = 0.166666667 # Sao 10 carros/min, entao 10/60 (seg) = 0.166666 # 1./10
                pSN = 0.066666667 # 4 carros/hora, entao 4/60 (seg) = 0.0666
                pLO = 0.066666667
                pOL = 0.066666667
            elif i < 32400: # Entre 6 e 9 da manha, utilizo a eq. geral da reta 
                #09:00 20 15 16 15
                pNS = (0.000925925925925926 * i - 10)/60 # 0.000925925925925926 X  - 10
                pSN = (0.0010185185185185184 *i - 18)/60 # Y = 0.0010185185185185184 X  - 18
                pLO = (0.0011111111111111111 *i - 20)/60 # Y = 0.0011111111111111111 X  - 20
                pOL = (0.0010185185185185184 *i - 18)/60 # Y = 0.0010185185185185184 X  - 18
            elif i < 43200: # Entra 9 e 12h
                #12:00 8 6 6 6
                pNS = (-0.0011111111111111111 *i  + 56)/60 # Y = -0.0011111111111111111 X  + 56
                pSN = (-0.0008333333333333334 *i  + 42)/60 # Y = -0.0008333333333333334 X  + 42
                pLO = (-0.000925925925925926 *i  + 46)/60 # Y = -0.000925925925925926 X  + 46
                pOL = (-0.0008333333333333334 *i  + 42)/60 # Y = -0.0008333333333333334 X  + 42
            elif i < 54000: # Entre 12h e 15h
                # 15:00 6 6 6 12
                pNS = (-0.00018518518518518518 *i  + 16)/60 # Y = -0.00018518518518518518 X  + 16
                pSN = (0 *i  + 6)/60 # Y = 0 X  + 6
                pLO = (0 *i  + 6)/60 # Y = 0 X  + 6
                pOL = (0.0005555555555555556 *i - 18)/60 # Y = 0.0005555555555555556 X  - 18
            elif i < 64800: # Entre 15h e 18h
                # 18:00 18 18 18 25
                pNS = (0.0011111111111111111 *i  - 54)/60 # Y = 0.0011111111111111111 X  - 54
                pSN = (0.0011111111111111111 *i  - 54)/60 # Y = 0.0011111111111111111 X  - 54
                pLO = (0.0011111111111111111 *i  - 54)/60 # Y = 0.0011111111111111111 X  - 54
                pOL = (0.0012037037037037038 *i  - 53)/60 # Y = 0.0012037037037037038 X  - 53
            elif i < 75600: # Entre 18h e 21h
                # 21:00 7 7 7 10
                pNS = (-0.0010185185185185184 *i  + 84)/60 # Y = -0.0010185185185185184 X  + 84
                pSN = (-0.0010185185185185184 *i  + 84)/60 # Y = -0.0010185185185185184 X  + 84
                pLO = (-0.0010185185185185184 *i  + 84)/60 # Y = -0.0010185185185185184 X  + 84
                pOL = (-0.001388888888888889 *i  + 115)/60 # Y = -0.001388888888888889 X  + 115
            else: # Entre 21h e 24h
                # 23:00 2 1 2 6
                pNS = (-0.000462962962962963 *i  + 42)/60 # Y = -0.000462962962962963 X  + 42
                pSN = (-0.0005555555555555556 *i  + 49)/60 # Y = -0.0005555555555555556 X  + 49
                pLO = (-0.000462962962962963 *i  + 42)/60 # Y = -0.000462962962962963 X  + 42
                pOL = (-0.00037037037037037035 *i  + 38)/60 # Y = -0.00037037037037037035 X  + 38

            # Criacao dos veiculos por probabilidade
            if random.uniform(0,1) < pNS:
                rotaAleatoria = random.randint(0,len(rotasNS)-1)
                print >> routes, '    <vehicle id="NS_%i" type="typeWE" route="%s" depart="%i" />' % (vehNr, rotasNS[rotaAleatoria], i)
                vehNr += 1
                lastVeh = i
            if random.uniform(0,1) < pSN:
                rotaAleatoria = random.randint(0,len(rotasSN)-1)
                print >> routes, '    <vehicle id="SN_%i" type="typeWE" route="%s" depart="%i" color="0,1,0.5" />' % (vehNr, rotasSN[rotaAleatoria], i)
                vehNr += 1
                lastVeh = i
            if random.uniform(0,1) < pLO:
                rotaAleatoria = random.randint(0,len(rotasLO)-1)
                print >> routes, '    <vehicle id="LO_%i" type="typeNS" route="%s" depart="%i" color="0,0.5,1"/>' % (vehNr, rotasLO[rotaAleatoria], i)
                vehNr += 1
                lastVeh = i
            if random.uniform(0,1) < pOL:
                rotaAleatoria = random.randint(0,len(rotasOL)-1)
                print >> routes, '    <vehicle id="OL_%i" type="typeNS" route="%s" depart="%i" color="0.5,1,1"/>' % (vehNr, rotasOL[rotaAleatoria], i)
                vehNr += 1
                lastVeh = i

            #print "pNS: %s\npSN: %s\npLO: %s\npOL: %s" % (pNS, pSN, pLO, pOL)

        print >> routes, "</routes>"

def run():
    """execute the TraCI control loop"""
    traci.init(PORT)
    #programPointer = len(PROGRAM)-1
    step = 0
    tempo = 0
    
    # getMinexpectedNumber() - Returns the number of vehicles which are in the net plus the
    #ones still waiting to start. This number may be smaller than
    #the actual number of vehicles still to come because of delayed
    #route file parsing. If the number is 0 however, it is
    #guaranteed that all route files have been parsed completely
    #and all vehicles have left the network.
    programPointer=0
    nivel = 1
    nivelAnterior = 1
    global PROGRAM

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        if programPointer == len(PROGRAM)-1:
            step = 0
        programPointer = step
        traci.trafficlights.setRedYellowGreenState("0", PROGRAM[programPointer])
        step += 1
        tempo += 1

        # Define se deve mudar a configuracao de PROGRAM pelo horario
        if not estatico:
            
            if tempo < 21600: # Entre 0 e 6 da manha
                PROGRAM = geraSinais(49,37,37,37)
                nivel = 1
            elif tempo < 32400: # Entre 6 e 9 da manha, utilizo a eq. geral da reta 
                PROGRAM = geraSinais(49,37,37,37)
                nivel = 2
                if nivelAnterior == 1:
                    nivelAnterior = 2
                    step = 0
            elif tempo < 43200: # Entra 9 e 12h
                PROGRAM = geraSinais(37,37,37,37)
                nivel = 3
                if nivelAnterior == 2:
                    nivelAnterior = 3
                    step = 0
            elif tempo < 54000: # Entre 12h e 15h
                PROGRAM = geraSinais(26,26,26,37)
                nivel = 4
                if nivelAnterior == 3:
                    nivelAnterior = 4
                    step = 0
            elif tempo < 64800: # Entre 15h e 18h
                PROGRAM = geraSinais(37,37,37,55)
                nivel = 5
                if nivelAnterior == 4:
                    nivelAnterior = 5
                    step = 0
            elif tempo < 75600: # Entre 18h e 21h
                PROGRAM = geraSinais(37,37,37,37)
                nivel = 6
                if nivelAnterior == 5:
                    nivelAnterior = 6
                    step = 0
            else: # Entre 21h e 24h
                PROGRAM = geraSinais(22,19,22,26)
                nivel = 7
                if nivelAnterior == 6:
                    nivelAnterior = 7
                    step = 0
        #print tempo
    traci.close()
    sys.stdout.flush()

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # first, generate the route file for this simulation
    generate_routefile()

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    sumoProcess = subprocess.Popen([sumoBinary, "-c", "data/cross.sumocfg", "--tripinfo-output", "tripinfo.xml", "--remote-port", str(PORT)], stdout=sys.stdout, stderr=sys.stderr)
    run()
    sumoProcess.wait()
