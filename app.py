from flask import Flask
import pandas as pd
import json
from markupsafe import escape
from flask import render_template, request, redirect, url_for
import re



app = Flask(__name__, static_folder='assets')

with open('data/squad_eval_context_only.json', 'r') as f:
    squad_context = json.load(f)
with open('data/tydiqa_eval_context_only.json', 'r') as f:
    tydiqa_context = json.load(f)
data_squad_qg = pd.read_excel('data/df_question_squad_inference_with_sim_score.xlsx')
data_tydiqa_qg = pd.read_excel('data/df_question_tydiqa_inference_with_sim_score.xlsx')

def get_highlighted_answer_in_context(answer, context):
    matches = re.finditer(r'\b' + re.escape(answer) + r'\b', context)
    return matches

def select_instance(index, data_source):
    if data_source == 'squad':
        data = data_squad_qg
        context = squad_context
    elif data_source == 'tydiqa':
        data = data_tydiqa_qg
        context = tydiqa_context
    else:
        return 'currently, the available options are squad or tydiqa'

    context = context[index]['context']
    selected = data.loc[index, : ].copy()
    matches = get_highlighted_answer_in_context(selected['answer'], context)
    offset = 0  

    for match in matches:
        start_idx = match.start() + offset
        end_idx = match.end() + offset
        matched_text = match.group()
        print(match)
        print(f"Matched Text: {match.group()}")
        print(f"Start Index: {match.start()}")
        print(f"End Index: {match.end()}")
        print(f"Match Span: {match.span()}")
        context = f"{context[:start_idx]}<mark>{matched_text}</mark>{context[end_idx:]}"
        print("-" * 40)
        offset += len(f"<mark></mark>")


    selected['context'] = context
    print(selected)

    if data_source == 'tydiqa':
        selected['score'] = [selected['bert_sim_baseline'], selected['bert_sim_v1'], selected['bert_sim_v2']]
    elif data_source == 'squad':
        selected['score'] = [selected['BERT_score_fuadi'], selected['BERT_score_v1'], selected['BERT_score_v2']]

    selected['hl_row'] = ["table-primary" if s == max(selected['score']) else "" for s in selected['score']]
    return dict(selected)

@app.route("/<source>/<int:index>")
def instance(index, source):
    selected = select_instance(index, source)
    
    return render_template('instances.html', data = selected, source = source)

@app.route("/<source>/redirect", methods=["POST"])
def redirect_to_instance(source):
    # Get the index from the form
    new_index = request.form.get("new_index")

    # Validate the index
    if not new_index or not new_index.isdigit() or int(new_index) < 1:
        return "Invalid index!", 400

    # Redirect to the target URL
    return redirect(url_for("instance", source=source, index=int(new_index)))


@app.route("/")
def dashboard():
    
    return render_template('hello.html')

