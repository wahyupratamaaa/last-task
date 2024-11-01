from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    url_for,
    redirect
    )
import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from bson import ObjectId

load_dotenv()  # Memuat file .env

app = Flask(__name__)

# Mengambil variabel dari .env
mongo_user = os.getenv('MONGO_USER')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_cluster_url = os.getenv('MONGO_CLUSTER_URL')


mongo_url = f'mongodb+srv://{mongo_user}:{mongo_password}@{mongo_cluster_url}/?retryWrites=true&w=majority'
client = MongoClient(mongo_url)
db = client.sparta_plus_week2


@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})  
    print('get data',words_result)

    words = []
    for word in words_result:
        definition = word.get('definition', [])
        if isinstance(definition, list) and definition:
            shortdef = definition[0].get('shortdef', 'Definition not available')
            print('data yang kau carii ta',definition)
        else:
            shortdef = 'Definition not available'

        words.append({
            'word': word.get('word', 'No word found'),
            'definition': shortdef
        })
        msg = request.args.get('msg')

    return render_template('index.html', words=words, msg=msg)
 
@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "543938be-681c-47e4-bfca-72041496f1b7";
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definition = response.json()
    print('WOI POQIII ERRORRR',definition)
   
    if response.status_code != 200:
        return jsonify ({'error': 'tidak ada api'}), 500

    definition = response.json()

    if not definition:
        return redirect(url_for('error', keyword=keyword))

    if type(definition[0]) is str:
        suggestions = ', '.join(definition)
        return redirect(url_for('error',keyword=keyword, suggestions=suggestions))

    status = request.args.get('status_give','new')
    return render_template(
        'detail.html',
        definition=definition,
          keyword= keyword  ,
            status=status)#     

@app.route('/error', methods=['GET'])
def error():
    keyword = request.args.get('keyword', '')
    suggestions = request.args.get('suggestions', '')
    # suggested_words = suggestions.split(',') if suggestions else []
    suggested_words = [word.strip() for word in suggestions.split(',') if word] if suggestions else []
    
    return render_template(
        'error.html',
        word=keyword,
        suggested_words=suggested_words
    )


@app.route('/practice')
def practice():
    return render_template('practice.html')

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()  # Menerima data sebagai JSON
    word = json_data.get('word_give')
    definition = json_data.get('definition_give')
    
    if word and definition:  # Memastikan data tidak kosong
        doc = {
            'word': word,
            'definition': definition,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        db.words.insert_one(doc)  # Simpan ke database
        return jsonify(
            {
                'result': 'success',
                'msg': f'Word {word} Berhasil di simpan',
            }
        )
    else:
        return jsonify({'result': 'error', 'msg': 'Incomplete data'}), 400

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.get_data().decode('utf-8')
    word = word.split('=')[1]

    db.words.delete_one({'word': word})
    db.examples.delete_many({'keyword': word})
    return jsonify({
        'result': 'success',
        'msg': f'Data {word} Berhasil di hapus'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    if word is None:
        return jsonify({'result': 'error', 'message': 'Word tidak ditemukan'})
    
    example_data = db.examples.find({'keyword': word})
    if example_data is None:
        return jsonify({'result': 'error', 'message': 'Data tidak ditemukan'})
    
    examples = [{
        'example': ex.get('example'),
        'id': str(ex.get('_id'))
    }
        for ex in example_data
    ]
    
    return jsonify({'result': 'success', 'examples': examples})
@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    keyword = request.form.get('keyword')
    example = request.form.get('example')
    doc = {
        'keyword': keyword,
        'example': example,
    }
    db.examples.insert_one(doc)
    print(doc)
    return jsonify ({
        'result': 'success', 
        'msg': f'Your example, {example} ,for the word, {keyword} was save'})
@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify ({'result': 'success', 'msg': f'Data {word} berhasil di hapus'})

try:

    print('server run')
except Exception as e:
    print("Gagal mengakses API:", e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
