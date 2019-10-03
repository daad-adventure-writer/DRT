#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# DAAD Reborn Tokenizer
# Version 0.2 alpha
# Copyright (C) 2010, 2013, 2018-2019 José Manuel Ferrer Ortiz
#
# Released under the GPL v2 license
#
# Requires Python 2.6+, optionally with progressbar module

from __future__ import print_function
import json
import sys

try:
  import progressbar
  hayProgreso = True
except:
  hayProgreso = False


num_abreviaturas = 128  # Número máximo de abreviaturas a encontrar

# Tabla de conversión de caracteres, posiciones 16-31 (inclusive)
daad_a_chr = ('ª', '¡', '¿', '«', '»', 'á', 'é', 'í', 'ó', 'ú', 'ñ', 'Ñ', 'ç', 'Ç', 'ü', 'Ü')
if sys.version_info[0] < 3:  # Python 2
  daad_a_chr = [c.decode ('utf8') for c in daad_a_chr]
else:
  daad_a_chr = [bytes (c, 'iso-8859-15').decode() for c in daad_a_chr]


# Calcula y devuelve las abreviaturas óptimas, y la longitud de las cadenas tras aplicarse
# maxAbrev Longitud máxima de las abreviaturas
# textos Cadenas sobre las que aplicar abreviaturas
def calcula_abreviaturas (maxAbrev, textos):
  cadenas     = textos  # Cadenas sobre las que se simulará la aplicación de abreviaturas
  longDespues = 0  # Longitud total de las cadenas tras aplicar abreviaturas, incluyendo espacio de éstas
  minAbrev    = 2  # Longitud mínima de las abreviaturas
  # Tomamos las mejores abreviaturas
  optimas = []  # Abreviaturas óptimas calculadas
  for i in range (num_abreviaturas):
    # Calculamos cuántas veces aparece cada combinación
    (ahorros, ocurrencias) = cuenta_ocurrencias (cadenas, minAbrev, maxAbrev)
    if not ahorros:  # Ya no hay más cadenas de longitud mínima
      break
    ordenAhorro = sorted (ahorros, key = ahorros.get, reverse = True)
    abreviatura = ordenAhorro[0]
    ahorro      = ahorros[abreviatura]
    # print ((abreviatura, ahorro, ocurrencias[abreviatura]))
    # Buscamos superconjuntos entre el resto de combinaciones posibles
    maxAhorroSup = ahorro  # Ahorro máximo combinado por reemplazar abreviatura por un superconjunto, entre ambos
    maxSuperCjto = None
    posMaxAhorro = None
    sconjto      = None
    if i < 100:  # En las últimas, es poco probable que se aproveche esto
      for d in range (1, len (ordenAhorro)):  # Buscamos superconjuntos entre el resto de combinaciones posibles
        if abreviatura in ordenAhorro[d]:
          sconjto   = ordenAhorro[d]
          ahorroSup = ahorros[sconjto] + ((ocurrencias[abreviatura] - ocurrencias[sconjto]) * (len (abreviatura) - 1))
          if ahorroSup > maxAhorroSup:
            maxAhorroSup = ahorroSup
            maxSuperCjto = sconjto
            posMaxAhorro = d
            # print ('"%s" (%d) es superconjunto de "%s", ahorros %d, ocurrencias %d. Ahorros combinados tomando éste %d' %
            #     (sconjto, d, abreviatura, ahorros[sconjto], ocurrencias[sconjto], ahorroSup))
    if posMaxAhorro:  # Tenía algún superconjunto (TODO: puede que siempre ocurra, si len (abreviatura) < maxAbrev)
      # print ('La entrada "' + ordenAhorro[posMaxAhorro] + '" (' + str (posMaxAhorro) + ') reemplaza "' + abreviatura + '" (0)')
      abreviatura = maxSuperCjto
    if maxAhorroSup < 1:
      break  # Ya no se ahorra nada más
    # Añadimos esta abreviatura a la lista de abreviaturas óptimas calculadas
    ahorro = ahorros[abreviatura]
    # print ((abreviatura, ahorro, ocurrencias[abreviatura]))
    optimas.append ((abreviatura, ahorro, ocurrencias[abreviatura]))
    longDespues += len (abreviatura)
    # Quitamos las ocurrencias de esta abreviatura en las cadenas
    c = 0
    nuevasCadenas = []
    while c < len (cadenas):
      partes = cadenas[c].split (abreviatura)
      if len (partes) > 1:  # La abreviatura aparecía en esa cadena
        cadenas[c] = partes[0]
        for p in range (1, len (partes)):
          nuevasCadenas.append (partes[p])
      c += 1
    cadenas += nuevasCadenas
  for cadena in cadenas:
    longCadena   = len (cadena) + 1
    longDespues += longCadena
  if len (optimas) < num_abreviaturas:
    longDespues += num_abreviaturas - len (optimas)  # Se reemplazarán por abreviaturas de un byte
  if prolijo:
    print ('Con longitud m\xc3\xa1xima de las abreviaturas %d, longitud de cadenas tras abreviar: %d.' % (maxAbrev, longDespues))
    # print (optimas)
  nuevasAbreviaturas = []
  for abreviatura in optimas:
    nuevasAbreviaturas.append (abreviatura[0])
  return (nuevasAbreviaturas, longDespues)

