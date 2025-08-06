# Decodificador de Mapas

Este programa encontra um pedaço de mapa dentro de um mapa completo e retorna as coordenadas correspondentes. Utiliza técnicas de template matching do OpenCV para encontrar a melhor correspondência. Também detecta um X vermelho no pedaço do mapa e calcula sua posição no mapa completo.

## Requisitos

Para executar este programa, você precisa ter instalado:

```
python 3.6+
opencv-python
numpy
pyautogui (para a ferramenta de captura de tela)
```

Você pode instalar as dependências usando:

```
pip install -r requirements.txt
```

## Como usar

### Ferramenta de Captura de Tela

A maneira mais fácil de usar o programa é com a ferramenta de captura de tela:

```
python capturar_tela.py
```

Esta ferramenta permite:
1. Selecionar uma área da tela com o mouse
2. Capturar a imagem do pedaço do mapa
3. Processar automaticamente para encontrar o X vermelho
4. Abrir o navegador com o link contendo as coordenadas exatas

### Processamento Manual

Alternativamente, você pode executar o processamento manual:

```
python map_decoder.py
```

Por padrão, o programa procura os arquivos `2Dmap0.png` (mapa completo) e `testemarquinho.png` (pedaço do mapa) no diretório atual.

#### Opções

- `--mapa-completo`: Especifica o caminho para o arquivo do mapa completo
- `--pedaco-mapa`: Especifica o caminho para o arquivo do pedaço do mapa
- `--visualizar`: Mostra uma visualização do resultado
- `--debug`: Salva imagens de debug para ajudar na detecção do X vermelho

Exemplo:

```
python map_decoder.py --visualizar --debug
```

## Resultado

O programa retorna:
1. As coordenadas do pedaço do mapa dentro do mapa completo
2. As coordenadas do X vermelho no pedaço do mapa
3. As coordenadas do X vermelho no mapa completo

Se a visualização estiver ativada, uma imagem será salva mostrando o mapa completo com:
- Um retângulo verde ao redor da área correspondente
- Um círculo vermelho na posição do X vermelho
