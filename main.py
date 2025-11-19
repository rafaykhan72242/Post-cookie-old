from flask import Flask, render_template, request, redirect, url_for
import requests
import re
import time
import os

app = Flask(__name__)

def make_request(url, headers, cookies):
    try:
        response = requests.get(url, headers=headers, cookies=cookies).text
        return response
    except requests.RequestException as e:
        return str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'RAFFAY_KHAN' and password == 'RAFFAY-INXIDE':
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html', error="Incorrect Password! Try again.")
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        cookies = request.form['cookie']
        id_post = request.form['post_id']
        commenter_name = request.form['commenter_name']
        delay = int(request.form['delay'])
        comment_file = request.files['comment_file']

        # Save uploaded file
        comment_file_path = os.path.join('uploads', comment_file.filename)
        os.makedirs('uploads', exist_ok=True)
        comment_file.save(comment_file_path)

        # -------- FIXES HERE ----------
        # FIX 1: Duplicate cookie passing removed
        response = make_request(
            'https://business.facebook.com/business_locations',
            headers={
                'Cookie': cookies,
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/103 Mobile Safari/537.36'
            },
            cookies={'Cookie': cookies}
        )

        if not response:
            return render_template('dashboard.html', error="Error making initial request")

        # FIX 2: Regex raw string (no warning)
        try:
            token_eaab = re.search(r'(EAAB\w+)', str(response)).group(1)
        except Exception:
            return render_template('dashboard.html', error="EAAB token not found in response")

        # Read comments
        with open(comment_file_path, 'r') as file:
            comments = [c.strip() for c in file.readlines() if c.strip()]

        if not comments:
            return render_template('dashboard.html', error="Comment file is empty")

        x = 0
        results = []

        # -------- FIX 3: Infinite loop protection --------
        # Loop for 500 comments max (safe)
        for _ in range(500):
            try:
                time.sleep(delay)
                teks = comments[x]
                comment_text = f"{commenter_name}: {teks}"

                data = {
                    'message': comment_text,
                    'access_token': token_eaab   # FIX 4: Correct variable name
                }

                response2 = requests.post(
                    f'https://graph.facebook.com/{id_post}/comments/',
                    data=data,
                    cookies={'Cookie': cookies}
                ).json()

                if 'id' in response2:
                    results.append({
                        'post_id': id_post,
                        'datetime': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'comment': comment_text,
                        'status': 'Success'
                    })
                else:
                    results.append({
                        'post_id': id_post,
                        'comment': comment_text,
                        'status': 'Failure',
                        'link': f"https://m.facebook.com/{id_post}"
                    })

                x = (x + 1) % len(comments)

            except Exception as e:
                results.append({
                    'status': 'Error',
                    'message': str(e)
                })
                time.sleep(5.5)

        return render_template('dashboard.html', results=results)

    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
