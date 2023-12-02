from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = bucket
region = region

db_conn = connections.Connection(
    host=host,
    port=3306,
    user=user,
    password=password,
    db=db

)
output = {}

@app.route("/", methods=['GET', 'POST'])
def Mainpage():
    return render_template('AddRecipe.html')


@app.route("/about")
def about():
    return render_template('About.html')


@app.route("/addrecipe", methods=['POST'])
def Add():
    recipe_id = request.form['recipe_id']
    recipe_name = request.form['recipe_name']
    recipe_ingredients = request.form['recipe_ingredients']
    recipe_process = request.form['recipe_process']
    famous_in_place = request.form['famous_in_place']
    recipe_picture_url = request.files['recipe_picture_url']

    insert = "INSERT INTO recipe VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
    if recipe_picture_url.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert, (recipe_id, recipe_name, recipe_ingredients, recipe_process, famous_in_place))
        db_conn.commit()
        recipe_picture_url_name_in_s3 = "recipe-id-" + str(recipe_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            s3.Bucket(bucket).put_object(Key=recipe_picture_url_name_in_s3, Body=recipe_picture_url)
            buckt_loc = boto3.client('s3').get_bucket_location(Bucket=bucket)
            loc_s3 = (buckt_loc['LocationConstraint'])

            if loc_s3 is None:
                loc_s3 = ''
            else:
                loc_s3 = '-' + loc_s3

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                loc_s3,
                bucket,
                recipe_picture_url_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    return render_template('RecipeAdded.html', recipe_name=recipe_name)

@app.route("/retrieve", methods=['POST'])
def fetch_data():
    recipe_name = request.form['recipe_name']

    if recipe_name is None:
        return "Please give recipe name."

    select = "SELECT * FROM recipe WHERE recipe_name = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select, (recipe_name,))
        data = cursor.fetchone()

        if data is None:
            return f"No recipe named {recipe_name} was found"

        recipe_id = data[0]
        recipe_data = {
            'recipe_id': data[0],
            'recipe_name': data[1],
            'recipe_ingredients': data[2],
            'recipe_process': data[3],
            'famous_in_place': data[4],
            'recipe_picture_url': get_s3(recipe_id),  
        }

        return render_template('GetRecipeDet.html', **recipe_data)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

def get_s3(recipe_id):
    loc_s3 = boto3.client('s3').get_bucket_location(Bucket=bucket)
    loc_s3 = loc_s3.get('LocationConstraint', '')
    loc_s3 = '' if loc_s3 is None else f"-{loc_s3}"
    image_key = f"recipe-id-{recipe_id}_image_file"
    return f"https://s3{loc_s3}.amazonaws.com/{bucket}/{image_key}"

@app.route("/getrecipe", methods=['GET'])
def get_recipe():
    return render_template('RetriveRecipe.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
