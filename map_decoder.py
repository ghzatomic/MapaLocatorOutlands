#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Decodificador de Mapas

Este programa encontra um pedaço de mapa dentro de um mapa completo e retorna as coordenadas.
Utiliza técnicas de template matching do OpenCV para encontrar a melhor correspondência.
Também detecta um X vermelho no pedaço do mapa e calcula sua posição no mapa completo.
"""

import cv2
import numpy as np
import argparse
from dataclasses import dataclass
from typing import Tuple, Optional, List


# Entidades
@dataclass
class Coordenadas:
    """Representa as coordenadas de um ponto no mapa."""
    x: int
    y: int
    confianca: float = 1.0  # Nível de confiança da correspondência (0-1)

    def __str__(self) -> str:
        return f"Coordenadas: X={self.x}, Y={self.y} (Confiança: {self.confianca:.2%})"


# Casos de Uso
class DetectorDeXVermelho:
    """Caso de uso para detectar um X vermelho em uma imagem."""
    
    def detectar(self, imagem: np.ndarray) -> Optional[Coordenadas]:
        """
        Detecta um X vermelho na imagem.
        
        Args:
            imagem: Imagem como array numpy
            
        Returns:
            Coordenadas do centro do X vermelho, ou None se não encontrar
        """
        # Informações específicas sobre o X vermelho
        # - Tamanho: 6x6 pixels
        # - Cor: #FF0000 (vermelho puro em RGB)
        
        # Criar uma máscara para detectar pixels de cor vermelha pura (#FF0000)
        # Em BGR (formato do OpenCV), #FF0000 é [0, 0, 255]
        # Permitir uma pequena variação na cor para lidar com compressão de imagem
        lower_red = np.array([0, 0, 240])  # Vermelho puro com pequena tolerância
        upper_red = np.array([15, 15, 255])
        mascara_vermelho_puro = cv2.inRange(imagem, lower_red, upper_red)
        
        # Encontrar contornos na máscara
        contornos, _ = cv2.findContours(mascara_vermelho_puro, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Se não encontrou contornos, tentar uma abordagem mais flexível
        if not contornos:
            # Abordagem alternativa: Detectar vermelho mais genericamente
            b, g, r = cv2.split(imagem)
            mascara_vermelho = cv2.threshold(cv2.subtract(r, cv2.max(b, g)), 30, 255, cv2.THRESH_BINARY)[1]
            contornos, _ = cv2.findContours(mascara_vermelho, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contornos:
                return None
        
        # Filtrar contornos com base no tamanho esperado (6x6 pixels)
        # Permitir uma pequena variação no tamanho
        candidatos = []
        for contorno in contornos:
            x, y, w, h = cv2.boundingRect(contorno)
            
            # Verificar se o tamanho está próximo de 6x6 pixels
            # Permitir uma variação de +/- 2 pixels
            if (4 <= w <= 8) and (4 <= h <= 8):
                # Verificar se a proporção é aproximadamente quadrada
                aspect_ratio = float(w) / h
                if 0.8 <= aspect_ratio <= 1.2:
                    area = cv2.contourArea(contorno)
                    candidatos.append((contorno, area, x, y, w, h))
        
        # Se não encontrou candidatos adequados
        if not candidatos:
            # Tentar uma abordagem mais flexível: pegar o menor contorno vermelho
            if contornos:
                areas = [(contorno, cv2.contourArea(contorno), *cv2.boundingRect(contorno)) 
                         for contorno in contornos]
                # Filtrar por tamanho mínimo
                areas = [a for a in areas if a[1] > 3]  # Área mínima
                
                if areas:
                    # Ordenar por proximidade ao tamanho esperado (6x6 = 36 pixels quadrados)
                    areas.sort(key=lambda a: abs(a[1] - 36))
                    contorno, area, x, y, w, h = areas[0]
                    
                    # Calcular o centro
                    cx = x + w // 2
                    cy = y + h // 2
                    return Coordenadas(x=cx, y=cy)
            return None
        
        # Ordenar candidatos por proximidade ao tamanho esperado (6x6 = 36 pixels quadrados)
        candidatos.sort(key=lambda c: abs(c[1] - 36))
        
        # Pegar o melhor candidato
        _, _, x, y, w, h = candidatos[0]
        
        # Calcular o centro do X
        cx = x + w // 2
        cy = y + h // 2
        
        return Coordenadas(x=cx, y=cy)


class LocalizadorDeMapa:
    """Caso de uso para localizar um pedaço de mapa dentro de um mapa completo."""
    
    def encontrar_correspondencia(self, mapa_completo: np.ndarray, 
                                 pedaco_mapa: np.ndarray) -> Optional[Coordenadas]:
        """
        Encontra a melhor correspondência do pedaço de mapa dentro do mapa completo.
        
        Args:
            mapa_completo: Imagem do mapa completo como array numpy
            pedaco_mapa: Imagem do pedaço do mapa como array numpy
            
        Returns:
            Coordenadas do canto superior esquerdo da melhor correspondência, ou None se não encontrar
        """
        # Aplicar template matching
        resultado = cv2.matchTemplate(mapa_completo, pedaco_mapa, cv2.TM_CCORR_NORMED)

        # Encontrar o valor máximo de correspondência e sua localização
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(resultado)

        # O TM_CCORR_NORMED retorna valores entre 0 e 1, onde 1 é a correspondência perfeita
        if max_val < 0.8:
            return None
            
        # As coordenadas são do canto superior esquerdo
        x, y = max_loc
        
        return Coordenadas(x=x, y=y, confianca=max_val)
        
    def calcular_coordenada_no_mapa_completo(self, coordenadas_pedaco: Coordenadas, 
                                           coordenadas_correspondencia: Coordenadas) -> Coordenadas:
        """
        Calcula a coordenada de um ponto do pedaço do mapa no mapa completo.
        
        Args:
            coordenadas_pedaco: Coordenadas do ponto no pedaço do mapa
            coordenadas_correspondencia: Coordenadas da correspondência no mapa completo
            
        Returns:
            Coordenadas do ponto no mapa completo
        """
        # A coordenada no mapa completo é a soma da coordenada do ponto no pedaço
        # com a coordenada da correspondência
        x_completo = coordenadas_correspondencia.x + coordenadas_pedaco.x
        y_completo = coordenadas_correspondencia.y + coordenadas_pedaco.y
        
        return Coordenadas(x=x_completo, y=y_completo)


# Adaptadores
class LeitorDeImagem:
    """Adaptador para leitura de arquivos de imagem."""
    
    @staticmethod
    def carregar(caminho_arquivo: str) -> Optional[np.ndarray]:
        """
        Carrega uma imagem do disco.
        
        Args:
            caminho_arquivo: Caminho para o arquivo de imagem
            
        Returns:
            Array numpy contendo a imagem, ou None se falhar
        """
        imagem = cv2.imread(caminho_arquivo)
        if imagem is None:
            print(f"Erro: Não foi possível carregar a imagem '{caminho_arquivo}'")
        return imagem


class VisualizadorDeResultados:
    """Adaptador para visualização dos resultados."""
    
    @staticmethod
    def mostrar_resultado(mapa_completo: np.ndarray, pedaco_mapa: np.ndarray, 
                         coordenadas: Coordenadas, coordenadas_x_vermelho: Optional[Coordenadas] = None) -> None:
        """
        Mostra visualmente o resultado da correspondência e salva em um arquivo.
        
        Args:
            mapa_completo: Imagem do mapa completo
            pedaco_mapa: Imagem do pedaço do mapa
            coordenadas: Coordenadas da correspondência
            coordenadas_x_vermelho: Coordenadas do X vermelho no mapa completo (opcional)
        """
        # Criar uma cópia do mapa completo para desenhar
        mapa_resultado = mapa_completo.copy()
        
        # Obter dimensões do pedaço do mapa
        altura_pedaco, largura_pedaco = pedaco_mapa.shape[:2]
        
        # Desenhar um retângulo ao redor da área correspondente
        ponto1 = (coordenadas.x, coordenadas.y)
        ponto2 = (coordenadas.x + largura_pedaco, coordenadas.y + altura_pedaco)
        cv2.rectangle(mapa_resultado, ponto1, ponto2, (0, 255, 0), 2)
        
        # Se tiver coordenadas do X vermelho, desenhar um círculo nele
        if coordenadas_x_vermelho:
            cv2.circle(mapa_resultado, 
                      (coordenadas_x_vermelho.x, coordenadas_x_vermelho.y), 
                      10, (0, 0, 255), -1)  # Círculo vermelho preenchido
            
            # Adicionar texto com as coordenadas
            texto = f"X={coordenadas_x_vermelho.x}, Y={coordenadas_x_vermelho.y}"
            cv2.putText(mapa_resultado, texto, 
                       (coordenadas_x_vermelho.x + 15, coordenadas_x_vermelho.y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Redimensionar para salvar se for muito grande
        altura_max = 1200
        largura_max = 1600
        
        altura_original, largura_original = mapa_resultado.shape[:2]
        escala = min(largura_max / largura_original, altura_max / altura_original)
        
        if escala < 1:
            nova_largura = int(largura_original * escala)
            nova_altura = int(altura_original * escala)
            mapa_resultado = cv2.resize(mapa_resultado, (nova_largura, nova_altura))
        
        # Salvar o resultado em um arquivo
        nome_arquivo = "resultado_deteccao.png"
        cv2.imwrite(nome_arquivo, mapa_resultado)
        print(f"Resultado salvo como '{nome_arquivo}'")
        
        try:
            # Tentar mostrar o resultado, se possível
            cv2.imshow("Resultado da Correspondência", mapa_resultado)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except:
            # Se falhar ao mostrar (por exemplo, usando opencv-headless), apenas continuar
            pass


# Interface principal
def main():
    """Função principal do programa."""
    parser = argparse.ArgumentParser(description='Encontra um pedaço de mapa dentro de um mapa completo.')
    parser.add_argument('--mapa-completo', default='2Dmap0.png', 
                        help='Caminho para o arquivo do mapa completo')
    parser.add_argument('--pedaco-mapa', default='testemarquinho.png', 
                        help='Caminho para o arquivo do pedaço do mapa')
    parser.add_argument('--visualizar', action='store_true', 
                        help='Mostrar visualização do resultado')
    parser.add_argument('--debug', action='store_true',
                        help='Mostrar imagens de debug para ajudar na detecção do X')
    args = parser.parse_args()
    
    # Carregar imagens
    leitor = LeitorDeImagem()
    mapa_completo = leitor.carregar(args.mapa_completo)
    pedaco_mapa = leitor.carregar(args.pedaco_mapa)
    
    if mapa_completo is None or pedaco_mapa is None:
        return 1
    
    # Encontrar correspondência do pedaço do mapa no mapa completo
    localizador = LocalizadorDeMapa()
    coordenadas = localizador.encontrar_correspondencia(mapa_completo, pedaco_mapa)
    
    if coordenadas is None:
        print("Não foi possível encontrar uma correspondência confiável.")
        return 1
    
    # Exibir resultado da correspondência
    print(f"Posição do pedaço do mapa: {coordenadas}")
    
    # Detectar X vermelho no pedaço do mapa
    detector = DetectorDeXVermelho()
    coordenadas_x_vermelho_pedaco = detector.detectar(pedaco_mapa)
    
    # Se o modo debug estiver ativado, salvar a imagem com a detecção
    if args.debug and pedaco_mapa is not None:
        debug_img = pedaco_mapa.copy()
        if coordenadas_x_vermelho_pedaco:
            cv2.circle(debug_img, 
                      (coordenadas_x_vermelho_pedaco.x, coordenadas_x_vermelho_pedaco.y), 
                      5, (0, 255, 0), -1)
            cv2.putText(debug_img, f"X detectado: ({coordenadas_x_vermelho_pedaco.x}, {coordenadas_x_vermelho_pedaco.y})", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(debug_img, "X não detectado", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imwrite("debug_deteccao_x.png", debug_img)
        print("Imagem de debug salva como 'debug_deteccao_x.png'")
    
    coordenadas_x_vermelho_completo = None
    
    if coordenadas_x_vermelho_pedaco:
        # Calcular a posição do X vermelho no mapa completo
        coordenadas_x_vermelho_completo = localizador.calcular_coordenada_no_mapa_completo(
            coordenadas_x_vermelho_pedaco, coordenadas)
        
        print(f"X vermelho encontrado no pedaço do mapa: {coordenadas_x_vermelho_pedaco}")
        print(f"X vermelho no mapa completo: {coordenadas_x_vermelho_completo}")
    else:
        print("Não foi possível encontrar o X vermelho no pedaço do mapa.")
    
    # Visualizar resultado se solicitado
    if args.visualizar:
        visualizador = VisualizadorDeResultados()
        visualizador.mostrar_resultado(
            mapa_completo, pedaco_mapa, coordenadas, coordenadas_x_vermelho_completo)
    
    return 0


# Funções auxiliares para uso externo
def encontrar_correspondencia(pedaco_mapa: np.ndarray, mapa_completo: np.ndarray) -> Optional[Coordenadas]:
    """Função auxiliar para encontrar um pedaço de mapa dentro do mapa completo.
    
    Args:
        pedaco_mapa: Imagem do pedaço do mapa
        mapa_completo: Imagem do mapa completo
        
    Returns:
        Coordenadas da correspondência ou None se não encontrar
    """
    localizador = LocalizadorDeMapa()
    return localizador.encontrar_correspondencia(mapa_completo, pedaco_mapa)


if __name__ == "__main__":
    exit(main())
