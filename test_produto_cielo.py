"""
Teste da função dividir_produto_cielo
"""

import pandas as pd


def dividir_produto_cielo(valor):
    """
    Divide e normaliza strings de "Produto cielo"
    """
    if pd.isna(valor):
        return None, None

    texto = str(valor).strip().upper()
    print(f"📥 Entrada: '{valor}' → '{texto}'")

    # Normalizar acentos e caracteres especiais para comparação
    texto_norm = (
        texto.replace("Á", "A")
        .replace("À", "A")
        .replace("Ã", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
        .replace("-", " ")  # Remove hífens
    )

    # Bandeiras conhecidas
    bandeiras_conhecidas = [
        "VISA ELECTRON",
        "MASTERCARD",
        "MAESTRO",
        "AMERICAN EXPRESS",
        "HIPERCARD",
        "DINERS",
        "DISCOVER",
        "AMEX",
        "VISA",
        "ELO",
        "MC",
        "CABAL",
        "PIX",
    ]

    bandeira = None
    forma = None

    # Identificar a bandeira no início
    for bandeira_candidata in bandeiras_conhecidas:
        if texto.startswith(bandeira_candidata):
            bandeira = bandeira_candidata
            resto = texto[len(bandeira_candidata) :].strip()
            resto_norm = texto_norm[len(bandeira_candidata) :].strip()

            # NORMALIZAR BANDEIRA: MC ou MAESTRO → MASTERCARD
            if bandeira in ["MC", "MAESTRO"]:
                bandeira = "MASTERCARD"

            # NORMALIZAR FORMA DE PAGAMENTO
            tem_pre_pago = (
                "PRE PAGO" in resto_norm
                or "PREPAGO" in resto_norm
                or ("PRE" in resto_norm and "PAGO" in resto_norm)
            )

            print(
                f"🔍 Resto: '{resto}' | Normalizado: '{resto_norm}' | Tem PRE PAGO: {tem_pre_pago}"
            )

            if tem_pre_pago and "CREDITO" in resto_norm:
                forma = "CREDITO A VISTA"
                print(f"✅ Convertido: CREDITO PRE PAGO → CREDITO A VISTA")
            elif tem_pre_pago and "DEBITO" in resto_norm:
                forma = "DEBITO A VISTA"
                print(f"✅ Convertido: DEBITO PRE PAGO → DEBITO A VISTA")
            elif resto_norm == "PARCELADO LOJA":
                forma = "CREDITO PARCELADO LOJA"
            else:
                forma = resto if resto else None

            print(f"📤 Saída: Bandeira='{bandeira}' | Forma='{forma}'\n")
            return bandeira, forma

    # Se não identificou bandeira
    print(f"⚠️ Bandeira não identificada no início. Texto completo: '{texto}'\n")
    return texto, None


# Testes com os valores do usuário
testes = [
    "American Express Crédito à vista",
    "Cabal Crédito à vista",
    "Cabal Débito à vista",
    "Elo Crédito à vista",
    "Elo Crédito pré-pago",
    "Elo Débito à vista",
    "Elo Débito pré-pago",
    "Hipercard Crédito à vista",
    "Mastercard Crédito à vista",
    "Mastercard Crédito pré-pago",
    "Mastercard Débito à vista",
    "Mastercard Débito pré-pago",
    "Pix Pix",
    "Visa Crédito à vista",
    "Visa Crédito conversor de moedas",
    "Visa Crédito pré-pago",
    "Visa Débito à vista",
    "Visa Débito pré-pago",
]

print("=" * 80)
print("TESTE: dividir_produto_cielo()")
print("=" * 80)

for teste in testes:
    bandeira, forma = dividir_produto_cielo(teste)
