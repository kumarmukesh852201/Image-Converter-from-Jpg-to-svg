from flask import Flask, render_template, request, send_file , abort
from PIL import Image
import io
import requests
import base64
import svgwrite
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15 MB limit

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            # Handle file upload
            if 'file' in request.files and request.files['file'].filename != '':
                file = request.files['file']
                filename, file_extension = os.path.splitext(file.filename)
                if file_extension.lower() == '.svg':
                    return render_template('message.html', message="The uploaded file is already in SVG format.")
                if file:
                    img = Image.open(file)
                    return convert_image_to_svg(img)
            # Handle URL upload
            elif 'url' in request.form and request.form['url'] != '':
                url = request.form['url']
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Check if the request was successful
                    if response.headers['Content-Type'] == 'image/svg+xml' or url.lower().endswith('.svg'):
                        return render_template('message.html', message="The provided URL points to an SVG file, which is already in SVG format.")
                    img = Image.open(io.BytesIO(response.content))
                    return convert_image_to_svg(img)
                except requests.exceptions.RequestException as e:
                    return render_template('message.html', message=f"Failed to fetch image from URL: {e}")
                except IOError:
                    return render_template('message.html', message="The provided URL does not contain a valid image.")
        except IOError:
            abort(413)
    return render_template('upload.html')

def convert_image_to_svg(img):
    img = img.convert('RGBA')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    b64_img = base64.b64encode(img_byte_arr).decode('utf-8')
    svg_data = f'<svg xmlns="http://www.w3.org/2000/svg" width="{img.width}" height="{img.height}"><image href="data:image/png;base64,{b64_img}" width="{img.width}" height="{img.height}"/></svg>'
    svg_io = io.BytesIO(svg_data.encode('utf-8'))
    return send_file(svg_io, mimetype='image/svg+xml', as_attachment=True, download_name='converted.svg')

@app.errorhandler(413)
def request_entity_too_large(error):
    return "The uploaded file size exceeds the 15 MB limit. Please upload a smaller file.", 413

if __name__ == '__main__':
    app.run(debug=True)