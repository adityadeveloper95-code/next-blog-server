import os

project_env = os.getenv("PROJECT_ENV", "dev").lower()

if project_env == "prod":
    from .prod import *  # noqa: F403
elif project_env == "test":
    from .test import *  # noqa: F403
else:
    from .dev import *  # noqa: F403

