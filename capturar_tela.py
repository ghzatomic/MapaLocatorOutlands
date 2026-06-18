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
import cv2
from PIL import ImageGrab, ImageTk
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
        self.root.title("MapDecoder - Selecione a área do mapa")
        self.root.attributes('-fullscreen', True)
        self.root.configure(background='black')
        # Garantir que ESC sempre saia do fullscreen
        self.root.bind("<Escape>", self.cancelar)
        self.root.bind("<KeyPress-q>", self.cancelar)
        self.root.bind("<KeyPress-Q>", self.cancelar)
        self.root.protocol("WM_DELETE_WINDOW", self.cancelar)

        # Definir nome do arquivo
        if nome_arquivo:
            self.nome_arquivo = nome_arquivo
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.nome_arquivo = f"captura_{timestamp}.png"

        # Variáveis para armazenar coordenadas
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.selecionando = False

        # Tirar screenshot do desktop para usar como fundo
        try:
            self.screenshot = ImageGrab.grab()
        except Exception:
            self.screenshot = pyautogui.screenshot()

        # Canvas para desenhar o retângulo de seleção
        self.canvas = tk.Canvas(
            root,
            cursor="cross",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Exibir screenshot como imagem de fundo
        self.screenshot_tk = ImageTk.PhotoImage(self.screenshot)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.screenshot_tk)

        # Instruções com fundo escuro para legibilidade
        instrucoes = "Clique e arraste para selecionar uma área. ESC ou Q para cancelar."
        largura_tela = self.screenshot.width
        self.canvas.create_rectangle(
            0, 0, largura_tela, 60,
            fill="black",
            stipple="gray50",
            outline=""
        )
        self.canvas.create_text(
            largura_tela // 2,
            30,
            text=instrucoes,
            fill="white",
            font=("Arial", 16)
        )

        # Configurar eventos
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        # Botão direito também cancela
        self.canvas.bind("<ButtonPress-3>", self.cancelar)

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
        
        # Recortar a área selecionada do screenshot já capturado
        try:
            screenshot = self.screenshot.crop((left, top, left + width, top + height))
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
                "--pedaco-mapa", self.nome_arquivo,
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
    
    def executar_auto_scan(self):
        """Executa scan automático procurando a moldura do mapa na tela."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        moldura_path = os.path.join(script_dir, "molduramapa.png")
        mapa_completo_path = os.path.join(script_dir, "2Dmap0.png")

        if not os.path.exists(moldura_path):
            print("Erro: Arquivo molduramapa.png não encontrado.")
            print("Coloque uma captura da moldura do mapa no diretório do programa.")
            self.root.destroy()
            return

        try:
            # Carregar moldura VAZIA para criar template que ignora o conteúdo do mapa
            moldura_vazia_path = os.path.join(script_dir, "molduramapasemmapa.png")
            if not os.path.exists(moldura_vazia_path):
                print("Erro: Arquivo molduramapasemmapa.png não encontrado.")
                self.root.destroy()
                return

            moldura_vazia = cv2.imread(moldura_vazia_path, cv2.IMREAD_UNCHANGED)
            if moldura_vazia is None:
                print("Erro: Não foi possível carregar molduramapasemmapa.png")
                self.root.destroy()
                return

            # Criar template: bordas reais da moldura, centro preenchido com cor neutra
            bgr = moldura_vazia[:, :, :3]
            alpha = moldura_vazia[:, :, 3]
            mascara_bordas = alpha >= 128
            cor_media_bordas = bgr[mascara_bordas].mean(axis=0)
            template = bgr.copy().astype(np.float32)
            template[~mascara_bordas] = cor_media_bordas
            template = np.clip(template, 0, 255).astype(np.uint8)

            try:
                screenshot = np.array(ImageGrab.grab())
            except Exception:
                screenshot = np.array(pyautogui.screenshot())
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

            # Template matching com centro neutro (ignora conteúdo do mapa)
            resultado = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

            # Margens fixas obtidas da transparência da molduramapasemmapa.png
            margem_esq = 6
            margem_dir = 3
            margem_sup = 24
            margem_inf = 21
            mh, mw = moldura_vazia.shape[:2]
            mapa_w = mw - margem_esq - margem_dir
            mapa_h = mh - margem_sup - margem_inf

            # Procurar os top candidatos e verificar qual tem mapa interno válido
            resultado_copia = resultado.copy()
            melhor_candidato = None
            melhor_score = 0

            for _ in range(10):
                _, val, _, loc = cv2.minMaxLoc(resultado_copia)
                if val < 0.25:
                    break

                cx, cy = loc
                # Extrair mapa interno deste candidato
                ix = cx + margem_esq
                iy = cy + margem_sup

                # Verificar se o mapa interno cabe na imagem
                if iy + mapa_h > screenshot.shape[0] or ix + mapa_w > screenshot.shape[1]:
                    resultado_copia[cy, cx] = 0
                    continue

                pedaco = screenshot[iy:iy + mapa_h, ix:ix + mapa_w]

                # Verificar se o pedaco tem conteúdo real (não é tudo preto/branco)
                if pedaco.size > 0:
                    std = pedaco.std()
                    media = pedaco.mean()
                    # Mapa válido: tem variação de cor e não é totalmente escuro
                    if std > 20 and media > 30 and media < 240:
                        if val > melhor_score:
                            melhor_score = val
                            melhor_candidato = (cx, cy, val, pedaco)

                # Zerar este pico para encontrar o próximo
                y1 = max(0, cy - 5)
                y2 = min(resultado_copia.shape[0], cy + 5)
                x1 = max(0, cx - 5)
                x2 = min(resultado_copia.shape[1], cx + 5)
                resultado_copia[y1:y2, x1:x2] = 0

            if melhor_candidato is None:
                print("Moldura não encontrada. Nenhum candidato com mapa interno válido.")
                print("Certifique-se de que o jogo está aberto com o mapa visível.")
                self.root.destroy()
                return

            mx, my, max_val, mapa_interno = melhor_candidato

            cv2.imwrite(self.nome_arquivo, mapa_interno)

            print(f"Auto-scan: moldura encontrada em ({mx}, {my}) com confiança {max_val:.2%}")
            print(f"Mapa interno extraído: {mapa_w}x{mapa_h} salvo como '{self.nome_arquivo}'")

            # Processar com map_decoder diretamente (sem messagebox)
            if not os.path.exists(mapa_completo_path):
                print(f"Erro: Mapa completo não encontrado em '{mapa_completo_path}'")
                self.root.destroy()
                return

            spec = importlib.util.spec_from_file_location("map_decoder", os.path.join(script_dir, "map_decoder.py"))
            map_decoder = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(map_decoder)

            pedaco_mapa = map_decoder.cv2.imread(self.nome_arquivo)
            mapa_completo = map_decoder.cv2.imread(mapa_completo_path)

            if pedaco_mapa is None or mapa_completo is None:
                print("Erro: Falha ao carregar imagens para processamento.")
                self.root.destroy()
                return

            localizador = map_decoder.LocalizadorDeMapa()
            coordenadas = localizador.encontrar_correspondencia(mapa_completo, pedaco_mapa)

            if coordenadas is None:
                print("Não foi possível encontrar uma correspondência confiável no mapa completo.")
                self.root.destroy()
                return

            detector = map_decoder.DetectorDeXVermelho()
            coordenadas_x = detector.detectar(pedaco_mapa)

            if coordenadas_x is None:
                print("X vermelho não encontrado no pedaço do mapa.")
                self.root.destroy()
                return

            x_completo = coordenadas.x + coordenadas_x.x
            y_completo = coordenadas.y + coordenadas_x.y

            print(f"\n=== RESULTADO DA DETECÇÃO ===")
            print(f"X vermelho encontrado nas coordenadas: X={x_completo}, Y={y_completo}")

            # Abrir navegador
            url = f"https://exploreoutlands.com/#pos:{x_completo},{y_completo},9"
            print(f"Abrindo navegador: {url}")
            webbrowser.open(url)

            # Salvar imagem com marcação
            mapa_com_marcacao = mapa_completo.copy()
            h, w = pedaco_mapa.shape[:2]
            cv2.rectangle(
                mapa_com_marcacao,
                (coordenadas.x, coordenadas.y),
                (coordenadas.x + w, coordenadas.y + h),
                (0, 255, 0), 2
            )
            cv2.circle(
                mapa_com_marcacao,
                (x_completo, y_completo),
                10, (0, 0, 255), 2
            )
            cv2.putText(
                mapa_com_marcacao,
                f"X: {x_completo}, Y: {y_completo}",
                (x_completo + 15, y_completo),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )
            cv2.imwrite("resultado_deteccao.png", mapa_com_marcacao)
            print(f"Imagem de resultado salva como 'resultado_deteccao.png'")

        except Exception as e:
            print(f"Erro no Auto-Scan: {str(e)}")
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass

    def cancelar(self, event=None):
        """Cancela a operação e fecha a aplicação."""
        self.root.destroy()

class JanelaControleAutoScan:
    """Janela pequena flutuante para disparar o auto-scan manualmente."""

    def __init__(self, root, nome_arquivo=None):
        self.root = root
        self.nome_arquivo = nome_arquivo
        self.root.title("MapDecoder Auto-Scan")
        self.root.attributes("-topmost", True)
        self.root.geometry("300x120+20+20")
        self.root.configure(background="#222222")
        self.root.resizable(False, False)
        self.root.bind("<F5>", self.disparar_scan)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # Labels e botão
        tk.Label(
            root,
            text="Posicione o mapa no jogo",
            bg="#222222",
            fg="white",
            font=("Arial", 12)
        ).pack(pady=(10, 2))

        tk.Label(
            root,
            text="e clique em Escanear ou aperte F5",
            bg="#222222",
            fg="#cccccc",
            font=("Arial", 10)
        ).pack(pady=(0, 8))

        self.botao = tk.Button(
            root,
            text="Escanear",
            command=self.disparar_scan,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=12,
            height=1
        )
        self.botao.pack()

    def disparar_scan(self, event=None):
        """Esconde a janela, aguarda brevemente e executa o scan."""
        self.botao.config(text="Escaneando...", state=tk.DISABLED)
        self.root.withdraw()
        # Aguardar 500ms para garantir que a janela sumiu antes do screenshot
        self.root.after(500, self._executar)

    def _executar(self):
        try:
            app = SeletorDeArea(self.root, self.nome_arquivo)
            app.executar_auto_scan()
        finally:
            try:
                self.root.destroy()
            except Exception:
                pass


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Captura um pedaço da tela e processa com map_decoder.")
    parser.add_argument("-o", "--output", help="Nome do arquivo de saída (PNG)")
    parser.add_argument("--apenas-capturar", action="store_true", help="Apenas captura a imagem sem processar")
    parser.add_argument("--auto-scan", action="store_true", help="Detecta automaticamente a moldura do mapa na tela")
    args = parser.parse_args()

    if args.auto_scan:
        root = tk.Tk()
        JanelaControleAutoScan(root, args.output)
        root.mainloop()
    else:
        root = tk.Tk()
        root.deiconify()
        app = SeletorDeArea(root, args.output)
        root.mainloop()

if __name__ == "__main__":
    main()
