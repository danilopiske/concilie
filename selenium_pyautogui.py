"""
Automação de pesquisas no Bing usando PyAutoGUI
Controla Chrome nativo (não-Selenium) via cliques e teclado

Requisitos:
    pip install pyautogui

Vantagens:
- Usa Chrome normal (com login persistido)
- Mais leve que Selenium
- Não detectado como bot

Desvantagens:
- Requer coordenadas de tela
- Menos confiável (depende de layout da página)
- Não pode minimizar janela
"""

import pyautogui
import time
import random
import string
import webbrowser

# Configurações de segurança do PyAutoGUI
pyautogui.FAILSAFE = True  # Mover mouse para canto superior esquerdo cancela
pyautogui.PAUSE = 0.5  # Pausa entre comandos


def gerar_palavra_aleatoria(tamanho_min=5, tamanho_max=12):
    """Gera palavra aleatória com letras minúsculas"""
    tamanho = random.randint(tamanho_min, tamanho_max)
    return "".join(random.choices(string.ascii_lowercase, k=tamanho))


def digitar_naturalmente(texto, velocidade_min=0.05, velocidade_max=0.15):
    """Digita texto letra por letra com velocidade variável"""
    for letra in texto:
        pyautogui.write(letra, interval=random.uniform(velocidade_min, velocidade_max))


def main():
    print("🚀 AUTOMAÇÃO BING COM PYAUTOGUI")
    print("=" * 50)
    print("\n⚠️  INSTRUÇÕES IMPORTANTES:")
    print("1. Script abrirá Bing no Chrome PADRÃO do sistema")
    print("2. Seu login do Bing será mantido!")
    print("3. NÃO minimize ou mova a janela durante execução")
    print("4. Mover mouse para CANTO SUPERIOR ESQUERDO cancela (FAILSAFE)")
    print("5. Ou pressione CTRL+C no terminal\n")

    input("▶️  Pressione ENTER para iniciar...")

    # Abrir Bing no navegador padrão
    print("\n📂 Abrindo Bing no Chrome...")
    webbrowser.open("https://www.bing.com")

    # Aguardar navegador abrir e página carregar
    print("⏳ Aguardando 5 segundos para página carregar...")
    time.sleep(5)

    print("\n" + "=" * 50)
    print("▶️  LOOP INICIADO - 30 EXECUÇÕES")
    print("=" * 50)
    print("⚠️  Deixe o Chrome VISÍVEL e NÃO mova a janela\n")

    TOTAL_EXECUCOES = 30
    contador = 0

    try:
        while contador < TOTAL_EXECUCOES:
            contador += 1
            palavra = gerar_palavra_aleatoria()

            print(f"🔄 [{contador}/{TOTAL_EXECUCOES}] - Palavra: '{palavra}'")

            # Focar na barra de pesquisa (CTRL+L foca URL, depois TAB vai para busca)
            pyautogui.hotkey("ctrl", "l")  # Foca na barra de endereço
            time.sleep(0.3)
            pyautogui.press("tab")  # Vai para barra de busca do Bing
            time.sleep(0.3)

            # Limpar conteúdo anterior (selecionar tudo e apagar)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.2)
            pyautogui.press("backspace")
            time.sleep(0.3)

            # Digitar palavra aleatória letra por letra
            print(f"   ⌨️  Digitando '{palavra}'...")
            digitar_naturalmente(palavra)

            # Pressionar ENTER para pesquisar
            time.sleep(0.3)
            pyautogui.press("enter")
            print(f"   ✅ Pesquisa realizada!")

            # Aguardar 7 segundos antes da próxima
            if contador < TOTAL_EXECUCOES:
                print(f"   ⏳ Aguardando 7 segundos...\n")
                time.sleep(4)

    except KeyboardInterrupt:
        print("\n\n⏹️  Loop interrompido pelo usuário (CTRL+C)!")

    except pyautogui.FailSafeException:
        print("\n\n⏹️  FAILSAFE ativado! Mouse movido para canto superior esquerdo.")

    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")

    finally:
        print("\n🏁 Execução finalizada.")
        print("💡 Chrome continua aberto com seu login preservado!")


if __name__ == "__main__":
    main()
