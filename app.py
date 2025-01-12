import uvicorn
from datetime import datetime
from sqlalchemy import extract
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.views import CustomView

from login import UsernameAndPasswordProvider
from models import engine, User, session

app = Starlette()

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Admin setup
admin = Admin(engine, title="Example: SQLAlchemy",
              base_url='/',
              auth_provider=UsernameAndPasswordProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key="qewrerthytju4")],
              )


# Extend ModelView to include search functionality ONLY by user_id
class CustomUserModelView(ModelView):
    column_searchable_list = ['user_id']  # Only allow searching by user_id


# Adding Custom View for User (pass icon as a keyword argument)
admin.add_view(CustomUserModelView(User, engine))


# Helper function to get users by user_id or date_adding
def get_users_by_user_id(session, user_id=None, current_month=None, current_year=None):
    query = session.query(User)

    if user_id:
        query = query.filter(User.user_id == user_id)

    if current_month and current_year:
        query = query.filter(
            User.date_adding.isnot(None),
            extract('month', User.date_adding) == current_month,
            extract('year', User.date_adding) == current_year
        )

    return query.all()


# Route for statistics with optional search by user_id
@app.route("/statistics")
async def statistics(request: Request):
    user_id_param = request.query_params.get("user_id", None)

    # Convert user_id_param to integer if it's provided
    user_id_param = int(user_id_param) if user_id_param else None

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    with session:
        # Fetch users by user_id if provided, otherwise fetch users for the current month and year
        users = get_users_by_user_id(session, user_id=user_id_param, current_month=current_month,
                                     current_year=current_year)

    print("Users fetched:", users)  # Debugging line

    user_list = [{"id": user.id, "user_id": user.user_id, "username": user.username, "date_adding": user.date_adding,
                  "last_permission_granted": user.last_permission_granted}
                 for user in users]
    user_count = len(users)

    return templates.TemplateResponse("statistics.html", {
        "request": request,
        "count": user_count,
        "users": user_list
    })


# Mount Admin to the Starlette app
admin.mount_to(app)

# Run the app
if __name__ == '__main__':
    uvicorn.run(app, host="k.feniks.best", port=8050)
