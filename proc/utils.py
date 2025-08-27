import json
import os
import unicodedata
import streamlit as st
from unidecode import unidecode
import re

def remover_acentos(texto):
    if isinstance(texto, str):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto

def limpar_forma_pgto(valor):
    if not isinstance(valor, str):
        return valor
    valor = unidecode(valor).upper()
    valor = re.sub(r'PRE[- ]?PAGO', 'A VISTA', valor)
    valor = re.sub(r'PRÉ[- ]?PAGO', 'A VISTA', valor)
    valor = valor.replace('ELECTRON', '')
    valor = valor.replace('HIPERCARD CREDITO', 'HIPERCARD CREDITO A VISTA')
    return valor.strip()

def normalizar_forma_pagamento(texto):
    if not isinstance(texto, str):
        return texto
    texto = remover_acentos(texto).upper()
    substituicoes = {
        "PARCELADO LOJA": "CREDITO PARCELADO LOJA",
        "PRE-PAGO": "A VISTA",
        "PRÉ-PAGO": "A VISTA",
        "PRÉ PAGO": "A VISTA",
        "CREDITO PRE PAGO": "CREDITO A VISTA",
        "CRÉDITO PRÉ-PAGO": "CREDITO A VISTA",
        "ELECTRON": ""
    }
    return substituicoes.get(texto.strip(), texto)

def normalizar_bandeira(texto):
    if not isinstance(texto, str):
        return texto
    texto = remover_acentos(texto).upper()
    substituicoes = {
        "AMEX": "AMERICAN EXPRESS",
        "MC": "MASTERCARD",
        "MAESTRO": "MASTERCARD"
    }
    return substituicoes.get(texto.strip(), texto)
