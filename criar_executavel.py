#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para criar um executável do MapDecoder usando PyInstaller.
Este script automatiza o processo de criação do executável.
"""

import os
import subprocess
import sys

def instalar_pyinstaller():
    """Instala o PyInstaller se não estiver instalado."""
    print("Verificando se o PyInstaller está instalado...")
    try:
        import PyInstaller
        print("PyInstaller já está instalado.")
        return True
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller instalado com sucesso.")
            return True
        except subprocess.CalledProcessError:
            print("Erro ao instalar PyInstaller. Por favor, instale manualmente com 'pip install pyinstaller'.")
            return False

def criar_executavel():
    """Cria o executável usando PyInstaller."""
    print("\nCriando executável do MapDecoder...")
    
    # Definir o nome do arquivo principal
    arquivo_principal = "capturar_tela.py"
    
    # Verificar se o arquivo principal existe
    if not os.path.exists(arquivo_principal):
        print(f"Erro: O arquivo {arquivo_principal} não foi encontrado.")
        return False
    
    # Definir ícone (opcional)
    icone = ""
    if os.path.exists("icone.ico"):
        icone = "--icon=icone.ico"
    
    # Comando para criar o executável
    comando = [
        sys.executable, 
        "-m", 
        "PyInstaller",
        "--onefile",  # Criar um único arquivo executável
        "--windowed",  # Não mostrar console (GUI)
        "--name", "MapDecoder",  # Nome do executável
        icone,
        "--add-data", "map_decoder.py;.",  # Incluir o arquivo map_decoder.py
        "--add-data", "2Dmap0.png;.",  # Incluir o mapa completo
        arquivo_principal
    ]
    
    # Remover opções vazias
    comando = [c for c in comando if c]
    
    try:
        # Executar o PyInstaller
        subprocess.check_call(comando)
        print("\nExecutável criado com sucesso!")
        print("Você pode encontrá-lo na pasta 'dist'.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nErro ao criar o executável: {e}")
        return False

def main():
    """Função principal."""
    print("=== Criador de Executável do MapDecoder ===\n")
    
    # Instalar PyInstaller se necessário
    if not instalar_pyinstaller():
        return 1
    
    # Criar o executável
    if not criar_executavel():
        return 1
    
    print("\nProcesso concluído.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
