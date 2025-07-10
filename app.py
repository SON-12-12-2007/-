from flask import Flask, request, redirect, url_for, render_template_string
from openai import OpenAI
import random

app = Flask(__name__)

user_fridge = []
current_id = 1


def ai(prompt, ask):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="",
    )
    completion = client.chat.completions.create(
        extra_body={},
        model="deepseek/deepseek-r1:free",
        messages=[{"role": "user", "content": f'{prompt}.{ask}'}])
    return completion.choices[0].message.content


def calculate_bmi(weight, height):
    if weight and height:
        return round(weight / ((height / 100) ** 2), 1)
    return None


def calculate_daily_norm(age, gender, weight, height, activity, goal):
    if not all([age, gender, weight, height]):
        return None

    if gender == "Мужской":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    activity_factors = {
        "Сидячий": 1.2,
        "Легкая активность": 1.375,
        "Умеренная активность": 1.55,
        "Активный": 1.725
    }

    tdee = bmr * activity_factors.get(activity, 1.2)

    if goal == "Похудение":
        tdee *= 0.85
    elif goal == "Набор массы":
        tdee *= 1.15

    protein = weight * 2 if goal == "Набор массы" else weight * 1.6
    fat = (tdee * 0.25) / 9
    carbs = (tdee - (protein * 4) - (fat * 9)) / 4

    return {
        "калории": round(tdee),
        "белки": round(protein),
        "жиры": round(fat),
        "углеводы": round(carbs)
    }


@app.route('/')
def start():
    fridge_content = ""
    for product in user_fridge:
        if product['unit'] == 'шт':
            fridge_content += f"<li>{product['name']} - {product['amount']} {product['unit']}</li>"
        else:
            fridge_content += f"<li>{product['name']} - {product['amount']}г</li>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Virtual Fridge</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .container {{
                display: flex;
                gap: 20px;
            }}
            .left-column, .right-column {{
                flex: 1;
            }}
            .middle-column {{
                flex: 2;
            }}
            .fridge-list {{
                background: #f8f8f8;
                padding: 20px;
                border-radius: 5px;
                min-height: 200px;
            }}
            .button {{
                display: block;
                width: 100%;
                padding: 15px;
                margin-bottom: 15px;
                background: #4CAF50;
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 5px;
                font-size: 16px;
            }}
            .button-blue {{
                background: #2196F3;
            }}
            .button-orange {{
                background: #FF9800;
            }}
            ul {{
                padding-left: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Virtual fridge</h1>
            <p>Наш сайт поможет вам сэкономить время и деньги, а также разработать специальный рацион питания конкретно для вас</p>
        </div>

        <div class="container">
            <div class="left-column">
                <a href="/recipe" class="button button-orange">Сгенерировать рецепт</a>
            </div>

            <div class="middle-column">
                <a href="/add_list" class="button">Пополнить холодильник</a>
                <div class="fridge-list">
                    <h3>Ваши продукты:</h3>
                    {fridge_content if user_fridge else "<p>Холодильник пуст</p>"}
                </div>
            </div>

            <div class="right-column">
                <a href="/analysis" class="button button-blue">Анализ питания от ИИ</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/add_list', methods=['GET', 'POST'])
def list_products():
    global current_id

    if request.method == 'POST':
        product = request.form.get('product')
        if product:
            is_countable = ai(
                'Ответь "да", если продукт обычно измеряется в штуках (например, яйца, бананы, яблоки), и "нет" если в граммах/миллилитрах (например, молоко, мука)',
                f'продукт: {product}'
            ).strip().lower() == 'да'
            unit_type = 'шт' if is_countable else 'г'

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Укажите количество</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }}
                    input, select {{ padding: 10px; width: 100%; margin: 10px 0; }}
                    button {{ padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; width: 100%; }}
                </style>
            </head>
            <body>
                <h2>Укажите количество для: {product}</h2>
                <form method="POST" action="/save_product">
                    <input type="hidden" name="product" value="{product}">
                    <input type="hidden" name="unit" value="{unit_type}">
                    <input type="number" step="0.1" name="quantity" placeholder="Количество" required>
                    <p>Единица измерения: {unit_type}</p>
                    <button type="submit">Добавить</button>
                </form>
            </body>
            </html>
            """

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Добавить продукт</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }
            input { padding: 10px; width: 100%; margin: 10px 0; }
            button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; width: 100%; }
        </style>
    </head>
    <body>
        <h2>Добавить продукт в холодильник</h2>
        <form method="POST">
            <input type="text" name="product" placeholder="Например: молоко, яйца" required>
            <button type="submit">Далее</button>
        </form>
    </body>
    </html>
    """


