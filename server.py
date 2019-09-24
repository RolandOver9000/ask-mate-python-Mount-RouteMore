from flask import Flask, render_template, request, redirect, url_for
import data_manager
import util

app = Flask(__name__)


@app.route("/")
def route_index():
    sorted_questions = data_manager.get_most_recent_questions()
    return render_template('index.html', sorted_questions=sorted_questions)


@app.route("/list")
def route_list():
    """
    Retrieves sorted questions and renders template for the page that lists them.
    Sorting parameters are either retrieved from the query string generated by pressing the 'Sort' button,
        or are set to default values.
    :return: rendered template
    """

    if request.args:
        order_by= request.args.get('order_by')
        order = request.args.get('order_direction')
    else:
        order_by, order = 'submission_time', 'desc'

    sorted_questions = data_manager.get_all_questions(order_by, order)
    return render_template('list.html', sorted_questions=sorted_questions,
                           selected_sorting=order_by, selected_order=order)


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
    tags = data_manager.get_tags_for_question(question_id)
    comments = data_manager.get_all_comments(question_id)
    return render_template('question.html', question=question, tags=tags,
                           answers=answers, question_ids=question_ids, comments=comments)


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


@app.route('/answer/<answer_id>/edit', methods=['GET', 'POST'])
def route_edit_answer(answer_id):
    answer_data = data_manager.get_single_entry('answer', answer_id)
    question_id = answer_data.get('question_id')
    question_data = data_manager.get_single_entry('question', question_id)

    if request.method == 'GET':
        return render_template('new_answer.html', answer=answer_data, question=question_data)

    user_inputs_for_answer = request.form.to_dict()
    data_manager.update_entry('answer', answer_id, user_inputs_for_answer)

    return redirect(url_for('display_question_and_answers', question_id=question_id))


@app.route('/question/<question_id>/new-tag', methods=["GET", "POST"])
def route_new_tag(question_id):
    existing_tags = data_manager.get_existing_tags()

    if request.method == "POST":
        tag = request.form.to_dict()
        if tag['new_tag'] == '':
            util.add_tag_to_question(question_id, int(tag['existing_tag']))
        else:
            util.add_new_tag_to_question(question_id, tag['new_tag'])

        return redirect(url_for('display_question_and_answers', question_id=question_id))

    return render_template('new_tag.html', existing_tags=existing_tags)


@app.route('/answer/<question_id>/<answer_id>/new_comment', methods=["GET", "POST"])
def add_new_comment_to_answer(question_id, answer_id):
    if request.method == "GET":
        answer_by_id = data_manager.get_single_entry('answer', answer_id)
        return render_template('new_comment.html', answer_by_id=answer_by_id)

    new_comment_data = {'new_comment': request.form['comment'],
                        'answer_id': answer_id,
                        'question_id': question_id
                        }
    data_manager.write_new_comment_data_to_table(new_comment_data)
    return redirect(url_for('display_question_and_answers', question_id=question_id, answer_id=answer_id))


@app.route('/question/<question_id>/new-comment', methods=["GET", "POST"])
def route_add_comment_to_question(question_id):
    if request.method == 'GET':
        question = data_manager.get_single_entry('question', question_id)
        return render_template('new_comment.html', answer_by_id=question)

    new_comment_data = {'new_comment': request.form['comment'],
                        'question_id': question_id,
                        'answer_id': None}
    data_manager.write_new_comment_data_to_table(new_comment_data)
    return redirect(url_for('display_question_and_answers', question_id=question_id))


@app.route('/search')
def route_search():
    search_phrase = request.args.get('search_phrase')
    sorted_questions = data_manager.get_questions_by_search_phrase(search_phrase)
    return render_template('search.html', sorted_questions=sorted_questions)


@app.route('/question/<question_id>/<answer_id>/<comment_id>/delete', methods=["GET", "POST"])
def delete_comment(question_id, answer_id, comment_id):
    if request.method == "GET":
        comment = data_manager.get_single_entry('comment', comment_id)
        answer_data = data_manager.get_single_entry('answer', answer_id)
        return render_template('delete_comment.html', answer=answer_data['message'], comment=comment)

    if request.form['delete-button'] == 'Yes':
        data_manager.delete_data_by_id('comment', comment_id)

    return redirect(url_for('display_question_and_answers', question_id=question_id))


@app.route('/comments/<comment_id>/edit')
def route_edit_comment(comment_id):
    comment_data = data_manager.get_single_entry('comment', comment_id)
    question_id = comment_data.get('question_id')

    if request.method == 'GET':
        return render_template('new_comment.html', comment=comment_data)

    user_inputs_for_comment = request.form.to_dict()
    data_manager.update_entry('comment', comment_id, user_inputs_for_comment)

    return redirect(url_for('display_question_and_answers', question_id=question_id))


if __name__ == '__main__':
    app.run(debug=True)
