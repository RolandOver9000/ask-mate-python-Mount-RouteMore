from flask import Flask, render_template, request, redirect, url_for
import connection
import data_manager

app = Flask(__name__)


@app.route("/")
@app.route("/list")
def route_list():
    """
    Retrieves sorted questions and renders template for the page that lists them.
    Sorting parameters are either retrieved from the query string generated by pressing the 'Sort' button,
        or are set to default values.
    :return: rendered template
    """

    if request.args:
        order_by = request.args.get('order_by')
        order_direction = request.args.get('order_direction')
    else:
        order_by, order_direction = 'submission_time', 'desc'

    sorted_questions = data_manager.get_all_questions()

    return render_template('list.html', sorted_questions=sorted_questions,
                           selected_sorting=order_by, selected_order=order_direction)


@app.route("/add-question", methods=['GET', 'POST'])
def route_add():

    if request.method == 'GET':
        return render_template('add-question.html', question_data={})

    user_inputs_for_question = request.form.to_dict()
    data_manager.insert_question(user_inputs_for_question)
    new_id = data_manager.get_latest_id('question')

    return redirect(url_for('display_question_and_answers', question_id=new_id))


@app.route('/question/<question_id>', methods=["GET", "POST"])
def display_question_and_answers(question_id):
    if request.method == 'GET':
        # update view number for question
        data_manager.increment_view_number(question_id)

    question_ids = data_manager.get_question_ids()
    question = data_manager.get_single_question(question_id)
    answers = data_manager.get_answers_for_question(question_id)
    return render_template('question.html', question=question, answers=answers, question_ids=question_ids)


@app.route('/question/<question_id>/vote', methods=['POST'])
def route_vote(question_id):
    vote_option, message_id, message_type = request.form['vote'].split(',')
    data_manager.handle_votes(vote_option, message_id, message_type)

    # the code=307 argument ensures that the request type (POST) is preserved after redirection
    # so that the view number of the question doesn't increase after voting
    return redirect(url_for('display_question_and_answers', question_id=question_id), code=307)


@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
def route_edit(question_id):
    question_data = data_manager.get_single_question(question_id)

    if request.method == 'GET':
        return render_template('add-question.html', question_data=question_data)

    user_inputs_for_question = request.form.to_dict()
    data_manager.update_entry('question', question_id, user_inputs_for_question)

    return redirect(url_for('display_question_and_answers', question_id=question_id))


@app.route("/question/<question_id>/new-answer", methods=["GET", "POST"])
def post_an_answer(question_id):
    if request.method == "POST":
        user_inputs_for_answer = request.form.to_dict()
        data_manager.write_new_answer_data_to_table(user_inputs_for_answer, question_id)
        return redirect(url_for('display_question_and_answers', question_id=question_id))
    else:
        question = data_manager.get_single_question(question_id)
        return render_template("new_answer.html", question=question)


@app.route('/question/<question_id>/delete')
def route_delete(question_id):
    data_manager.delete_question(question_id)

    return redirect(url_for('route_list'))


@app.route('/question/<question_id>/<answer_id>/delete')
def route_delete_answer(question_id, answer_id):
    data_manager.delete_answer(answer_id)
    return redirect(url_for('display_question_and_answers', question_id=question_id))


if __name__ == '__main__':
    app.run(debug=True)