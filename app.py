import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView

from login import UsernameAndPasswordProvider
from models import engine
from models import User

app = Starlette()

admin = Admin(engine, title="Example: SQLAlchemy",
              base_url='/',
              auth_provider=UsernameAndPasswordProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key="qewrerthytju4")],
              )

admin.add_view(ModelView(User, icon='fas fa-user'))

admin.mount_to(app)
if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8030)