@app.route('/save_product', methods=['POST'])
def save_product():
    global current_id
    product = request.form.get('product')
    quantity = request.form.get('quantity')
    unit = request.form.get('unit')

    if not product or not quantity:
        return redirect(url_for('product_not_found'))

    try:
        quantity = float(quantity)
    except:
        return redirect(url_for('product_not_found'))

    ans = ai(
        'напиши информацию о продукте (название,калории,белки,жиры,углеводы на 100г) в формате: продукт,калории,белки,жиры,углеводы. Если не пищевой продукт, ответь "не_еда"',
        f'продукт: {product}'
    )

    if ans.strip().lower() == 'не_еда':
        return redirect(url_for('product_not_found'))

    try:
        name, calories, protein, fat, carbs = ans.split(',')
        user_fridge.append({
            'id': current_id,
            'name': name.strip(),
            'nutrition': {
                'калории': float(calories),
                'белки': float(protein),
                'жиры': float(fat),
                'углеводы': float(carbs)
            },
            'amount': quantity,
            'unit': unit
        })
        current_id += 1
        return redirect(url_for('start'))
    except:
        return redirect(url_for('product_not_found'))


@app.route('/product_not_found')
def product_not_found():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Продукт не найден</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }
            a { color: #2196F3; text-decoration: none; }
        </style>
    </head>
    <body>
        <h2>Продукт не найден</h2>
        <a href="/add_list">← Попробовать снова</a>
    </body>
    </html>
    """


@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    if request.method == 'POST':
        age = int(request.form['age'])
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        activity = request.form['activity']
        goal = request.form['goal']

        bmi = calculate_bmi(weight, height)
        daily_norm = calculate_daily_norm(age, gender, weight, height, activity, goal)

        analysis_prompt = (
            f"Проанализируй питание для {age}-летнего {'мужчины' if gender == 'Мужской' else 'женщины'} с ИМТ {bmi}. "
            f"Цель: {goal}. Активность: {activity}. "
            f"Продукты в холодильнике: {', '.join(p['name'] for p in user_fridge)}. "
            "Дай рекомендации по питанию, укажи на возможные дефициты. "
            "Будь конкретным и научно обоснованным."
        )

        ai_analysis = ai(analysis_prompt, "")

        recipe_prompt = (
                "Предложи 2 рецепта используя эти продукты: " + ", ".join(p['name'] for p in user_fridge) + ". "
                                                                                                            "И 1 рецепт из других полезных продуктов. Формат: "
                                                                                                            "1. [Название] - [Ингредиенты] - [Краткое описание]"
        )

        recipes = ai(recipe_prompt, "")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Анализ питания</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 20px; background: #f8f8f8; border-radius: 5px; }}
                pre {{ white-space: pre-wrap; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 15px; background: #2196F3; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Анализ питания от ИИ</h1>

            <div class="section">
                <h2>Ваша норма КБЖУ</h2>
                <p>Калории: {daily_norm['калории']} ккал</p>
                <p>Белки: {daily_norm['белки']} г</p>
                <p>Жиры: {daily_norm['жиры']} г</p>
                <p>Углеводы: {daily_norm['углеводы']} г</p>
            </div>

            <div class="section">
                <h2>Рекомендации</h2>
                <pre>{ai_analysis}</pre>
            </div>

            <div class="section">
                <h2>Рецепты</h2>
                <pre>{recipes}</pre>
            </div>

            <a href="/">← На главную</a>
        </body>
        </html>
        """

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Анализ питания</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }
            input, select { padding: 10px; width: 100%; margin: 10px 0; }
            button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; width: 100%; }
        </style>
    </head>
    <body>
        <h1>Анализ питания</h1>
        <form method="POST">
            <input type="number" name="age" placeholder="Возраст" required>
            <select name="gender" required>
                <option value="Мужской">Мужской</option>
                <option value="Женский">Женский</option>
            </select>
            <input type="number" step="0.1" name="weight" placeholder="Вес (кг)" required>
            <input type="number" step="0.1" name="height" placeholder="Рост (см)" required>
            <select name="activity" required>
                <option value="Сидячий">Сидячий образ жизни</option>
                <option value="Легкая активность">Легкая активность</option>
                <option value="Умеренная активность">Умеренная активность</option>
                <option value="Активный">Активный образ жизни</option>
            </select>
            <select name="goal" required>
                <option value="Похудение">Похудение</option>
                <option value="Поддержание веса">Поддержание веса</option>
                <option value="Набор массы">Набор массы</option>
            </select>
            <button type="submit">Получить анализ</button>
        </form>
    </body>
    </html>
    """


@app.route('/recipe', methods=['GET', 'POST'])
def generate_recipe():
    if request.method == 'POST':
        if 'custom_products' in request.form:
            custom_products = request.form.get('custom_products', '').strip()
            if custom_products:
                product_list = [p.strip() for p in custom_products.split(',') if p.strip()]
                return generate_recipe_response(product_list)

        elif 'fridge_products' in request.form:
            selected_ids = request.form.getlist('product_checkbox')
            product_list = []
            for product in user_fridge:
                if str(product['id']) in selected_ids:
                    product_list.append(product['name'])
            return generate_recipe_response(product_list)

    return render_recipe_form()


def render_recipe_form():
    fridge_products_html = ""
    for product in user_fridge:
        fridge_products_html += f"""
        <div style="margin: 5px 0;">
            <input type="checkbox" id="product_{product['id']}" name="product_checkbox" value="{product['id']}">
            <label for="product_{product['id']}">{product['name']} ({product['amount']}{product['unit']})</label>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Генератор рецептов</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .columns {{ display: flex; gap: 20px; }}
            .column {{ flex: 1; padding: 20px; background: #f8f8f8; border-radius: 5px; }}
            textarea {{ width: 100%; height: 150px; padding: 10px; }}
            button {{ padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; width: 100%; }}
            .button-blue {{ background: #2196F3; }}
            a {{ display: inline-block; margin-top: 20px; color: #2196F3; }}
        </style>
    </head>
    <body>
        <h1>Сгенерировать рецепт</h1>
        <div class="columns">
            <div class="column">
                <h3>Выберите из холодильника:</h3>
                <form method="POST">
                    {fridge_products_html if user_fridge else "<p>В холодильнике пока нет продуктов</p>"}
                    <button type="submit" name="fridge_products" {'disabled' if not user_fridge else ''}>Сгенерировать</button>
                </form>
            </div>
            <div class="column">
                <h3>Или введите свои продукты:</h3>
                <form method="POST">
                    <textarea name="custom_products" placeholder="Введите продукты через запятую"></textarea>
                    <button type="submit" name="custom_products" class="button-blue">Сгенерировать</button>
                </form>
            </div>
        </div>
        <a href="/">← На главную</a>
    </body>
    </html>
    """


def generate_recipe_response(product_list):
    if len(product_list) < 3:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ошибка</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }
                a { color: #2196F3; text-decoration: none; }
            </style>
        </head>
        <body>
            <h2>Недостаточно продуктов</h2>
            <p>Нужно минимум 3 продукта</p>
            <a href="/recipe">← Попробовать снова</a>
        </body>
        </html>
        """

    recipe_prompt = (
            "Сгенерируй проверенный рецепт из продуктов: " + ", ".join(product_list) + ". "
                                                                                       "Формат:\n\n"
                                                                                       "1. Название блюда\n\n"
                                                                                       "2. Ингредиенты с количествами\n\n"
                                                                                       "3. Пошаговый рецепт\n\n"
                                                                                       "Используй только стандартные кулинарные техники. "
                                                                                       "Если продукты не сочетаются, напиши 'Невозможно создать безопасный рецепт из этих продуктов'"
    )

    recipe = ai(recipe_prompt, "")
    formatted_recipe = recipe.replace('\n\n', '<br><br>').replace('\n', '<br>')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Рецепт</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .recipe-box {{ background: #f8f8f8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            a {{ display: inline-block; margin-top: 20px; padding: 10px 15px; background: #2196F3; color: white; text-decoration: none; border-radius: 5px; }}
            .button-green {{ background: #4CAF50; margin-right: 10px; }}
        </style>
    </head>
    <body>
        <h1>Ваш рецепт</h1>
        <div class="recipe-box">
            {formatted_recipe}
        </div>
        <div>
            <a href="/recipe" class="button-green">Новый рецепт</a>
            <a href="/">На главную</a>
        </div>
    </body>
    </html>
    """


if __name__ == '__main__':
    app.run(debug=True)