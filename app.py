import json
import os

import plotly
import werkzeug
from elasticsearch import Elasticsearch
from flask import Flask, render_template, request, flash, jsonify  # import flask
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional

from config import Config, ROOT_DIR_MAIN, dir_output
from load_elasticsearch import search_city_stat, search_zip_stat, init_elastic_search, search_city_stat_comp, \
    search_zip_stat_comp
from plot_from_db import plotly_normal_curve

app = Flask(__name__,
            static_folder="./static",
            template_folder="./templates")  # create an findpermit instance
CORS(app)
app.templates_auto_reload = True
app.config.from_object(Config)
db = SQLAlchemy(app)

from models import *

Bootstrap(app)

app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    if app.config['ELASTICSEARCH_URL'] else None

with app.app_context():
    init_elastic_search(app.elasticsearch)


class FindPermitForm(FlaskForm):
    city = StringField('City', validators=[Optional()])
    state = StringField('State', validators=[Optional()])
    zip_code = StringField('ZIP', validators=[Optional()])
    work = StringField('Work', validators=[Optional()])
    button = SubmitField('Search')

    def validate(self):
        if not super(FindPermitForm, self).validate():
            return False
        if not self.city.data and not self.state.data:
            msg = 'fill the state and city or Zip'
            self.city.errors.append(msg)
            self.state.errors.append(msg)
            return False
        return True


@app.route('/', methods=["GET", "POST"])
def main():
    form = FindPermitForm(request.form)
    img_city = []
    img_zip = []
    if request.method == 'POST':
        if form.city.data and form.state.data and form.work.data:
            # strCity='Boston', strState='MA',  strCombOnt='remodel kitchen'
            str_onto = form.city.data + ' ' + form.state.data + ', ' + form.work.data
            if app.elasticsearch:
                df = search_city_stat(app.elasticsearch, scode=form.state.data, city=form.city.data,
                                      ontology=form.work.data)
            else:

                df = CityStateStatistic.query.join(UsCities, CityStateStatistic.sourcecity == UsCities.id).join(
                    UsStates,
                    CityStateStatistic.sourcestate == UsStates.id).join(
                    CombOntology, CityStateStatistic.ncombont == CombOntology.id).filter(
                    UsStates.scode == form.state.data).filter(
                    UsCities.city == form.city.data).filter(CombOntology.desc_comb_ontology == form.work.data).first()
            if not df:
                flash('Not data')
            else:
                res_plot_set = df['plot_set'].replace("\'", "\"").replace('array', '').replace('(',
                                                                                               '').replace(
                    ')',
                    '')

                res_json = json.loads(res_plot_set)
                # q25 = df.my_column_name_25
                # q50 = df.my_column_name_50
                # q75 = df.my_column_name_75
                q25 = df['q_25']
                q50 = df['q_50']
                q75 = df['q_75']
                print(df['id'])
                query_city = search_city_stat_comp(app.elasticsearch, df['id'])
                print(query_city)
                logo_norm = plot_image(res_json, q25=q25, q50=q50, q75=q75, str_onto=str_onto, save=True, show=False,
                                       dir=os.path.join(ROOT_DIR_MAIN, r'static/images'), fig_name=str_onto)
                fake_norm = fake_normal_more(q25=q25, q50=q50, q75=q75, str_onto=str_onto, save=True, show=False,
                                             dir=os.path.join(ROOT_DIR_MAIN, 'static/images'), fig_name=str_onto)
                img_city = [os.path.join(dir_output, logo_norm), os.path.join(dir_output, fake_norm)]

        elif form.zip_code.data and form.work.data:
            str_onto = form.zip_code.data + ', ' + form.work.data
            # df = ZipStatistic.query.join(CombOntology, ZipStatistic.ncombont == CombOntology.id).filter(
            #     ZipStatistic.zip == form.zip_code.data).filter(
            #     CombOntology.desc_comb_ontology == form.work.data).first()

            df = search_zip_stat(app.elasticsearch, zip=form.zip_code.data, ontology=form.work.data)
            if not df:
                flash('Not data')
            else:
                res_plot_set = df['plot_set'].replace("\'", "\"").replace('array', '').replace('(',
                                                                                               '').replace(
                    ')',
                    '')

                print(str_onto)
                res_json = json.loads(res_plot_set)
                # q25 = df.my_column_name_25
                # q50 = df.my_column_name_50
                # q75 = df.my_column_name_75
                q25 = df['q_25']
                q50 = df['q_50']
                q75 = df['q_75']
                query_zip = search_zip_stat_comp(app.elasticsearch, df['id'])
                print(query_zip)
                logo_norm = plot_image(res_json, q25=q25, q50=q50, q75=q75, str_onto=str_onto, save=True, show=False,
                                       dir=os.path.join(ROOT_DIR_MAIN, 'static/images'), fig_name=str_onto)
                fake_norm = fake_normal_more(q25=q25, q50=q50, q75=q75, str_onto=str_onto, save=True, show=False,
                                             dir=os.path.join(ROOT_DIR_MAIN, 'static/images'),
                                             fig_name=str_onto)
                img_zip = [os.path.join(dir_output, logo_norm), os.path.join(dir_output, fake_norm)]

        return render_template("main.html", img_city=img_city, img_zip=img_zip, form=form)
    return render_template("main.html", form=form)  # which returns "hello world"


