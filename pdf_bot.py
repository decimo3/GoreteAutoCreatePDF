#!/bin/env python
''' Script to generate PDFs from image folders '''
import os
import sys
import logging
import mimetypes
from logging.handlers import TimedRotatingFileHandler
from io import BytesIO
from tkinter.filedialog import askdirectory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image

# Allow loading of truncated images
# (some JPGs may be slightly corrupted)
#from PIL import ImageFile
#ImageFile.LOAD_TRUNCATED_IMAGES = True

#region CONSTANTES
LOGGING_MAX_BACKUP = 7
BANNER_MAX_LENGHT = 100
BANNER_DEFAULT_CHAR = '#'
IMAGE_DPI = 200
POINTS_PER_INCH = 72
A4_WIDTH_INCH = 8.27
A4_HEIGHT_INCH = 11.69
IMAGE_DEFAULT_QUALITY = 75
PAGE_WIDTH, PAGE_HEIGHT = A4
IMAGE_MAX_WIDTH = int(A4_WIDTH_INCH * IMAGE_DPI)
IMAGE_MAX_HEIGHT = int(A4_HEIGHT_INCH * IMAGE_DPI)
#endregion

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        TimedRotatingFileHandler(
            when='midnight',
            interval=1,
            filename='pdf_bot.log',
            backupCount=LOGGING_MAX_BACKUP
        )
    ]
)
log = logging.getLogger(os.path.basename(__file__))

def presentation_center(text: str) -> str:
    ''' Function to center a text '''
    spaces = ' ' * ((BANNER_MAX_LENGHT - len(text)) // 2)
    return BANNER_DEFAULT_CHAR + spaces + text + spaces + BANNER_DEFAULT_CHAR

def pesentation_banner() -> None:
    ''' Function to write a banner on stdout '''
    print(BANNER_DEFAULT_CHAR * BANNER_MAX_LENGHT)
    print(presentation_center('Programa de geração de PDFs do MestreRuan'))
    print(presentation_center('Repositório:  https://github.com/decimo3/pdf_bot/'))
    print(BANNER_DEFAULT_CHAR * BANNER_MAX_LENGHT)

def normalize_image(img: Image.Image) -> ImageReader:
    ''' Function to reduce image size '''
    # Força RGB (remove alpha)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Escala para caber no A4
    width, height = img.size
    scale = min(IMAGE_MAX_WIDTH / width, IMAGE_MAX_HEIGHT / height)
    width = int(width * scale)
    height = int(height * scale)
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    # Salva em memória para realizar a compressão
    buffer = BytesIO()
    img.save(
        buffer,
        format="JPEG",
        quality=IMAGE_DEFAULT_QUALITY,
        subsampling=0,
        optimize=True,
        progressive=True
    )
    buffer.seek(0)
    return ImageReader(buffer)

def create_pdf(base_folder: str, folder: str) -> None:
    ''' Function to create PDFs to each folder '''
    fullpath = os.path.join(base_folder, folder)
    log.info('entrando na pasta %s...', fullpath)
    filepath = os.path.join(base_folder, folder + '.pdf')
    pdf_writer = canvas.Canvas(filepath)
    for item in os.listdir(fullpath):
        current = os.path.join(fullpath, item)
        log.info('Item atual: %s', current)
        if os.path.isdir(current):
            continue
        filetype = mimetypes.guess_type(current)
        if (filetype[0] is None) or ('image' not in filetype[0]):
            log.error('%s não é uma imagem! Pulando...', current)
            continue
        try:
            # Open image with Pillow to rotate
            image = Image.open(current)
            width, height = image.size
            if width > height:
                image = image.transpose(Image.Transpose.ROTATE_90)
            image = normalize_image(image)
            width, height = image.getSize() # reasign values due change
            # Transform pixels to points
            width = width * POINTS_PER_INCH / IMAGE_DPI
            height = height * POINTS_PER_INCH / IMAGE_DPI
            # set page size to A$ default size
            pdf_writer.setPageSize(A4)
            pdf_writer.drawImage(
                image=image,
                x=(PAGE_WIDTH - width) / 2,
                y=(PAGE_HEIGHT - height) / 2,
                width=width,
                height=height)
            pdf_writer.showPage()
            log.info('Imagem %s inserida no documento.', current)
        except OSError:
            # Skip truncated or unreadable images but continue processing
            log.error('%s erro ao processar! Pulando...', current)
    pdf_writer.save()
    log.info('Documento %s salvo com sucesso!', filepath)


if '__main__' == __name__:
    pesentation_banner()
    directory = askdirectory()
    log.info('Pasta raiz selecionada: %s', directory)
    if not directory:
        log.error('Não foi selecionada nenhuma pasta!')
    for item in os.listdir(directory):
        current = os.path.join(directory, item)
        if not os.path.isdir(current):
            log.error('%s não é uma pasta! Pulando...', current)
            continue
        create_pdf(directory, item)
    log.info('Programa finalizado! Digite qualquer tecla para sair.')
    input()
