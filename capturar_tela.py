#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ferramenta para capturar um pedaço da tela selecionado pelo usuário.
Permite selecionar uma região com o mouse, salva como imagem PNG e processa com o map_decoder.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import pyautogui
import datetime
import argparse
import subprocess
import importlib.util
import numpy as np
import webbrowser

class SeletorDeArea:
    """Classe que permite selecionar uma área da tela com o mouse."""
    
    def __init__(self, root, nome_arquivo=None):
        """
        Inicializa o seletor de área.
        
        Args:
            root: Janela principal do Tkinter
            nome_arquivo: Nome do arquivo para salvar a captura (opcional)
        """
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)  # Transparência para ver a tela por trás
        self.root.configure(background='grey')
        
        # Definir nome do arquivo
        if nome_arquivo:
            self.nome_arquivo = nome_arquivo
        else:
            # Usar timestamp como nome de arquivo padrão
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.nome_arquivo = f"captura_{timestamp}.png"
        
        # Variáveis para armazenar coordenadas
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.selecionando = False
        
        # Canvas para desenhar o retângulo de seleção
        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Instruções
        instrucoes = "Clique e arraste para selecionar uma área. Pressione ESC para cancelar."
        self.canvas.create_text(
            root.winfo_screenwidth() // 2, 
            30, 
            text=instrucoes, 
            fill="white", 
            font=("Arial", 16)
        )
        
        # Configurar eventos
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", self.cancelar)
        
        # Retângulo de seleção
        self.rect_id = None
        
    def on_press(self, event):
        """Callback quando o botão do mouse é pressionado."""
        self.selecionando = True
        self.start_x = event.x
        self.start_y = event.y
        
        # Criar retângulo inicial
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )
    
    def on_drag(self, event):
        """Callback quando o mouse é arrastado."""
        if self.selecionando:
            self.end_x = event.x
            self.end_y = event.y
            # Atualizar retângulo
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, self.end_x, self.end_y)
    
    def on_release(self, event):
        """Callback quando o botão do mouse é solto."""
        self.selecionando = False
        self.end_x = event.x
        self.end_y = event.y
        
        # Capturar a área selecionada
        self.capturar_area()
        
    def capturar_area(self):
        """Captura a área selecionada, salva como PNG e processa com map_decoder."""
        # Garantir que start seja o ponto superior esquerdo e end o inferior direito
        left = min(self.start_x, self.end_x)
        top = min(self.start_y, self.end_y)
        width = abs(self.end_x - self.start_x)
        height = abs(self.end_y - self.start_y)
        
        # Verificar se a área selecionada é válida
        if width < 10 or height < 10:
            messagebox.showerror("Erro", "Área selecionada muito pequena. Tente novamente.")
            self.root.destroy()
            return
        
        # Esconder a janela para capturar a tela sem a interface
        self.root.withdraw()
        
        try:
            # Capturar a região selecionada
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # Salvar a imagem
            screenshot.save(self.nome_arquivo)
            
            # Processar a imagem com map_decoder
            self.processar_com_map_decoder()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao capturar a tela: {str(e)}")
            self.root.destroy()
    
    def processar_com_map_decoder(self):
        """Processa a imagem capturada com o map_decoder."""
        try:
            # Verificar se o arquivo map_decoder.py existe no mesmo diretório
            script_dir = os.path.dirname(os.path.abspath(__file__))
            map_decoder_path = os.path.join(script_dir, "map_decoder.py")
            
            if not os.path.exists(map_decoder_path):
                messagebox.showerror("Erro", "Arquivo map_decoder.py não encontrado.")
                self.root.destroy()
                return
            
            # Método 1: Importar o módulo map_decoder e usar diretamente
            try:
                # Importar o módulo map_decoder dinamicamente
                spec = importlib.util.spec_from_file_location("map_decoder", map_decoder_path)
                map_decoder = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(map_decoder)
                
                # Verificar se existe um mapa completo para processar
                mapa_completo_path = os.path.join(script_dir, "2Dmap0.png")
                
                if os.path.exists(mapa_completo_path):
                    # Executar o processamento
                    resultado = self.executar_map_decoder_interno(map_decoder, self.nome_arquivo, mapa_completo_path)
                    messagebox.showinfo(
                        "Processamento Concluído", 
                        f"Imagem salva como '{self.nome_arquivo}'\n"
                        f"Resultado do processamento: {resultado}"
                    )
                else:
                    # Se não encontrar o mapa completo, perguntar se deseja apenas salvar a imagem
                    resposta = messagebox.askyesno(
                        "Mapa Completo Não Encontrado", 
                        "O arquivo do mapa completo (2Dmap0.png) não foi encontrado.\n"
                        "Deseja apenas salvar a imagem capturada?"
                    )
                    
                    if resposta:
                        messagebox.showinfo(
                            "Sucesso", 
                            f"Imagem salva como '{self.nome_arquivo}'"
                        )
                    else:
                        # Excluir a imagem capturada se o usuário não quiser salvá-la
                        if os.path.exists(self.nome_arquivo):
                            os.remove(self.nome_arquivo)
            
            except Exception as e:
                # Método 2 (fallback): Executar como processo separado
                self.executar_map_decoder_externo()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar a imagem: {str(e)}")
        
        # Fechar aplicação
        self.root.destroy()
    
    def executar_map_decoder_interno(self, map_decoder_module, pedaco_mapa_path, mapa_completo_path):
        """Executa o map_decoder importado como módulo."""
        try:
            # Carregar as imagens
            pedaco_mapa = map_decoder_module.cv2.imread(pedaco_mapa_path)
            mapa_completo = map_decoder_module.cv2.imread(mapa_completo_path)
            
            if pedaco_mapa is None or mapa_completo is None:
                return "Erro ao carregar as imagens"
            
            # Encontrar o pedaço do mapa no mapa completo
            resultado = map_decoder_module.encontrar_correspondencia(pedaco_mapa, mapa_completo)
            
            if resultado is None:
                return "Pedaço do mapa não encontrado no mapa completo"
            
            # Detectar o X vermelho no pedaço do mapa
            detector = map_decoder_module.DetectorDeXVermelho()
            coordenadas_x = detector.detectar(pedaco_mapa)
            
            if coordenadas_x is None:
                return "X vermelho não encontrado no pedaço do mapa"
            
            # Calcular as coordenadas do X vermelho no mapa completo
            x_no_mapa_completo = resultado.x + coordenadas_x.x
            y_no_mapa_completo = resultado.y + coordenadas_x.y
            
            # Salvar imagem com visualização
            mapa_com_marcacao = mapa_completo.copy()
            # Desenhar retângulo ao redor do pedaço do mapa
            cv2 = map_decoder_module.cv2
            h, w = pedaco_mapa.shape[:2]
            cv2.rectangle(
                mapa_com_marcacao, 
                (resultado.x, resultado.y), 
                (resultado.x + w, resultado.y + h), 
                (0, 255, 0), 2
            )
            # Desenhar círculo no X vermelho
            cv2.circle(
                mapa_com_marcacao, 
                (x_no_mapa_completo, y_no_mapa_completo), 
                10, (0, 0, 255), 2
            )
            # Adicionar texto com as coordenadas
            cv2.putText(
                mapa_com_marcacao,
                f"X: {x_no_mapa_completo}, Y: {y_no_mapa_completo}",
                (x_no_mapa_completo + 15, y_no_mapa_completo),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )
            
            # Salvar a imagem com o resultado
            resultado_path = "resultado_deteccao.png"
            cv2.imwrite(resultado_path, mapa_com_marcacao)
            
            # Exibir resultado no console
            print(f"\n=== RESULTADO DA DETECÇÃO ===\n")
            print(f"X vermelho encontrado nas coordenadas: X={x_no_mapa_completo}, Y={y_no_mapa_completo}")
            print(f"Imagem de resultado salva como '{resultado_path}'")
            print(f"\nAbrindo navegador com as coordenadas...\n")
            
            # Abrir navegador com as coordenadas
            url = f"https://exploreoutlands.com/#pos:{x_no_mapa_completo},{y_no_mapa_completo},9"
            webbrowser.open(url)
            
            # Perguntar se deseja apagar a imagem capturada
            resposta = messagebox.askokcancel(
                "Resultado Encontrado", 
                f"X vermelho encontrado nas coordenadas:\n\n" 
                f"X = {x_no_mapa_completo}\n" 
                f"Y = {y_no_mapa_completo}\n\n" 
                f"O navegador foi aberto com o link:\n{url}\n\n" 
                f"Pressione OK para continuar e apagar a imagem capturada."
            )
            
            # Apagar a imagem capturada se o usuário pressionar OK
            if resposta and os.path.exists(self.nome_arquivo):
                os.remove(self.nome_arquivo)
                print(f"Imagem capturada '{self.nome_arquivo}' foi apagada.")
            
            return f"X vermelho encontrado nas coordenadas ({x_no_mapa_completo}, {y_no_mapa_completo}) do mapa completo"
            
        except Exception as e:
            return f"Erro durante o processamento: {str(e)}"
    
    def executar_map_decoder_externo(self):
        """Executa o map_decoder como um processo externo."""
        try:
            # Construir o comando para executar o map_decoder
            comando = [
                sys.executable,  # Python atual
                "map_decoder.py",
                "--pedaco", self.nome_arquivo,
                "--debug"
            ]
            
            # Executar o comando
            resultado = subprocess.run(
                comando, 
                capture_output=True, 
                text=True,
                check=False
            )
            
            # Extrair coordenadas da saída do programa
            coordenadas_x = None
            coordenadas_y = None
            
            # Procurar por coordenadas na saída
            for linha in resultado.stdout.splitlines():
                if "X vermelho no mapa completo" in linha:
                    try:
                        # Tentar extrair as coordenadas da linha
                        partes = linha.split("X=")[1].split(",")
                        coordenadas_x = int(partes[0].strip())
                        coordenadas_y = int(partes[1].split("Y=")[1].strip().split(" ")[0])
                    except:
                        pass
            
            if resultado.returncode == 0 and coordenadas_x is not None and coordenadas_y is not None:
                # Exibir resultado no console
                print(f"\n=== RESULTADO DA DETECÇÃO ===\n")
                print(f"X vermelho encontrado nas coordenadas: X={coordenadas_x}, Y={coordenadas_y}")
                
                # Abrir navegador com as coordenadas
                url = f"https://exploreoutlands.com/#pos:{coordenadas_x},{coordenadas_y}"
                print(f"Abrindo navegador com o link: {url}")
                webbrowser.open(url)
                
                # Perguntar se deseja apagar a imagem capturada
                resposta = messagebox.askokcancel(
                    "Resultado Encontrado", 
                    f"X vermelho encontrado nas coordenadas:\n\n" 
                    f"X = {coordenadas_x}\n" 
                    f"Y = {coordenadas_y}\n\n" 
                    f"O navegador foi aberto com o link:\n{url}\n\n" 
                    f"Pressione OK para continuar e apagar a imagem capturada."
                )
                
                # Apagar a imagem capturada se o usuário pressionar OK
                if resposta and os.path.exists(self.nome_arquivo):
                    os.remove(self.nome_arquivo)
                    print(f"Imagem capturada '{self.nome_arquivo}' foi apagada.")
            
            elif resultado.returncode == 0:
                messagebox.showinfo(
                    "Processamento Concluído", 
                    f"Imagem salva como '{self.nome_arquivo}'\n"
                    f"Saída do map_decoder:\n{resultado.stdout}"
                )
            else:
                messagebox.showwarning(
                    "Processamento com Avisos", 
                    f"Imagem salva como '{self.nome_arquivo}'\n"
                    f"Saída do map_decoder:\n{resultado.stdout}\n"
                    f"Erros:\n{resultado.stderr}"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Erro no Processamento", 
                f"Imagem salva como '{self.nome_arquivo}'\n"
                f"Falha ao executar map_decoder: {str(e)}"
            )
    
    def cancelar(self, event=None):
        """Cancela a operação e fecha a aplicação."""
        self.root.destroy()

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Captura um pedaço da tela e processa com map_decoder.")
    parser.add_argument("-o", "--output", help="Nome do arquivo de saída (PNG)")
    parser.add_argument("--apenas-capturar", action="store_true", help="Apenas captura a imagem sem processar")
    args = parser.parse_args()
    
    # Inicializar interface
    root = tk.Tk()
    app = SeletorDeArea(root, args.output)
    root.mainloop()

if __name__ == "__main__":
    main()