@app.route('/city_search', methods=["GET"])
def city_search():
    city = request.form.get('city', type=str)
    scode = request.form.get('scode', type=str)
    comb_ontoloy = request.form.get('ontology', type=str)
    print(city, scode, comb_ontoloy)
    if city and scode and comb_ontoloy:
        # strCity='Boston', strState='MA',  strCombOnt='remodel kitchen'
        str_onto = city + ' ' + scode + ', ' + comb_ontoloy
        df = search_city_stat(app.elasticsearch, scode=scode, city=city,
                              ontology=comb_ontoloy)
        if df:
            res_plot_set = df['plot_set'].replace("\'", "\"").replace('array', '').replace('(',
                                                                                           '').replace(
                ')',
                '')
            res_json = json.loads(res_plot_set)
            q25 = df['q_25']
            q50 = df['q_50']
            q75 = df['q_75']
            query_city = search_city_stat_comp(app.elasticsearch, df['id'])
            print(query_city)
            plot_data = plotly_normal_curve(q25=q25, q50=q50, q75=q75, str_onto=str_onto)
            print(plot_data)
            #     TODO:// func for plot generator
            return jsonify(figure=json.dumps(plot_data, cls=plotly.utils.PlotlyJSONEncoder), company=query_city)
        else:
            return jsonify(figure=[], company=[])
    else:
        return None


@app.route('/zip_search', methods=["GET", "POST"])
def zip_search():
    zip = request.args.get('city', type=str)
    comb_ontoloy = request.args.get('ontology', type=str)
    if zip and comb_ontoloy:
        # strCity='Boston', strState='MA',  strCombOnt='remodel kitchen'
        str_onto = zip + ', ' + comb_ontoloy
        df = search_zip_stat(app.elasticsearch, zip=zip,
                             ontology=comb_ontoloy)
        if df:
            res_plot_set = df['plot_set'].replace("\'", "\"").replace('array', '').replace('(',
                                                                                           '').replace(
                ')',
                '')
            res_json = json.loads(res_plot_set)
            q25 = df['q_25']
            q50 = df['q_50']
            q75 = df['q_75']
            query_city = search_zip_stat_comp(app.elasticsearch, df['id'])
            plot_data = plotly_normal_curve(q25=q25, q50=q50, q75=q75, str_onto=str_onto)
            #     TODO:// func for plot generator
            return jsonify(figure=plot_data, company=query_city)
        else:
            return jsonify(figure=[], company=[])
    else:
        return None


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return 'bad request!', 400


if __name__ == "__main__":  # on running python findpermit.py
    app.run(host='0.0.0.0', port=5000)