# Devuelve cuántas veces aparece cada combinación de caracteres en las cadenas dadas, y cuánto se ahorraría por abreviar cada una de ellas
def cuenta_ocurrencias (cadenas, minAbrev, maxAbrev):
  ahorros     = {}  # Cuántos bytes en total se ahorrarían por abreviar cada ocurrencia
  ocurrencias = {}  # Cuántas veces aparece cada combinación de caracteres
  for cadena in cadenas:
    longCadena = len (cadena)
    if longCadena < minAbrev:
      continue
    for pos in range (0, (longCadena - minAbrev) + 1):
      for longAbrev in range (minAbrev, min (maxAbrev, longCadena - pos) + 1):
        ahorro     = longAbrev - 1
        ocurrencia = cadena[pos:pos + longAbrev]
        if ocurrencia in ocurrencias:
          ahorros[ocurrencia]     += ahorro
          ocurrencias[ocurrencia] += 1
        else:
          ahorros[ocurrencia]     = 0  # No se ahorra ni desperdicia nada
          ocurrencias[ocurrencia] = 1
  return (ahorros, ocurrencias)


if len (sys.argv) < 2 or (len (sys.argv) == 2 and sys.argv[1][0] == '-'):
  print ('Uso:', sys.argv[0], '<entrada.json> [salida.tok] [-v]')
  sys.exit()

prolijo = sys.argv[-1] == '-v'

if sys.version_info[0] < 3:  # Python 2
  fichero = open (sys.argv[1], 'r')
  jsonBD  = json.load (fichero, encoding = 'iso-8859-1')
else:
  fichero = open (sys.argv[1], 'r', encoding = 'iso-8859-1')
  jsonBD  = json.load (fichero)
fichero.close()
longAntes = 0    # Longitud total de los textos antes de abreviar
textos    = []   # Cadenas sobre las que aplicar abreviaturas
for tipoTextos in ('messages', 'sysmess', 'locations'):
  for texto in jsonBD[tipoTextos]:
    textos.append (texto['Text'])
    longCadena  = len (texto['Text']) + 1
    longAntes  += longCadena
print ('Longitud de los textos sin abreviar (excluyendo objetos):', longAntes)

longMin = 999999
if prolijo or not hayProgreso:
  rango = range (3, 30)
else:
  progreso = progressbar.ProgressBar()
  rango    = progreso (range (3, 30))
for maxAbrev in rango:
  try:
    (posibles, longAbrev) = calcula_abreviaturas (maxAbrev, list (textos))
  except KeyboardInterrupt:
    break
  if longAbrev < longMin:
    abreviaturas = posibles  # Conjunto de abreviaturas que produjo la máxima reduccíón
    longMin      = longAbrev  # Reducción máxima de longitud total de textos lograda
    longMax      = maxAbrev   # Longitud máxima en la búsqueda de abreviaturas
print (longAntes - longMin, 'bytes ahorrados por abreviación de textos')
if prolijo:
  print()
  print ('La mejor combinación de abreviaturas se encontró con longitud máxima de abreviatura', longMax)
  print (len (abreviaturas), 'abreviaturas en total, que son:')
  print (abreviaturas)
print()

# Ponemos abreviaturas de relleno
for i in range (len (abreviaturas), num_abreviaturas):
  abreviaturas.append (chr (127))
abreviaturas = [chr (127)] + abreviaturas  # Hay que dejar eso como la primera abreviatura

hexadecimales = []
for abreviatura in abreviaturas:
  cuenta      = 0
  hexadecimal = ''
  for caracter in abreviatura:
    if ord (caracter) > 127:  # Conversión necesaria
      try:
        caracter = daad_a_chr.index (caracter) + 16
      except:
        cuenta += 1
        caracter = ord (caracter)
    elif caracter == '\n':
      caracter = ord ('\r')
    else:
      caracter = ord (caracter)
    hexadecimal += hex (caracter)[2:].zfill (2)
  hexadecimales.append (hexadecimal)
  if cuenta:
    print ('Error al convertir la abreviatura "%s": tiene %d caracteres que exceden el código 127, pero no salen en daad_a_chr' %
      (abreviatura, cuenta))

salidaJson = {
  'compression': 'advanced',
  'tokens': hexadecimales,
} 
if len (sys.argv) < 3 or (len (sys.argv) == 3 and sys.argv[2] == '-v'):
  print (json.dumps (salidaJson))
else:
  fichero = open (sys.argv[2], 'w')
  fichero.write (json.dumps (salidaJson))
  fichero.close()
  print ('Abreviaturas guardadas en:', sys.argv[2])
