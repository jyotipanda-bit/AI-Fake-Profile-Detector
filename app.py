from flask import Flask, render_template, request
import easyocr
import numpy as np
from PIL import Image
import re

app = Flask(__name__)

# OCR Reader
reader = easyocr.Reader(['en'])


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():

    image = request.files.get('profile_image')

    score = 0
    reasons = []

    followers = 0
    following = 0
    posts = 0

    detected_text = ""

    if image and image.filename != "":

        try:

            # Read image
            img = Image.open(image).convert("RGB")

            img_array = np.array(img)

            # OCR
            results = reader.readtext(img_array)

            text_list = []

            for item in results:
                text_list.append(item[1])

            detected_text = " ".join(text_list).lower()

            # Extract numbers
            numbers = re.findall(r'\d+(?:,\d+)?', detected_text)

            clean_numbers = []

            for num in numbers:

                num = num.replace(",", "")

                try:
                    clean_numbers.append(int(num))
                except:
                    pass

            # Guess Instagram stats
            if len(clean_numbers) >= 3:

                posts = clean_numbers[0]
                followers = clean_numbers[1]
                following = clean_numbers[2]

            # POSTS ANALYSIS

            if posts == 0:
                score += 40
                reasons.append("No posts detected")

            elif posts < 3:
                score += 20
                reasons.append("Very few posts")

            elif posts > 10:
                score -= 10

            # FOLLOWERS ANALYSIS

            if followers < 10:
                score += 35
                reasons.append("Extremely low followers")

            elif followers < 50:
                score += 20
                reasons.append("Very low followers")

            elif followers > 500:
                score -= 15

            # FOLLOWING ANALYSIS

            if following > 3000:
                score += 30
                reasons.append("Too many following accounts")

            elif following > 1000:
                score += 10
                reasons.append("High following count")

            # USERNAME ANALYSIS

            usernames = re.findall(r'[a-zA-Z0-9_.]+', detected_text)

            for user in usernames:

                digit_count = sum(c.isdigit() for c in user)

                if digit_count >= 4:
                    score += 20
                    reasons.append("Suspicious username pattern")
                    break

                elif digit_count >= 2:
                    score += 10
                    reasons.append("Username contains numbers")
                    break

            # PRIVATE ACCOUNT

            if "private" in detected_text:
                score += 5
                reasons.append("Private account")

            # PROFILE PHOTO ANALYSIS

            unique_colors = len(
                np.unique(
                    img_array.reshape(-1, img_array.shape[2]),
                    axis=0
                )
            )

            if unique_colors < 100:
                score += 25
                reasons.append("Default or blank profile picture")

            # BIO ANALYSIS

            suspicious_words = [
                "crypto",
                "bitcoin",
                "earn money",
                "dm me",
                "promotion",
                "trading"
            ]

            for word in suspicious_words:

                if word in detected_text:
                    score += 15
                    reasons.append(f"Suspicious bio keyword: {word}")

        except Exception as e:

            return render_template(
                'index.html',
                result=f"Error: {e}",
                score=0,
                reasons=[]
            )

    else:

        return render_template(
            'index.html',
            result="Please upload a screenshot",
            score=0,
            reasons=[]
        )

    # FINAL SCORE FIX

    if score < 0:
        score = 0

    if score > 100:
        score = 100

    # FINAL RESULT

    if score >= 50:

        result = "⚠️ Fake Profile Detected"

    else:

        result = "✅ Real Profile Detected"

    return render_template(
        'index.html',
        result=result,
        score=score,
        reasons=reasons
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)