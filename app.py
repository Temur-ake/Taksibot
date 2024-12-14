import uvicorn
from datetime import datetime
from sqlalchemy.orm import Session
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

# Adding User Model to Admin
admin.add_view(ModelView(User, icon='fas fa-user'))


@app.route("/statistics")
async def statistics(request: Request):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    with session:
        users = session.query(User).filter(
            User.date_adding.isnot(None),
            extract('month', User.date_adding) == current_month,
            extract('year', User.date_adding) == current_year
        ).all()

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
