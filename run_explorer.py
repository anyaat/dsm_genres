from flask import Flask, url_for
from dsm_genres import *

app_explorer = Flask(__name__)

app_explorer.register_blueprint(genre)

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app_explorer.jinja_env.globals['url_for_other_page'] = url_for_other_page

if __name__ == '__main__':
    app_explorer.run()

