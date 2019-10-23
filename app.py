from flask import Flask, jsonify, request, render_template
from werkzeug import secure_filename
import codecs
import markowitz as mk
import csv

app = Flask(__name__)

@app.route('/upload', methods=['GET'])
def upload():
   return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))

        a = open(f.filename)
        opt = mk.Optimizer(a)
        alloc = opt.portfolio_alloc
                
        output_type = request.form.get('select')
        if output_type == 'json':
            return alloc
        else:
            output = [[], []]
            for i in alloc:
                output[0] += [i]
                output[1] += [str(alloc[i])]
            return ','.join(output[0]) + '\n' + ','.join(output[1])

if __name__ == '__main__':
    app.run(debug=True)