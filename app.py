import uvicorn
from datetime import datetime
from sqlalchemy import extract
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin, ModelView
from login import UsernameAndPasswordProvider
from models import engine, User, Driver, session

app = Starlette()

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Admin setup
admin = Admin(
    engine,
    title="Taxi Bot Admin",
    base_url='/',
    auth_provider=UsernameAndPasswordProvider(),
    middlewares=[Middleware(SessionMiddleware, secret_key="qewrerthytju4")],
)


# 🔹 **Custom Model Views**
class CustomUserModelView(ModelView):
    """🔍 Allow searching users by ID & username in Admin Panel"""
    column_searchable_list = ['user_id', 'username']


class CustomDriverModelView(ModelView):
    """🚖 Manage drivers, searchable by telegram_id, name, or route"""
    column_searchable_list = ['telegram_id', 'full_name', 'route']
    column_list = ['id', 'telegram_id', 'full_name', 'route', 'queue', 'client_count', 'date_added']


# 🔹 **Register models in the Admin Panel**
admin.add_view(CustomUserModelView(User, engine))
admin.add_view(CustomDriverModelView(Driver, engine))


@app.route("/statistics")
async def statistics(request: Request):
    """📊 User statistics for the current month"""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Ensure session is scoped properly
    with session.begin():
        users = session.query(User).filter(
            User.date_adding.isnot(None),
            extract('month', User.date_adding) == current_month,
            extract('year', User.date_adding) == current_year
        ).all()

    user_list = [{
        "id": user.id,
        "user_id": user.user_id,
        "username": user.username,
        "date_adding": user.date_adding,
        "last_permission_granted": user.last_permission_granted
    } for user in users]

    return templates.TemplateResponse("statistics.html", {
        "request": request,
        "count": len(users),
        "users": user_list
    })


# Mount Admin to the Starlette app
admin.mount_to(app)

# Run the app
if __name__ == '__main__':
    uvicorn.run(app, host="t.feniks.best", port=8060)
