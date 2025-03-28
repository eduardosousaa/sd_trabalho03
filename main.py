from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageFilter, ImageTk
import os
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, Label
import requests
import threading

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS imagens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome_arquivo TEXT,
                        filtro_aplicado TEXT,
                        data_hora TEXT
                    )''')
    conn.commit()
    conn.close()

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo inválido'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    image = Image.open(filepath)
    processed_image = image.filter(ImageFilter.CONTOUR)
    processed_filepath = os.path.join(PROCESSED_FOLDER, file.filename)
    processed_image.save(processed_filepath)
    
    conn = sqlite3.connect('images.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO imagens (nome_arquivo, filtro_aplicado, data_hora) VALUES (?, ?, ?)',
                   (file.filename, 'CONTOUR', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
    return send_file(processed_filepath, mimetype='image/png')

def select_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        with open(file_path, 'rb') as file:
            response = requests.post('http://localhost:5000/upload', files={'file': file})
            if response.status_code == 200:
                processed_image_path = "processed_image.png"
                with open(processed_image_path, 'wb') as img_file:
                    img_file.write(response.content)
                
                print("Imagem processada salva como 'processed_image.png'")
                
                display_image(processed_image_path)
            else:
                print("Erro ao enviar a imagem.")

def display_image(image_path):
    img = Image.open(image_path)
    img = img.resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)

    label_image.config(image=img_tk)
    label_image.image = img_tk

if __name__ == '__main__':
    init_db()

    # Inicia o Flask em uma thread separada
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False})
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia a interface gráfica (Tkinter)
    root = tk.Tk()
    root.title("Cliente de Upload de Imagem")

    btn_upload = tk.Button(root, text="Selecionar Imagem", command=select_image)
    btn_upload.pack(pady=20)

    # Label para exibir a imagem processada
    label_image = Label(root)
    label_image.pack(pady=20)

    root.mainloop()
