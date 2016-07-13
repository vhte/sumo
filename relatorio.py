#!/usr/bin/env python
from __future__ import division
import os, sys
import optparse
import subprocess
import random
from xml.dom import minidom


xmldoc = minidom.parse('tripinfo.xml')
itemlist = xmldoc.getElementsByTagName('tripinfo')
print "Total de carros: %i" % (len(itemlist))
#print itemlist[0].attributes['arrival'].value
print "Tempo de chegada do ultimo carro: %s" % (itemlist[len(itemlist)-1].attributes['arrival'].value)

# Calculo do total de carros que atravessaram NS, SN, LO, OL
NS = 0
SN = 0
LO = 0
OL = 0
for s in itemlist:
	# python nao tem switch case :(
	if "NS" in s.attributes['id'].value:
		NS += 1
	elif "SN" in s.attributes['id'].value:
		SN += 1
	elif "LO" in s.attributes['id'].value:
		LO += 1
	elif "OL" in s.attributes['id'].value:
		OL += 1

print "TOTAL DE CARROS\nNorte/Sul: %i\nSul/Norte: %i\nLeste/Oeste: %i\nOeste/Leste: %i" % (NS,SN,LO,OL)

# Podemos melhorar isto aqui e verificar os carros que passaram nos horarios de pico, etc...
# Usar o duration e waitSteps

tempos = []
for s in itemlist:
	#if 28800.0 <= float(s.getAttribute('arrival')) <= 36000.0: # 8, 9 e 10 da manha
	if 61200.0 <= float(s.getAttribute('arrival')) <= 68400.0: # 17, 18 e 19 da tarde
		tempos.append(s.getAttribute('duration'))
	#tempos.append(s.getAttribute('duration'))
	#print s.getAttribute('duration')
f = open('teste.xml', 'w')

print >> f, "x = ["
print >> f,', '.join(tempos)
print >> f, " ];"

soma = 0
for s in tempos:
	soma += float(s)
media = soma/len(tempos)
print "Media: %s" % (media)