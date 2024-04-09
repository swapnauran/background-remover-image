from flask import Flask, render_template, request, send_file
from rembg import remove as remove_background
from PIL import Image
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('indexhtml', error='No file part')

        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')

        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            input_path = convert_to_png(filepath)

            output_filename = 'bg_removed_' + filename.rsplit('.', 1)[0] + '.png'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

            img = Image.open(input_path)
            bg_removed_img = remove_background(img)
            bg_removed_img.save(output_path, format='PNG')

            schedule_image_deletion(filepath, output_path)

            return render_template('index.html', result=True, filename=output_filename)
    return render_template('index.html')

def convert_to_png(input_path):
    img = Image.open(input_path)
    output_path = os.path.splitext(input_path)[0] + '.png'

    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    img.save(output_path, format='PNG')
    return output_path

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

def schedule_image_deletion(original_path, processed_path):
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_image, 'interval', seconds=120, args=[original_path, processed_path])
    scheduler.start()

def delete_image(original_path, processed_path):
    try:
        os.remove(original_path)
        os.remove(processed_path)
    except OSError as e:
        print(f"Error deleting images: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
