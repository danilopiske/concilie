import streamlit as st
import json
import hashlib
from conf.settings import USUARIOS_FILE

def carregar_usuarios():
    try:
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def autenticar(usuario, senha):
    usuarios = carregar_usuarios()
    senha_hash = hash_senha(senha)
    for u in usuarios:
        if u["usuario"] == usuario and u["senha"] == senha_hash:
            return u
    return None